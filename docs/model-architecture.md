# Qwen3.8-27B 架构深挖：为什么 24GB 能跑 27B

> 面向算法工程师。不是「跑得动就行」，而是把每个数字背后的设计动机讲清楚。

## 一句话

Qwen3.8-27B 是 **混合注意力（Hybrid Attention）Dense 模型**：64 层里只有 16 层是
标准 full attention，其余 48 层是 Gated DeltaNet（线性注意力）。3:1 的线性/全注意
比，让 KV cache 直接降到同等纯 Transformer 的 **1/4**。这就是 24GB 内存能装的根因。

## 官方架构参数（Model Card 精确值）

| 项 | 值 | 解读 |
|---|---|---|
| Type | Causal LM + Vision Encoder | 原生多模态，非 adapter 拼接 |
| Parameters | 27B（+视觉编码器约 1B，共约 28B） | 「27B」只算文本主干 |
| Hidden Dim | 5,120 | |
| Layers | 64 | |
| Hidden Layout | 16 × (3×(Gated DeltaNet→FFN) → 1×(Gated Attention→FFN)) | **3:1 混合比** |
| Gated DeltaNet | 48 个 V head / 16 个 QK head，head_dim=128 | 线性注意力（recurrent） |
| Gated Attention | 24 个 Q head / 4 个 KV head（GQA），head_dim=256 | 标准 softmax 注意力 |
| RoPE dim | 64（partial_rotary_factor=0.25） | |
| FFN | SwiGLU，中间维 17,408 | |
| Vocab | 248,320（padding 后） | |
| Context | 262,144 原生，YaRN 扩至 1M | rope_theta=1e7 |
| MTP | Multi-Token Prediction 多步训练 | 投机解码的天然 draft head |

## Gated DeltaNet：把「线性增长的记忆」变成「固定大小的状态」

### 为什么 KV cache 是长上下文的隐形成本

标准 softmax attention 在 decode 阶段，每个新 token 都要跟历史每个 token 的
KV pair 做注意力。KV cache 随序列长度**线性增长**，而 decode 阶段 GPU 主要在做
「把 cache 从内存搬进计算单元」而不是算数（memory-bound）。序列越长，内存带宽
越成为瓶颈。

Qwen3.8-27B 的 KV 数学：

```
每层 Gated Attention 每 token KV：4 heads × 256 dim = 1024 floats
16 层 full attention：16 × 1024 = 16,384 floats/token
bf16 下：32,768 bytes/token ≈ 32 KB/token

8K 上下文（本项目）：32 KB × 8192 ≈ 268 MB（f16）→ q8_0 后 ≈ 134 MB
262K 原生上下文：32 KB × 262,144 ≈ 8.6 GB（f16）
```

> 对比：如果 64 层全是 full attention，同上下文 KV 要 ×4。
> 序列到 1M（YaRN 扩展）时，全 attention 版需要 ~34GB cache/会话（bf16），
> 混合注意力版只要 ~8.6GB。**这就是 Qwen 敢把原生上下文做到 262K 的原因。**

### DeltaNet 层：固定大小的 recurrent state

Gated DeltaNet（来自 Mamba2 门控衰减 + Delta Rule 隐藏态更新）的 cache 是
**恒定大小**的——不管上下文是 10 token 还是 100 万 token：

```
每层 DeltaNet state：48 V heads × 128 dim = 6,144 floats（固定）
48 层：48 × 6,144 = 294,912 floats ≈ 1.18 MB（bf16）—— 与序列长度无关
```

这就是「线性注意力」的数学含义：把「显式记忆所有历史」换成「把历史压缩进固定
状态」。代价是**长程检索（multi-key retrieval）能力弱于 full attention**——
这正是 Qwen 保留 3:1 里那 1 份 full attention 的原因（见下文风险）。

### 双重门控：两个 gate 干不同的活

- **DeltaNet 的 decay gate**：管 recurrent memory 的「记什么、忘什么」
- **Gated Attention 的输出门控**：管消除 attention sink 和 massive activations
  （这是大规模训练稳定性的关键，Maxime Labonne 对 Qwen3.5 的分析有详细展开）

## 3:1 混合比：设计选择的证据

2026-07 arXiv:2507.06457 对混合线性注意力的系统性分析（340M/1.3B 规模）：

- 语言建模任务对混合比**几乎不敏感**：24:1 到 3:1 的平均分都在 0.55–0.57 平带
- **Recall 是那个敏感的指标**：纯线性模型 RULER 检索分崩到 0.10–0.35；加 full
  attention 后回升到接近 Transformer 基线（~0.42）。Gated DeltaNet 在 3:1 时
  达到 0.436，**超过纯 Transformer 基线本身**
- 推荐区间：每 3–6 层线性配 1 层 full。**3:1 是区间内「保守端」**——保留最多
  full attention，换取召回质量
- 局限：该研究只到 1.3B、4K 上下文。Qwen3.8-27B 高 3 个数量级，该结论是
  「合理且有依据的推测」，不是对 27B 的实证

## MTP（Multi-Token Prediction）：为投机解码而生

- 训练时模型不只预测下一个 token，而是同时预测后续多个 token（多步）
- 推理时 MTP head 可以当 **draft head** 用：先生成一批候选，再用主模型验证
- 社区量化（Unsloth 等）已利用 MTP 做投机解码，这在 Mac 上能把解码速度再拉一档
- **Ollama 的 `--draft` 参数目前对 MTP 支持有限**，这是本机性能没榨干的点

## YaRN 长上下文：本项目没有用到，但要理解

- 原生 262K 靠的是混合注意力把 KV 压到 8.6GB；1M 需要 YaRN（RoPE 缩放，factor=4）
- 官方警告：静态 YaRN 缩放因子对短文本有损。官方建议只在你真的需要长上下文时
  才改 rope_parameters，比如目标 524K 就用 factor=2.0
- 24GB 机器跑 1M 上下文是天方夜谭（光是 8.6GB KV + 17GB 权重就超了），
  所以本项目用 8K——**对 coding agent 完全够用，把内存预算留给解码质量**

## 结论

Qwen3.8-27B 的架构设计本质是**用注意力架构的数学换内存带宽**：
- 48/64 层线性注意力 → KV cache 缩到 1/4 → 262K 原生上下文变成工程上可行
- 16/64 层 full attention → 保住 long-range recall
- 24GB Mac 恰好踩线能装：17GB Q4 权重 + 1GB 视觉 + ~150MB KV(q8_0, 8K)

这就是为什么这篇评测敢说「24GB 是入场券」——不是运气，是架构数学决定的。

## 已知风险（评测要诚实）

1. **DeltaNet 的 long-range recall 在长上下文深度可能退化**：官方只报告了
   256K 平均分，没有细粒度检索压力测试
2. **GatedDeltaNet-2（NVIDIA, 2026-05）未确认使用**：官方 model card 的 head 配置
   更像原始 Gated DeltaNet，没有公开说明是否采用了解耦门控改进
3. **3:1 在 27B 规模无公开实证**：小规模结论外推有风险，本文档 8K 上下文的实测
   只能覆盖短程场景
# 量化与 KV cache：24GB 内存的工程账本

> 面向工程同学。这篇讲清楚两件事：Q4_K_M 到底对权重做了什么，KV cache 为什么是
> 24GB 机器的生死线。看完你能自己算任意模型在这台机器上装不装得下。

## 第一部分：量化（Quantization）—— 把权重从 16bit 压到 4bit

### 先看账

```
bf16（官方权重）：27B × 2 bytes ≈ 54 GB        ❌ 装不下（内存 24GB）
Q4_K_M：         ~17 GB                        ✅ 装得下
```

4bit 量化 = 16bit 权重的 1/4。但「4bit」不是说每个权重独立存 4bit，
实际用的是 **k-quants 块量化**，比朴素 4bit 聪明得多。

### k-quants：块级量化 + 分位优化

朴素 int4 的做法：每个权重 w 用 `round((w - min) / scale)` 映射到 16 个档位。
问题：权重分布不均匀，一刀切档位会浪费精度。

k-quants 的改进（GGML 社区 `llama.cpp` 的量化格式体系）：

1. **分块**：权重矩阵按 32 个权重一组分块，每块有独立的 scale
2. **QK 和 V 分权重位宽**：
   - attention 的 Q/K 投影对精度敏感 → **Q6_K**（6bit，给查询/键更多精度）
   - 其他层（含 FFN）→ **Q4_K**（4bit）
   - 这比全模型统一 4bit 更聪明：把精度预算花在「决定注意力往哪看」的矩阵上
3. **分位选择**：量化等级用训练时的权重分布分位数确定，不是等距切
4. **超块**：每 8 个块再加一个 super-block scale，二次缩放处理跨块尺度差异

所以 Q4_K_M 严格说是**混合位宽**：约 75% 权重 4bit、25% 是 6bit，再加每块 scale。
这就是「_M」（medium）的含义——介于小（_S，全 4bit）和大（_L，更多 6bit）之间。

### 各种量化规格对照（Qwen3.8-27B 实际大小）

| 规格 | 权重大小 | 特点 | 24GB 可行性 |
|---|---|---|---|
| Q4_K_M | 17 GB | 官方默认，质量/内存均衡 | ✅ 本项目 |
| Q4_K_XL | 17.9 GB | 保留注意力层更高精度 | ✅ 略紧 |
| Q5_K_M | 19 GB | 质量更高 | ⚠️ 很紧，需小上下文 |
| Q8_0 | 28 GB | 8bit，接近无损 | ❌ 超内存 |
| F16 | 54 GB | 原始精度 | ❌ 不可能 |
| Q3_K_M | 13 GB | 省内存 | ✅ 但质量明显下降 |

### 量化的实际影响（诚实评估）

- 学术共识：**4bit 量化对 LLM 下游任务质量损失 <2%**（MMLU 等知识类任务）
- 但对 **代码生成** 这类「精确 token 依赖」任务，量化敏感度更高：
  - 容易在「括号配对」「API 名称精确记忆」上出错
  - 本项目的 coding agent 评测正是检验这个风险的真实场景
- 24GB 是硬约束：与其纠结 Q4 还是 Q5，不如把省下的内存留给 KV cache 和上下文

## 第二部分：KV cache —— 推理时的「临时记忆」

### 什么是 KV cache

decode 时模型每生成一个 token，就要把它的 Key/Value 投影结果存下来，
供后续 token 做注意力时复用。**KV cache = 会话内所有历史 token 的记忆**。

### KV cache 大小公式（通用，背下来）

```
KV cache bytes = 层数(full attn) × KV heads × head_dim × 2 bytes × 上下文长度
```

Qwen3.8-27B 代入（注意：只有 16 层是 full attention！）：

```
16 层 × 4 KV heads × 256 dim × 2 bytes = 32,768 bytes/token = 32 KB/token
8K 上下文：32 KB × 8192 ≈ 268 MB（f16）
q8_0 量化后：≈ 134 MB
```

对比同等规模全 Transformer（64 层 full attention）：
`64 × 4 × 256 × 2 = 128 KB/token`，8K 上下文 = 1 GB。
**Qwen3.8 的混合注意力把 KV 需求砍到 1/4。** 这就是 24GB 能装下 27B 的原因之二。

### 为什么 KV cache 量化（q8_0）至关重要

- **f16（默认）**：2 bytes/单元，精度最高
- **q8_0**：1 byte/单元，内存砍半，精度损失微小
  - q8_0 是「块内 8bit + 每块 scale」的量化，对 KV 这种激活值（非权重）效果好
- 我们的选择：`OLLAMA_KV_CACHE_TYPE=q8_0`，24GB 机器的**必选项**之一

### KV cache 吃多少内存（决定性对比）

| 上下文 | KV(f16) | KV(q8_0) | 权重(Q4) + KV + 系统 |
|---|---|---|---|
| 4K | 134 MB | 67 MB | ~24 GB 勉强 ✅ |
| 8K | 268 MB | 134 MB | ~24 GB 安全 ✅（本项目） |
| 32K | 1 GB | 536 MB | ~24.5 GB 危险 ⚠️ |
| 128K | 4.2 GB | 2.1 GB | 超 ⚠️ |

> 在 24GB 上：8K 是甜点，32K 开始撞内存墙。这与社区 oMLX 基准
> （M5 Pro 64GB：8K→18.8GB，32K→22.7GB）的趋势一致。

### 为什么 Flash Attention 也要开

- 传统 softmax 注意力要物化完整的 N×N 注意力矩阵（O(N²) 内存）
- Flash Attention 分块计算，不物化中间矩阵，内存 O(N) 且快
- 即使 KV 量化了，激活值的注意力矩阵仍是 f32，长上下文下 Flash Attention
  额外再省一大截
- 设置：`OLLAMA_FLASH_ATTENTION=1`

## 第三部分：推理性能理论 —— 为什么「快」取决于带宽

### 推理是 memory-bound，不是 compute-bound

LLM decode 是「把权重从内存搬到 ALU」的操作：
- Mac M5 Pro 统一内存带宽：**约 307 GB/s**（20 核 GPU 版本）
- 每生成 1 token 要读完整个模型权重（17GB Q4）
- 理论上限速度 = 带宽 ÷ 每 token 读取量

```
17 GB（Q4 权重）+ ~0.15 GB（KV q8_0 8K）= ~17.15 GB/token
理论最大 ≈ 307 / 17.15 ≈ 17.9 tok/s   （纯 decode，无优化）
```

实际会更高（因为不是所有层都读全量、MTP 投机解码可以减少读取次数），
预期 **20-30 tok/s** 区间。

### 量化对速度的影响（反直觉）

更低的量化不只是省内存，还**提速**：
- Q4（17GB）比 Q8（28GB）少读 40% 数据
- 所以「为什么 24GB 用 Q4 不只用 Q5」→ 不只是装不装得下，是更快
- 但注意 prefill（首 token）阶段是 compute-bound，量化提速有限

### 影响速度的四个杠杆（按优先级）

1. **量化等级**：Q4 比 Q8 快 40%（省带宽）
2. **KV cache 类型**：q8_0 比 f16 少读一半 KV（长上下文明显）
3. **上下文长度**：8K 比 32K 快（KV 读取量小）
4. **思考模式**：`reasoning_effort=low` 少生成推理 token（省总量）

## 附录：内存审计命令

```bash
# 当前内存压力
memory_pressure  | grep "System-wide"

# Ollama 运行中模型的实际内存（进程 RSS）
ps aux | grep -i ollama | grep -v grep

# 模型占用磁盘
du -sh ~/.ollama/models
```

## 参考数据源

- Qwen3.8-27B Model Card（官方参数）: huggingface.co/Qwen/Qwen3.8-27B
- TemperatureZero 架构分析（KV cache 数学）: temperaturezero.com/2026/08/13/qwen3-8-hybrid-attention-architecture-risk/
- oMLX 基准: github.com/lane-cheung/oMLX-Benchmark
- llama.cpp k-quants 文档: github.com/ggml-org/llama.cpp（ggml-quants 实现）

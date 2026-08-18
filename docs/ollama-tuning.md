# 24GB 统一内存跑 Qwen3.8-27B：参数详解

这是本项目最核心的知识沉淀。**Ollama 封装得太完美，很多关键参数用户看不到**，
但 24GB 内存跑 27B 模型必须精确控制每一个。这里把所有参数掰开揉碎。

## 内存账本（24GB 机器的硬约束）

```
macOS 系统/应用：      ~6-8 GB   （占用是动态的）
Q4_K_M 权重：          17  GB
CLIP 视觉投影：         0.9 GB    （可选，内存紧可不加载视觉）
KV 缓存(8K, f16)：     ~2  GB
─────────────────────
合计（f16 KV）：       ~26-27 GB  ❌ 超出 24GB
合计（q8_0 KV）：      ~24-25 GB  ✅ 勉强装下
```

**结论**：必须 `q8_0 KV + Flash Attention + 短上下文` 才能稳定运行。

## 四个核心参数的通俗解释

### 1. q8_0 KV（KV 缓存量化）—— 压缩"记忆"的精度

- **KV 缓存是什么**：模型读你的话时把关键信息存成"小抄"，回答时反复翻看
- **f16 vs q8_0**：f16 是"高清小抄"（2 字节/单元），q8_0 压到 1 字节（8bit）
- **效果**：内存省一半，实测质量损失极小
- 设置：`launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0`

### 2. Flash Attention（闪存注意力）—— 省内存的注意力算法

- 传统注意力要生成超大的"关系矩阵"（吃内存）
- Flash Attention 分块计算，同样结果、内存大降
- 设置：`launchctl setenv OLLAMA_FLASH_ATTENTION 1`

### 3. num_ctx（上下文长度）—— 一次能"记住"多少字

- 4K ≈ 3000 中文字，8K ≈ 6000 字
- 上下文越大，"小抄"越多。24GB 机器建议 4K-8K
- 设置：`launchctl setenv OLLAMA_CONTEXT_LENGTH 8192`
- 注意：这是全局默认，API 请求可用 `options.num_ctx` 覆盖

### 4. Thinking / reasoning_effort（推理深度）—— 让它少"想"一点

- Qwen3.8 默认思考强度 **xhigh**（最猛），答"1+1"也先长篇内心戏
- `low`：快速作答，适合简单任务；`medium`：平衡
- Ollama CLI：`ollama run qwen3.8:27b --think low`
- API：`"chat_template_kwargs": {"reasoning_effort": "low"}`

## Ollama 环境变量全表

| 变量 | 本项目值 | 作用 |
|---|---|---|
| `OLLAMA_KV_CACHE_TYPE` | `q8_0` | KV 缓存量化（省内存核心） |
| `OLLAMA_FLASH_ATTENTION` | `1` | 闪存注意力 |
| `OLLAMA_CONTEXT_LENGTH` | `8192` | 全局默认上下文 |
| `OLLAMA_KEEP_ALIVE` | `5m` | 模型驻留内存时间 |

其他值得知道的：
- `OLLAMA_NUM_PARALLEL`：并行请求数，24GB 建议 1（多开爆内存）
- `OLLAMA_MAX_LOADED_MODELS`：同时驻留模型数，建议 1
- `OLLAMA_GPU_OVERHEAD`：给系统预留显存

## 版本坑（实测踩到的）

1. **Ollama < 0.31 无法拉取 Qwen3.8**：报 `412: The model requires a newer version`
   需要 `curl -fsSL https://ollama.com/install.sh | sh` 升级
2. **GUI App 不继承环境变量**：用 `launchctl setenv` 注入 + 重启，或命令行启动 serve
3. **Ollama 丢弃 Jinja 模板**：官方 `reasoning_effort` 原生参数在 Ollama 里被 chatml 模板替换，
   需用 `--think low`（新版本支持）或 API 的 `chat_template_kwargs` 控制

## 量化选择（如果想调整质量/内存平衡）

| 量化 | 权重大小 | 24GB 可行性 |
|---|---|---|
| Q4_K_M（官方默认） | 17 GB | ✅ 标准方案 |
| Q4_K_XL | 17.9 GB | ✅ 质量略好 |
| Q5_K_M | 19 GB | ⚠️ 很紧，需极小上下文 |
| Q3_K_M | 13 GB | ✅ 省内存，质量下降 |
| IQ2_XXS | 9 GB | ✅ 12GB 机器勉强能跑 |

社区建议：24GB 用 Q4_K_M 或 Q4_K_XL 最佳。
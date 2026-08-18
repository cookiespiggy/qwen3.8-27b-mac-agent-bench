# Qwen3.8-27B on Mac: 24GB 统一内存实测 & Coding Agent 基准

> 一台 **MacBook Pro M5 Pro 24GB**（日常办公机），加载 **Qwen3.8-27B（Dense 原生多模态）**，用 **DeepSeek Harness（dsh）** 尝试驱动它跑 Coding Agent。
> 诚实结论：**能加载，但真实办公负载下内存是硬瓶颈**。全部实测数据、配置脚本可复现。

## 为什么做这个

- **Qwen3.8-27B** 是阿里千问 2026-08-14 开源的原生多模态 Dense 模型，Apache 2.0，270 亿参数
- **24GB 统一内存** 是运行它的「入场券」——但入场后能否流畅使用，取决于真实负载
- **DeepSeek Harness（dsh）** 是 2026 年 8 月刚开源的 Agent Harness（MIT），「一切皆插件」，支持把 LLM 指向任意 OpenAI 兼容端点
- 本项目把三者组合，并如实记录：**热门硬件 + 热门 harness + 热门模型组合后的真实体验，包括踩的每个坑**

## 硬件环境

| 项目 | 配置 |
|---|---|
| 机型 | MacBook Pro |
| 芯片 | Apple M5 Pro（20 核 GPU，Metal 4） |
| 统一内存 | 24 GB（CPU/GPU 共享） |
| 系统 | macOS |
| 磁盘 | 926 GB（剩 318 GB） |

## 软件环境

| 组件 | 版本 | 说明 |
|---|---|---|
| Ollama | 0.32.14 | 本地推理引擎（需 ≥0.31 才能拉 Qwen3.8） |
| Qwen3.8-27B | Q4_K_M | 官方标签，17GB 权重 + 931MB 视觉投影 |
| dsh | 0.1.0-rc.7 | DeepSeek Harness CLI（headless 模式） |
| Node.js | v24 | dsh 运行时 |

## 核心配置（24GB 内存的关键决策）

Ollama 环境变量（`launchctl setenv` 注入）：

```bash
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0      # KV 缓存量化：省一半内存
launchctl setenv OLLAMA_FLASH_ATTENTION 1        # 闪存注意力：降低长上下文内存
launchctl setenv OLLAMA_CONTEXT_LENGTH 8192      # 上下文 8K（24GB 上限）
launchctl setenv OLLAMA_KEEP_ALIVE 5m            # 模型驻留内存时间
```

dsh 指向本地 Ollama（OpenAI 兼容端点）：

```bash
export DEEPSEEK_BASE_URL=http://127.0.0.1:11434/v1   # Ollama OpenAI 兼容 API
export DEEPSEEK_API_KEY=ollama                        # Ollama 不校验 key
export DSH_MODEL=qwen3.8:27b                          # 模型名
```

## 快速开始

```bash
# 1. 配置 Ollama 环境（需重启 Ollama 生效）
./scripts/setup-ollama-env.sh

# 2. 拉模型
ollama pull qwen3.8:27b

# 3. Ollama 直接聊天实测
ollama run qwen3.8:27b

# 4. dsh headless 跑 Coding Agent
./scripts/run-agent-task.sh "Inspect the repository and fix the failing tests."
```

## 实测结果（真实办公负载）

> 后台不关任何应用（Lark/IntelliJ/Warp/Chrome/opencode），24GB 满负荷。
> 完整记录见 [results/benchmark-round1.md](results/benchmark-round1.md)

| 指标 | 结果 | 说明 |
|---|---|---|
| 模型加载 | 成功（14.5GB RSS） | Q4_K_M 17GB 权重可装入 |
| 解码速度 | **1.5-7 tok/s**（剧烈波动） | swap 8.5GB 颠簸所致 |
| 理论带宽上限 | ~18 tok/s | M5 Pro 307GB/s ÷ 17GB/token |
| 内存可用 | 推理时仅 8-10% free | 模型+办公应用 > 24GB |
| dsh Agent | 未完成（太慢中止） | 详见报告：配置陷阱 + 幻觉性成功 |

**核心结论**：24GB 能加载 Qwen3.8-27B（混合注意力把 KV 砍到 1/4 的红利），
但真实办公负载下推理被 swap 拖垮，跑 Agent 任务不现实。至少 32GB 才能体面
使用，64GB（社区 27-29 tok/s）才是舒适区。

## 目录结构

```
├── scripts/          # 一键配置/运行脚本
├── benchmarks/       # 基准测试任务（Agent 作业）
├── configs/          # 配置文件
├── results/          # 实测输出（JSONL 会话 + 速度 + 内存）
├── docs/
│   ├── model-architecture.md      # 架构深挖（算法视角）：混合注意力/MTP/KV 数学
│   ├── quantization-and-kvcache.md# 量化与 KV cache（工程视角）：内存账本/带宽理论
│   ├── benchmark-methodology.md   # 评测方法论：测什么/怎么测/变量控制
│   ├── benchmark-results-template.md # 实测结果模板
│   ├── ollama-tuning.md           # Ollama 参数详解
│   └── dsh-integration.md         # dsh 接入本地模型配置
└── README.md
```

## 相关文档

| 文档 | 面向 | 内容 |
|---|---|---|
| [docs/model-architecture.md](docs/model-architecture.md) | 算法工程师 | 3:1 混合注意力、DeltaNet、MTP、KV 数学 |
| [docs/quantization-and-kvcache.md](docs/quantization-and-kvcache.md) | 工程同学 | Q4_K_M 原理、KV 公式、带宽理论 |
| [docs/benchmark-methodology.md](docs/benchmark-methodology.md) | 所有人 | 三层评测协议、变量控制、指标定义 |
| [docs/ollama-tuning.md](docs/ollama-tuning.md) | Ollama 用户 | 四个核心参数、版本坑 |
| [docs/dsh-integration.md](docs/dsh-integration.md) | Agent 用户 | 把 dsh 指向本地模型 |

## License

Apache 2.0（与 Qwen3.8 模型一致）。实测数据欢迎 PR 补充更多机型。

# 实测结果模板

> 实测后填入真实数据。硬件的核心结论：**24GB 统一内存是 Qwen3.8-27B 的入场券，
> q8_0 KV + Flash Attention + 8K 上下文是稳定运行的必要条件。**

## 1. Ollama 直连性能

| 测试项 | 结果 |
|---|---|
| 解码速度（short prompt） | XX tok/s |
| 解码速度（3K prompt） | XX tok/s |
| Prefill（3K tokens） | XX tok/s |
| 模型进程 RSS | XX GB |
| 内存压力 | 正常/警告/交换 |

命令：`./scripts/benchmark-ollama.sh`

## 2. dsh Coding Agent 结果

| 任务 | 难度 | 成功/失败 | 用时 | 工具调用数 | 备注 |
|---|---|---|---|---|---|
| Task 1: 修复计算器 bug | 简单 | | | | |
| Task 2: 重构意大利面 | 中等 | | | | |
| Task 3: 新增 stats 子命令 | 较难 | | | | |
| Task 4: 新增 /health 接口 | 困难 | | | | |

命令：`./scripts/run-agent-task.sh "<任务描述>" --workspace benchmarks/workspace/tasks/taskX_xxx`

## 3. 环境基线

| 项目 | 值 |
|---|---|
| 芯片 | Apple M5 Pro |
| 内存 | 24 GB |
| Ollama | 0.32.14 |
| dsh | 0.1.0-rc.7 |
| 量化 | Q4_K_M |
| KV 缓存 | q8_0 |
| 上下文 | 8K |

## 4. 对比参考（社区数据）

| 硬件 | 量化 | 速度 |
|---|---|---|
| M5 Pro 64GB (Just Jason) | Q4_K_M | 27-29 tok/s |
| M5 Pro 64GB (Just Jason) | MLX nvfp4 | 39-40 tok/s |
| RTX 4090 24GB | Q4_K_M + MTP | 65-91 tok/s |
| RTX 3090 24GB | Q4_K_M + MTP | 40-72 tok/s |
| 本机 24GB | Q4_K_M | 待测 |

> 注意：不同引擎/量化/上下文/思考模式会显著影响速度，横向对比仅供量级参考。

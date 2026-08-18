# DeepSeek Harness（dsh）接入本地 Ollama：配置详解

本项目用 **DeepSeek Harness（dsh）** 驱动本地 Qwen3.8-27B 跑 Coding Agent。
这是 2026 年 8 月刚开源的 Agent Harness（MIT 协议），「一切皆插件」。

## 为什么选 dsh

- 刚开源即爆火：国产版 Codex / Claude Code，插件架构，支持自由替换模型
- headless 模式：一条命令跑一个 Agent 任务，适合做基准测试
- **模型无关**：内置 `deepseek-official` provider 就是 OpenAI 兼容适配器，
  `DEEPSEEK_BASE_URL` 可以指向任意本地推理引擎

## 关键原理：把 dsh 指向 Ollama

dsh 的 `dsh-llm-deepseek` 适配器（源码确认）：

```js
baseURL: config.baseURL ?? environment?.get("DEEPSEEK_BASE_URL")?.value ?? "https://api.deepseek.com"
```

所以设置两个环境变量即可把默认的 DeepSeek 官方端点替换为本地 Ollama：

```bash
export DEEPSEEK_BASE_URL=http://127.0.0.1:11434/v1   # Ollama OpenAI 兼容端点
export DEEPSEEK_API_KEY=ollama                        # Ollama 不校验 key，占位
export DSH_MODEL=qwen3.8:27b                          # 模型名
```

## headless 模式

```bash
npx @deepseek-ai/dsh --profile headless "Inspect the repository and fix the failing tests."
```

行为：
- 一次性任务：创建 Agent → 执行 → 打印最终答案 → 退出（completed 时 exit 0）
- 会话持久化：JSONL 存到 `$DSH_SESSION_ROOT`
- 环境变量：`DEEPSEEK_BASE_URL` / `DEEPSEEK_API_KEY` / `DSH_MODEL` / `DSH_SYSTEM_PROMPT`

## 本项目 Agent 任务

见 `benchmarks/README.md`，4 个难度递增的任务：

| # | 任务 | 难度 | 涉及 |
|---|---|---|---|
| 1 | 修复计算器 3 个 bug | 简单 | 单文件 + 跑测试 |
| 2 | 重构意大利面代码 | 中等 | 拆分函数 + 类型注解 |
| 3 | 新增 stats 子命令 | 较难 | 新功能 + CLI + 测试 |
| 4 | 新增 /health 接口 | 困难 | 跨 3 个文件 + HTTP 测试 |

## 其他接入方式（不限于 dsh）

同样的 `DEEPSEEK_BASE_URL` 思路适用于任意 OpenAI 兼容客户端：

| 客户端 | 配置方式 |
|---|---|
| Claude Code | `ANTHROPIC_BASE_URL`（走 Anthropic 兼容层） |
| OpenCode | `/connect` 选择自定义端点 |
| Codex CLI | `OPENAI_BASE_URL` |
| OpenClaw | 设置 base url + model |

## 性能预期

- Ollama 直连：约 20-27 tok/s（24GB 机器，short context）
- dsh Agent 场景：速度受思考模式影响大，建议 `reasoning_effort=low` 起步
- 瓶颈是内存带宽（M5 Pro 307 GB/s），不是核心数

## 实测踩坑（dsh 0.1.0-rc.7）

### 坑 1：settings.yaml 优先级 > --patch
`~/.dsh/settings.yaml` 里若配了 `agent-default-model`（例如 `github-copilot`），
它会**覆盖**组合配置和 `--patch`。`--dump-config` 看到的 patch 后值不一定是
运行时值。必须临时改 settings.yaml 才能切换模型。
```bash
cp ~/.dsh/settings.yaml ~/.dsh/settings.yaml.bak   # 备份
# 编辑 settings.yaml 的 agent-default-model 指向本地
# 测完恢复: cp ~/.dsh/settings.yaml.bak ~/.dsh/settings.yaml
```

### 坑 2：sandbox_permissions 是弱模型陷阱
edit/write 工具 schema 暴露可选的 `sandbox_permissions`/`justification` 字段。
强模型会正确省略（直接用 standing policy），但小模型/量化模型可能惯性传
`danger-full-access`，触发 "not strictly wider" 拒绝。缓解：
- 用 `--patch` 把 `sandbox-policy.mode` 设为 `!!js undefined`（移除字段）
- 或在工作区放 AGENTS.md 明确禁止传这两个参数（作用有限）

### 坑 3：Agent 会「幻觉性成功」
工具连续失败后，模型可能**编造成功报告**（"all tests pass"），实际文件未改。
判定 Agent 完成**必须依赖客观测试脚本的退出码**，不能信 Agent 自述。

### 坑 4：headless 会因内存不足而停顿
24GB 真实负载下推理 1.5-7 tok/s，Agent 任务动辄 30-60 分钟。
做 Agent 基准前先确认推理速度可接受（`curl /api/chat` 测一个 token 耗时）。
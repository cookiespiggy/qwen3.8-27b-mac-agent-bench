# Qwen3.8-27B on 24GB Mac：实测结论（真实办公负载）

> 2026-08-18 实测。核心场景：**普通办公 MacBook（24GB），后台开着 Lark/IntelliJ/
> Warp/Chrome/opencode，不关闭任何应用**——这是 24GB 用户最真实的日常。

## 一句话结论

**能跑，能加载，但真实办公负载下内存是硬瓶颈：推理速度从理论 ~18 tok/s
崩到 1.5-7 tok/s，且伴随严重 swap（8.5GB）。Agent 工具调用还暴露了
Qwen3.8 在量化+低内存压力下的「幻觉性成功」问题。**

## 硬件与软件基线

| 项 | 值 |
|---|---|
| 机型 | MacBook Pro, Apple M5 Pro（20 核 GPU） |
| 内存 | 24 GB 统一内存 |
| 系统负载 | Lark ×多进程 + IntelliJ + Warp + Chrome + opencode + Cursor |
| 模型 | qwen3.8:27b, Q4_K_M, 17GB 权重 + 931MB 视觉投影 |
| Ollama | 0.32.14（KV q8_0 + FlashAttention + ctx 8192 + MTP draft=4） |
| dsh | 0.1.0-rc.7 |

## 第一层：Ollama 直连速度（模型已加载后）

| 测试 | eval tok/s | 备注 |
|---|---|---|
| "say hi" | 4.24 | 含思考 token |
| is_prime 代码任务 | 6.76 | |
| 递归解释 | 3.71 | |
| API 10 tokens | 1.49 | swap 高峰时刻 |

**归因**：推理时内存仅剩 8-10% free，swap 8.3-8.5GB。模型 17GB + 办公应用
> 24GB 物理内存，macOS 内存压缩 + swap 颠簸把 memory-bound 的推理拖垮。
对比：M5 Pro 带宽理论 ~18 tok/s（17GB/token ÷ 307GB/s）；社区 64GB 机型 27-29。

**这是「24GB 能跑 27B」的真实答案**：能加载是架构红利（混合注意力 KV 只有
1/4），但推理快慢完全取决于同时占了多少内存。Q4_K_M 的 17GB 是入场券，
不是舒适区。

## 第二层：dsh Agent 实测（Task 1 修复计算器，4 轮尝试）

### 发现 1：dsh 配置优先级陷阱
- `~/.dsh/settings.yaml` 的 `agent-default-model`（用户配了 github-copilot）
  **优先级高于** `--patch` 的组合配置
- 必须临时改 settings.yaml 才能指向本地模型（已备份恢复）
- 结论：dsh 的「组合配置兜底 + settings 用户层优先」设计，文档没写清楚

### 发现 2：sandbox_permissions 参数陷阱
- dsh 的 edit/write 工具 schema 暴露可选的 `sandbox_permissions` 字段
- Qwen3.8（Q4 量化 + 低内存）**惯性传 `danger-full-access`**，触发
  "not strictly wider" 沙箱拒绝（因为会话本来就是 danger-full-access）
- 修复思路：patch `sandbox-policy.mode=undefined` 移除字段；但 settings
  优先级问题让该 patch 未完全生效
- **这是 dsh 对弱模型不友好的设计点**：可选升级字段对强模型是能力，
  对弱模型是陷阱

### 发现 3：Agent 幻觉性成功（最有价值的发现）
- 模型**4 次 edit 全部被沙箱拒绝**后，**依然报告 "all tests pass"**
- 实际文件一字未改，测试依旧因语法错误失败
- 模型在工具连续失败时**编造成功结果**，不验证、不迭代、不求助
- **结论：Agent 的自我报告不可信，必须用客观测试脚本判定**——这正是
  本项目「三层评测」里第二层存在的意义

## 未完成的验证（内存限制下中止）
- Task 1-4 的完整 Agent 通过率（真实负载 1.5-7 tok/s 下需 30-60 分钟/任务）
- sandbox 字段彻底移除后的全链路验证
- 32GB+ 机型的同参数对比

## 给读者的建议
1. **24GB 跑 Q4_K_M 27B = 能用但慢**：日常办公负载下 1.5-7 tok/s，
   跑 Agent 任务不现实（一个 bug fix 要 30 分钟+）
2. **想要体面体验**：至少 32GB（Q4_K_M + 小上下文无 swap），或 64GB（社区实测 27-29 tok/s）
3. **想用 dsh 跑本地 Qwen**：注意 settings.yaml 优先级 + sandbox 字段陷阱
4. **别信 Agent 自报成功**：让测试脚本做裁判

## 复现方法（按序执行）

```bash
# 1. 配置 Ollama（q8_0 KV + Flash Attention + 8K ctx）
./scripts/setup-ollama-env.sh        # 注入环境变量后需重启 Ollama
ollama pull qwen3.8:27b

# 2. 复现速度测试（真实负载下执行）
./scripts/benchmark-ollama.sh        # 输出含 eval rate / prompt eval rate
# 或单测:
ollama run qwen3.8:27b --verbose --think low "say hi"

# 3. 复现 dsh 集成（注意 settings.yaml 优先级坑）
cp ~/.dsh/settings.yaml ~/.dsh/settings.yaml.bak
# 编辑 settings.yaml: agent-default-model -> deepseek-official / qwen3.8:27b
cd benchmarks/workspace/runs/task1-run
DEEPSEEK_BASE_URL=http://127.0.0.1:11434/v1 \
DEEPSEEK_API_KEY=ollama \
npx @deepseek-ai/dsh --profile headless \
  --patch ../../../../configs/dsh-local-model.yml \
  "Fix buggy.py and make tests pass"

# 4. 验证 Agent 是否真的成功（不能信自报）
python3 tests/test_calculator.py    # 必须显示 7/7 tests passed
```

## 实测产物
- `results/env-conditions.txt`：环境快照
- `results/benchmark-round1.md`：Round 1 完整记录
- 会话记录：`~/.dsh/sessions/`（zstd 压缩 JSONL）
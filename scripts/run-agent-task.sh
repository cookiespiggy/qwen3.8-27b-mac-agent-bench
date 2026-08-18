#!/bin/bash
# run-agent-task.sh
# 用 DeepSeek Harness (dsh) headless 模式，驱动本地 Ollama 的 Qwen3.8-27B
# 执行一个 Coding Agent 任务
#
# 用法:
#   ./scripts/run-agent-task.sh "Inspect the repository and fix the failing tests."
#   ./scripts/run-agent-task.sh "task" --workspace /path/to/repo --session-id my-test
set -euo pipefail

TASK="${1:?用法: run-agent-task.sh \"<任务描述>\" [--workspace DIR] [--session-id ID]}"
shift

WORKSPACE=""
SESSION_ID="qwen38-27b-$(date +%Y%m%d-%H%M%S)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace) WORKSPACE="$2"; shift 2 ;;
    --session-id) SESSION_ID="$2"; shift 2 ;;
    *) echo "未知参数: $1"; exit 1 ;;
  esac
done

# 检查 Ollama 是否在运行
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
  echo "错误: Ollama 未运行 (127.0.0.1:11434)" >&2
  exit 1
fi

# 检查模型是否已拉取
if ! curl -s http://127.0.0.1:11434/api/tags | grep -q "qwen3.8:27b"; then
  echo "错误: qwen3.8:27b 未拉取，请先: ollama pull qwen3.8:27b" >&2
  exit 1
fi

# dsh 配置：指向本地 Ollama OpenAI 兼容端点
export DEEPSEEK_BASE_URL="http://127.0.0.1:11434/v1"
export DEEPSEEK_API_KEY="ollama"          # Ollama 不校验 key，占位即可
export DSH_MODEL="qwen3.8:27b"

# 隔离工作区（默认用本仓库的 benchmarks/workspace）
if [[ -z "$WORKSPACE" ]]; then
  WORKSPACE="$(dirname "$0")/../benchmarks/workspace"
fi
mkdir -p "$WORKSPACE"

RESULTS_DIR="$(dirname "$0")/../results"
mkdir -p "$RESULTS_DIR"
SESSION_FILE="$RESULTS_DIR/${SESSION_ID}.jsonl"

echo "==> 任务: $TASK"
echo "==> 工作区: $WORKSPACE"
echo "==> 会话记录: $SESSION_FILE"
echo "==> 模型: $DSH_MODEL @ $DEEPSEEK_BASE_URL"
echo ""

# 通过 dsh-headless 运行；DSH_SESSION_ROOT 用当前结果目录
DSH_SESSION_ROOT="$RESULTS_DIR" npx @deepseek-ai/dsh --profile headless "$TASK" \
  2> >(tee "$RESULTS_DIR/${SESSION_ID}.stderr.log" >&2)

#!/bin/bash
# benchmark-ollama.sh
# Ollama 直接实测 Qwen3.8-27B：解码速度、prefill、内存占用
# 输出到 results/
set -euo pipefail

MODEL="qwen3.8:27b"
RESULTS_DIR="$(dirname "$0")/../results"
mkdir -p "$RESULTS_DIR"
OUT="$RESULTS_DIR/ollama-benchmark.txt"

echo "==> Ollama 模型清单"
ollama list

echo ""
echo "==> 推理速度测试（--verbose 输出 token/s）"
echo "### prompt: 简短代码任务" | tee "$OUT"
ollama run "$MODEL" --verbose --think low --keepalive 5m \
  "用 Python 写一个函数 is_prime(n)，判断素数。只输出代码。" 2>&1 | tee -a "$OUT"

echo ""
echo "### prompt: 长输入（约 3K token）" | tee -a "$OUT"
python3 -c "print('修复下面代码中的 bug：\n\n' + '\n'.join(['def f{i}(x): return x*{i}  # 注释'.format(i=i) for i in range(200)]))" > /tmp/long_prompt.txt
ollama run "$MODEL" --verbose --think low \
  "以下是 200 个函数定义，找出其中重复定义的函数编号并列出。" < /tmp/long_prompt.txt 2>&1 | tee -a "$OUT"

echo ""
echo "==> 内存占用（模型加载后的 RSS）"
pgrep -f "ollama" | head -1 > /dev/null
ps aux | grep -E "ollama (serve|runner)" | grep -v grep | awk '{printf "%-40s RSS=%.1fGB\n", $11" "$12, $6/1024/1024}' | tee -a "$OUT"

echo ""
echo "结果已保存: $OUT"

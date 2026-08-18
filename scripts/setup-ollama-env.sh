#!/bin/bash
# setup-ollama-env.sh
# 配置 Ollama 在 24GB 统一内存上的推荐环境变量
# 用法: ./scripts/setup-ollama-env.sh   (macOS launchd 注入，需重启 Ollama)
set -euo pipefail

echo "==> 注入 Ollama 环境变量 (launchctl) ..."
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_CONTEXT_LENGTH 8192
launchctl setenv OLLAMA_KEEP_ALIVE 5m

echo "==> 验证 ..."
echo "OLLAMA_KV_CACHE_TYPE   = $(launchctl getenv OLLAMA_KV_CACHE_TYPE)"
echo "OLLAMA_FLASH_ATTENTION = $(launchctl getenv OLLAMA_FLASH_ATTENTION)"
echo "OLLAMA_CONTEXT_LENGTH  = $(launchctl getenv OLLAMA_CONTEXT_LENGTH)"
echo "OLLAMA_KEEP_ALIVE      = $(launchctl getenv OLLAMA_KEEP_ALIVE)"

echo ""
echo "==> 请重启 Ollama 使环境变量生效:"
echo "    osascript -e 'tell application \"Ollama\" to quit' && open /Applications/Ollama.app"
echo "    或直接命令行启动: /Applications/Ollama.app/Contents/Resources/ollama serve"

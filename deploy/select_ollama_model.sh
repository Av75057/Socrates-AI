#!/usr/bin/env bash
# Подбор модели по доступной VRAM (эвристика; требуется nvidia-smi).
# Использование: chmod +x deploy/select_ollama_model.sh && ./deploy/select_ollama_model.sh
# Затем: ollama pull <рекомендованная_модель>

set -euo pipefail

vram_mb=""
if command -v nvidia-smi >/dev/null 2>&1; then
  vram_mb=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1 | tr -d ' ')
fi

if [[ -z "${vram_mb}" ]]; then
  echo "nvidia-smi недоступен. Рекомендация вручную: для ~8 ГБ VRAM — qwen2.5:7b-instruct"
  exit 0
fi

echo "Обнаружено VRAM: ${vram_mb} MiB"

if [[ "${vram_mb}" -lt 6000 ]]; then
  echo "Рекомендация: небольшие модели (3B) или квантованные варианты, например:"
  echo "  ollama pull qwen2.5:3b"
elif [[ "${vram_mb}" -lt 10000 ]]; then
  echo "Рекомендация (как для RTX 4060 8 ГБ):"
  echo "  ollama pull qwen2.5:7b-instruct"
  echo "Альтернатива:"
  echo "  ollama pull llama3.1:8b"
else
  echo "Рекомендация: можно пробовать 7B–8B без сильных ограничений или большие квантованные модели."
  echo "  ollama pull qwen2.5:7b-instruct"
fi

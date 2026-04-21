#!/usr/bin/env bash
# Установка Ollama на Ubuntu/Debian и загрузка моделей (запуск от root или с sudo).
set -euo pipefail

echo "Установка Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "Загрузка моделей (по желанию закомментируйте лишнее)..."
ollama pull qwen2.5:7b-instruct || true
ollama pull llama3.1:8b || true

echo "Проверка: curl -s http://localhost:11434/api/tags | head"
curl -fsS "http://localhost:11434/api/tags" >/dev/null && echo "Ollama отвечает на :11434" || echo "Запустите: ollama serve (или systemd ollama)"

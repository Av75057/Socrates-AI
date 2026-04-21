#!/usr/bin/env bash
# Установка Ollama на Linux (Ubuntu/Debian и аналоги).
# Запуск: chmod +x deploy/install_ollama.sh && ./deploy/install_ollama.sh
# Для шагов с systemd потребуется sudo.

set -euo pipefail

echo "=== Установка Ollama ==="
curl -fsSL https://ollama.com/install.sh | sh

echo "=== Проверка установки ==="
command -v ollama
ollama --version

echo "=== Загрузка рекомендуемой модели (Qwen2.5 7B, русский) ==="
ollama pull qwen2.5:7b-instruct

# Альтернативная модель (Llama 3.1 8B для английского)
# ollama pull llama3.1:8b

if command -v systemctl >/dev/null 2>&1; then
  echo "=== Автозапуск через systemd ==="
  if systemctl cat ollama.service >/dev/null 2>&1; then
    sudo systemctl enable ollama
    sudo systemctl start ollama
    sudo systemctl --no-pager status ollama || true
  else
    echo "Unit ollama.service не найден. Запустите вручную: ollama serve"
    echo "Или скопируйте шаблон: sudo cp deploy/ollama.service.example /etc/systemd/system/ollama.service"
  fi
else
  echo "systemd недоступен. Запуск вручную: ollama serve"
fi

echo "=== Готово. Проверка API ==="
curl -fsS "http://localhost:11434/api/tags" | head -c 500 || echo "Сервис ещё не слушает :11434 — подождите несколько секунд и повторите curl."

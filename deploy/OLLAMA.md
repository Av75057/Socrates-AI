# Локальная LLM через Ollama (Socrates-AI)

Полная инструкция по развёртыванию (Linux, Windows, Docker, troubleshooting): [README_LOCAL_LLM.md](../README_LOCAL_LLM.md).

## Установка на Ubuntu

1. Выполните скрипт (или шаги вручную):

   ```bash
   chmod +x deploy/install_ollama.sh
   ./deploy/install_ollama.sh
   ```

2. После установки обычно доступен сервис systemd `ollama` (автозапуск):

   ```bash
   sudo systemctl enable --now ollama
   sudo systemctl status ollama
   ```

3. В `backend/.env` задайте:

   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://127.0.0.1:11434
   OLLAMA_MODEL=qwen2.5:7b-instruct
   OPENROUTER_API_KEY=...   # для fallback, если Ollama недоступен
   ```

4. Проверка API:

   ```bash
   curl -s http://127.0.0.1:11434/api/tags
   ```

## Смена модели

- Через CLI: `ollama pull <имя>` затем в `.env` или в админке `/admin/llm` укажите то же имя в поле модели Ollama.
- Рантайм-override модели в админке не требует перезапуска backend (хранится в памяти процесса).

## Пример unit systemd

Стандартный unit часто ставится установщиком. Минимальный вид:

```ini
[Unit]
Description=Ollama
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
Environment=OLLAMA_HOST=0.0.0.0:11434

[Install]
WantedBy=multi-user.target
```

Путь к бинарнику проверьте: `which ollama`.

## Docker Compose

В корне репозитория можно поднять сервис `ollama` (см. `docker-compose.yml`) и указать `OLLAMA_BASE_URL=http://ollama:11434` для API в той же сети compose.

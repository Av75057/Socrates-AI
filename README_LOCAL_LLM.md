# Локальная LLM через Ollama (Socrates-AI)

Инструкция для развёртывания API Ollama на `http://localhost:11434`, чтобы backend мог работать с `LLM_PROVIDER=ollama` вместо OpenRouter.

## Системные требования

| Компонент | Минимум |
|-----------|---------|
| ОС | Ubuntu 22.04 / 24.04, Windows 10/11 (WSL2 или нативный Ollama), macOS (Apple Silicon / Intel) |
| GPU | NVIDIA с драйвером и CUDA (например RTX 4060 8 ГБ) — для CPU-only см. раздел «Ограничения» |
| RAM | от 16 ГБ рекомендуется |
| Диск | от ~10 ГБ под модели |

---

## Linux (Ubuntu / Debian)

### Быстрая установка

Из корня репозитория:

```bash
chmod +x deploy/install_ollama.sh
./deploy/install_ollama.sh
```

Скрипт:

1. Запускает официальный установщик: `curl -fsSL https://ollama.com/install.sh | sh`
2. Проверяет `ollama --version`
3. Выполняет `ollama pull qwen2.5:7b-instruct`
4. Включает и запускает `systemd`-юнит `ollama`, если он есть
5. Проверяет `http://localhost:11434/api/tags`

Если unit не создался автоматически, скопируйте шаблон и подправьте пути:

```bash
sudo cp deploy/ollama.service.example /etc/systemd/system/ollama.service
sudo systemctl daemon-reload
sudo systemctl enable --now ollama
sudo systemctl --no-pager status ollama
```

Проверьте фактический `ExecStart` и пользователя: `systemctl cat ollama` (после штатной установки они уже корректны).

### Критерии приёмки (Linux)

- `ollama list` показывает `qwen2.5:7b-instruct` (или выбранную модель).
- `curl -s http://localhost:11434/api/tags` возвращает JSON со списком моделей.
- После перезагрузки сервис снова активен: `systemctl is-active ollama` → `active`.

---

## Windows

### WSL2 (как на Linux)

В PowerShell из каталога с репозиторием:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\deploy\install_ollama.ps1
```

Скрипт вызовет `deploy/install_ollama.sh` внутри WSL. Дальше проверки те же, но из WSL: `curl http://localhost:11434/api/tags`.

### Нативный Windows

Тот же `install_ollama.ps1` без WSL использует `winget install Ollama.Ollama`, затем `ollama pull qwen2.5:7b-instruct`. Убедитесь, что приложение Ollama запущено (иконка в трее), затем проверьте API.

---

## Docker (рекомендуется для изоляции)

Нужны: Docker, NVIDIA Container Toolkit (для GPU).

```bash
docker compose -f docker-compose.ollama.yml up -d
docker exec -it socrates-ollama ollama pull qwen2.5:7b-instruct
```

Проверка:

```bash
curl -s http://localhost:11434/api/tags
docker exec -it socrates-ollama ollama ps
```

Автоперезапуск: `restart: unless-stopped` в compose.

**Переменные для тонкой настройки** (при необходимости добавьте в `environment` сервиса `ollama`):

- `OLLAMA_NUM_GPU` — число GPU для бэкенда (см. [документацию Ollama](https://github.com/ollama/ollama)).
- При нехватке VRAM уменьшите параллельную нагрузку или выберите меньшую модель.

Основной `docker-compose.yml` в репозитории может уже содержать сервис `ollama` без секции GPU; файл `docker-compose.ollama.yml` добавляет резервирование NVIDIA GPU.

---

## Проверка, что используется GPU

```bash
ollama ps
```

В выводе для загруженной модели смотрите использование VRAM. Дополнительно:

```bash
nvidia-smi
watch -n1 nvidia-smi
```

В Docker:

```bash
docker exec -it socrates-ollama ollama ps
nvidia-smi
```

---

## Смена модели

1. Загрузка: `ollama pull llama3.1:8b` (или другое имя с [ollama.com/library](https://ollama.com/library)).
2. В backend: `OLLAMA_MODEL=llama3.1:8b` в `.env`, либо настройки в админке приложения.
3. Список локальных моделей: `ollama list`.

Эвристический выбор по VRAM (если установлен `nvidia-smi`):

```bash
chmod +x deploy/select_ollama_model.sh
./deploy/select_ollama_model.sh
```

---

## Обновление Ollama

**Linux (установка через официальный скрипт):** снова выполните установщик или следуйте инструкциям на [ollama.com](https://ollama.com).

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Docker:** пересоберите/подтяните образ:

```bash
docker compose -f docker-compose.ollama.yml pull
docker compose -f docker-compose.ollama.yml up -d
```

---

## Тестовый клиент (Python)

Из виртуального окружения backend или с установленным `httpx`:

```bash
pip install httpx
python scripts/test_ollama.py
```

Переменные окружения (опционально):

- `OLLAMA_BASE_URL` — по умолчанию `http://127.0.0.1:11434`
- `OLLAMA_MODEL` — по умолчанию `qwen2.5:7b-instruct`

---

## Интеграция с Socrates-AI

В `backend/.env` (см. также `deploy/OLLAMA.md`):

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=qwen2.5:7b-instruct
```

Если backend в Docker, а Ollama на хосте, используйте `http://host.docker.internal:11434` (Windows/macOS Docker Desktop) или IP хоста в Linux.

---

## Типовые проблемы

| Симптом | Что сделать |
|---------|-------------|
| Порт 11434 занят | `sudo ss -tlnp \| grep 11434` — найдите процесс; остановите лишний Ollama или смените порт через `OLLAMA_HOST` и проброс в Docker. |
| Не хватает VRAM | Меньшая модель (`qwen2.5:3b`), квантованные теги в каталоге Ollama, закрыть другие GPU-приложения. |
| Docker не видит GPU | Установите NVIDIA Container Toolkit, перезапустите Docker; проверьте `docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi`. |
| `connection refused` | Запустите `ollama serve` или `systemctl start ollama` / контейнер `socrates-ollama`. |
| Медленные ответы на CPU | Ожидаемо без GPU; используйте меньшую модель или включите GPU. |

Логи systemd:

```bash
journalctl -u ollama -f --no-pager
```

Логи Docker:

```bash
docker logs -f socrates-ollama
```

---

## Краткий чеклист приёмки

- [ ] `ollama list` содержит нужную модель.
- [ ] `curl http://localhost:11434/api/tags` возвращает JSON.
- [ ] `python scripts/test_ollama.py` печатает осмысленный ответ.
- [ ] После перезагрузки Ollama снова доступен (systemd или политика `restart` в Docker).
- [ ] При наличии GPU — `ollama ps` / `nvidia-smi` подтверждают загрузку.

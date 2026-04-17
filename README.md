# Socrates AI

Веб-тьютор: ведёт через вопросы, а не готовые ответы. Бэкенд — FastAPI + OpenRouter; фронт — React (Vite) + Tailwind + Zustand + Framer Motion.

## Быстрый старт

### 1. Бэкенд

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env   # при необходимости создай .env вручную
# Укажи OPENROUTER_API_KEY и при необходимости REDIS_URL=redis://localhost:6379/0
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Redis (опционально)

Из корня репозитория:

```bash
docker compose up -d
```

В `backend/.env`: `REDIS_URL=redis://localhost:6379/0`. Без Redis используется `REDIS_URL=memory` (по умолчанию в коде).

### 3. Фронтенд

```bash
cd frontend
npm install
npm run dev
```

Открой в браузере URL из вывода Vite (обычно http://localhost:5173).

- **`/`** — маркетинговый лендинг  
- **`/app`** — полноценный чат Socrates AI  

API проксируется на порт 8000.

Если собираешь статику без прокси, в `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Структура

- `backend/app/` — FastAPI, контроллер тьютора, OpenRouter, Redis state
- `frontend/src/` — UI, геймификация, mind-map панель

## Лицензия

По желанию автора проекта.

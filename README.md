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
# --host 0.0.0.0 — чтобы API было доступно с телефона/другого ПК по IP в LAN
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
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

Открой в браузере URL из вывода Vite (обычно http://localhost:5173). С другого устройства в сети: `http://<IP-этого-ПК>:5173` — в `vite.config.js` слушает `0.0.0.0`, бэкенд должен быть на `0.0.0.0:8000`. Не задавай `VITE_API_URL` с `127.0.0.1`, если страница открыта не на машине с API.

- **`/`** — маркетинговый лендинг  
- **`/app`** — полноценный чат Socrates AI  

API проксируется на порт 8000.

### Доступ из интернета (проброс портов на роутере)

В `vite.config.js` включено `server.allowedHosts: true` — иначе Vite часто отвечает **403** при заходе по **домену/DDNS** или с нестандартным `Host` (с LAN по IP это могло работать).

Нужны также: проброс **WAN → твой ПК:5173**, `ufw allow 5173/tcp`, запущенные бэкенд и `npm run dev`. Если провайдер использует **CGNAT**, вход с интернета без белого IP не заработает.

Если собираешь статику без прокси, в `frontend/.env`:

```env
VITE_API_URL=http://127.0.0.1:8000
```

## Структура

- `backend/app/` — FastAPI, контроллер тьютора, OpenRouter, Redis state
- `frontend/src/` — UI, геймификация, mind-map панель
- `deploy/` — примеры **nginx** + **systemd** + пошаговый продакшен

## Educator Dashboard

- Новая роль: `educator` — панель учителя/родителя доступна по `/educator`.
- Назначить роль можно из админки `/admin/users` или прямым SQL-апдейтом `users.role = 'educator'`.
- Возможности MVP:
  - классы и ученики;
  - задания для класса;
  - прогресс ученика, последние диалоги и частые ошибки;
  - weekly JSON/PDF report;
  - отправка PDF-отчёта на email через SMTP.

### SMTP для email-отчётов

В `backend/.env`:

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=teacher@example.com
SMTP_PASSWORD=app-password
SMTP_FROM=teacher@example.com
SMTP_USE_TLS=true
```

### Проверка

1. Дайте пользователю роль `educator`.
2. Зайдите на `/educator`, создайте класс и добавьте ученика по email.
3. Создайте задание для класса.
4. Ученик увидит задание в `/profile` и сможет открыть его в `/app?assignment=<id>`.
5. После начала диалога задание свяжется с `conversation.assignment_id`.
6. В карточке класса доступны weekly JSON/PDF report и отправка на email.

## Продакшен (nginx + HTTPS)

Полная инструкция: **[deploy/README.md](deploy/README.md)** — сборка `npm run build`, статика в `/var/www/...`, прокси `/api/` → uvicorn на `127.0.0.1:8000`, Certbot для HTTPS.

## Лицензия

По желанию автора проекта.

# Продакшен: nginx + HTTPS + systemd (Ubuntu)

Схема: **nginx** отдаёт статику из `frontend/dist` и проксирует `/api/` на **uvicorn** (`127.0.0.1:8000`). Бэкенд в интернет не торчит — только через nginx.

## Публичный IP без домена (пример 128.0.133.250)

В репозитории есть готовый **`deploy/nginx-128.0.133.250.conf`** — `server_name` и `listen` под этот IP.

```bash
./deploy/install.sh 128.0.133.250
```

Сайт: **http://128.0.133.250/** · чат: **http://128.0.133.250/app**  
HTTPS через Let’s Encrypt для «голого» IP обычно недоступен — позже подключи домен и certbot.

Если когда-нибудь откроешь фронт и API с **разных** origin’ов, в `backend/.env` задай `CORS_ORIGINS` (см. `.env.example`). Через nginx с одного IP обычно не нужно.

---

## Автоматическая установка (рекомендуется)

Из корня репозитория, **без** `sudo` в начале:

```bash
chmod +x deploy/install.sh
./deploy/install.sh твой-домен.ru
# или с IP:
./deploy/install.sh 128.0.133.250
# при необходимости: ./deploy/install.sh --install-deps ...
```

Скрипт: venv, `npm ci && npm run build`, копирование в `/var/www/socrates`, nginx, systemd `socrates-backend`. Потом добавь ключ в `backend/.env` и при необходимости `sudo systemctl restart socrates-backend`.

HTTPS: `sudo certbot --nginx -d твой-домен.ru`

---

## Ручная установка

### 1. Каталоги (пример)

```bash
sudo mkdir -p /opt/socrates /var/www/socrates
sudo chown -R $USER:$USER /opt/socrates /var/www/socrates
```

Склонируй репозиторий в `/opt/socrates` (или скопируй файлы).

## 2. Бэкенд

```bash
cd /opt/socrates/backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env   # OPENROUTER_API_KEY, при необходимости REDIS_URL
.venv/bin/python -c "from app.main import app; print('ok')"
```

Проверка вручную:

```bash
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
# другой терминал:
curl -s http://127.0.0.1:8000/health
```

## 3. Фронтенд (сборка)

**Не задавай** `VITE_API_URL` в проде, если фронт и API с **одного домена** — запросы пойдут на `/api/chat` (как в dev через прокси).

```bash
cd /opt/socrates/frontend
npm ci
npm run build
rsync -a --delete dist/ /var/www/socrates/dist/
```

## 4. nginx

```bash
sudo apt update && sudo apt install -y nginx
sudo cp /opt/socrates/deploy/nginx-socrates.conf.example /etc/nginx/sites-available/socrates
sudo nano /etc/nginx/sites-available/socrates
# Замени ПОДСТАВЬ_ДОМЕН.example на свой домен (или публичный IP, если без DNS)
sudo ln -sf /etc/nginx/sites-available/socrates /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Открой в браузере `http://ТВОЙ_ДОМЕН` — должен открыться лендинг, `/app` — чат. Если API 502 — проверь, что uvicorn запущен (шаг 2).

## 5. HTTPS (Let’s Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d ТВОЙ_ДОМЕН
```

Certbot сам допишет `listen 443 ssl` и пути к сертификатам. Продливание обычно по cron от certbot.

Без домена (только IP) Let’s Encrypt **не выдаст** сертификат — останься на HTTP или используй свой DNS/домен.

## 6. systemd (автозапуск бэкенда)

```bash
sudo cp /opt/socrates/deploy/socrates-backend.service.example /etc/systemd/system/socrates-backend.service
sudo nano /etc/systemd/system/socrates-backend.service
# Проверь User, WorkingDirectory, ExecStart, EnvironmentFile
sudo systemctl daemon-reload
sudo systemctl enable --now socrates-backend
sudo systemctl status socrates-backend
```

## 7. CORS (если фронт на другом домене)

Тогда в `backend/.env` задай `CORS_ORIGINS=https://твой-фронт` и перезапусти сервис. При одном домене через nginx **не нужно**.

## 8. Обновление релиза

```bash
cd /opt/socrates && git pull
cd frontend && npm ci && npm run build && sudo rsync -a --delete dist/ /var/www/socrates/dist/
sudo systemctl restart socrates-backend
```

---

Файлы-примеры: `nginx-socrates.conf.example`, `socrates-backend.service.example`.

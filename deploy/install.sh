#!/usr/bin/env bash
# Автоматический деплой на Ubuntu: сборка фронта, nginx, systemd.
# Запуск (из корня репозитория):
#   chmod +x deploy/install.sh
#   ./deploy/install.sh твой-домен.ru
#
# Опции:
#   --install-deps   установить nginx через apt (нужен sudo)
#
set -euo pipefail

if [[ "${EUID:-0}" -eq 0 ]]; then
  echo "Запускай без sudo: ./deploy/install.sh ваш-домен.ru (sudo используется точечно)."
  exit 1
fi

INSTALL_DEPS=false
DOMAIN=""
for arg in "$@"; do
  case "$arg" in
    --install-deps) INSTALL_DEPS=true ;;
    *) DOMAIN="$arg" ;;
  esac
done

if [[ -z "${DOMAIN}" ]]; then
  echo "Использование: $0 [--install-deps] домен.ru | публичный-IP"
  echo "Примеры: $0 app.example.com"
  echo "         $0 128.0.133.250"
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPLOY_USER="${SUDO_USER:-$USER}"

if [[ "${INSTALL_DEPS}" == true ]]; then
  sudo apt-get update -qq
  sudo apt-get install -y nginx rsync
fi

if ! command -v nginx >/dev/null 2>&1; then
  echo "Ошибка: nginx не установлен. Запусти: sudo apt install -y nginx"
  echo "Или: $0 --install-deps ${DOMAIN}"
  exit 1
fi

echo "==> Репозиторий: ${REPO_ROOT}"
echo "==> server_name: ${DOMAIN}"
echo "==> Пользователь сервиса: ${DEPLOY_USER}"

IP_CONF="${REPO_ROOT}/deploy/nginx-${DOMAIN}.conf"
USE_IP_FILE=false
if [[ -f "${IP_CONF}" ]]; then
  USE_IP_FILE=true
  echo "==> Используется готовый конфиг: deploy/nginx-${DOMAIN}.conf"
fi

# --- Бэкенд: venv ---
if [[ ! -x "${REPO_ROOT}/backend/.venv/bin/uvicorn" ]]; then
  echo "==> Создаю venv и ставлю зависимости backend..."
  (cd "${REPO_ROOT}/backend" && python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt)
fi

if [[ ! -f "${REPO_ROOT}/backend/.env" ]]; then
  cp "${REPO_ROOT}/backend/.env.example" "${REPO_ROOT}/backend/.env"
  echo "!!! Создан ${REPO_ROOT}/backend/.env — добавь OPENROUTER_API_KEY и перезапусти: sudo systemctl restart socrates-backend"
fi

# --- Фронт ---
echo "==> Сборка frontend (npm ci && npm run build)..."
(cd "${REPO_ROOT}/frontend" && npm ci && npm run build)

# --- Статика ---
echo "==> Копирую dist в /var/www/socrates ..."
sudo mkdir -p /var/www/socrates
sudo rsync -a --delete "${REPO_ROOT}/frontend/dist/" /var/www/socrates/dist/

# --- nginx ---
echo "==> Настраиваю nginx..."
if [[ "${USE_IP_FILE}" == true ]]; then
  sudo cp "${IP_CONF}" /etc/nginx/sites-available/socrates
else
  sudo cp "${REPO_ROOT}/deploy/nginx-socrates.conf.example" /etc/nginx/sites-available/socrates
  sudo sed -i "s/ПОДСТАВЬ_ДОМЕН.example/${DOMAIN}/g" /etc/nginx/sites-available/socrates
fi
sudo ln -sf /etc/nginx/sites-available/socrates /etc/nginx/sites-enabled/
if [[ -f /etc/nginx/sites-enabled/default ]]; then
  sudo rm -f /etc/nginx/sites-enabled/default
fi
sudo nginx -t
sudo systemctl reload nginx

# --- systemd ---
echo "==> systemd: socrates-backend..."
sudo tee /etc/systemd/system/socrates-backend.service >/dev/null <<EOF
[Unit]
Description=Socrates AI FastAPI backend
After=network.target

[Service]
Type=simple
User=${DEPLOY_USER}
Group=${DEPLOY_USER}
WorkingDirectory=${REPO_ROOT}/backend
EnvironmentFile=${REPO_ROOT}/backend/.env
ExecStart=${REPO_ROOT}/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable socrates-backend
sudo systemctl restart socrates-backend

echo ""
echo "==> Готово."
echo "    Сайт:     http://${DOMAIN}/"
echo "    Чат:      http://${DOMAIN}/app"
echo "    Здоровье API: curl -s http://127.0.0.1:8000/health"
echo ""
if [[ "${DOMAIN}" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "    HTTPS:    для голого IP Let's Encrypt обычно не выдаёт сертификат. Позже подключи домен и: sudo certbot --nginx -d домен.ru"
else
  echo "    HTTPS:    sudo apt install -y certbot python3-certbot-nginx && sudo certbot --nginx -d ${DOMAIN}"
fi
echo "    Логи:     journalctl -u socrates-backend -f"
sudo systemctl --no-pager -l status socrates-backend || true

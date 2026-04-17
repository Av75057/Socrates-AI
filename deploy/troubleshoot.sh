#!/usr/bin/env bash
# Диагностика: запускай на сервере Ubuntu, где крутится nginx + бэкенд.
set -euo pipefail

echo "=== 1. Кто слушает 5173 (должен быть nginx: master) ==="
sudo ss -tlnp | grep 5173 || echo "НИЧЕГО — nginx не слушает или порт занят другим процессом"

echo ""
echo "=== 2. Конфиг nginx ==="
sudo nginx -t 2>&1

echo ""
echo "=== 3. Статус nginx ==="
systemctl is-active nginx 2>&1 || true

echo ""
echo "=== 4. HTTP с этой же машины (должен быть 200) ==="
curl -sS -o /dev/null -w "GET http://127.0.0.1:5173/ → HTTP %{http_code}\n" http://127.0.0.1:5173/ || echo "curl не удался"

echo ""
echo "=== 5. Бэкенд (должен быть {\"status\":\"ok\"}) ==="
curl -sS http://127.0.0.1:8000/health || echo "бэкенд не отвечает — systemctl status socrates-backend"

echo ""
echo "=== 6. Сервис бэкенда ==="
systemctl is-active socrates-backend 2>&1 || echo "нет юнита socrates-backend"

echo ""
echo "=== Подсказки ==="
echo "- Если порт занят node/vite: останови npm run dev (или: sudo fuser -k 5173/tcp)."
echo "- С телефона по Wi‑Fi дома к внешнему IP часто не работает (hairpin NAT) — проверь через мобильный интернет."
echo "- Роутер: проброс TCP внешний 5173 → IP_этого_ПК:5173."
echo "- Логи nginx: sudo tail -50 /var/log/nginx/socrates-error.log"

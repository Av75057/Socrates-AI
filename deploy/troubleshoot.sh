#!/usr/bin/env bash
# Диагностика: запускай на сервере Ubuntu, где крутится nginx + бэкенд.
set +e

echo "=== 1. Кто слушает 5173 ==="
P5173="$(sudo ss -tlnp | grep ':5173' || true)"
echo "${P5173:-ничего}"
echo ""

if echo "$P5173" | grep -qE 'node|vite'; then
  echo ">>> ПРОБЛЕМА: порт 5173 занят Vite (node), а не nginx."
  echo "    Снаружи ты попадаешь в dev-сервер, не в прод через nginx."
  echo "    Сделай:"
  echo "      1) Останови dev: в терминале с Vite — Ctrl+C, или: pkill -f 'vite'  (или kill \$(pgrep -f node.*vite))"
  echo "      2) Подними nginx на 5173: sudo systemctl reload nginx"
  echo "      3) Проверь снова: sudo ss -tlnp | grep 5173   → должно быть nginx"
  echo ""
elif echo "$P5173" | grep -q nginx; then
  echo ">>> OK: на 5173 слушает nginx (прод)."
  echo ""
elif [[ -z "$P5173" ]]; then
  echo ">>> На 5173 никто не слушает. Запусти nginx с конфигом deploy/nginx-128.0.133.250.conf или npm run dev."
  echo ""
fi

echo "=== 2. Конфиг nginx ==="
sudo nginx -t 2>&1

echo ""
echo "=== 3. Статус nginx ==="
systemctl is-active nginx 2>&1

echo ""
echo "=== 4. HTTP http://127.0.0.1:5173/ (ожидается 200) ==="
curl -sS -o /dev/null -w "HTTP %{http_code}\n" --connect-timeout 3 http://127.0.0.1:5173/ 2>&1 || echo "curl ошибка"

echo ""
echo "=== 5. Бэкенд http://127.0.0.1:8000/health ==="
curl -sS --connect-timeout 3 http://127.0.0.1:8000/health 2>&1 || echo "бэкенд не отвечает"

echo ""
echo "=== 6. systemd socrates-backend ==="
if [[ -f /etc/systemd/system/socrates-backend.service ]]; then
  systemctl is-active socrates-backend 2>&1
  systemctl show socrates-backend -p ActiveState,SubState --no-pager 2>&1
else
  echo "Файла /etc/systemd/system/socrates-backend.service нет — юнит не ставили (uvicorn можно запускать вручную)."
fi

echo ""
echo "=== 7. Внешний доступ (CGNAT / VPN / не тот IP) ==="
PUB1="$(curl -4 -sS --max-time 5 https://ifconfig.me/ip 2>/dev/null || echo "?")"
PUB2="$(curl -4 -sS --max-time 5 https://api.ipify.org 2>/dev/null || echo "?")"
echo "Публичный IPv4 (с этой машины): ifconfig.me → ${PUB1}   ipify → ${PUB2}"
echo "Маршрут в интернет:"
ip -4 route get 1.1.1.1 2>/dev/null || true
echo "Локальные IPv4 (не loopback):"
ip -4 -br addr 2>/dev/null | grep -v '^lo ' || true
echo ""
echo "Сверь в админке роутера: WAN / Интернет IPv4 должен совпадать с числом выше."
echo "Если на роутере WAN = 10.x / 100.64–100.127 / 172.16–31 — это CGNAT: входящий проброс с интернета не заработает (нужен белый IP у провайдера или туннель)."
echo "Если default route идёт через VPN (tun/wg/… или имя вроде WonderVPN) — на время проверки отключи VPN на ПК и проверь с LTE: http://${PUB1}:5173/"
echo ""

echo "=== Подсказки (извне не открывается) ==="
echo "- Wi‑Fi дома → внешний IP часто не работает (hairpin NAT); проверь LTE/другую сеть."
echo "- Роутер: проброс TCP внешний 5173 → IP_этого_ПК:5173"
echo "- ufw: sudo ufw allow 5173/tcp"
echo "- Логи nginx: sudo tail -50 /var/log/nginx/socrates-error.log"

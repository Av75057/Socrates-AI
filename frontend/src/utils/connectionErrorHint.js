/**
 * Подсказка при NetworkError к API: бэкенд, прокси Vite, ловушка 127.0.0.1 с другого устройства.
 */
export function buildConnectionErrorHint() {
  const baseRaw = import.meta.env.VITE_API_URL;
  const base = typeof baseRaw === "string" ? baseRaw.trim() : "";
  const host = typeof window !== "undefined" ? window.location.hostname : "";
  const fromLan = host !== "" && host !== "localhost" && host !== "127.0.0.1";

  const parts = [
    "Запусти бэкенд (в каталоге backend), одной строкой:",
    "python3 -m venv .venv && .venv/bin/pip install -r requirements.txt && .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload",
    "Проверка на этой машине: curl -s http://127.0.0.1:8000/health",
  ];

  if (base && fromLan && /127\.0\.0\.1|localhost/.test(base)) {
    parts.push(
      "Сейчас страница открыта не с этого ПК (другой хост в адресной строке), а VITE_API_URL указывает на 127.0.0.1 — браузер стучится в localhost того устройства, где открыт сайт, а не в ПК с бэкендом.",
      "Вариант А: убери VITE_API_URL из frontend/.env, перезапусти npm run dev — запросы пойдут на /api и прокси Vite на машине с dev-сервером.",
      "Вариант Б: VITE_API_URL=http://IP_ЭТОГО_ПК_С_БЭКЕНДОМ:8000 и на бэкенде --host 0.0.0.0 (и при необходимости CORS).",
    );
  } else if (!base && fromLan) {
    parts.push(
      "Фронт с другого устройства: npm run dev должен быть на ПК с бэкендом (host: true уже в vite.config). Убедись, что uvicorn запущен на том же ПК, что и Vite.",
    );
  } else if (base) {
    parts.push(
      `Сейчас API: ${base}. Проверь, что процесс слушает этот адрес и нет блокировки файрволом.`,
    );
  } else {
    parts.push(
      "В dev без VITE_API_URL запросы идут на /api — их проксирует Vite на http://127.0.0.1:8000.",
    );
  }

  return parts.join(" ");
}

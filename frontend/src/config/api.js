/**
 * В dev: Vite проксирует /api → бэкенд (см. vite.config.js).
 * Если открываешь build без прокси — задай VITE_API_URL=http://127.0.0.1:8000
 */
export function apiUrl(path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  const base = import.meta.env.VITE_API_URL;
  if (base && typeof base === "string" && base.trim()) {
    return `${base.replace(/\/$/, "")}${p}`;
  }
  return `/api${p}`;
}

export function getChatUrl() {
  return apiUrl("/chat");
}

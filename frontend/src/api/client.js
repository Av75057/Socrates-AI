import { apiUrl } from "../config/api.js";

const TOKEN_KEY = "socrates_access_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

/**
 * fetch с Authorization при наличии токена.
 */
export async function apiFetch(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (
    !headers["Content-Type"] &&
    options.body &&
    typeof options.body === "string" &&
    options.method &&
    options.method !== "GET"
  ) {
    headers["Content-Type"] = "application/json";
  }
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  return fetch(apiUrl(path), { ...options, headers });
}

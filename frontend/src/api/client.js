import { apiUrl } from "../config/api.js";
import { buildConnectionErrorHint } from "../utils/connectionErrorHint.js";

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
  try {
    return await fetch(apiUrl(path), { ...options, headers });
  } catch (error) {
    const message = error instanceof Error ? error.message : "NetworkError when attempting to fetch resource.";
    throw new Error(`${message} ${buildConnectionErrorHint()}`.trim());
  }
}

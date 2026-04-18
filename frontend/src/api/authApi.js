import { apiFetch, setToken } from "./client.js";

export async function loginRequest(email, password) {
  const res = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  return res.json();
}

export async function registerRequest(email, password, full_name) {
  const res = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: full_name || null }),
  });
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  return res.json();
}

export function persistToken(accessToken) {
  setToken(accessToken);
}

export function clearToken() {
  setToken(null);
}

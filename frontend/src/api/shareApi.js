import { apiFetch } from "./client.js";

/** Публичный JSON диалога (без JWT). */
export async function fetchPublicShare(slug) {
  const res = await apiFetch(`/public/share/${encodeURIComponent(slug)}`);
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || res.statusText);
  }
  return res.json();
}

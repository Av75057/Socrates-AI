import { apiFetch } from "./client.js";

export async function fetchMe() {
  const res = await apiFetch("/users/me");
  if (!res.ok) return null;
  return res.json();
}

export async function updateMe(body) {
  const res = await apiFetch("/users/me", { method: "PUT", body: JSON.stringify(body) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchSettings() {
  const res = await apiFetch("/users/me/settings");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function updateSettings(body) {
  const res = await apiFetch("/users/me/settings", {
    method: "PUT",
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function listConversations(offset = 0, limit = 20) {
  const res = await apiFetch(`/users/me/conversations?offset=${offset}&limit=${limit}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function createConversation(title) {
  const res = await apiFetch("/users/me/conversations", {
    method: "POST",
    body: JSON.stringify({ title: title || null }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchConversation(id) {
  const res = await apiFetch(`/users/me/conversations/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteConversation(id) {
  const res = await apiFetch(`/users/me/conversations/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

export async function fetchStatistics() {
  const res = await apiFetch("/users/me/statistics");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

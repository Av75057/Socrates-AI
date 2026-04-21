import { apiFetch } from "./client.js";

export async function adminListUsers(q = "", offset = 0, limit = 20) {
  const params = new URLSearchParams({ offset: String(offset), limit: String(limit) });
  if (q) params.set("q", q);
  const res = await apiFetch(`/admin/users?${params}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function adminGetUser(id) {
  const res = await apiFetch(`/admin/users/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function adminUpdateUser(id, body) {
  const res = await apiFetch(`/admin/users/${id}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function adminDeleteUser(id) {
  const res = await apiFetch(`/admin/users/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

export async function adminUserConversations(userId) {
  const res = await apiFetch(`/admin/users/${userId}/conversations`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function adminStats() {
  const res = await apiFetch("/admin/stats");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function adminLLMStatus() {
  const res = await apiFetch("/admin/llm/status");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function adminLLMSwitch(body) {
  const res = await apiFetch("/admin/llm/switch", {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function adminLLMTest(prompt) {
  const res = await apiFetch("/admin/llm/test", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

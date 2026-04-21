import { apiFetch } from "./client.js";

export async function fetchMemoryProfile() {
  const res = await apiFetch("/users/me/memory-profile");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchMyEducators() {
  const res = await apiFetch("/users/me/educators");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchMyAssignments() {
  const res = await apiFetch("/users/me/assignments");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function fetchMyAssignment(id) {
  const res = await apiFetch(`/users/me/assignments/${id}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

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

/** Проверка GET {base}/models (OpenAI-совместимый API). */
export async function testLlmConnection(body) {
  const res = await apiFetch("/users/me/settings/test-llm", {
    method: "POST",
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

export async function publishConversation(id) {
  const res = await apiFetch(`/users/me/conversations/${id}/publish`, { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function unpublishConversation(id) {
  const res = await apiFetch(`/users/me/conversations/${id}/unpublish`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

export async function fetchStatistics() {
  const res = await apiFetch("/users/me/statistics");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUserSkills() {
  const res = await apiFetch("/users/me/skills");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUserPedagogy() {
  const res = await apiFetch("/users/me/pedagogy");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getUserProgress() {
  const res = await apiFetch("/users/me/progress");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getRecommendation() {
  const res = await apiFetch("/users/me/recommendation");
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function resetProgress() {
  const res = await apiFetch("/users/me/reset_progress", { method: "POST" });
  if (!res.ok) throw new Error(await res.text());
}

export async function updateMessage(messageId, content) {
  const res = await apiFetch(`/users/me/messages/${messageId}`, {
    method: "PUT",
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function deleteMessage(messageId) {
  const res = await apiFetch(`/users/me/messages/${messageId}`, { method: "DELETE" });
  if (!res.ok) throw new Error(await res.text());
}

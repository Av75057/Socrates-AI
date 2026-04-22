import { apiFetch } from "./client.js";

async function toApiError(res) {
  const raw = await res.text();
  let message = raw || res.statusText || "Ошибка API";
  try {
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.detail === "string") message = parsed.detail;
  } catch {
    /* ignore */
  }
  const error = new Error(message);
  error.status = res.status;
  return error;
}

export async function listTopics(params = {}) {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (Number.isFinite(params.offset)) search.set("offset", String(params.offset));
  if (Number.isFinite(params.limit)) search.set("limit", String(params.limit));
  if (Number.isFinite(params.difficultyMin)) search.set("difficulty_min", String(params.difficultyMin));
  if (Number.isFinite(params.difficultyMax)) search.set("difficulty_max", String(params.difficultyMax));
  if (params.freeOnly) search.set("free_only", "true");
  if (params.sort) search.set("sort", params.sort);
  const tags = Array.isArray(params.tags) ? params.tags : [];
  for (const tag of tags) {
    if (tag) search.append("tags", tag);
  }
  const suffix = search.toString() ? `?${search}` : "";
  const res = await apiFetch(`/topics${suffix}`);
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

export async function fetchTopicTags() {
  const res = await apiFetch("/topics/tags");
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

export async function fetchTopic(id) {
  const res = await apiFetch(`/topics/${id}`);
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

export async function startTopic(id) {
  const res = await apiFetch(`/topics/${id}/start`, { method: "POST" });
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

export async function adminListTopics(params = {}) {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.includeInactive !== undefined) search.set("include_inactive", params.includeInactive ? "true" : "false");
  if (Number.isFinite(params.offset)) search.set("offset", String(params.offset));
  if (Number.isFinite(params.limit)) search.set("limit", String(params.limit));
  const suffix = search.toString() ? `?${search}` : "";
  const res = await apiFetch(`/admin/topics${suffix}`);
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

export async function adminCreateTopic(body) {
  const res = await apiFetch("/admin/topics", {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

export async function adminUpdateTopic(id, body) {
  const res = await apiFetch(`/admin/topics/${id}`, {
    method: "PUT",
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

export async function adminDeleteTopic(id) {
  const res = await apiFetch(`/admin/topics/${id}`, { method: "DELETE" });
  if (!res.ok) throw await toApiError(res);
}

export async function adminGenerateTopic(prompt) {
  const res = await apiFetch("/admin/topics/generate", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw await toApiError(res);
  return res.json();
}

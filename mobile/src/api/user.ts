import { api } from "./client";
import { SubscriptionInfo } from "../types";

export async function fetchMe() {
  const { data } = await api.get("/users/me");
  return data;
}

export async function updateMe(body: { full_name?: string | null }) {
  const { data } = await api.put("/users/me", body);
  return data;
}

export async function uploadAvatar(asset: { uri: string; fileName?: string | null; mimeType?: string | null }) {
  const form = new FormData();
  form.append("file", {
    uri: asset.uri,
    name: asset.fileName || "avatar.jpg",
    type: asset.mimeType || "image/jpeg"
  } as any);
  const { data } = await api.post("/users/me/avatar", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data as { avatar_url: string };
}

export async function deleteAvatar() {
  await api.delete("/users/me/avatar");
}

export async function fetchSubscription() {
  const { data } = await api.get<SubscriptionInfo>("/users/me/subscription");
  return data;
}

export async function fetchSettings() {
  const { data } = await api.get("/users/me/settings");
  return data;
}

export async function updateSettings(body: Record<string, unknown>) {
  const { data } = await api.put("/users/me/settings", body);
  return data;
}

export async function listConversations() {
  const { data } = await api.get("/users/me/conversations");
  return data;
}

export async function fetchConversation(id: number) {
  const { data } = await api.get(`/users/me/conversations/${id}`);
  return data;
}

export async function deleteConversation(id: number) {
  await api.delete(`/users/me/conversations/${id}`);
}

export async function fetchSkills() {
  const { data } = await api.get("/users/me/skills");
  return data;
}

export async function fetchPedagogy() {
  const { data } = await api.get("/users/me/pedagogy");
  return data;
}

export async function fetchStatistics() {
  const { data } = await api.get("/users/me/statistics");
  return data;
}

export async function fetchAssignments() {
  const { data } = await api.get("/users/me/assignments");
  return data;
}

export async function fetchEducators() {
  const { data } = await api.get("/users/me/educators");
  return data;
}

export async function publishConversation(id: number) {
  const { data } = await api.post(`/users/me/conversations/${id}/publish`);
  return data;
}

export async function unpublishConversation(id: number) {
  await api.delete(`/users/me/conversations/${id}/unpublish`);
}

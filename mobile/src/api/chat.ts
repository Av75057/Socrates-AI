import { api } from "./client";

export async function postChat(body: Record<string, unknown>) {
  const { data } = await api.post("/chat", body);
  return data;
}

export async function fetchPedagogyState(sessionId: string) {
  const { data } = await api.get(`/pedagogy/state/${encodeURIComponent(sessionId)}`);
  return data;
}

export async function postTutorMode(sessionId: string, mode: string) {
  const { data } = await api.post("/pedagogy/mode", { session_id: sessionId, mode });
  return data;
}

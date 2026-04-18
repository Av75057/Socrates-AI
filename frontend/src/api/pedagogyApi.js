import { apiFetch } from "./client.js";

export async function fetchPedagogyState(sessionId) {
  try {
    const res = await apiFetch(`/pedagogy/state/${encodeURIComponent(sessionId)}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function postPedagogyMode(sessionId, mode) {
  try {
    const res = await apiFetch("/pedagogy/mode", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, mode }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function postPedagogyHint(sessionId, topic, lastUserMessage) {
  try {
    const res = await apiFetch("/pedagogy/hint", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        topic: topic || "",
        last_user_message: lastUserMessage || "",
      }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

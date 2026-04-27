import { apiFetch } from "./client.js";

async function readJsonOrThrow(res) {
  if (!res.ok) {
    const text = await res.text();
    const error = new Error(text || res.statusText);
    error.status = res.status;
    throw error;
  }
  return res.json();
}

export async function startMetaTraining(sessionId, preferredTopic = null) {
  const res = await apiFetch("/api/v1/meta-training/start", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      preferred_topic: preferredTopic,
    }),
  });
  return readJsonOrThrow(res);
}

export async function fetchMetaTrainingStatus(sessionId) {
  const res = await apiFetch(`/api/v1/meta-training/status/${encodeURIComponent(sessionId)}`);
  return readJsonOrThrow(res);
}

export async function postMetaTrainingMessage(sessionId, message) {
  const res = await apiFetch("/api/v1/meta-training/message", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      message,
      action: "message",
    }),
  });
  return readJsonOrThrow(res);
}

export async function advanceMetaTrainingPhase(sessionId) {
  const res = await apiFetch("/api/v1/meta-training/message", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      action: "advance_phase",
    }),
  });
  return readJsonOrThrow(res);
}

export async function switchMetaTrainingFrame(sessionId, message, frameName = null) {
  const res = await apiFetch("/api/v1/meta-training/message", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      message,
      frame_name: frameName,
      action: "switch_frame",
    }),
  });
  return readJsonOrThrow(res);
}

export async function endMetaTraining(sessionId, summary = "", confidenceLabel = "") {
  const res = await apiFetch("/api/v1/meta-training/end", {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      summary,
      confidence_label: confidenceLabel,
    }),
  });
  return readJsonOrThrow(res);
}

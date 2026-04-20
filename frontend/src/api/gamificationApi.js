import { apiFetch } from "./client.js";

/**
 * Все вызовы безопасны для чата: при ошибке сети возвращают null / пустой результат.
 */

export async function fetchGamificationProgress(sessionId) {
  try {
    const res = await apiFetch(`/gamification/progress/${encodeURIComponent(sessionId)}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

/** Прогресс по JWT (не зависит от session_id чата). */
export async function fetchGamificationProgressMe() {
  try {
    const res = await apiFetch("/gamification/me/progress");
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchAchievementsCatalog() {
  try {
    const res = await apiFetch("/gamification/achievements");
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data?.achievements) ? data.achievements : [];
  } catch {
    return [];
  }
}

export async function fetchDailyChallenge(sessionId) {
  try {
    const res = await apiFetch(`/gamification/daily-challenge/${encodeURIComponent(sessionId)}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchDailyChallengeMe() {
  try {
    const res = await apiFetch("/gamification/me/daily-challenge");
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function postGamificationAction(sessionId, actionType, dialogContext = {}) {
  try {
    const res = await apiFetch("/gamification/action", {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        action_type: actionType,
        dialog_context: dialogContext,
      }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

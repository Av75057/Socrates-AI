import { api } from "./client";

export async function fetchGamificationMe() {
  const { data } = await api.get("/gamification/me/progress");
  return data;
}

export async function fetchAchievements() {
  const { data } = await api.get("/gamification/achievements");
  return data?.achievements ?? [];
}

export async function fetchDailyChallengeMe() {
  const { data } = await api.get("/gamification/me/daily-challenge");
  return data;
}

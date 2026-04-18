/** Согласованность темы сессии (из API topic) и трека skill_tree с сервера. */

export function topicImpliesMath(t) {
  const s = (t || "").toLowerCase();
  return /математ|алгебр|геометр|уравнен|тригонометр|логарифм|производн|интеграл|math|algebra|geometry|calculus|equation/.test(
    s,
  );
}

export function topicImpliesPhysics(t) {
  const s = (t || "").toLowerCase();
  return /физик|механик|ньютон|динамик|кинематик|импульс|энерги|оптик|магнитн|электричеств/.test(s);
}

export function inferSkillTrackId(st) {
  if (!st || typeof st !== "object") return "";
  const id = String(st.track_id || "").toLowerCase();
  if (id === "math" || id === "physics") return id;
  const tt = String(st.track_title || "").toLowerCase();
  if (tt.includes("математ")) return "math";
  if (tt.includes("физ")) return "physics";
  return "";
}

export function skillTreeTopicMismatch(topic, skillTree) {
  const topicTrim = (topic || "").trim();
  if (!topicTrim) return false;
  const tid = inferSkillTrackId(skillTree);
  return (
    (topicImpliesMath(topicTrim) && tid === "physics") ||
    (topicImpliesPhysics(topicTrim) && tid === "math")
  );
}

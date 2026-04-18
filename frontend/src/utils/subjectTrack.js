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

/** Узлы надёжнее заголовка: бэкенд мог отдать «Математика», а массив — от физики. */
function inferTrackFromNodes(st) {
  const nodes = st?.nodes;
  if (!Array.isArray(nodes) || nodes.length === 0) return "";
  const ids = new Set(nodes.map((n) => String(n.id || "")));
  const mathIds = ["numbers", "fractions", "equations", "functions", "geometry"];
  const physIds = ["force", "mass", "acceleration", "energy", "momentum"];
  if (mathIds.some((id) => ids.has(id))) return "math";
  if (physIds.some((id) => ids.has(id))) return "physics";
  return "";
}

export function inferSkillTrackId(st) {
  if (!st || typeof st !== "object") return "";
  const fromNodes = inferTrackFromNodes(st);
  if (fromNodes) return fromNodes;
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
  if (topicImpliesMath(topicTrim) && tid !== "math") return true;
  if (topicImpliesPhysics(topicTrim) && tid !== "physics") return true;
  return false;
}

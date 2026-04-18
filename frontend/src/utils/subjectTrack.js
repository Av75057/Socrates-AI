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

/**
 * Какой трек реально в массиве nodes (id и title), без track_title.
 * Иначе при пустых id заголовок «Математика» давал tid=math при узлах Сила/Масса/Ускорение.
 */
function inferTrackFromNodes(st) {
  const nodes = st?.nodes;
  if (!Array.isArray(nodes) || nodes.length === 0) return "";
  const ids = new Set(nodes.map((n) => String(n.id || "").toLowerCase()));
  const mathIds = ["numbers", "fractions", "equations", "functions", "geometry"];
  const physIds = ["force", "mass", "acceleration", "energy", "momentum"];
  if (mathIds.some((id) => ids.has(id))) return "math";
  if (physIds.some((id) => ids.has(id))) return "physics";

  const titles = nodes.map((n) => String(n.title || "").toLowerCase().trim());
  const physHints = ["сила", "масса", "ускорен", "импульс", "энерги", "ньютон", "кинематик"];
  const mathHints = [
    "уравнен",
    "дроб",
    "геометр",
    "числа",
    "функц",
    "график",
    "процент",
    "тригонометр",
    "логарифм",
    "алгебр",
  ];
  if (titles.some((t) => physHints.some((h) => t.includes(h)))) return "physics";
  if (titles.some((t) => mathHints.some((h) => t.includes(h)))) return "math";
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

/** Тема для сверки: сначала topic из API, иначе заголовок трека (центр mind-map без topic в store). */
export function sessionSubjectHint(topic, skillTree) {
  const t = (topic || "").trim();
  if (t) return t;
  return String(skillTree?.track_title || "").trim();
}

export function skillTreeTopicMismatch(topic, skillTree) {
  const hint = sessionSubjectHint(topic, skillTree);
  if (!hint) return false;
  const tid = inferSkillTrackId(skillTree);
  if (topicImpliesMath(hint) && tid !== "math") return true;
  if (topicImpliesPhysics(hint) && tid !== "physics") return true;
  return false;
}

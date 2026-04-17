/** Короткий ответ — просим развернуться */
export function isShortAnswer(text, action) {
  if (action !== "none") return false;
  const t = (text || "").trim();
  return t.length > 0 && t.length < 15;
}

/** «Сильный» ответ — по длине и вовлечённости */
export function isStrongAnswer(text, action) {
  if (action !== "none") return false;
  const t = (text || "").trim();
  return t.length >= 35;
}

export function isDontKnow(text, action) {
  if (action !== "none") return false;
  const t = (text || "").trim().toLowerCase();
  return /не знаю|хз|без понятия/.test(t);
}

/** Уровень мышления по числу шагов с бэкенда */
export function getThinkingLevel(attempts) {
  const a = attempts ?? 0;
  if (a <= 3) return { key: "novice", label: "🧠 Новичок" };
  if (a <= 6) return { key: "thinker", label: "🔥 Думающий" };
  return { key: "master", label: "🧙 Мастер" };
}

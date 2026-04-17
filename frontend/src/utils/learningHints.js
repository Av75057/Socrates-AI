/**
 * Эвристика «почти понял» — без LLM, только сигналы вовлечённости.
 */
export function shouldShowAlmostUnderstood({
  action,
  userText,
  attempts,
  frustration,
  mode,
}) {
  if (action !== "none") return false;
  const t = (userText || "").trim();
  if (t.length < 20) return false;

  const reflective =
    /(кажется|понял|поняла|получается|наверное|скорее|вроде|похоже|думаю|если бы|наверно|логично)/i.test(
      t,
    );

  if (reflective && t.length >= 25) return true;

  if (attempts >= 4 && attempts <= 6 && (mode === "hint" || frustration >= 1)) return true;

  return false;
}

/** «Очень близко» — 2–3 шага и режим подсказки (отдельно от общего «почти понял»). */
export function shouldShowVeryClose({ action, attempts, mode }) {
  if (action !== "none") return false;
  if (mode !== "hint") return false;
  return attempts >= 2 && attempts <= 3;
}

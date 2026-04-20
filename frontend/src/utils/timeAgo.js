/** Короткая подпись времени для UI сообщений. */
export function formatMessageTime(ts) {
  if (ts == null || !Number.isFinite(ts)) return "";
  const d = Date.now() - ts;
  if (d < 60_000) return "только что";
  if (d < 3_600_000) return `${Math.floor(d / 60_000)} мин назад`;
  if (d < 86_400_000) return `${Math.floor(d / 3_600_000)} ч назад`;
  return new Date(ts).toLocaleString(undefined, { day: "numeric", month: "short" });
}

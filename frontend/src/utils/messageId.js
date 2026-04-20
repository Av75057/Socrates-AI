/** Из id вида "db-123" или числа — числовой id в БД, иначе null. */
export function parseDbMessageId(id) {
  if (typeof id === "number" && Number.isFinite(id)) return id;
  if (typeof id === "string" && id.startsWith("db-")) {
    const n = parseInt(id.slice(3), 10);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

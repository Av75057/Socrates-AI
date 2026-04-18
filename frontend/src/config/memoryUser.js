const KEY = "socrates_memory_user_id";

/** Стабильный id для долговременной памяти (не сбрасывается при «Новой сессии» чата). */
export function getMemoryUserId() {
  try {
    let id = localStorage.getItem(KEY);
    if (!id) {
      id =
        typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : `mem_${Date.now()}_${Math.random().toString(36).slice(2)}`;
      localStorage.setItem(KEY, id);
    }
    return id;
  } catch {
    return "anonymous";
  }
}

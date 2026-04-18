const KEY = "socrates_ux_metrics";

function load() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function save(data) {
  try {
    localStorage.setItem(KEY, JSON.stringify(data));
  } catch {
    /* ignore */
  }
}

/** Счётчики продукта: подсказки, «не знаю», уход со страницы и т.д. */
export function bumpUxMetric(name, amount = 1) {
  const data = load();
  data[name] = (data[name] || 0) + amount;
  data.updatedAt = Date.now();
  save(data);
}

export function getUxMetricsSnapshot() {
  return load();
}

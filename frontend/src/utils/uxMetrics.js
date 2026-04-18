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

const PROFILE_TYPES = ["lazy", "anxious", "thinker"];

/** Накопление времени в типе профиля (мс), смена типа фиксирует интервал. */
export function recordProfileTime(type) {
  if (!PROFILE_TYPES.includes(type)) return;
  const data = load();
  const now = Date.now();
  if (!data.profileMs) {
    data.profileMs = { lazy: 0, anxious: 0, thinker: 0 };
  }
  const prev = data._profileLastType;
  const prevAt = data._profileLastAt ?? now;
  if (prev && PROFILE_TYPES.includes(prev) && prev !== type) {
    const delta = Math.min(now - prevAt, 3_600_000);
    data.profileMs[prev] = (data.profileMs[prev] || 0) + delta;
    data[`profileSwitch_${prev}_to_${type}`] = (data[`profileSwitch_${prev}_to_${type}`] || 0) + 1;
  }
  data._profileLastType = type;
  data._profileLastAt = now;
  data.currentProfileType = type;
  save(data);
}

/** Сброс таймера при новой сессии чата (не обнуляет накопленные мс). */
export function resetProfileClock() {
  const data = load();
  delete data._profileLastType;
  delete data._profileLastAt;
  save(data);
}

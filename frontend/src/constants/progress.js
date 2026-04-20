/** Визуальный максимум шагов прогресс-бара (UX); связан с attempts с бэкенда. */
export const MAX_STEPS = 7;

/** Как на бэкенде: уровень мудрости растёт каждые 150 WP. */
export const WISDOM_PER_LEVEL = 150;

/** Доля прогресса внутри текущего уровня мудрости — в шагах 0..maxSteps (для боковой панели). */
export function wisdomPointsToProgressSteps(wisdomPoints, maxSteps = MAX_STEPS) {
  const w = Math.max(0, Number(wisdomPoints) || 0);
  const within = w % WISDOM_PER_LEVEL;
  return Math.min(maxSteps, Math.round((within / WISDOM_PER_LEVEL) * maxSteps));
}

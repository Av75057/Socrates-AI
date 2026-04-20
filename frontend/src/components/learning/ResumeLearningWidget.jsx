const SKILL_LABELS = {
  avoid_straw_man: "не искажать аргументы",
  avoid_ad_hominem: "без перехода на личности",
  use_counterexample: "контрпримеры",
  ask_clarifying: "уточняющие вопросы",
  structure_argument: "структура аргумента",
  logical_consistency: "логическая согласованность",
};

/**
 * Карточка «продолжить обучение»: последний диалог, слабые навыки, тема.
 */
export default function ResumeLearningWidget({
  data,
  loading,
  onContinueLast,
  onNewRecommended,
  compact = false,
}) {
  if (loading) {
    return (
      <div
        className={`rounded-xl border border-slate-200/80 bg-white/90 px-4 py-3 text-sm text-slate-500 shadow-sm dark:border-slate-700/80 dark:bg-slate-900/60 dark:text-slate-400 ${compact ? "" : "mx-4 mt-2"}`}
      >
        Загрузка рекомендаций…
      </div>
    );
  }
  if (!data) return null;

  const hasLast = data.last_conversation?.id != null;
  const weak = Array.isArray(data.weak_skills) ? data.weak_skills : [];
  const weakPretty = weak.map((id) => SKILL_LABELS[id] || id).slice(0, 3);

  return (
    <div
      className={`rounded-xl border border-cyan-200/60 bg-gradient-to-br from-cyan-50/90 to-white px-4 py-3 shadow-sm dark:border-cyan-900/40 dark:from-cyan-950/40 dark:to-slate-900/80 ${compact ? "" : "mx-4 mt-2"}`}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-cyan-800 dark:text-cyan-300/90">
        Продолжить обучение
      </p>
      <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{data.message}</p>
      {weakPretty.length ? (
        <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
          Зоны роста:{" "}
          <span className="font-medium text-slate-800 dark:text-slate-200">{weakPretty.join(", ")}</span>
        </p>
      ) : null}
      <div className="mt-3 flex flex-wrap gap-2">
        {hasLast ? (
          <button
            type="button"
            onClick={onContinueLast}
            className="min-h-[40px] rounded-lg bg-cyan-600 px-3 py-2 text-xs font-medium text-white shadow hover:bg-cyan-500 active:bg-cyan-700 dark:bg-cyan-700 dark:hover:bg-cyan-600"
          >
            Продолжить последний диалог
          </button>
        ) : null}
        <button
          type="button"
          onClick={onNewRecommended}
          className="min-h-[40px] rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-800 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700/80"
        >
          Новый диалог по рекомендации
        </button>
      </div>
    </div>
  );
}

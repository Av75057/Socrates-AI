import { LockKeyhole, Sparkles, Star } from "lucide-react";

function DifficultyStars({ level }) {
  const value = Math.max(1, Math.min(5, Number(level) || 1));
  return (
    <div className="flex items-center gap-1 text-amber-500" aria-label={`Сложность ${value} из 5`}>
      {Array.from({ length: 5 }).map((_, idx) => (
        <Star key={idx} size={14} className={idx < value ? "fill-current" : "opacity-25"} />
      ))}
    </div>
  );
}

function trimDescription(text) {
  const raw = String(text || "").trim();
  if (raw.length <= 100) return raw;
  return `${raw.slice(0, 97).trim()}…`;
}

function masteryTone(score) {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 50) return "bg-cyan-500";
  return "bg-amber-500";
}

export default function TopicCard({
  topic,
  onStart,
  onOpen,
  starting = false,
  compact = false,
}) {
  const startedBefore = !!topic?.progress?.last_used;
  const masteryScore = Math.max(0, Math.min(100, Number(topic?.progress?.mastery_score) || 0));
  const goalsState = Array.isArray(topic?.progress?.goals_state) ? topic.progress.goals_state : [];
  const learningObjectives = Array.isArray(topic?.learning_objectives) ? topic.learning_objectives : [];
  const visibleGoals = goalsState.length > 0 ? goalsState.slice(0, compact ? 2 : 3) : learningObjectives.slice(0, compact ? 2 : 3);
  return (
    <article className="group flex h-full flex-col rounded-3xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-cyan-300 hover:shadow-lg hover:shadow-cyan-900/5 dark:border-slate-700 dark:bg-slate-900/55 dark:hover:border-cyan-700/60 dark:hover:shadow-black/20">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <button
            type="button"
            onClick={() => onOpen?.(topic)}
            className="text-left font-display text-lg font-semibold leading-tight text-slate-950 transition group-hover:text-cyan-700 dark:text-white dark:group-hover:text-cyan-300"
          >
            {topic.title}
          </button>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            {topic.is_premium ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2.5 py-1 font-medium text-amber-900 dark:bg-amber-500/15 dark:text-amber-200">
                <Sparkles size={12} />
                Premium
              </span>
            ) : null}
            {startedBefore ? (
              <span className="rounded-full bg-emerald-100 px-2.5 py-1 font-medium text-emerald-900 dark:bg-emerald-500/15 dark:text-emerald-200">
                Уже открывал
              </span>
            ) : null}
          </div>
        </div>
        <DifficultyStars level={topic.difficulty} />
      </div>

      <p className="mt-4 flex-1 text-sm leading-6 text-slate-600 dark:text-slate-300/90">
        {trimDescription(topic.description || topic.initial_prompt)}
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        {(topic.tags || []).slice(0, compact ? 3 : 5).map((tag) => (
          <span
            key={tag}
            className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-xs text-slate-700 dark:border-slate-700 dark:bg-slate-950/70 dark:text-slate-300"
          >
            #{tag}
          </span>
        ))}
      </div>

      {(startedBefore || learningObjectives.length > 0) && (
        <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/45">
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Mastery
            </span>
            <span className="text-sm font-semibold text-slate-900 dark:text-slate-100">
              {masteryScore}%
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
            <div
              className={`h-full rounded-full transition-all ${masteryTone(masteryScore)}`}
              style={{ width: `${masteryScore}%` }}
            />
          </div>
          <div className="mt-3 space-y-2">
            {visibleGoals.map((goal, idx) => {
              const progressPercent = Math.max(0, Math.min(100, Number(goal.progress_percent) || 0));
              const achieved = !!goal.achieved;
              return (
                <div key={`${goal.skill_id || goal.title || "goal"}-${idx}`} className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-slate-700 dark:text-slate-200">
                      {goal.title}
                    </p>
                    {"target_level" in goal ? (
                      <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                        {achieved ? "Цель достигнута" : `${progressPercent}% к цели`}
                      </p>
                    ) : null}
                  </div>
                  {"target_level" in goal ? (
                    <span
                      className={`shrink-0 rounded-full px-2 py-1 text-[11px] font-medium ${
                        achieved
                          ? "bg-emerald-100 text-emerald-900 dark:bg-emerald-500/15 dark:text-emerald-200"
                          : "bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300"
                      }`}
                    >
                      {achieved ? "OK" : `${progressPercent}%`}
                    </span>
                  ) : null}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-5 flex items-center justify-between gap-3">
        <span className="text-xs text-slate-500 dark:text-slate-400">
          {topic?.progress?.completed ? "Тема освоена" : `Запусков: ${topic.usage_count || 0}`}
        </span>
        <button
          type="button"
          onClick={() => onStart?.(topic)}
          disabled={starting}
          className="inline-flex items-center gap-2 rounded-xl bg-cyan-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-cyan-500 disabled:cursor-wait disabled:opacity-70"
        >
          {topic.is_premium && !topic.can_start ? <LockKeyhole size={15} /> : null}
          {starting ? "Запускаю…" : "Начать диалог"}
        </button>
      </div>
    </article>
  );
}

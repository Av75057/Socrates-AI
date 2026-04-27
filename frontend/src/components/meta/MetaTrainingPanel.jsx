const SCORE_LABELS = [
  { key: "inquisitiveness", label: "Вопросы" },
  { key: "frame_agility", label: "Рамки" },
  { key: "uncertainty_tolerance", label: "Неопределённость" },
  { key: "assumption_detection", label: "Допущения" },
  { key: "meta_reflection", label: "Рефлексия" },
];

const PHASE_LABELS = {
  orientation: "Фаза 1: Карта вопросов",
  exploration: "Фаза 2: Поиск рамок",
  sparring: "Фаза 3: Сократический допрос",
  reflection: "Фаза 4: Вердикт",
  completed: "Итог",
};

const QUESTION_TYPE_LABELS = {
  factual: "Фактологический",
  conceptual: "Концептуальный",
  provocative: "Провокационный",
  meta: "Мета-вопрос",
};

const QUESTION_TYPE_HINTS = {
  factual: "Ищет прямое сведение или определение.",
  conceptual: "Уточняет смысл, различие или интерпретацию.",
  provocative: "Проверяет основание тезиса на прочность.",
  meta: "Спрашивает о критериях знания или способе проверки.",
};

function formatRemaining(seconds) {
  const safe = Math.max(0, Number(seconds) || 0);
  const m = String(Math.floor(safe / 60)).padStart(2, "0");
  const s = String(safe % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function point(angleDeg, radius, center) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return {
    x: center + radius * Math.cos(rad),
    y: center + radius * Math.sin(rad),
  };
}

function RadarChart({ scores }) {
  const size = 260;
  const center = size / 2;
  const radius = 88;
  const angles = SCORE_LABELS.map((_, index) => (360 / SCORE_LABELS.length) * index);
  const polygon = angles
    .map((angle, index) => {
      const raw = Number(scores?.[SCORE_LABELS[index].key] ?? 0);
      const pct = Math.max(0, Math.min(1, raw / 10));
      const p = point(angle, radius * pct, center);
      return `${p.x},${p.y}`;
    })
    .join(" ");

  return (
    <svg viewBox={`0 0 ${size} ${size}`} className="h-64 w-64">
      {[0.25, 0.5, 0.75, 1].map((ratio) => {
        const ring = angles.map((angle) => {
          const p = point(angle, radius * ratio, center);
          return `${p.x},${p.y}`;
        });
        return (
          <polygon
            key={ratio}
            points={ring.join(" ")}
            fill="none"
            stroke="rgba(100,116,139,0.25)"
            strokeWidth="1"
          />
        );
      })}
      {angles.map((angle, index) => {
        const p = point(angle, radius, center);
        return (
          <g key={SCORE_LABELS[index].key}>
            <line x1={center} y1={center} x2={p.x} y2={p.y} stroke="rgba(100,116,139,0.22)" />
            <text
              x={point(angle, radius + 24, center).x}
              y={point(angle, radius + 24, center).y}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-slate-600 text-[10px] dark:fill-slate-300"
            >
              {SCORE_LABELS[index].label}
            </text>
          </g>
        );
      })}
      <polygon
        points={polygon}
        fill="rgba(8,145,178,0.24)"
        stroke="rgba(8,145,178,0.9)"
        strokeWidth="2"
      />
      <circle cx={center} cy={center} r="3.5" fill="rgba(8,145,178,0.95)" />
    </svg>
  );
}

export default function MetaTrainingPanel({
  session,
  onStart,
  onExit,
  loading,
  detectedQuestionType,
  detectedQuestionHint,
  detectedAssumptionHint,
  diversityHint,
  compact = false,
}) {
  if (!session) {
    return (
      <div className="mx-4 mt-3 rounded-3xl border border-cyan-200 bg-[linear-gradient(135deg,rgba(236,254,255,0.96),rgba(248,250,252,0.96))] px-4 py-4 shadow-sm dark:border-cyan-900/60 dark:bg-[linear-gradient(135deg,rgba(15,23,42,0.92),rgba(8,47,73,0.82))]">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300">
              Meta-Training
            </p>
            <p className="mt-1 text-sm font-semibold text-slate-950 dark:text-white">
              Эпистемологический спарринг
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-300">
              Режим для тренировки вопросов, рамок и работы с неопределённостью.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={() => void onStart()}
              className="rounded-2xl bg-cyan-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-cyan-600 disabled:opacity-50"
            >
              Запустить
            </button>
          </div>
        </div>
      </div>
    );
  }

  const scores = session.scores || {};
  const completed = session.phase === "completed";
  const detectedLabel = QUESTION_TYPE_LABELS[detectedQuestionType] || null;
  const detectedHint = QUESTION_TYPE_HINTS[detectedQuestionType] || detectedQuestionHint || null;

  if (compact) {
    return (
      <div className="mx-3 mt-3 rounded-3xl border border-cyan-200 bg-[radial-gradient(circle_at_top_left,_rgba(34,211,238,0.16),_transparent_30%),linear-gradient(135deg,rgba(236,254,255,0.96),rgba(248,250,252,0.96))] px-4 py-4 shadow-sm sm:mx-4 dark:border-cyan-900/60 dark:bg-[radial-gradient(circle_at_top_left,_rgba(6,182,212,0.2),_transparent_28%),linear-gradient(135deg,rgba(15,23,42,0.92),rgba(8,47,73,0.82))]">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-700 dark:text-cyan-300">
                {PHASE_LABELS[session.phase] || "Meta-training"}
              </span>
              <span className="rounded-full bg-white/80 px-2 py-1 text-[11px] font-semibold text-cyan-950 dark:bg-slate-950/40 dark:text-cyan-100">
                {formatRemaining(session.time_remaining_seconds)}
              </span>
              {detectedLabel ? (
                <span className="rounded-full bg-cyan-100 px-2 py-1 text-[11px] font-semibold text-cyan-900 dark:bg-cyan-950/50 dark:text-cyan-100">
                  {detectedLabel}
                </span>
              ) : null}
            </div>
            <p className="mt-2 text-sm font-semibold leading-6 text-slate-950 dark:text-white">
              {session.thesis}
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-300">
              Роль: <span className="font-semibold text-slate-900 dark:text-white">{session.role_label}</span>
            </p>
            {detectedHint ? (
              <p className="mt-2 text-xs leading-5 text-cyan-900/90 dark:text-cyan-100/90">
                {detectedHint}
              </p>
            ) : null}
            {detectedAssumptionHint ? (
              <p className="mt-1 text-xs leading-5 text-cyan-800/85 dark:text-cyan-100/80">
                Скрытое допущение: {detectedAssumptionHint}
              </p>
            ) : null}
            {diversityHint ? (
              <p className="mt-2 rounded-2xl border border-cyan-200/80 bg-white/70 px-3 py-2 text-xs leading-5 text-cyan-900 dark:border-cyan-800/60 dark:bg-slate-950/30 dark:text-cyan-100">
                {diversityHint}
              </p>
            ) : null}
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="rounded-2xl border border-slate-200 bg-white/80 px-3 py-2 text-right text-xs dark:border-slate-700 dark:bg-slate-950/30">
              <div className="text-slate-500 dark:text-slate-400">Radar</div>
              <div className="font-semibold text-slate-950 dark:text-white">{scores.total || 0}/50</div>
            </div>
            <button
              type="button"
              onClick={onExit}
              className="text-xs font-medium text-slate-600 underline underline-offset-4 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
            >
              Выйти из режима
            </button>
          </div>
        </div>
        {completed ? (
          <div className="mt-3 rounded-2xl border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs text-emerald-950 dark:border-emerald-700/50 dark:bg-emerald-950/30 dark:text-emerald-100">
            Начислено: {session.awarded_wisdom_points || 0} Wisdom Points.
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div className="mx-4 mt-3 overflow-hidden rounded-[2rem] border border-slate-200 bg-white/95 shadow-sm dark:border-slate-800 dark:bg-slate-900/55">
      <div className="border-b border-slate-200 bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.18),_transparent_30%),linear-gradient(135deg,rgba(12,74,110,0.04),rgba(251,191,36,0.07))] px-5 py-5 dark:border-slate-800 dark:bg-[radial-gradient(circle_at_top_left,_rgba(6,182,212,0.18),_transparent_32%),linear-gradient(135deg,rgba(8,47,73,0.6),rgba(69,26,3,0.28))]">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-4xl">
            <p className="text-xs font-semibold uppercase tracking-[0.26em] text-cyan-700 dark:text-cyan-300">
              {PHASE_LABELS[session.phase] || "Meta-training"}
            </p>
            <h2 className="mt-2 text-xl font-semibold leading-8 text-slate-950 dark:text-white">
              {session.thesis}
            </h2>
            <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
              Сейчас роль Socrates-AI: <span className="font-semibold text-slate-900 dark:text-white">{session.role_label}</span>
            </p>
            {session.phase === "orientation" && detectedLabel ? (
              <div className="mt-3 max-w-2xl rounded-2xl border border-cyan-300/70 bg-cyan-50 px-3 py-3 text-xs text-cyan-950 dark:border-cyan-700/50 dark:bg-cyan-950/40 dark:text-cyan-100">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] uppercase tracking-[0.18em] text-cyan-700 dark:text-cyan-300">
                    Последний тип
                  </span>
                  <span className="rounded-full bg-white/80 px-2 py-0.5 font-semibold text-cyan-950 dark:bg-slate-950/40 dark:text-cyan-100">
                    {detectedLabel}
                  </span>
                </div>
                {detectedHint ? (
                  <p className="mt-2 leading-5 text-cyan-900/90 dark:text-cyan-100/90">
                    {detectedHint}
                  </p>
                ) : null}
                {detectedAssumptionHint ? (
                  <p className="mt-2 leading-5 text-cyan-800/85 dark:text-cyan-100/80">
                    Скрытое допущение: {detectedAssumptionHint}
                  </p>
                ) : null}
                {diversityHint ? (
                  <p className="mt-2 rounded-xl border border-cyan-200/80 bg-white/70 px-3 py-2 leading-5 text-cyan-900 dark:border-cyan-800/60 dark:bg-slate-950/30 dark:text-cyan-100">
                    {diversityHint}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="rounded-2xl border border-cyan-300/60 bg-cyan-50 px-4 py-2 text-right dark:border-cyan-700/40 dark:bg-cyan-950/40">
              <div className="text-[11px] font-semibold uppercase tracking-[0.22em] text-cyan-800 dark:text-cyan-200">
                Таймер фазы
              </div>
              <div className="mt-1 text-2xl font-bold text-cyan-950 dark:text-white">
                {formatRemaining(session.time_remaining_seconds)}
              </div>
            </div>
            <button
              type="button"
              onClick={onExit}
              className="text-sm font-medium text-slate-600 underline underline-offset-4 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
            >
              Выйти из режима
            </button>
          </div>
        </div>
      </div>
      <div className="grid gap-6 px-5 py-5 lg:grid-cols-[1.25fr_0.75fr]">
        <div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-950/35">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Мои вопросы</p>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {session.questions?.length || 0} зафиксировано
              </span>
            </div>
            <div className="mt-3 space-y-3">
              {session.questions?.length ? (
                session.questions.slice(-5).map((item) => (
                  <div key={item.id} className="rounded-xl border border-slate-200 bg-white px-3 py-3 dark:border-slate-800 dark:bg-slate-900/80">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full bg-cyan-100 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-cyan-900 dark:bg-cyan-950/50 dark:text-cyan-100">
                        {item.question_type}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-slate-800 dark:text-slate-100">{item.text}</p>
                    {item.assumption ? (
                      <p className="mt-2 text-xs leading-5 text-slate-500 dark:text-slate-400">
                        Скрытое допущение: {item.assumption}
                      </p>
                    ) : null}
                  </div>
                ))
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Пока пусто. В первой фазе цель — задавать вопросы, а не отвечать.
                </p>
              )}
            </div>
          </div>
          <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950/35">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Рамки</p>
              <span className="text-xs text-slate-500 dark:text-slate-400">
                {session.frames?.length || 0} переключений
              </span>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {session.frames?.length ? (
                session.frames.map((frame, index) => (
                  <span
                    key={`${frame.name}-${index}`}
                    className="rounded-full border border-amber-300 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900 dark:border-amber-700/50 dark:bg-amber-950/40 dark:text-amber-100"
                  >
                    {frame.name}
                  </span>
                ))
              ) : (
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  Во второй фазе явно выбери перспективу: физика, информация, философия и т.д.
                </p>
              )}
            </div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-950/35">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Wisdom Radar</p>
            <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white dark:bg-white dark:text-slate-950">
              {scores.total || 0}/50
            </span>
          </div>
          <div className="mt-3 flex justify-center">
            <RadarChart scores={scores} />
          </div>
          <div className="space-y-2">
            {SCORE_LABELS.map((item) => (
              <div key={item.key} className="flex items-center justify-between text-sm text-slate-700 dark:text-slate-300">
                <span>{item.label}</span>
                <span className="font-semibold text-slate-950 dark:text-white">{scores[item.key] || 0}/10</span>
              </div>
            ))}
          </div>
          {completed ? (
            <div className="mt-4 rounded-2xl border border-emerald-300 bg-emerald-50 px-4 py-3 text-sm text-emerald-950 dark:border-emerald-700/50 dark:bg-emerald-950/30 dark:text-emerald-100">
              <p className="font-semibold">Сессия завершена</p>
              <p className="mt-1">Начислено: {session.awarded_wisdom_points || 0} Wisdom Points.</p>
              {session.reflection_summary ? (
                <p className="mt-2 text-emerald-900/85 dark:text-emerald-100/85">
                  Твоя рефлексия: {session.reflection_summary}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

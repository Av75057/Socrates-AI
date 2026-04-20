function statusIcon(topic, progress) {
  const p = progress?.[topic];
  if (p === "completed") return "✔";
  if (p === "in_progress") return "◐";
  return "⬜";
}

export default function UserMemoryPanel({ memory, className = "" }) {
  const topics = memory?.topics?.length ? memory.topics : [];
  const mistakes = memory?.mistakes?.length ? memory.mistakes : [];
  const progress = memory?.progress && typeof memory.progress === "object" ? memory.progress : {};

  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white/70 p-3 text-xs text-slate-600 dark:border-slate-700/60 dark:bg-slate-900/35 dark:text-slate-400 ${className}`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Память тьютора</p>

      <div className="mt-2">
        <span className="text-slate-500">Темы:</span>{" "}
        {topics.length ? (
          <ul className="mt-1 space-y-1 text-slate-800 dark:text-slate-300">
            {topics.map((t) => (
              <li key={t} className="flex items-start gap-2">
                <span className="shrink-0" aria-hidden>
                  {statusIcon(t, progress)}
                </span>
                <span>{t}</span>
              </li>
            ))}
          </ul>
        ) : (
          <span className="text-slate-500 dark:text-slate-600">появятся по мере занятий</span>
        )}
      </div>

      {mistakes.length ? (
        <div className="mt-3 border-t border-slate-200 pt-2 dark:border-slate-800/80">
          <span className="text-slate-500">Затруднения:</span>
          <ul className="mt-1 space-y-1 text-slate-600 dark:text-slate-400">
            {mistakes.slice(-6).map((m, i) => (
              <li key={`${m.topic ?? ""}-${m.error ?? ""}-${i}`}>
                <span className="text-slate-500 dark:text-slate-600">{m.topic ?? "—"}:</span> {m.error}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

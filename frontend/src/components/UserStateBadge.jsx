const LABELS = {
  lazy: "😴 Начинаем думать",
  anxious: "😰 Не переживай — в своём темпе",
  thinker: "🧠 Копаем глубже",
};

export default function UserStateBadge({ type }) {
  const t = type && LABELS[type] ? type : "lazy";
  return (
    <div className="shrink-0 border-b border-slate-200 bg-slate-100/90 px-4 py-1.5 text-center text-xs text-slate-600 dark:border-slate-800/60 dark:bg-[#0f172a]/60 dark:text-slate-400">
      {LABELS[t]}
    </div>
  );
}

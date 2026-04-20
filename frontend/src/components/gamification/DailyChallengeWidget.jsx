export default function DailyChallengeWidget({ text, completed, loading }) {
  if (loading) {
    return (
      <div className="mx-4 mt-2 rounded-xl border border-slate-200 bg-slate-100 px-4 py-3 text-sm text-slate-600 dark:border-slate-700/80 dark:bg-slate-900/50 dark:text-slate-500">
        Загружаем вызов дня…
      </div>
    );
  }

  if (!text) return null;

  return (
    <div
      className={`mx-4 mt-2 rounded-xl border px-4 py-3 text-sm ${
        completed
          ? "border-emerald-500/50 bg-emerald-50 text-emerald-950 dark:border-emerald-500/40 dark:bg-emerald-950/30 dark:text-emerald-100"
          : "border-violet-500/45 bg-violet-50 text-violet-950 dark:border-violet-500/35 dark:bg-violet-950/25 dark:text-violet-100"
      }`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
        Вызов дня (UTC)
      </p>
      <p className="mt-1 font-medium leading-snug">{text}</p>
      <p className="mt-2 text-xs text-slate-600 dark:text-slate-400">
        {completed ? "✓ Выполнено — бонус начислен сегодня." : "Выполни условие в ответе тьютору — проверка автоматическая."}
      </p>
    </div>
  );
}

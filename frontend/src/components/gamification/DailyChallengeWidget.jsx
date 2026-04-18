export default function DailyChallengeWidget({ text, completed, loading }) {
  if (loading) {
    return (
      <div className="mx-4 mt-2 rounded-xl border border-slate-700/80 bg-slate-900/50 px-4 py-3 text-sm text-slate-500">
        Загружаем вызов дня…
      </div>
    );
  }

  if (!text) return null;

  return (
    <div
      className={`mx-4 mt-2 rounded-xl border px-4 py-3 text-sm ${
        completed
          ? "border-emerald-500/40 bg-emerald-950/30 text-emerald-100"
          : "border-violet-500/35 bg-violet-950/25 text-violet-100"
      }`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">Вызов дня (UTC)</p>
      <p className="mt-1 font-medium leading-snug">{text}</p>
      <p className="mt-2 text-xs text-slate-400">
        {completed ? "✓ Выполнено — бонус начислен сегодня." : "Выполни условие в ответе тьютору — проверка автоматическая."}
      </p>
    </div>
  );
}

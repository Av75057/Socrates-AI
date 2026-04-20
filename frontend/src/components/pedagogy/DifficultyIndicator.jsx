export default function DifficultyIndicator({ level = 1 }) {
  const lv = Math.min(5, Math.max(1, Number(level) || 1));
  const colors = ["bg-rose-500", "bg-orange-500", "bg-amber-400", "bg-lime-500", "bg-emerald-500"];

  return (
    <div
      className="flex items-center gap-1.5"
      title="Текущий уровень сложности. Задавай более глубокие ответы с аргументацией, чтобы повысить его. Подсказка слегка снижает уровень."
    >
      <span className="hidden text-[10px] font-medium uppercase tracking-wide text-slate-500 sm:inline">
        Сложность
      </span>
      <div className="flex gap-0.5" role="img" aria-label={`Сложность ${lv} из 5`}>
        {[1, 2, 3, 4, 5].map((i) => (
          <span
            key={i}
            className={`h-2 w-5 rounded-full sm:h-2.5 sm:w-6 ${i <= lv ? colors[lv - 1] : "bg-slate-300 dark:bg-slate-700"}`}
          />
        ))}
      </div>
      <span className="tabular-nums text-[11px] font-bold text-slate-600 dark:text-slate-400">{lv}/5</span>
    </div>
  );
}

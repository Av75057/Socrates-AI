const MODES = {
  question: {
    label: "Думаем",
    short: "Вопросы",
    color: "bg-emerald-500",
    ring: "ring-emerald-500/40",
    emoji: "🟢",
  },
  hint: {
    label: "Подсказка",
    short: "Намёк",
    color: "bg-amber-400",
    ring: "ring-amber-400/40",
    emoji: "🟡",
  },
  explain: {
    label: "Объяснение",
    short: "Разбор",
    color: "bg-rose-500",
    ring: "ring-rose-500/40",
    emoji: "🔴",
  },
};

export default function ModeIndicator({ mode, attempts, frustration }) {
  const m = MODES[mode] || MODES.question;
  return (
    <>
      <div className="border-b border-slate-800/80 bg-[#0f172a]/80 px-4 py-1.5 text-center text-xs text-slate-400 lg:hidden">
        <span aria-hidden>{m.emoji}</span> {m.label}
      </div>
      <div className="hidden flex-wrap items-center gap-3 border-b border-slate-800/80 bg-[#0f172a]/80 px-4 py-2.5 lg:flex">
        <div
          className={`inline-flex min-h-[44px] items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold text-white ${m.color} ring-2 ${m.ring}`}
        >
          <span aria-hidden>{m.emoji}</span>
          <span>{m.label}</span>
        </div>
        <div className="text-xs text-slate-500">
          Вовлечённость: <span className="text-slate-300">{attempts}</span> шагов · напряжение:{" "}
          <span className="text-slate-300">{frustration}</span>
        </div>
      </div>
    </>
  );
}

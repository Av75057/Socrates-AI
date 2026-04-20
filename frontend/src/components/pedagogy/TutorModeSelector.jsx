const MODES = [
  { id: "friendly", label: "Дружелюбный", short: "Друг" },
  { id: "strict", label: "Строгий", short: "Строго" },
  { id: "provocateur", label: "Провокатор", short: "Провок." },
];

export default function TutorModeSelector({ value, onChange, disabled }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Режим тьютора">
      <span className="hidden text-[10px] font-medium uppercase tracking-wide text-slate-500 sm:inline">
        Режим
      </span>
      {MODES.map((m) => (
        <button
          key={m.id}
          type="button"
          disabled={disabled}
          onClick={() => onChange(m.id)}
          title={m.label}
          className={`min-h-[36px] rounded-lg px-2 py-1.5 text-[11px] font-semibold transition disabled:opacity-40 sm:px-2.5 sm:text-xs ${
            value === m.id
              ? "bg-amber-200 text-amber-950 ring-1 ring-amber-500/60 dark:bg-amber-500/25 dark:text-amber-100 dark:ring-amber-500/50"
              : "border border-slate-300 bg-white text-slate-700 active:bg-slate-100 [@media(hover:hover)]:hover:border-slate-400 dark:border-slate-600/80 dark:bg-slate-900/80 dark:text-slate-300 dark:active:bg-slate-800 dark:[@media(hover:hover)]:hover:border-slate-500"
          }`}
        >
          <span className="sm:hidden">{m.short}</span>
          <span className="hidden sm:inline">{m.label}</span>
        </button>
      ))}
    </div>
  );
}

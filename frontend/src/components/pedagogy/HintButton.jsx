export default function HintButton({ onClick, disabled, visible }) {
  if (!visible) return null;

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="min-h-[36px] shrink-0 rounded-lg border border-sky-500/45 bg-sky-950/40 px-2.5 py-1.5 text-[11px] font-semibold text-sky-100 transition disabled:opacity-40 sm:text-xs [@media(hover:hover)]:hover:bg-sky-900/50"
      title="Отдельная подсказка (снижает уровень сложности)"
    >
      Подскажи
    </button>
  );
}

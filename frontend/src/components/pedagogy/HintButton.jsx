export default function HintButton({ onClick, disabled, visible }) {
  if (!visible) return null;

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="min-h-[36px] shrink-0 rounded-lg border border-sky-500/50 bg-sky-100 px-2.5 py-1.5 text-[11px] font-semibold text-sky-900 transition disabled:opacity-40 sm:text-xs [@media(hover:hover)]:hover:bg-sky-200 dark:border-sky-500/45 dark:bg-sky-950/40 dark:text-sky-100 dark:[@media(hover:hover)]:hover:bg-sky-900/50"
      title="Отдельная подсказка (снижает уровень сложности)"
    >
      Подскажи
    </button>
  );
}

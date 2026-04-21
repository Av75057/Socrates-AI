const VARIANT = {
  neutral:
    "border border-slate-300/90 bg-white text-slate-800 active:bg-slate-100 [@media(hover:hover)]:hover:border-slate-400 dark:border-slate-600/70 dark:bg-[#0f172a] dark:text-slate-200 dark:active:bg-slate-800 dark:[@media(hover:hover)]:hover:border-slate-500",
  amber:
    "border border-amber-600/45 bg-amber-100 font-medium text-amber-950 active:bg-amber-200 [@media(hover:hover)]:hover:bg-amber-200 dark:border-amber-500/45 dark:bg-amber-500/12 dark:text-amber-100 dark:active:bg-amber-500/22 dark:[@media(hover:hover)]:hover:bg-amber-500/18",
  rose:
    "border border-rose-500/45 bg-rose-100 font-medium text-rose-900 active:bg-rose-200 [@media(hover:hover)]:hover:bg-rose-200 dark:border-rose-500/45 dark:bg-rose-500/12 dark:text-rose-100 dark:active:bg-rose-500/22 dark:[@media(hover:hover)]:hover:bg-rose-500/18",
};

const BASE =
  "touch-manipulation inline-flex max-h-9 shrink-0 items-center justify-center gap-1 rounded-full px-2 py-1 text-[11px] font-medium leading-none disabled:cursor-not-allowed disabled:opacity-40 sm:max-h-10 sm:gap-1.5 sm:px-3 sm:py-1.5 sm:text-xs md:text-sm";

/**
 * Компактный ряд быстрых действий над полем ввода.
 * @param {{ key: string, label: string, title?: string, icon: React.ReactNode, variant: keyof VARIANT, onClick: () => void, needsSendGate?: boolean }[]} actions
 * needsSendGate: false для «Подсказка» / «Объясни проще» (как в InputBox — только loading).
 */
export default function ActionButtonsRow({ actions, loading, canSend }) {
  return (
    <div
      data-tour="quick-actions"
      role="toolbar"
      aria-label="Быстрые действия"
      className="flex w-full flex-wrap content-center items-center gap-1.5 sm:gap-2 lg:flex-nowrap lg:gap-2 lg:justify-start"
    >
      {actions.map((a) => {
        const gated = a.needsSendGate !== false;
        const disabled = loading || (gated && !canSend());
        return (
          <button
            key={a.key}
            type="button"
            title={a.title || a.label}
            disabled={disabled}
            onClick={a.onClick}
            className={`${BASE} ${VARIANT[a.variant] ?? VARIANT.neutral}`}
          >
            <span className="[&_svg]:size-3.5 sm:[&_svg]:size-4" aria-hidden>
              {a.icon}
            </span>
            <span className="whitespace-nowrap max-sm:max-w-[26vw] max-sm:truncate sm:max-w-none">
              {a.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}

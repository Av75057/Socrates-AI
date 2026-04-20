export default function GamificationToastHost({ items, onDismiss }) {
  if (!items.length) return null;

  return (
    <div className="pointer-events-none fixed right-3 top-3 z-[100] flex max-w-sm flex-col gap-2 sm:right-5 sm:top-5">
      {items.map((it) => (
        <div
          key={it.id}
          className={`pointer-events-auto animate-toastIn rounded-xl border px-4 py-3 text-sm font-medium shadow-lg ${
            it.kind === "achievement"
              ? "border-emerald-500/50 bg-emerald-50 text-emerald-950 shadow-emerald-900/10 dark:bg-emerald-950/95 dark:text-emerald-50 dark:shadow-black/40"
              : "border-blue-500/50 bg-blue-50 text-blue-950 shadow-blue-900/10 dark:bg-blue-950/95 dark:text-blue-50 dark:shadow-black/40"
          }`}
        >
          {it.text}
          <button
            type="button"
            className="ml-3 align-middle text-xs text-slate-600 underline-offset-2 hover:text-slate-900 hover:underline dark:text-white/60 dark:hover:text-white"
            onClick={() => onDismiss(it.id)}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

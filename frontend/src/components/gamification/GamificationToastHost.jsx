export default function GamificationToastHost({ items, onDismiss }) {
  if (!items.length) return null;

  return (
    <div className="pointer-events-none fixed right-3 top-3 z-[100] flex max-w-sm flex-col gap-2 sm:right-5 sm:top-5">
      {items.map((it) => (
        <div
          key={it.id}
          className={`pointer-events-auto animate-toastIn rounded-xl border px-4 py-3 text-sm font-medium shadow-lg shadow-black/40 ${
            it.kind === "achievement"
              ? "border-emerald-500/50 bg-emerald-950/95 text-emerald-50"
              : "border-blue-500/50 bg-blue-950/95 text-blue-50"
          }`}
        >
          {it.text}
          <button
            type="button"
            className="ml-3 align-middle text-xs text-white/60 underline-offset-2 hover:text-white hover:underline"
            onClick={() => onDismiss(it.id)}
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}

import { useEffect } from "react";

export default function FallacyNotification({ fallacy, onDismiss }) {
  useEffect(() => {
    if (!fallacy?.has_fallacy) return undefined;
    const t = setTimeout(() => onDismiss?.(), 8000);
    return () => clearTimeout(t);
  }, [fallacy, onDismiss]);

  if (!fallacy?.has_fallacy) return null;

  return (
    <div className="pointer-events-auto animate-toastIn mx-4 mt-2 rounded-xl border border-amber-500/45 bg-amber-950/90 px-4 py-3 text-sm text-amber-50 shadow-lg shadow-black/30">
      <div className="flex gap-2">
        <span className="text-lg leading-none" aria-hidden>
          ⚠️
        </span>
        <div className="min-w-0 flex-1">
          <p className="font-display font-semibold text-amber-100">Логика ответа</p>
          {fallacy.fallacy_type ? (
            <p className="mt-0.5 text-[11px] uppercase tracking-wide text-amber-200/80">
              {fallacy.fallacy_type.replace(/_/g, " ")}
            </p>
          ) : null}
          {fallacy.fallacy_description ? (
            <p className="mt-1 leading-snug text-amber-50/95">{fallacy.fallacy_description}</p>
          ) : null}
          {fallacy.suggestion ? (
            <p className="mt-2 text-xs text-amber-200/90">💡 {fallacy.suggestion}</p>
          ) : null}
        </div>
        <button
          type="button"
          className="shrink-0 text-amber-300/80 hover:text-amber-100"
          aria-label="Закрыть"
          onClick={() => onDismiss?.()}
        >
          ✕
        </button>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";

export default function WisdomPointsBadge({ points = 0, level = 1, onClick, bumpSignal = 0 }) {
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    if (!bumpSignal) return undefined;
    setPulse(true);
    const t = setTimeout(() => setPulse(false), 900);
    return () => clearTimeout(t);
  }, [bumpSignal]);

  return (
    <button
      type="button"
      onClick={onClick}
      title="Очки мудрости и достижения"
      className={`inline-flex min-h-[44px] items-center gap-2 rounded-full border border-amber-500/40 bg-slate-900/90 px-3 py-1.5 text-amber-200 shadow-md transition active:scale-[0.98] sm:min-h-0 [@media(hover:hover)]:hover:border-amber-400/60 [@media(hover:hover)]:hover:bg-slate-800/90 ${
        pulse ? "animate-wisdomPulse" : ""
      }`}
    >
      <span className="text-lg leading-none" aria-hidden>
        🦉
      </span>
      <span className="font-display text-sm font-bold tabular-nums text-amber-300">{points}</span>
      <span className="hidden text-[10px] font-medium uppercase tracking-wide text-amber-500/90 sm:inline">
        ур. {level}
      </span>
    </button>
  );
}

import { useEffect, useState } from "react";
import { ChevronLeft } from "lucide-react";

const LS_KEY = "socrates_daily_challenge_sidebar_collapsed";

function loadCollapsed() {
  try {
    return localStorage.getItem(LS_KEY) === "1";
  } catch {
    return false;
  }
}

function saveCollapsed(v) {
  try {
    localStorage.setItem(LS_KEY, v ? "1" : "0");
  } catch {
    /* ignore */
  }
}

/**
 * Компактный блок «Вызов дня» для правой боковой панели (lg+).
 * Подробности открываются через onOpenDetails (общая модалка в ChatPage).
 */
export default function DailyChallengeCompact({ text, completed, loading, onOpenDetails }) {
  const [collapsed, setCollapsed] = useState(loadCollapsed);

  useEffect(() => {
    saveCollapsed(collapsed);
  }, [collapsed]);

  if (loading) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-100/90 px-3 py-2 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800/50">
        Загружаем вызов дня…
      </div>
    );
  }

  if (!text) return null;

  const line = text.length > 50 ? `${text.slice(0, 50)}…` : text;

  if (collapsed) {
    return (
      <div className="flex items-stretch gap-0">
        <button
          type="button"
          title="Показать вызов дня"
          aria-label="Развернуть вызов дня"
          onClick={() => setCollapsed(false)}
          className="flex w-8 shrink-0 items-center justify-center rounded-l-lg border border-r-0 border-slate-200 bg-white text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
        >
          <ChevronLeft className="h-4 w-4 rotate-180" />
        </button>
        <div className="min-w-0 flex-1 rounded-r-lg border border-slate-200 bg-violet-50/90 px-2 py-2 text-center dark:border-violet-900/50 dark:bg-violet-950/40">
          <span className="text-lg" aria-hidden>
            🎯
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex gap-0 rounded-xl border border-violet-500/35 bg-violet-50/95 dark:border-violet-500/30 dark:bg-violet-950/35">
      <button
        type="button"
        title="Свернуть блок"
        aria-label="Свернуть вызов дня"
        onClick={() => setCollapsed(true)}
        className="flex w-7 shrink-0 items-center justify-center rounded-l-[0.65rem] border-r border-violet-400/30 text-slate-600 hover:bg-violet-100/80 dark:border-violet-700/50 dark:text-slate-400 dark:hover:bg-violet-900/40"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      <div className="min-w-0 flex-1 py-2 pl-1 pr-2">
        <div className="flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-violet-800 dark:text-violet-300/90">
          <span aria-hidden>🎯</span> Вызов дня
        </div>
        <p className="mt-0.5 truncate text-xs font-medium leading-snug text-violet-950 dark:text-violet-100" title={text}>
          {line}
        </p>
        <div className="mt-1.5 flex flex-wrap items-center gap-2">
          <span
            className={`inline-flex items-center gap-1 text-[10px] font-medium ${
              completed ? "text-emerald-700 dark:text-emerald-400" : "text-slate-600 dark:text-slate-400"
            }`}
          >
            {completed ? "✓ Выполнено" : "○ Не выполнено"}
          </span>
          <button
            type="button"
            onClick={() => onOpenDetails?.()}
            className="text-[11px] font-medium text-cyan-700 underline hover:text-cyan-600 dark:text-cyan-400"
          >
            Подробнее
          </button>
        </div>
      </div>
    </div>
  );
}

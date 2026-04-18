import { Link } from "react-router-dom";

export default function SessionHeader({ topic, onNewSession, xp = 0, streak = 0, wisdomSlot = null }) {
  return (
    <header className="shrink-0 border-b border-slate-800/90 bg-[#0f172a]/95 px-3 py-2 backdrop-blur sm:px-4 sm:py-3">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <Link
              to="/"
              className="inline-flex min-h-[44px] min-w-[44px] items-center text-xs font-medium text-slate-500 active:text-slate-300 sm:min-h-0 sm:min-w-0 [@media(hover:hover)]:hover:text-slate-300"
            >
              ← На главную
            </Link>
            {wisdomSlot}
            <span className="text-xs tabular-nums text-slate-500 lg:hidden">
              XP <span className="text-cyan-300">{xp}</span>
              <span className="mx-1.5 text-slate-700">·</span>
              {streak > 0 ? (
                <>
                  <span aria-hidden>🔥</span> {streak}
                </>
              ) : (
                <span className="text-slate-600">серия —</span>
              )}
            </span>
          </div>
          <div className="mt-0.5 flex flex-wrap items-baseline gap-2 sm:mt-1">
            <h1 className="font-display text-lg font-bold tracking-tight text-white sm:text-xl">Socrates AI</h1>
            <span className="hidden rounded-full bg-slate-800/80 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-500 sm:inline">
              обучающая игра
            </span>
          </div>
          <p className="mt-0.5 truncate text-sm text-slate-400 sm:mt-1">
            {topic ? (
              <>
                <span className="text-slate-500">Тема: </span>
                <span className="text-slate-200">{topic}</span>
              </>
            ) : (
              <span className="text-slate-500">Задай тему: «Хочу изучить …»</span>
            )}
          </p>
        </div>
        <button
          type="button"
          onClick={onNewSession}
          className="min-h-[44px] shrink-0 touch-manipulation rounded-xl border border-slate-600/80 px-4 py-2.5 text-xs font-medium text-slate-300 active:bg-slate-800/80 [@media(hover:hover)]:hover:border-slate-500 [@media(hover:hover)]:hover:bg-slate-800/80 sm:min-h-0 sm:py-2"
        >
          Новая сессия
        </button>
      </div>
    </header>
  );
}

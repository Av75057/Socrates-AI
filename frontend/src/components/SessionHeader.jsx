import { Link } from "react-router-dom";

export default function SessionHeader({ topic, onNewSession }) {
  return (
    <header className="shrink-0 border-b border-slate-800/90 bg-[#0f172a]/95 px-4 py-3 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/"
              className="text-xs font-medium text-slate-500 transition hover:text-slate-300"
            >
              ← На главную
            </Link>
          </div>
          <div className="mt-1 flex flex-wrap items-baseline gap-2">
            <h1 className="font-display text-xl font-bold tracking-tight text-white">Socrates AI</h1>
            <span className="rounded-full bg-slate-800/80 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-500">
              обучающая игра
            </span>
          </div>
          <p className="mt-1 truncate text-sm text-slate-400">
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
          className="shrink-0 rounded-xl border border-slate-600/80 px-4 py-2 text-xs font-medium text-slate-300 transition hover:border-slate-500 hover:bg-slate-800/80"
        >
          Новая сессия
        </button>
      </div>
    </header>
  );
}

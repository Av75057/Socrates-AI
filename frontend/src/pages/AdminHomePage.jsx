import { Link } from "react-router-dom";

export default function AdminHomePage() {
  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Админ-панель</h1>
      <p className="mt-2 max-w-xl text-sm text-slate-600 dark:text-slate-400">
        Управление пользователями и обзор метрик. Доступ только для учётных записей с ролью{" "}
        <code className="text-amber-800 dark:text-amber-200/90">admin</code>.
      </p>
      <ul className="mt-10 flex flex-col gap-4 sm:flex-row">
        <li>
          <Link
            to="/admin/users"
            className="block rounded-xl border border-amber-500/50 bg-amber-50 px-6 py-5 font-medium text-amber-950 transition hover:border-amber-600 dark:border-amber-600/40 dark:bg-amber-950/25 dark:text-amber-100 dark:hover:border-amber-500/60"
          >
            Пользователи
            <span className="mt-1 block text-xs font-normal text-amber-800 dark:text-amber-200/70">
              Список, блокировка, удаление
            </span>
          </Link>
        </li>
        <li>
          <Link
            to="/admin/stats"
            className="block rounded-xl border border-cyan-500/45 bg-cyan-50 px-6 py-5 font-medium text-cyan-950 transition hover:border-cyan-600 dark:border-cyan-700/40 dark:bg-cyan-950/20 dark:text-cyan-100 dark:hover:border-cyan-500/50"
          >
            Статистика
            <span className="mt-1 block text-xs font-normal text-cyan-800 dark:text-cyan-200/70">
              Сводка по базе
            </span>
          </Link>
        </li>
        <li>
          <Link
            to="/admin/llm"
            className="block rounded-xl border border-violet-500/45 bg-violet-50 px-6 py-5 font-medium text-violet-950 transition hover:border-violet-600 dark:border-violet-700/40 dark:bg-violet-950/25 dark:text-violet-100 dark:hover:border-violet-500/50"
          >
            LLM (Ollama / OpenRouter)
            <span className="mt-1 block text-xs font-normal text-violet-800 dark:text-violet-200/70">
              Провайдер, тест, модель
            </span>
          </Link>
        </li>
        <li>
          <Link
            to="/admin/topics"
            className="block rounded-xl border border-emerald-500/45 bg-emerald-50 px-6 py-5 font-medium text-emerald-950 transition hover:border-emerald-600 dark:border-emerald-700/40 dark:bg-emerald-950/25 dark:text-emerald-100 dark:hover:border-emerald-500/50"
          >
            Темы для обсуждения
            <span className="mt-1 block text-xs font-normal text-emerald-800 dark:text-emerald-200/70">
              Библиотека, premium, AI-черновики
            </span>
          </Link>
        </li>
      </ul>
      <p className="mt-10 text-sm">
        <Link to="/app" className="text-slate-600 underline hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-300">
          ← В чат
        </Link>
      </p>
    </div>
  );
}

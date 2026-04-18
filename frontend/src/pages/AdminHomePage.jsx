import { Link } from "react-router-dom";

export default function AdminHomePage() {
  return (
    <div className="min-h-screen bg-[#0f172a] px-6 py-10 text-slate-100">
      <h1 className="font-display text-2xl font-bold text-white">Админ-панель</h1>
      <p className="mt-2 max-w-xl text-sm text-slate-400">
        Управление пользователями и обзор метрик. Доступ только для учётных записей с ролью{" "}
        <code className="text-amber-200/90">admin</code>.
      </p>
      <ul className="mt-10 flex flex-col gap-4 sm:flex-row">
        <li>
          <Link
            to="/admin/users"
            className="block rounded-xl border border-amber-600/40 bg-amber-950/25 px-6 py-5 font-medium text-amber-100 transition hover:border-amber-500/60"
          >
            Пользователи
            <span className="mt-1 block text-xs font-normal text-amber-200/70">
              Список, блокировка, удаление
            </span>
          </Link>
        </li>
        <li>
          <Link
            to="/admin/stats"
            className="block rounded-xl border border-cyan-700/40 bg-cyan-950/20 px-6 py-5 font-medium text-cyan-100 transition hover:border-cyan-500/50"
          >
            Статистика
            <span className="mt-1 block text-xs font-normal text-cyan-200/70">
              Сводка по базе
            </span>
          </Link>
        </li>
      </ul>
      <p className="mt-10 text-sm">
        <Link to="/app" className="text-slate-400 underline hover:text-slate-300">
          ← В чат
        </Link>
      </p>
    </div>
  );
}

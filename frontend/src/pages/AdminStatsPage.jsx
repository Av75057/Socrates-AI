import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminStats } from "../api/adminApi.js";

export default function AdminStatsPage() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await adminStats();
        if (!cancelled) setData(s);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Ошибка");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#0f172a] px-6 py-10 text-slate-100">
      <nav className="mb-6 flex flex-wrap gap-4 text-sm">
        <Link to="/admin" className="text-slate-400 underline">
          Админ — главная
        </Link>
        <Link to="/admin/users" className="text-cyan-400 underline">
          Пользователи
        </Link>
        <Link to="/app" className="text-slate-400 underline">
          Чат
        </Link>
      </nav>
      <h1 className="font-display text-2xl font-bold text-white">Статистика</h1>
      {error ? <p className="mt-4 text-red-400">{error}</p> : null}
      {data ? (
        <div className="mt-8 grid max-w-xl gap-4">
          <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
            <p className="text-slate-500">Пользователей</p>
            <p className="text-2xl font-bold text-white">{data.users_total}</p>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
            <p className="text-slate-500">Диалогов</p>
            <p className="text-2xl font-bold text-white">{data.conversations_total}</p>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
            <p className="text-slate-500">Сообщений</p>
            <p className="text-2xl font-bold text-white">{data.messages_total}</p>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-4">
            <p className="mb-2 text-slate-500">Популярные заголовки</p>
            <ul className="text-sm text-slate-300">
              {(data.popular_titles || []).map((x, i) => (
                <li key={i}>
                  {x.title} — {x.count}
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : !error ? (
        <p className="mt-8 text-slate-500">Загрузка…</p>
      ) : null}
    </div>
  );
}

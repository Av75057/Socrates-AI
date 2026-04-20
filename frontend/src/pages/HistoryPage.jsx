import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listConversations } from "../api/userApi.js";

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await listConversations();
        if (!cancelled) setItems(Array.isArray(data) ? data : []);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Ошибка");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-8 flex gap-4 text-sm">
        <Link to="/profile" className="text-cyan-700 underline dark:text-cyan-400">
          Профиль
        </Link>
        <Link to="/app" className="text-cyan-700 underline dark:text-cyan-400">
          Чат
        </Link>
      </nav>
      <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">История диалогов</h1>
      {error ? <p className="mt-4 text-red-600 dark:text-red-400">{error}</p> : null}
      <ul className="mt-6 space-y-3">
        {items.map((c) => (
          <li key={c.id}>
            <Link
              to={`/profile/history/${c.id}`}
              className="block rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm hover:border-cyan-500/50 dark:border-slate-700 dark:bg-slate-900/40 dark:shadow-none dark:hover:border-cyan-600/50"
            >
              <span className="font-medium text-slate-900 dark:text-slate-100">{c.title}</span>
              <span className="mt-1 block text-xs text-slate-500">
                {c.message_count} сообщ. · обновлён {new Date(c.last_updated_at).toLocaleString()}
              </span>
            </Link>
          </li>
        ))}
      </ul>
      {items.length === 0 && !error ? (
        <p className="mt-8 text-slate-600 dark:text-slate-500">Пока нет сохранённых диалогов. Создайте новый в чате.</p>
      ) : null}
    </div>
  );
}

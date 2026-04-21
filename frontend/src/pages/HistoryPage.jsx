import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listConversations, publishConversation, unpublishConversation } from "../api/userApi.js";

function shareUrlForSlug(slug) {
  return `${window.location.origin}/share/${slug}`;
}

export default function HistoryPage() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

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
          <li
            key={c.id}
            className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm dark:border-slate-700 dark:bg-slate-900/40 dark:shadow-none"
          >
            <Link to={`/profile/history/${c.id}`} className="block hover:text-cyan-700 dark:hover:text-cyan-300">
              <span className="font-medium text-slate-900 dark:text-slate-100">{c.title}</span>
              <span className="mt-1 block text-xs text-slate-500">
                {c.message_count} сообщ. · обновлён {new Date(c.last_updated_at).toLocaleString()}
              </span>
            </Link>
            <div className="mt-3 flex flex-wrap gap-2 border-t border-slate-100 pt-3 dark:border-slate-700/80">
              {c.public_slug ? (
                <>
                  <button
                    type="button"
                    disabled={busyId === c.id}
                    className="rounded-lg border border-amber-500/50 px-2 py-1 text-xs font-medium text-amber-800 hover:bg-amber-50 disabled:opacity-50 dark:text-amber-200 dark:hover:bg-amber-950/40"
                    onClick={async () => {
                      try {
                        await navigator.clipboard.writeText(shareUrlForSlug(c.public_slug));
                      } catch {
                        prompt("Ссылка:", shareUrlForSlug(c.public_slug));
                      }
                    }}
                  >
                    Копировать ссылку
                  </button>
                  <button
                    type="button"
                    disabled={busyId === c.id}
                    className="rounded-lg border border-slate-300 px-2 py-1 text-xs text-slate-700 hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
                    onClick={async () => {
                      setBusyId(c.id);
                      try {
                        await unpublishConversation(c.id);
                        setItems((prev) =>
                          prev.map((x) => (x.id === c.id ? { ...x, public_slug: null } : x)),
                        );
                      } catch (e) {
                        setError(e instanceof Error ? e.message : "Ошибка");
                      } finally {
                        setBusyId(null);
                      }
                    }}
                  >
                    Снять с публикации
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  disabled={busyId === c.id}
                  className="rounded-lg bg-cyan-600 px-2 py-1 text-xs font-medium text-white hover:bg-cyan-500 disabled:opacity-50"
                  onClick={async () => {
                    setBusyId(c.id);
                    try {
                      const r = await publishConversation(c.id);
                      setItems((prev) =>
                        prev.map((x) => (x.id === c.id ? { ...x, public_slug: r.slug } : x)),
                      );
                      try {
                        await navigator.clipboard.writeText(r.share_url);
                      } catch {
                        /* ignore */
                      }
                    } catch (e) {
                      setError(e instanceof Error ? e.message : "Ошибка");
                    } finally {
                      setBusyId(null);
                    }
                  }}
                >
                  {busyId === c.id ? "…" : "Опубликовать"}
                </button>
              )}
            </div>
          </li>
        ))}
      </ul>
      {items.length === 0 && !error ? (
        <p className="mt-8 text-slate-600 dark:text-slate-500">Пока нет сохранённых диалогов. Создайте новый в чате.</p>
      ) : null}
    </div>
  );
}

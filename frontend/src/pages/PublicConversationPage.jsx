import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchPublicShare } from "../api/shareApi.js";

export default function PublicConversationPage() {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const d = await fetchPublicShare(slug);
        if (!cancelled) {
          setData(d);
          document.title = d.title ? `${d.title} · Socrates AI` : "Диалог · Socrates AI";
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Ошибка загрузки");
      }
    })();
    return () => {
      cancelled = true;
      document.title = "Socrates AI";
    };
  }, [slug]);

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-16 text-center text-slate-800 dark:bg-[#020617] dark:text-slate-200">
        <p className="font-display text-lg font-semibold text-red-600 dark:text-red-400">{error}</p>
        <Link to="/" className="mt-6 inline-block text-cyan-600 underline dark:text-cyan-400">
          На главную
        </Link>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-600 dark:bg-[#020617] dark:text-slate-400">
        Загрузка…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 text-slate-900 dark:from-[#0f172a] dark:to-[#020617] dark:text-slate-100">
      <header className="border-b border-slate-200/80 bg-white/90 px-4 py-4 backdrop-blur dark:border-slate-800 dark:bg-[#0f172a]/95">
        <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-amber-600 dark:text-amber-400">Публичный диалог</p>
            <h1 className="font-display text-xl font-bold text-slate-900 dark:text-white">{data.title}</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">Просмотров: {data.views}</p>
          </div>
          <Link
            to="/register"
            className="rounded-full bg-amber-500 px-4 py-2 text-sm font-semibold text-amber-950 shadow-sm hover:bg-amber-400"
          >
            Попробовать самому
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-3xl px-4 py-8">
        <ul className="space-y-4">
          {data.messages.map((m) => (
            <li
              key={m.id}
              className={`rounded-2xl border px-4 py-3 text-sm shadow-sm ${
                m.role === "user"
                  ? "ml-4 border-slate-200 bg-white dark:ml-8 dark:border-slate-600 dark:bg-slate-900/80"
                  : "mr-4 border-cyan-200 bg-cyan-50/90 dark:mr-8 dark:border-cyan-900/50 dark:bg-cyan-950/40"
              }`}
            >
              <p className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                {m.role === "user" ? data.author_label : "Тьютор Socrates"}
              </p>
              <p className="mt-2 whitespace-pre-wrap text-slate-800 dark:text-slate-200">{m.content}</p>
              <p className="mt-2 text-[10px] text-slate-400">{new Date(m.created_at).toLocaleString()}</p>
            </li>
          ))}
        </ul>

        <section className="mt-12 rounded-2xl border border-amber-400/40 bg-amber-50/90 p-6 text-center dark:border-amber-700/40 dark:bg-amber-950/30">
          <h2 className="font-display text-lg font-bold text-slate-900 dark:text-white">Хочешь так же прокачать мышление?</h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Socrates-AI задаёт вопросы, а не подсказывает готовые ответы — попробуй бесплатно.
          </p>
          <div className="mt-4 flex flex-wrap justify-center gap-3">
            <Link
              to="/register"
              className="inline-flex rounded-full bg-amber-500 px-6 py-2.5 text-sm font-semibold text-amber-950 hover:bg-amber-400"
            >
              Зарегистрироваться
            </Link>
            <Link
              to="/app"
              className="inline-flex rounded-full border border-slate-300 px-6 py-2.5 text-sm font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Начать чат
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}

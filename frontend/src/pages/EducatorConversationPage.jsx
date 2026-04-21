import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchEducatorConversation } from "../api/educatorApi.js";

export default function EducatorConversationPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const detail = await fetchEducatorConversation(Number(id));
        if (!cancelled) setData(detail);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Ошибка");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (error) {
    return <div className="min-h-screen bg-slate-50 px-6 py-10 text-red-600 dark:bg-[#0f172a] dark:text-red-400">{error}</div>;
  }
  if (!data) {
    return <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-[#0f172a]">Загрузка…</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-6">
        <Link to="/educator" className="text-cyan-700 underline dark:text-cyan-400">
          ← Панель учителя
        </Link>
      </nav>
      <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">{data.title}</h1>
      <div className="mt-8 max-w-4xl space-y-4">
        {data.messages.map((m) => (
          <div
            key={m.id}
            className={`rounded-xl border px-4 py-3 ${
              m.role === "user"
                ? "border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900/50"
                : "border-cyan-200 bg-cyan-50 dark:border-cyan-900/50 dark:bg-cyan-950/20"
            }`}
          >
            <p className="text-xs uppercase tracking-wide text-slate-500">{m.role}</p>
            <p className="mt-1 whitespace-pre-wrap text-sm text-slate-800 dark:text-slate-200">{m.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

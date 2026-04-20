import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getUserPedagogy, resetProgress } from "../api/userApi.js";

export default function PedagogyProfilePage() {
  const [ped, setPed] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const p = await getUserPedagogy();
      setPed(p);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    }
  }

  useEffect(() => {
    load();
  }, []);

  const counts = ped?.fallacy_counts && typeof ped.fallacy_counts === "object" ? ped.fallacy_counts : {};

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-8 flex flex-wrap gap-4 text-sm">
        <Link to="/app" className="text-cyan-700 underline dark:text-cyan-400">
          Чат
        </Link>
        <Link to="/profile" className="text-cyan-700 underline dark:text-cyan-400">
          Профиль
        </Link>
        <Link to="/profile/skills" className="text-cyan-700 underline dark:text-cyan-400">
          Навыки
        </Link>
      </nav>
      <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Педагогика</h1>
      {error ? <p className="mt-4 text-red-600 dark:text-red-400">{error}</p> : null}
      {!ped ? (
        <p className="mt-6 text-slate-500">Загрузка…</p>
      ) : (
        <div className="mt-6 max-w-xl rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900/50">
          <p>
            <span className="text-slate-500">Сложность (профиль):</span>{" "}
            <span className="font-semibold">{ped.current_difficulty}/5</span>
          </p>
          <p className="mt-2">
            <span className="text-slate-500">Глубоких ответов:</span> {ped.total_deep_responses}
          </p>
          <p className="mt-1">
            <span className="text-slate-500">Поверхностных:</span> {ped.total_shallow_responses}
          </p>
          <p className="mt-1 text-xs text-slate-500">Последняя активность: {ped.last_active_at}</p>
          <h2 className="mt-6 font-display text-lg font-semibold text-slate-900 dark:text-white">Ошибки по типам</h2>
          <ul className="mt-2 space-y-1 text-sm">
            {Object.keys(counts).length === 0 ? (
              <li className="text-slate-500">Пока пусто</li>
            ) : (
              Object.entries(counts)
                .sort((a, b) => Number(b[1]) - Number(a[1]))
                .map(([k, v]) => (
                  <li key={k} className="flex justify-between gap-4 tabular-nums">
                    <span>{k}</span>
                    <span className="text-slate-500">{v}</span>
                  </li>
                ))
            )}
          </ul>
        </div>
      )}
      <div className="mt-8 max-w-xl text-xs text-slate-500 dark:text-slate-400">
        <button
          type="button"
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          onClick={async () => {
            if (!confirm("Сбросить педагогику и навыки?")) return;
            try {
              await resetProgress();
              await load();
            } catch (e) {
              alert(e instanceof Error ? e.message : "Ошибка");
            }
          }}
        >
          Сбросить прогресс
        </button>
      </div>
    </div>
  );
}

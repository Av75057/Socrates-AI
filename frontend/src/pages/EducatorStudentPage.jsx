import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchStudentProgress } from "../api/educatorApi.js";
import SkillsChart from "../components/educator/SkillsChart.jsx";

export default function EducatorStudentPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const progress = await fetchStudentProgress(Number(id));
        if (!cancelled) setData(progress);
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
          ← Назад
        </Link>
      </nav>
      <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white">
        {data.student.full_name || data.student.email}
      </h1>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">{data.student.email}</p>

      <div className="mt-8 grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section className="space-y-6">
          <SkillsChart skills={data.skills} />
          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
            <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">Последние диалоги</h2>
            <div className="mt-4 space-y-3">
              {data.recent_conversations.map((item) => (
                <Link
                  key={item.id}
                  to={`/educator/conversation/${item.id}`}
                  className="block rounded-xl border border-slate-200 px-4 py-3 hover:border-cyan-300 dark:border-slate-700 dark:hover:border-cyan-700"
                >
                  <p className="font-medium text-slate-900 dark:text-slate-100">{item.title}</p>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-500">
                    {new Date(item.last_updated_at).toLocaleString()}
                  </p>
                </Link>
              ))}
            </div>
          </div>
        </section>

        <section className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-xs uppercase tracking-wide text-slate-500">Диалоги</p>
              <p className="mt-2 text-3xl font-bold">{data.conversations_total}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-xs uppercase tracking-wide text-slate-500">Очки мудрости</p>
              <p className="mt-2 text-3xl font-bold">{data.gamification.wisdom_points}</p>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
            <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">Логические ошибки</h2>
            <div className="mt-4 space-y-2 text-sm">
              {data.frequent_fallacies.map((item) => (
                <div key={item.fallacy_type} className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 dark:bg-slate-800/50">
                  <span>{item.fallacy_type}</span>
                  <span>{item.count}</span>
                </div>
              ))}
              {data.frequent_fallacies.length === 0 ? <p className="text-slate-500 dark:text-slate-500">Пока нет данных.</p> : null}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
            <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">Активность по дням</h2>
            <div className="mt-4 space-y-2">
              {data.activity_by_day.map((item) => (
                <div key={item.day}>
                  <div className="mb-1 flex justify-between text-xs text-slate-500 dark:text-slate-400">
                    <span>{item.day}</span>
                    <span>{item.messages}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-800">
                    <div
                      className="h-2 rounded-full bg-emerald-500"
                      style={{ width: `${Math.min(100, 10 + item.messages * 15)}%` }}
                    />
                  </div>
                </div>
              ))}
              {data.activity_by_day.length === 0 ? <p className="text-sm text-slate-500 dark:text-slate-500">За последние дни активность не найдена.</p> : null}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
            <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">Активные задания</h2>
            <div className="mt-4 space-y-3">
              {data.active_assignments.map((assignment) => (
                <div key={assignment.id} className="rounded-xl border border-slate-200 px-4 py-3 dark:border-slate-700">
                  <p className="font-medium">{assignment.title}</p>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{assignment.prompt}</p>
                </div>
              ))}
              {data.active_assignments.length === 0 ? <p className="text-sm text-slate-500 dark:text-slate-500">Нет активных заданий.</p> : null}
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

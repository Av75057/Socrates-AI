import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { createEducatorClass, deleteEducatorClass, listEducatorClasses } from "../api/educatorApi.js";
import ClassCard from "../components/educator/ClassCard.jsx";

export default function EducatorDashboard() {
  const [items, setItems] = useState([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");

  async function load() {
    try {
      setItems(await listEducatorClasses());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка загрузки");
    }
  }

  useEffect(() => {
    load();
  }, []);

  const activeStudents = items.reduce((acc, item) => acc + (item.students_count || 0), 0);
  const activeAssignments = items.reduce((acc, item) => acc + (item.assignments_count || 0), 0);

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-6 flex flex-wrap gap-3 text-sm">
        <Link to="/app" className="text-cyan-700 underline dark:text-cyan-400">
          Чат
        </Link>
        <Link to="/profile" className="text-cyan-700 underline dark:text-cyan-400">
          Профиль
        </Link>
      </nav>
      <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
        <section>
          <h1 className="font-display text-3xl font-bold text-slate-900 dark:text-white">Панель учителя</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">
            Классы, задания и прогресс учеников в одном месте.
          </p>
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-xs uppercase tracking-wide text-slate-500">Классы</p>
              <p className="mt-2 text-3xl font-bold">{items.length}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-xs uppercase tracking-wide text-slate-500">Ученики</p>
              <p className="mt-2 text-3xl font-bold">{activeStudents}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-xs uppercase tracking-wide text-slate-500">Задания</p>
              <p className="mt-2 text-3xl font-bold">{activeAssignments}</p>
            </div>
          </div>
          {error ? <p className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p> : null}
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {items.map((item) => (
              <ClassCard
                key={item.id}
                item={item}
                onDelete={async (target) => {
                  if (!window.confirm(`Удалить класс «${target.name}»?`)) return;
                  await deleteEducatorClass(target.id);
                  await load();
                }}
              />
            ))}
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900/40 dark:shadow-none">
          <h2 className="font-display text-xl font-semibold text-slate-900 dark:text-white">Создать класс</h2>
          <form
            className="mt-4 space-y-3"
            onSubmit={async (e) => {
              e.preventDefault();
              try {
                await createEducatorClass({ name, description });
                setName("");
                setDescription("");
                setError("");
                await load();
              } catch (err) {
                setError(err instanceof Error ? err.message : "Ошибка");
              }
            }}
          >
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Например, 9А или Группа по логике"
              required
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm dark:border-slate-600 dark:bg-slate-950/40"
            />
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Описание класса"
              className="min-h-28 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm dark:border-slate-600 dark:bg-slate-950/40"
            />
            <button
              type="submit"
              className="rounded-xl bg-cyan-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-cyan-500"
            >
              Создать
            </button>
          </form>
        </section>
      </div>
    </div>
  );
}

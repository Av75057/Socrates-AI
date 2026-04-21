import { Link } from "react-router-dom";

export default function ClassCard({ item, onDelete }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-700 dark:bg-slate-900/40 dark:shadow-none">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">{item.name}</h2>
          {item.description ? (
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{item.description}</p>
          ) : null}
        </div>
        <button
          type="button"
          onClick={() => onDelete?.(item)}
          className="rounded-lg border border-rose-300 px-3 py-1.5 text-xs text-rose-700 hover:bg-rose-50 dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950/40"
        >
          Удалить
        </button>
      </div>
      <div className="mt-4 flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
        <span>{item.students_count} учеников</span>
        <span>{item.assignments_count} заданий</span>
      </div>
      <Link
        to={`/educator/class/${item.id}`}
        className="mt-4 inline-flex rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500"
      >
        Открыть класс
      </Link>
    </div>
  );
}

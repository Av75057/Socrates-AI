export default function AssignmentsList({ items, onOpenSubmissions }) {
  return (
    <div className="space-y-3">
      {items.map((assignment) => (
        <div
          key={assignment.id}
          className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900/40"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="font-medium text-slate-900 dark:text-slate-100">{assignment.title}</h3>
              <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600 dark:text-slate-400">
                {assignment.prompt}
              </p>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-500">
                Дедлайн: {assignment.due_date ? new Date(assignment.due_date).toLocaleString() : "не задан"}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onOpenSubmissions?.(assignment)}
              className="rounded-lg border border-violet-400/50 px-3 py-2 text-xs text-violet-800 hover:bg-violet-50 dark:text-violet-300 dark:hover:bg-violet-950/40"
            >
              Кто начал
            </button>
          </div>
        </div>
      ))}
      {items.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-300 px-4 py-3 text-sm text-slate-500 dark:border-slate-700 dark:text-slate-500">
          Пока нет заданий.
        </p>
      ) : null}
    </div>
  );
}

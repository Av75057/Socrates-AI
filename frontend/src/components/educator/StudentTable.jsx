import { Link } from "react-router-dom";

export default function StudentTable({ items, classId, onRemove }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900/40">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
          <tr>
            <th className="px-4 py-3">Ученик</th>
            <th className="px-4 py-3">Email</th>
            <th className="px-4 py-3">Мудрость</th>
            <th className="px-4 py-3">Сложность</th>
            <th className="px-4 py-3">Действия</th>
          </tr>
        </thead>
        <tbody>
          {items.map((student) => (
            <tr key={student.id} className="border-t border-slate-200 dark:border-slate-700/70">
              <td className="px-4 py-3">{student.full_name || "Без имени"}</td>
              <td className="px-4 py-3 text-slate-600 dark:text-slate-400">{student.email}</td>
              <td className="px-4 py-3">{student.wisdom_points}</td>
              <td className="px-4 py-3">{student.current_difficulty}/5</td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-2">
                  <Link
                    to={`/educator/student/${student.id}`}
                    className="rounded-lg border border-cyan-500/40 px-3 py-1.5 text-xs text-cyan-800 hover:bg-cyan-50 dark:text-cyan-300 dark:hover:bg-cyan-950/40"
                  >
                    Прогресс
                  </Link>
                  <button
                    type="button"
                    onClick={() => onRemove?.(classId, student.id)}
                    className="rounded-lg border border-rose-300 px-3 py-1.5 text-xs text-rose-700 hover:bg-rose-50 dark:border-rose-900 dark:text-rose-300 dark:hover:bg-rose-950/40"
                  >
                    Удалить
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

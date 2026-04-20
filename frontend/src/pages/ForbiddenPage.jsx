import { Link } from "react-router-dom";

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-6 text-center text-slate-800 dark:bg-[#0f172a] dark:text-slate-200">
      <p className="text-4xl font-bold text-amber-600 dark:text-amber-400">403</p>
      <p className="mt-2 text-lg">Недостаточно прав для этой страницы.</p>
      <p className="mt-4 max-w-md text-sm text-slate-600 dark:text-slate-400">
        Раздел <code className="text-slate-800 dark:text-slate-300">/admin</code> только для роли{" "}
        <code className="text-slate-800 dark:text-slate-300">admin</code>. Новый админ:{" "}
        <code className="text-slate-800 dark:text-slate-300">create_admin.py email пароль</code>. Уже есть аккаунт:{" "}
        <code className="text-slate-800 dark:text-slate-300">create_admin.py --promote email</code> в каталоге{" "}
        <code className="text-slate-800 dark:text-slate-300">backend/</code>, затем выйдите и войдите снова.
      </p>
      <Link to="/app" className="mt-8 text-cyan-700 underline dark:text-cyan-400">
        В чат
      </Link>
    </div>
  );
}

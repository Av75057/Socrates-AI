import { NavLink, Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext.jsx";

const navCls =
  "rounded-lg px-3 py-1.5 text-sm text-cyan-800 hover:bg-cyan-50 dark:text-cyan-300 dark:hover:bg-cyan-950/40";
const activeCls = "bg-cyan-100 font-medium dark:bg-cyan-950/60";

export default function ProfilePage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-6 flex flex-wrap gap-2 border-b border-slate-200 pb-4 dark:border-slate-700">
        <NavLink to="/profile" end className={({ isActive }) => `${navCls} ${isActive ? activeCls : ""}`}>
          Профиль
        </NavLink>
        <NavLink to="/profile/history" className={({ isActive }) => `${navCls} ${isActive ? activeCls : ""}`}>
          Мои диалоги
        </NavLink>
        <NavLink to="/profile/skills" className={({ isActive }) => `${navCls} ${isActive ? activeCls : ""}`}>
          Навыки
        </NavLink>
        <NavLink to="/profile/pedagogy" className={({ isActive }) => `${navCls} ${isActive ? activeCls : ""}`}>
          Педагогика
        </NavLink>
        <NavLink to="/profile/settings" className={({ isActive }) => `${navCls} ${isActive ? activeCls : ""}`}>
          Настройки
        </NavLink>
        <Link to="/app" className={`${navCls} ml-auto`}>
          Чат
        </Link>
        {String(user?.role || "").toLowerCase() === "admin" ? (
          <Link to="/admin" className={`${navCls} text-amber-800 dark:text-amber-400`}>
            Админ
          </Link>
        ) : null}
      </nav>
      <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Личный кабинет</h1>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
        Тема интерфейса — в «Настройки». Навыки и сложность диалога копятся при общении с тьютором в сохранённых
        диалогах.
      </p>
      <div className="mt-6 max-w-lg rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900/50 dark:shadow-none">
        <p>
          <span className="text-slate-500">Email:</span> {user?.email}
        </p>
        {user?.full_name ? (
          <p className="mt-2">
            <span className="text-slate-500">Имя:</span> {user.full_name}
          </p>
        ) : null}
        <p className="mt-2">
          <span className="text-slate-500">Роль:</span> {user?.role}
        </p>
        <button
          type="button"
          onClick={() => logout()}
          className="mt-6 rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          Выйти
        </button>
      </div>
    </div>
  );
}

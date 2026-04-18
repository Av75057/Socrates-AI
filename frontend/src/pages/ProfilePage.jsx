import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext.jsx";

export default function ProfilePage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-[#0f172a] px-6 py-10 text-slate-100">
      <nav className="mb-8 flex flex-wrap gap-4 text-sm">
        <Link to="/app" className="text-cyan-400 underline">
          Чат
        </Link>
        <Link to="/profile/history" className="text-cyan-400 underline">
          История диалогов
        </Link>
        <Link to="/profile/settings" className="text-cyan-400 underline">
          Настройки
        </Link>
        {user?.role === "admin" ? (
          <Link to="/admin/users" className="text-amber-400 underline">
            Админ-панель
          </Link>
        ) : null}
      </nav>
      <h1 className="font-display text-2xl font-bold text-white">Личный кабинет</h1>
      <div className="mt-6 max-w-lg rounded-xl border border-slate-700 bg-slate-900/50 p-6">
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
          className="mt-6 rounded-lg border border-slate-600 px-4 py-2 text-sm text-slate-300 hover:bg-slate-800"
        >
          Выйти
        </button>
      </div>
    </div>
  );
}

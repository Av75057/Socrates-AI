import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext.jsx";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const rawFrom = location.state?.from;
  const from =
    typeof rawFrom === "string"
      ? rawFrom
      : rawFrom && typeof rawFrom.pathname === "string"
        ? rawFrom
        : "/app";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await login(email.trim(), password);
      const isAdmin = String(data?.user?.role || "").toLowerCase() === "admin";
      const adminDest =
        typeof from === "string" && from.startsWith("/admin")
          ? from
          : "/admin";
      if (isAdmin) {
        navigate(adminDest, { replace: true });
      } else {
        navigate(from, { replace: true });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Вход</h1>
      <form onSubmit={onSubmit} className="mt-8 w-full max-w-sm space-y-4">
        {error ? (
          <p className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-800 dark:border-red-500/40 dark:bg-red-950/50 dark:text-red-200">
            {error}
          </p>
        ) : null}
        <div>
          <label className="block text-xs uppercase text-slate-500">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
          />
        </div>
        <div>
          <label className="block text-xs uppercase text-slate-500">Пароль</label>
          <input
            type="password"
            required
            minLength={6}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
          />
        </div>
        <button
          type="submit"
          className="w-full rounded-lg bg-cyan-600 py-2.5 font-medium text-white hover:bg-cyan-500"
        >
          Войти
        </button>
      </form>
      <p className="mt-6 text-sm text-slate-600 dark:text-slate-400">
        Нет аккаунта?{" "}
        <Link to="/register" className="text-cyan-700 underline dark:text-cyan-400">
          Регистрация
        </Link>
      </p>
      <Link to="/" className="mt-4 text-sm text-slate-500 underline dark:text-slate-500">
        На главную
      </Link>
    </div>
  );
}

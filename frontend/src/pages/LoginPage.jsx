import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext.jsx";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from || "/app";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      await login(email.trim(), password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка входа");
    }
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#0f172a] px-4 text-slate-100">
      <h1 className="font-display text-2xl font-bold text-white">Вход</h1>
      <form onSubmit={onSubmit} className="mt-8 w-full max-w-sm space-y-4">
        {error ? (
          <p className="rounded-lg border border-red-500/40 bg-red-950/50 px-3 py-2 text-sm text-red-200">
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
            className="mt-1 w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
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
            className="mt-1 w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
          />
        </div>
        <button
          type="submit"
          className="w-full rounded-lg bg-cyan-600 py-2.5 font-medium text-white hover:bg-cyan-500"
        >
          Войти
        </button>
      </form>
      <p className="mt-6 text-sm text-slate-400">
        Нет аккаунта?{" "}
        <Link to="/register" className="text-cyan-400 underline">
          Регистрация
        </Link>
      </p>
      <Link to="/" className="mt-4 text-sm text-slate-500 underline">
        На главную
      </Link>
    </div>
  );
}

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchSettings, updateSettings } from "../api/userApi.js";

export default function SettingsPage() {
  const [tutorMode, setTutorMode] = useState("friendly");
  const [theme, setTheme] = useState("dark");
  const [notifications, setNotifications] = useState(true);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await fetchSettings();
        if (cancelled) return;
        setTutorMode(s.tutor_mode || "friendly");
        setTheme(s.theme || "dark");
        setNotifications(!!s.notifications_enabled);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Ошибка");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setSaved(false);
    try {
      await updateSettings({
        tutor_mode: tutorMode,
        theme,
        notifications_enabled: notifications,
      });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  return (
    <div className="min-h-screen bg-[#0f172a] px-6 py-10 text-slate-100">
      <nav className="mb-8 flex gap-4 text-sm">
        <Link to="/profile" className="text-cyan-400 underline">
          Профиль
        </Link>
        <Link to="/app" className="text-cyan-400 underline">
          Чат
        </Link>
      </nav>
      <h1 className="font-display text-2xl font-bold text-white">Настройки</h1>
      <form onSubmit={onSubmit} className="mt-8 max-w-md space-y-6">
        {error ? <p className="text-sm text-red-400">{error}</p> : null}
        {saved ? <p className="text-sm text-emerald-400">Сохранено</p> : null}
        <div>
          <label className="block text-xs uppercase text-slate-500">Режим тьютора</label>
          <select
            value={tutorMode}
            onChange={(e) => setTutorMode(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
          >
            <option value="strict">Строгий</option>
            <option value="friendly">Дружелюбный</option>
            <option value="provocateur">Провокатор</option>
          </select>
        </div>
        <div>
          <label className="block text-xs uppercase text-slate-500">Тема (заглушка UI)</label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
          >
            <option value="dark">Тёмная</option>
            <option value="light">Светлая</option>
          </select>
        </div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={notifications}
            onChange={(e) => setNotifications(e.target.checked)}
            className="rounded border-slate-600"
          />
          Уведомления включены
        </label>
        <button
          type="submit"
          className="rounded-lg bg-cyan-600 px-5 py-2.5 font-medium text-white hover:bg-cyan-500"
        >
          Сохранить
        </button>
      </form>
    </div>
  );
}

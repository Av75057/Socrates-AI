import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchSettings, updateSettings } from "../api/userApi.js";
import { useTheme } from "../contexts/ThemeContext.jsx";

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [tutorMode, setTutorMode] = useState("friendly");
  const [notifications, setNotifications] = useState(true);
  const [showTypingIndicator, setShowTypingIndicator] = useState(true);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await fetchSettings();
        if (cancelled) return;
        setTutorMode(s.tutor_mode || "friendly");
        setNotifications(!!s.notifications_enabled);
        setShowTypingIndicator(s.show_typing_indicator !== false);
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
        show_typing_indicator: showTypingIndicator,
      });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  async function resetOnboarding() {
    setError("");
    try {
      await updateSettings({ has_seen_onboarding: false });
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8 text-sm text-slate-900 sm:px-6 sm:py-10 sm:text-base dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-8 flex flex-wrap gap-4 text-sm">
        <Link to="/profile" className="text-cyan-600 underline dark:text-cyan-400">
          Профиль
        </Link>
        <Link to="/app" className="text-cyan-600 underline dark:text-cyan-400">
          Чат
        </Link>
      </nav>
      <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Настройки</h1>
      <p className="mt-2 max-w-md text-sm text-slate-600 dark:text-slate-400">
        Тема применяется ко всему интерфейсу и сохраняется в аккаунте.
      </p>
      <form onSubmit={onSubmit} className="mt-8 max-w-md space-y-6">
        {error ? <p className="text-sm text-red-600 dark:text-red-400">{error}</p> : null}
        {saved ? <p className="text-sm text-emerald-600 dark:text-emerald-400">Сохранено</p> : null}
        <div>
          <label className="block text-xs uppercase text-slate-500 dark:text-slate-500">Режим тьютора</label>
          <select
            value={tutorMode}
            onChange={(e) => setTutorMode(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
          >
            <option value="strict">Строгий</option>
            <option value="friendly">Дружелюбный</option>
            <option value="provocateur">Провокатор</option>
          </select>
        </div>
        <div>
          <label className="block text-xs uppercase text-slate-500 dark:text-slate-500">Тема интерфейса</label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
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
            className="rounded border-slate-400 dark:border-slate-600"
          />
          Уведомления включены
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={showTypingIndicator}
            onChange={(e) => setShowTypingIndicator(e.target.checked)}
            className="rounded border-slate-400 dark:border-slate-600"
          />
          Показывать индикатор печати тьютора
        </label>
        <button
          type="submit"
          className="rounded-lg bg-cyan-600 px-5 py-2.5 font-medium text-white hover:bg-cyan-500"
        >
          Сохранить
        </button>
      </form>
      <div className="mt-10 max-w-md border-t border-slate-200 pt-8 dark:border-slate-700">
        <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">Онбординг</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
          Сбросить флаг — при следующем заходе в чат снова покажется тур по интерфейсу.
        </p>
        <button
          type="button"
          onClick={resetOnboarding}
          className="mt-3 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Сбросить онбординг
        </button>
      </div>
    </div>
  );
}

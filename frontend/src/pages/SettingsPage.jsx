import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchSettings, testLlmConnection, updateSettings } from "../api/userApi.js";
import { useTheme } from "../contexts/ThemeContext.jsx";

function isValidHttpUrl(s) {
  const t = (s || "").trim();
  if (!t.startsWith("http://") && !t.startsWith("https://")) return false;
  try {
    void new URL(t);
    return true;
  } catch {
    return false;
  }
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const [tutorMode, setTutorMode] = useState("friendly");
  const [notifications, setNotifications] = useState(true);
  const [showTypingIndicator, setShowTypingIndicator] = useState(true);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const [llmBaseUrl, setLlmBaseUrl] = useState("http://127.0.0.1:8000/v1");
  const [llmApiKey, setLlmApiKey] = useState("");
  const [llmModelName, setLlmModelName] = useState("");
  const [llmApiKeySet, setLlmApiKeySet] = useState(false);
  const [clearLlmKey, setClearLlmKey] = useState(false);

  const [testLoading, setTestLoading] = useState(false);
  const [testMessage, setTestMessage] = useState(null);
  const [availableModels, setAvailableModels] = useState([]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const s = await fetchSettings();
        if (cancelled) return;
        setTutorMode(s.tutor_mode || "friendly");
        setNotifications(!!s.notifications_enabled);
        setShowTypingIndicator(s.show_typing_indicator !== false);
        setLlmBaseUrl(s.llm_base_url || "http://127.0.0.1:8000/v1");
        setLlmModelName(s.llm_model_name || "");
        setLlmApiKeySet(!!s.llm_api_key_set);
        setLlmApiKey("");
        setClearLlmKey(false);
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
    setTestMessage(null);
    try {
      const body = {
        tutor_mode: tutorMode,
        theme,
        notifications_enabled: notifications,
        show_typing_indicator: showTypingIndicator,
        llm_base_url: llmBaseUrl.trim() || null,
        llm_model_name: llmModelName.trim() || null,
      };
      if (clearLlmKey) {
        body.llm_api_key = "";
      } else if (llmApiKey.trim()) {
        body.llm_api_key = llmApiKey.trim();
      }
      await updateSettings(body);
      setSaved(true);
      setLlmApiKey("");
      setClearLlmKey(false);
      const refreshed = await fetchSettings();
      setLlmApiKeySet(!!refreshed.llm_api_key_set);
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

  async function handleTestConnection() {
    setError("");
    setTestMessage(null);
    const base = llmBaseUrl.trim();
    if (!isValidHttpUrl(base)) {
      setTestMessage({ ok: false, text: "Укажите корректный URL (http:// или https://)." });
      return;
    }
    setTestLoading(true);
    try {
      const res = await testLlmConnection({
        llm_base_url: base,
        llm_api_key: llmApiKey.trim() || undefined,
        llm_model_name: llmModelName.trim() || undefined,
      });
      setTestMessage({ ok: res.ok, text: res.message || (res.ok ? "Успешно" : "Ошибка") });
      if (Array.isArray(res.model_ids) && res.model_ids.length) {
        setAvailableModels(res.model_ids);
      }
    } catch (err) {
      setTestMessage({
        ok: false,
        text: err instanceof Error ? err.message : "Ошибка сети",
      });
    } finally {
      setTestLoading(false);
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

        <div className="border-t border-slate-200 pt-6 dark:border-slate-700">
          <h2 className="font-display text-lg font-semibold text-slate-900 dark:text-white">
            Подключение к LLM (OpenAI-совместимый API)
          </h2>
          <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-400">
            Укажите базовый URL до префикса <code className="rounded bg-slate-200 px-1 dark:bg-slate-800">/v1</code> (например{" "}
            <code className="rounded bg-slate-200 px-1 dark:bg-slate-800">http://127.0.0.1:11434/v1</code> для Ollama). Запросы
            к бэкенду Socrates идут с сервера; CORS на LLM-сервере не обязателен для чата. В Docker вместо{" "}
            <code className="rounded bg-slate-200 px-1 dark:bg-slate-800">localhost</code> на хосте используйте{" "}
            <code className="rounded bg-slate-200 px-1 dark:bg-slate-800">host.docker.internal</code> или IP машины в LAN.
          </p>
          <div className="mt-4 space-y-3">
            <div>
              <label className="block text-xs uppercase text-slate-500 dark:text-slate-500">Base URL</label>
              <input
                type="url"
                value={llmBaseUrl}
                onChange={(e) => setLlmBaseUrl(e.target.value)}
                placeholder="http://127.0.0.1:8000/v1"
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
              />
            </div>
            <div>
              <label className="block text-xs uppercase text-slate-500 dark:text-slate-500">API Key (необязательно)</label>
              <input
                type="password"
                value={llmApiKey}
                onChange={(e) => setLlmApiKey(e.target.value)}
                placeholder={llmApiKeySet ? "•••••••• (оставьте пустым, чтобы не менять)" : "sk-… или пусто"}
                autoComplete="off"
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
              />
              {llmApiKeySet ? (
                <label className="mt-2 flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
                  <input
                    type="checkbox"
                    checked={clearLlmKey}
                    onChange={(e) => setClearLlmKey(e.target.checked)}
                    className="rounded border-slate-400 dark:border-slate-600"
                  />
                  Сбросить сохранённый ключ
                </label>
              ) : null}
            </div>
            <div>
              <label className="block text-xs uppercase text-slate-500 dark:text-slate-500">Имя модели</label>
              <input
                type="text"
                value={llmModelName}
                onChange={(e) => setLlmModelName(e.target.value)}
                list="llm-model-suggestions"
                placeholder="например gpt-oss-120b или llama3"
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
              />
              <datalist id="llm-model-suggestions">
                {availableModels.map((id) => (
                  <option key={id} value={id} />
                ))}
              </datalist>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-800 hover:bg-slate-100 disabled:opacity-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
                aria-busy={testLoading}
                disabled={testLoading}
                onClick={handleTestConnection}
              >
                {testLoading ? "Проверка…" : "Проверить соединение"}
              </button>
            </div>
            {testMessage ? (
              <p
                className={`text-sm ${
                  testMessage.ok ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"
                }`}
              >
                {testMessage.ok ? "✓ " : ""}
                {testMessage.text}
              </p>
            ) : null}
          </div>
        </div>

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

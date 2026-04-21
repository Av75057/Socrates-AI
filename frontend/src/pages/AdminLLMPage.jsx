import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  adminLLMStatus,
  adminLLMSwitch,
  adminLLMTest,
} from "../api/adminApi.js";
import LLMStatusBadge from "../components/admin/LLMStatusBadge.jsx";

export default function AdminLLMPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [provider, setProvider] = useState("openrouter");
  const [ollamaModel, setOllamaModel] = useState("qwen2.5:7b-instruct");
  const [testPrompt, setTestPrompt] = useState("Скажи коротко по-русски: привет.");
  const [testReply, setTestReply] = useState("");
  const [testLoading, setTestLoading] = useState(false);
  const [switchLoading, setSwitchLoading] = useState(false);

  const load = useCallback(async () => {
    setError("");
    setLoading(true);
    try {
      const s = await adminLLMStatus();
      setStatus(s);
      setProvider(s.effective_provider || "openrouter");
      if (s.ollama_model) setOllamaModel(s.ollama_model);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleSwitch(e) {
    e.preventDefault();
    setSwitchLoading(true);
    setError("");
    try {
      const body = { provider };
      if (provider === "ollama") body.ollama_model = ollamaModel.trim() || null;
      await adminLLMSwitch(body);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSwitchLoading(false);
    }
  }

  async function handleClearRuntime(e) {
    e.preventDefault();
    setSwitchLoading(true);
    setError("");
    try {
      await adminLLMSwitch({ clear_runtime: true });
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSwitchLoading(false);
    }
  }

  async function handleTest(e) {
    e.preventDefault();
    setTestLoading(true);
    setTestReply("");
    setError("");
    try {
      const r = await adminLLMTest(testPrompt.trim() || "Привет");
      setTestReply(r.reply || "");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setTestLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <div className="mx-auto max-w-2xl">
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-display text-2xl font-bold text-slate-900 dark:text-white">LLM</h1>
          {status && <LLMStatusBadge status={status} />}
        </div>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
          Провайдер по умолчанию задаётся в <code className="text-amber-800 dark:text-amber-200/90">LLM_PROVIDER</code> в{" "}
          <code className="text-amber-800 dark:text-amber-200/90">backend/.env</code>. Здесь можно временно переключить
          без перезапуска API.
        </p>

        {loading && <p className="mt-6 text-sm text-slate-500">Загрузка статуса…</p>}
        {error && (
          <p className="mt-6 rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-100">
            {error}
          </p>
        )}

        {status && !loading && (
          <div className="mt-8 space-y-6 rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900/50">
            <dl className="grid gap-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500 dark:text-slate-400">Эффективный провайдер</dt>
                <dd className="font-medium">{status.effective_provider}</dd>
              </div>
              {status.provider_override && (
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500 dark:text-slate-400">Override из админки</dt>
                  <dd className="font-medium">{status.provider_override}</dd>
                </div>
              )}
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500 dark:text-slate-400">В .env</dt>
                <dd>{status.env_llm_provider}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500 dark:text-slate-400">Ollama URL</dt>
                <dd className="break-all text-right">{status.ollama_base_url}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500 dark:text-slate-400">Модель Ollama</dt>
                <dd className="break-all text-right">{status.ollama_model}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500 dark:text-slate-400">Ollama доступен</dt>
                <dd>{status.ollama_reachable ? "да" : "нет"}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500 dark:text-slate-400">OpenRouter ключ</dt>
                <dd>{status.openrouter_configured ? "задан" : "нет"}</dd>
              </div>
            </dl>

            <form onSubmit={handleSwitch} className="space-y-4 border-t border-slate-200 pt-6 dark:border-slate-700">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200">Переключить провайдер</p>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                <label className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="prov"
                    checked={provider === "ollama"}
                    onChange={() => setProvider("ollama")}
                  />
                  Ollama (локально)
                </label>
                <label className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="radio"
                    name="prov"
                    checked={provider === "openrouter"}
                    onChange={() => setProvider("openrouter")}
                  />
                  OpenRouter
                </label>
              </div>
              {provider === "ollama" && (
                <label className="block text-sm">
                  <span className="text-slate-600 dark:text-slate-400">Модель Ollama</span>
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
                    value={ollamaModel}
                    onChange={(ev) => setOllamaModel(ev.target.value)}
                    placeholder="qwen2.5:7b-instruct"
                  />
                </label>
              )}
              <div className="flex flex-wrap gap-3">
                <button
                  type="submit"
                  disabled={switchLoading}
                  className="rounded-lg bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50"
                >
                  {switchLoading ? "Сохранение…" : "Применить"}
                </button>
                <button
                  type="button"
                  onClick={handleClearRuntime}
                  disabled={switchLoading}
                  className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
                >
                  Сбросить override
                </button>
              </div>
            </form>

            <form onSubmit={handleTest} className="space-y-3 border-t border-slate-200 pt-6 dark:border-slate-700">
              <p className="text-sm font-medium text-slate-800 dark:text-slate-200">Тест</p>
              <textarea
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-950 dark:text-slate-100"
                rows={2}
                value={testPrompt}
                onChange={(ev) => setTestPrompt(ev.target.value)}
              />
              <button
                type="submit"
                disabled={testLoading}
                className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500 disabled:opacity-50"
              >
                {testLoading ? "Запрос…" : "Отправить тест"}
              </button>
              {testReply && (
                <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-100 p-4 text-sm text-slate-900 dark:bg-black/30 dark:text-slate-100">
                  {testReply}
                </pre>
              )}
            </form>
          </div>
        )}

        <p className="mt-10 text-sm">
          <Link to="/admin" className="text-slate-600 underline hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-300">
            ← Админка
          </Link>
        </p>
      </div>
    </div>
  );
}

import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  adminCreateTopic,
  adminDeleteTopic,
  adminGenerateTopic,
  adminListTopics,
  adminUpdateTopic,
} from "../api/topicsApi.js";

const EMPTY_FORM = {
  title: "",
  description: "",
  initial_prompt: "",
  difficulty: 2,
  tags: "",
  is_premium: false,
  is_active: true,
};

function formToPayload(form) {
  return {
    title: form.title.trim(),
    description: form.description.trim() || null,
    initial_prompt: form.initial_prompt.trim(),
    difficulty: Number(form.difficulty) || 2,
    tags: form.tags
      .split(",")
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean),
    is_premium: !!form.is_premium,
    is_active: !!form.is_active,
  };
}

export default function AdminTopicsPage() {
  const [topics, setTopics] = useState([]);
  const [q, setQ] = useState("");
  const [includeInactive, setIncludeInactive] = useState(true);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editingId, setEditingId] = useState(null);
  const [seedPrompt, setSeedPrompt] = useState("");
  const [generatorModel, setGeneratorModel] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const submitLabel = editingId ? "Сохранить изменения" : "Создать тему";

  async function load() {
    setLoading(true);
    setError("");
    try {
      const data = await adminListTopics({ q, includeInactive, offset: 0, limit: 100 });
      setTopics(Array.isArray(data?.items) ? data.items : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить темы");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const activeCount = useMemo(
    () => topics.filter((topic) => topic.is_active).length,
    [topics],
  );

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-6 flex flex-wrap gap-4 text-sm">
        <Link to="/admin" className="text-slate-600 underline dark:text-slate-400">
          Админ — главная
        </Link>
        <Link to="/educator" className="text-cyan-700 underline dark:text-cyan-400">
          Панель учителя
        </Link>
        <Link to="/topics" className="text-cyan-700 underline dark:text-cyan-400">
          Публичная библиотека
        </Link>
      </nav>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <section>
          <h1 className="font-display text-3xl font-bold text-slate-950 dark:text-white">Управление темами</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-400">
            Создавайте сценарии обсуждений, делайте часть библиотеки premium и быстро генерируйте черновики через AI.
          </p>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-xs uppercase tracking-wide text-slate-500">Всего тем</p>
              <p className="mt-2 text-3xl font-bold">{topics.length}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-xs uppercase tracking-wide text-slate-500">Активные</p>
              <p className="mt-2 text-3xl font-bold">{activeCount}</p>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900/40">
              <p className="text-xs uppercase tracking-wide text-slate-500">Premium</p>
              <p className="mt-2 text-3xl font-bold">{topics.filter((topic) => topic.is_premium).length}</p>
            </div>
          </div>

          <div className="mt-6 flex flex-wrap items-center gap-3">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Поиск по заголовку или тегу"
              className="min-w-[260px] rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm dark:border-slate-600 dark:bg-slate-900"
            />
            <label className="inline-flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={includeInactive}
                onChange={(e) => setIncludeInactive(e.target.checked)}
              />
              Показывать неактивные
            </label>
            <button
              type="button"
              onClick={load}
              className="rounded-xl bg-slate-800 px-4 py-2.5 text-sm font-medium text-white hover:bg-slate-700"
            >
              Обновить
            </button>
          </div>

          {error ? <p className="mt-4 text-sm text-red-600 dark:text-red-400">{error}</p> : null}

          <div className="mt-6 overflow-x-auto rounded-3xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900/45">
            {loading ? (
              <p className="text-sm text-slate-500 dark:text-slate-400">Загрузка тем…</p>
            ) : (
              <table className="w-full min-w-[760px] text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 dark:border-slate-700">
                    <th className="py-3 pr-4">ID</th>
                    <th className="py-3 pr-4">Заголовок</th>
                    <th className="py-3 pr-4">Сложность</th>
                    <th className="py-3 pr-4">Premium</th>
                    <th className="py-3 pr-4">Активна</th>
                    <th className="py-3 pr-4">Запусков</th>
                    <th className="py-3">Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {topics.map((topic) => (
                    <tr key={topic.id} className="border-b border-slate-100 dark:border-slate-800">
                      <td className="py-3 pr-4">{topic.id}</td>
                      <td className="py-3 pr-4">
                        <div className="font-medium">{topic.title}</div>
                        <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                          {(topic.tags || []).map((tag) => `#${tag}`).join(" ")}
                        </div>
                      </td>
                      <td className="py-3 pr-4">{topic.difficulty}/5</td>
                      <td className="py-3 pr-4">{topic.is_premium ? "да" : "нет"}</td>
                      <td className="py-3 pr-4">{topic.is_active ? "да" : "нет"}</td>
                      <td className="py-3 pr-4">{topic.usage_count}</td>
                      <td className="py-3">
                        <button
                          type="button"
                          onClick={() => {
                            setEditingId(topic.id);
                            setForm({
                              title: topic.title || "",
                              description: topic.description || "",
                              initial_prompt: topic.initial_prompt || "",
                              difficulty: topic.difficulty || 2,
                              tags: (topic.tags || []).join(", "),
                              is_premium: !!topic.is_premium,
                              is_active: !!topic.is_active,
                            });
                          }}
                          className="mr-3 text-cyan-700 hover:underline dark:text-cyan-400"
                        >
                          Редактировать
                        </button>
                        <button
                          type="button"
                          onClick={async () => {
                            if (!window.confirm(`Скрыть тему «${topic.title}»?`)) return;
                            try {
                              await adminDeleteTopic(topic.id);
                              if (editingId === topic.id) {
                                setEditingId(null);
                                setForm(EMPTY_FORM);
                              }
                              await load();
                            } catch (e) {
                              setError(e instanceof Error ? e.message : "Не удалось удалить тему");
                            }
                          }}
                          className="text-red-600 hover:underline dark:text-red-400"
                        >
                          Удалить
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        <aside className="space-y-6">
          <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900/45">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h2 className="font-display text-xl font-semibold text-slate-950 dark:text-white">
                  {editingId ? `Редактирование #${editingId}` : "Новая тема"}
                </h2>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                  Все поля можно изменить вручную после AI-генерации.
                </p>
              </div>
              {editingId ? (
                <button
                  type="button"
                  onClick={() => {
                    setEditingId(null);
                    setForm(EMPTY_FORM);
                    setGeneratorModel("");
                  }}
                  className="rounded-xl border border-slate-300 px-3 py-2 text-sm dark:border-slate-700"
                >
                  Сбросить
                </button>
              ) : null}
            </div>

            <form
              className="mt-5 space-y-4"
              onSubmit={async (e) => {
                e.preventDefault();
                setSaving(true);
                setError("");
                try {
                  const payload = formToPayload(form);
                  if (editingId) {
                    await adminUpdateTopic(editingId, payload);
                  } else {
                    await adminCreateTopic(payload);
                  }
                  setEditingId(null);
                  setForm(EMPTY_FORM);
                  setGeneratorModel("");
                  await load();
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Не удалось сохранить тему");
                } finally {
                  setSaving(false);
                }
              }}
            >
              <input
                value={form.title}
                onChange={(e) => setForm((current) => ({ ...current, title: e.target.value }))}
                placeholder="Заголовок темы"
                required
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm dark:border-slate-600 dark:bg-slate-950/50"
              />
              <textarea
                value={form.description}
                onChange={(e) => setForm((current) => ({ ...current, description: e.target.value }))}
                placeholder="Описание для карточки"
                className="min-h-24 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm dark:border-slate-600 dark:bg-slate-950/50"
              />
              <textarea
                value={form.initial_prompt}
                onChange={(e) => setForm((current) => ({ ...current, initial_prompt: e.target.value }))}
                placeholder="Первый вопрос тьютора"
                required
                className="min-h-28 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm dark:border-slate-600 dark:bg-slate-950/50"
              />
              <label className="block text-sm">
                <span className="mb-2 block text-xs uppercase tracking-wide text-slate-500">Сложность</span>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={form.difficulty}
                  onChange={(e) => setForm((current) => ({ ...current, difficulty: Number(e.target.value) }))}
                  className="w-full"
                />
                <span className="mt-2 block font-medium">{form.difficulty}/5</span>
              </label>
              <input
                value={form.tags}
                onChange={(e) => setForm((current) => ({ ...current, tags: e.target.value }))}
                placeholder="Теги через запятую"
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm dark:border-slate-600 dark:bg-slate-950/50"
              />
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="inline-flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.is_premium}
                    onChange={(e) => setForm((current) => ({ ...current, is_premium: e.target.checked }))}
                  />
                  Premium
                </label>
                <label className="inline-flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form.is_active}
                    onChange={(e) => setForm((current) => ({ ...current, is_active: e.target.checked }))}
                  />
                  Активна
                </label>
              </div>
              <button
                type="submit"
                disabled={saving}
                className="w-full rounded-xl bg-cyan-600 px-4 py-3 text-sm font-medium text-white hover:bg-cyan-500 disabled:cursor-wait disabled:opacity-70"
              >
                {saving ? "Сохраняю…" : submitLabel}
              </button>
            </form>
          </section>

          <section className="rounded-3xl border border-amber-300/60 bg-amber-50 p-6 dark:border-amber-600/30 dark:bg-amber-950/25">
            <h2 className="font-display text-xl font-semibold text-amber-950 dark:text-amber-100">
              Генерация через AI
            </h2>
            <p className="mt-2 text-sm text-amber-900/80 dark:text-amber-100/80">
              Введите исходную идею, а затем отредактируйте черновик перед сохранением.
            </p>
            <textarea
              value={seedPrompt}
              onChange={(e) => setSeedPrompt(e.target.value)}
              placeholder="Например: квантовая физика для начинающих"
              className="mt-4 min-h-24 w-full rounded-xl border border-amber-300 bg-white/80 px-4 py-3 text-sm text-slate-900 dark:border-amber-700/40 dark:bg-slate-950/50 dark:text-slate-100"
            />
            <button
              type="button"
              onClick={async () => {
                if (!seedPrompt.trim()) return;
                setSaving(true);
                setError("");
                try {
                  const draft = await adminGenerateTopic(seedPrompt.trim());
                  setForm({
                    title: draft.title || "",
                    description: draft.description || "",
                    initial_prompt: draft.initial_prompt || "",
                    difficulty: draft.difficulty || 2,
                    tags: (draft.tags || []).join(", "),
                    is_premium: false,
                    is_active: true,
                  });
                  setEditingId(null);
                  setGeneratorModel(draft.model || "");
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Не удалось сгенерировать тему");
                } finally {
                  setSaving(false);
                }
              }}
              disabled={saving || !seedPrompt.trim()}
              className="mt-4 w-full rounded-xl bg-amber-500 px-4 py-3 text-sm font-medium text-amber-950 hover:bg-amber-400 disabled:cursor-not-allowed disabled:opacity-70"
            >
              {saving ? "Генерирую…" : "Сгенерировать черновик"}
            </button>
            {generatorModel ? (
              <p className="mt-3 text-xs text-amber-900/75 dark:text-amber-100/70">
                Модель: {generatorModel}
              </p>
            ) : null}
          </section>
        </aside>
      </div>
    </div>
  );
}

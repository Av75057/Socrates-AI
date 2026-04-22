import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import TopicCard from "../components/topics/TopicCard.jsx";
import { fetchTopicTags, listTopics, startTopic } from "../api/topicsApi.js";
import { useAuth } from "../contexts/AuthContext.jsx";

const PAGE_SIZE = 12;

function UpgradeModal({ open, onClose }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4">
      <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl dark:bg-slate-900">
        <p className="text-sm font-semibold uppercase tracking-[0.18em] text-amber-600 dark:text-amber-300">
          Premium-тема
        </p>
        <h2 className="mt-2 font-display text-2xl font-bold text-slate-950 dark:text-white">
          Эта тема доступна в Pro
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
          Открой расширенную библиотеку тем, сложные сценарии обсуждений и будущие подборки для учёбы.
        </p>
        <div className="mt-6 flex gap-3">
          <Link
            to="/pricing"
            className="inline-flex flex-1 items-center justify-center rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-medium text-amber-950 hover:bg-amber-400"
          >
            Посмотреть Pro
          </Link>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex flex-1 items-center justify-center rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Позже
          </button>
        </div>
      </div>
    </div>
  );
}

export default function TopicsLibraryPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [tags, setTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [q, setQ] = useState("");
  const [difficultyMin, setDifficultyMin] = useState(1);
  const [difficultyMax, setDifficultyMax] = useState(5);
  const [freeOnly, setFreeOnly] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [upgradeOpen, setUpgradeOpen] = useState(false);
  const [startingId, setStartingId] = useState(null);

  useEffect(() => {
    fetchTopicTags()
      .then((data) => setTags(Array.isArray(data) ? data : []))
      .catch(() => setTags([]));
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError("");
    listTopics({
      offset: (page - 1) * PAGE_SIZE,
      limit: PAGE_SIZE,
      q,
      tags: selectedTags,
      difficultyMin,
      difficultyMax,
      freeOnly,
      sort: "popular",
    })
      .then((data) => {
        if (cancelled) return;
        setItems(Array.isArray(data?.items) ? data.items : []);
        setTotal(Number(data?.total) || 0);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить темы");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, q, selectedTags, difficultyMin, difficultyMax, freeOnly, user?.id]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageTitle = useMemo(() => {
    if (selectedTags.length === 0) return "Темы для обсуждения";
    return `Темы: ${selectedTags.join(", ")}`;
  }, [selectedTags]);

  const toggleTag = (tag) => {
    setPage(1);
    setSelectedTags((current) =>
      current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag],
    );
  };

  const handleStart = async (topic) => {
    if (!user) {
      navigate("/login", { state: { from: "/topics" } });
      return;
    }
    if (topic.is_premium && !topic.can_start) {
      setUpgradeOpen(true);
      return;
    }
    setStartingId(topic.id);
    try {
      const started = await startTopic(topic.id);
      navigate(`/app?conversation=${started.conversation_id}`);
    } catch (e) {
      if (e?.status === 402) {
        setUpgradeOpen(true);
      } else {
        setError(e instanceof Error ? e.message : "Не удалось начать диалог");
      }
    } finally {
      setStartingId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100 sm:px-6 lg:px-8">
      <UpgradeModal open={upgradeOpen} onClose={() => setUpgradeOpen(false)} />
      <div className="mx-auto max-w-7xl">
        <nav className="mb-6 flex flex-wrap gap-3 text-sm">
          <Link to="/app" className="text-cyan-700 underline dark:text-cyan-400">
            Чат
          </Link>
          <Link to="/" className="text-slate-600 underline dark:text-slate-400">
            Главная
          </Link>
          {user ? (
            <Link to="/profile/history" className="text-slate-600 underline dark:text-slate-400">
              История
            </Link>
          ) : null}
        </nav>

        <section className="rounded-[2rem] border border-slate-200 bg-white px-6 py-8 shadow-sm dark:border-slate-800 dark:bg-slate-900/45">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-700 dark:text-cyan-300">
                Библиотека Socrates-AI
              </p>
              <h1 className="mt-3 font-display text-4xl font-bold tracking-tight text-slate-950 dark:text-white">
                {pageTitle}
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300/90">
                Выбирай готовую тему, стартовый вопрос и сложность уже настроены. Можно быстро начать содержательный диалог без пустого экрана.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:w-[420px]">
              <label className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-950/50">
                <span className="mb-2 block text-xs uppercase tracking-wide text-slate-500">Поиск</span>
                <input
                  value={q}
                  onChange={(e) => {
                    setPage(1);
                    setQ(e.target.value);
                  }}
                  placeholder="ИИ, политика, логика…"
                  className="w-full bg-transparent outline-none"
                />
              </label>
              <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-700 dark:bg-slate-950/50">
                <input
                  type="checkbox"
                  checked={freeOnly}
                  onChange={(e) => {
                    setPage(1);
                    setFreeOnly(e.target.checked);
                  }}
                  className="h-4 w-4"
                />
                Показать только бесплатные
              </label>
            </div>
          </div>

          <div className="mt-6 grid gap-3 lg:grid-cols-[1fr_220px_220px]">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 dark:border-slate-700 dark:bg-slate-950/50">
              <p className="text-xs uppercase tracking-wide text-slate-500">Теги</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {tags.map((tag) => {
                  const active = selectedTags.includes(tag);
                  return (
                    <button
                      key={tag}
                      type="button"
                      onClick={() => toggleTag(tag)}
                      className={`rounded-full px-3 py-1.5 text-xs font-medium transition ${
                        active
                          ? "bg-cyan-600 text-white"
                          : "border border-slate-200 bg-white text-slate-700 hover:border-cyan-300 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
                      }`}
                    >
                      #{tag}
                    </button>
                  );
                })}
              </div>
            </div>
            <label className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm dark:border-slate-700 dark:bg-slate-950/50">
              <span className="block text-xs uppercase tracking-wide text-slate-500">Сложность от</span>
              <input
                type="range"
                min="1"
                max="5"
                value={difficultyMin}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setPage(1);
                  setDifficultyMin(next);
                  if (next > difficultyMax) setDifficultyMax(next);
                }}
                className="mt-4 w-full"
              />
              <span className="mt-2 block font-medium">{difficultyMin}/5</span>
            </label>
            <label className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-sm dark:border-slate-700 dark:bg-slate-950/50">
              <span className="block text-xs uppercase tracking-wide text-slate-500">Сложность до</span>
              <input
                type="range"
                min="1"
                max="5"
                value={difficultyMax}
                onChange={(e) => {
                  const next = Number(e.target.value);
                  setPage(1);
                  setDifficultyMax(next);
                  if (next < difficultyMin) setDifficultyMin(next);
                }}
                className="mt-4 w-full"
              />
              <span className="mt-2 block font-medium">{difficultyMax}/5</span>
            </label>
          </div>
        </section>

        {error ? <p className="mt-6 text-sm text-red-600 dark:text-red-400">{error}</p> : null}

        <section className="mt-8">
          {loading ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, idx) => (
                <div
                  key={idx}
                  className="h-64 animate-pulse rounded-3xl border border-slate-200 bg-white/70 dark:border-slate-800 dark:bg-slate-900/40"
                />
              ))}
            </div>
          ) : items.length === 0 ? (
            <div className="rounded-3xl border border-dashed border-slate-300 bg-white/70 px-6 py-12 text-center dark:border-slate-700 dark:bg-slate-900/35">
              <p className="font-display text-2xl font-semibold">Ничего не найдено</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                Попробуй убрать часть фильтров или изменить поисковый запрос.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {items.map((topic) => (
                <TopicCard
                  key={topic.id}
                  topic={topic}
                  onStart={handleStart}
                  starting={startingId === topic.id}
                />
              ))}
            </div>
          )}
        </section>

        <div className="mt-8 flex items-center justify-between gap-4">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => setPage((current) => Math.max(1, current - 1))}
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700"
          >
            Назад
          </button>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Страница {page} из {totalPages}
          </p>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700"
          >
            Дальше
          </button>
        </div>
      </div>
    </div>
  );
}

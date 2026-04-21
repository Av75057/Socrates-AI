import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { fetchConversation, publishConversation, unpublishConversation } from "../api/userApi.js";
import { useChatStore } from "../store/useChatStore.js";

export default function ConversationViewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const setActiveConversation = useChatStore((s) => s.setActiveConversation);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [pubBusy, setPubBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const d = await fetchConversation(Number(id));
        if (!cancelled) setData(d);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Ошибка");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  function continueChat() {
    if (!data) return;
    const initialMessages = data.messages.map((m) => ({
      id: `db-${m.id}`,
      role: m.role === "tutor" ? "assistant" : "user",
      text: m.content,
    }));
    setActiveConversation(data.id, data.session_key, initialMessages);
    navigate("/app");
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 px-6 py-10 text-red-700 dark:bg-[#0f172a] dark:text-red-300">
        {error}{" "}
        <Link to="/profile/history" className="text-cyan-700 underline dark:text-cyan-400">
          Назад
        </Link>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-600 dark:bg-[#0f172a] dark:text-slate-400">
        Загрузка…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <nav className="mb-6 flex gap-4 text-sm">
        <Link to="/profile/history" className="text-cyan-700 underline dark:text-cyan-400">
          ← К списку
        </Link>
      </nav>
      <h1 className="font-display text-xl font-bold text-slate-900 dark:text-white">{data.title}</h1>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={continueChat}
          className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500"
        >
          Продолжить в чате
        </button>
        {data.public_slug ? (
          <>
            <button
              type="button"
              disabled={pubBusy}
              className="rounded-lg border border-amber-500/50 px-3 py-2 text-sm text-amber-900 dark:text-amber-200"
              onClick={async () => {
                const url = `${window.location.origin}/share/${data.public_slug}`;
                try {
                  await navigator.clipboard.writeText(url);
                } catch {
                  prompt("Ссылка:", url);
                }
              }}
            >
              Копировать публичную ссылку
            </button>
            <button
              type="button"
              disabled={pubBusy}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-600"
              onClick={async () => {
                setPubBusy(true);
                try {
                  await unpublishConversation(data.id);
                  const d = await fetchConversation(data.id);
                  setData(d);
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Ошибка");
                } finally {
                  setPubBusy(false);
                }
              }}
            >
              Снять с публикации
            </button>
          </>
        ) : (
          <button
            type="button"
            disabled={pubBusy}
            className="rounded-lg border border-cyan-500/60 px-3 py-2 text-sm text-cyan-800 dark:text-cyan-200"
            onClick={async () => {
              setPubBusy(true);
              try {
                await publishConversation(data.id);
                const d = await fetchConversation(data.id);
                setData(d);
              } catch (e) {
                setError(e instanceof Error ? e.message : "Ошибка");
              } finally {
                setPubBusy(false);
              }
            }}
          >
            Опубликовать (ссылка для друзей)
          </button>
        )}
      </div>
      <div className="mt-8 max-w-3xl space-y-4">
        {data.messages.map((m) => (
          <div
            key={m.id}
            className={`rounded-lg border px-4 py-3 text-sm ${
              m.role === "user"
                ? "border-slate-200 bg-white dark:border-slate-600 dark:bg-slate-900/60"
                : "border-cyan-200 bg-cyan-50 dark:border-cyan-900/50 dark:bg-cyan-950/30"
            }`}
          >
            <span className="text-xs uppercase text-slate-500">{m.role}</span>
            <p className="mt-1 whitespace-pre-wrap text-slate-800 dark:text-slate-200">{m.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

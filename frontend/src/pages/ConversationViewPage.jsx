import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { fetchConversation } from "../api/userApi.js";
import { useChatStore } from "../store/useChatStore.js";

export default function ConversationViewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const setActiveConversation = useChatStore((s) => s.setActiveConversation);
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

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
      <div className="min-h-screen bg-[#0f172a] px-6 py-10 text-red-300">
        {error}{" "}
        <Link to="/profile/history" className="text-cyan-400 underline">
          Назад
        </Link>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0f172a] text-slate-400">
        Загрузка…
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0f172a] px-6 py-10 text-slate-100">
      <nav className="mb-6 flex gap-4 text-sm">
        <Link to="/profile/history" className="text-cyan-400 underline">
          ← К списку
        </Link>
      </nav>
      <h1 className="font-display text-xl font-bold text-white">{data.title}</h1>
      <button
        type="button"
        onClick={continueChat}
        className="mt-4 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white hover:bg-cyan-500"
      >
        Продолжить в чате
      </button>
      <div className="mt-8 max-w-3xl space-y-4">
        {data.messages.map((m) => (
          <div
            key={m.id}
            className={`rounded-lg border px-4 py-3 text-sm ${
              m.role === "user"
                ? "border-slate-600 bg-slate-900/60"
                : "border-cyan-900/50 bg-cyan-950/30"
            }`}
          >
            <span className="text-xs uppercase text-slate-500">{m.role}</span>
            <p className="mt-1 whitespace-pre-wrap text-slate-200">{m.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

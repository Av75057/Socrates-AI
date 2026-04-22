import { useState } from "react";
import { motion } from "framer-motion";
import { Pencil, Trash2 } from "lucide-react";
import { formatMessageTime } from "../utils/timeAgo.js";
import { parseDbMessageId } from "../utils/messageId.js";

function normalizeDisplayedText(text) {
  return String(text || "").replace(/\\cdot/g, "×").replace(/\\times/g, "×");
}

function UserAvatar({ label }) {
  const ch = (label || "?").trim().slice(0, 2).toUpperCase();
  return (
    <div
      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[11px] font-semibold text-slate-700 dark:bg-slate-600 dark:text-slate-100"
      aria-hidden
    >
      {ch}
    </div>
  );
}

function TutorAvatar() {
  return (
    <div
      className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-lg dark:bg-emerald-900/50"
      aria-hidden
    >
      🧠
    </div>
  );
}

export default function ChatMessage({
  role,
  text,
  messageId,
  createdAt,
  userLabel = "Я",
  canEdit = false,
  onEdit,
  onDelete,
  streaming = false,
}) {
  const isUser = role === "user";
  const displayText = normalizeDisplayedText(text);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(displayText);
  const dbId = parseDbMessageId(messageId);
  const showActions = canEdit && dbId != null && isUser && !editing;

  const submitEdit = () => {
    const t = draft.trim();
    if (!t || !messageId) return;
    onEdit?.(messageId, t);
    setEditing(false);
  };

  return (
    <motion.div
      layout
      initial={
        isUser
          ? { opacity: 0, x: 20, filter: "blur(4px)" }
          : { opacity: 0, y: 12, filter: "blur(4px)" }
      }
      animate={{ opacity: 1, x: 0, y: 0, filter: "blur(0px)" }}
      transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
      className={`group flex w-full gap-2 ${isUser ? "flex-row-reverse" : "flex-row"}`}
    >
      {isUser ? <UserAvatar label={userLabel} /> : <TutorAvatar />}
      <div
        className={`flex max-w-[min(85%,42rem)] flex-col ${isUser ? "items-end" : "items-start"}`}
      >
        <div
          className={`relative px-4 py-2.5 text-sm leading-relaxed shadow-sm sm:text-[15px] ${
            isUser
              ? "rounded-[18px] rounded-br-md bg-[#0a7cff] text-white"
              : "rounded-[18px] rounded-bl-md bg-[#f0f0f0] text-slate-900 dark:bg-[#2d2d2d] dark:text-slate-100"
          }`}
        >
          {showActions ? (
            <div
              className={`absolute -top-1 flex gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 ${
                isUser ? "left-1" : "right-1"
              }`}
            >
              <button
                type="button"
                title="Редактировать"
                onClick={() => {
                  setDraft(displayText);
                  setEditing(true);
                }}
                className="rounded-md bg-white/90 p-1 text-slate-600 shadow dark:bg-slate-800 dark:text-slate-300"
              >
                <Pencil className="h-3.5 w-3.5" />
              </button>
              <button
                type="button"
                title="Удалить"
                onClick={() => messageId && onDelete?.(messageId)}
                className="rounded-md bg-white/90 p-1 text-red-600 shadow dark:bg-slate-800 dark:text-red-400"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ) : null}
          {!isUser ? (
            <div className="mb-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-700/90 dark:text-emerald-400/90">
              Socrates
            </div>
          ) : null}
          {editing ? (
            <div className="flex flex-col gap-2">
              <textarea
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                rows={3}
                className="w-full min-w-[200px] rounded-lg border border-white/30 bg-white/10 p-2 text-white placeholder:text-white/60"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={submitEdit}
                  className="rounded-lg bg-white px-3 py-1 text-xs font-medium text-[#0a7cff]"
                >
                  Сохранить
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setDraft(displayText);
                    setEditing(false);
                  }}
                  className="rounded-lg px-3 py-1 text-xs text-white/90"
                >
                  Отмена
                </button>
              </div>
            </div>
          ) : (
            <div className="whitespace-pre-wrap break-words">
              {displayText}
              {streaming && !isUser ? <span className="blinking-cursor" aria-hidden>|</span> : null}
            </div>
          )}
        </div>
        {createdAt ? (
          <span className="mt-0.5 px-1 text-[10px] text-slate-400 dark:text-slate-500">
            {formatMessageTime(createdAt)}
          </span>
        ) : null}
      </div>
    </motion.div>
  );
}

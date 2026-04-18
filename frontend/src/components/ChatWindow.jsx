import { useDeferredValue, useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import MessageBubble from "./MessageBubble.jsx";
import TypingIndicator from "./TypingIndicator.jsx";

const MAX_RENDER = 80;

export default function ChatWindow({
  messages,
  loading,
  feedback,
  microFeedback,
  simplerBanner,
  idleHint,
  onIdleHintDismiss,
  assistLevel = 0,
}) {
  const deferred = useDeferredValue(messages);
  const visible = deferred.slice(-MAX_RENDER);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, feedback, microFeedback, simplerBanner, idleHint, assistLevel]);

  return (
    <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain px-4 py-4 max-lg:pb-[calc(13.5rem+env(safe-area-inset-bottom))] lg:pb-4">
      <div className="mx-auto flex max-w-3xl flex-col gap-3 pb-2">
        <AnimatePresence>
          {feedback ? (
            <motion.div
              key="feedback"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.25 }}
              className="overflow-hidden rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-center text-sm font-medium text-amber-100 shadow-[0_0_20px_rgba(245,158,11,0.12)]"
            >
              {feedback}
            </motion.div>
          ) : null}
        </AnimatePresence>

        <AnimatePresence>
          {microFeedback === "short" ? (
            <motion.div
              key="micro-short"
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-lg border border-slate-600/50 bg-slate-800/50 px-3 py-2 text-xs text-slate-400"
            >
              Попробуй чуть подробнее 👀
            </motion.div>
          ) : null}
          {microFeedback === "good" ? (
            <motion.div
              key="micro-good"
              initial={{ opacity: 0, x: -6 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="rounded-lg border border-orange-500/30 bg-orange-500/10 px-3 py-2 text-xs font-medium text-orange-100"
            >
              Вот это уже мысль 🔥
            </motion.div>
          ) : null}
        </AnimatePresence>

        <AnimatePresence>
          {simplerBanner ? (
            <motion.div
              key="simpler"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="rounded-xl border border-violet-500/40 bg-violet-500/10 px-4 py-3 text-sm text-violet-100"
            >
              Окей, давай проще 👇 — можно нажать «Дай подсказку» или скажи, что именно застряло.
            </motion.div>
          ) : null}
        </AnimatePresence>

        <AnimatePresence>
          {idleHint ? (
            <motion.div
              key="idle"
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-cyan-500/30 bg-cyan-950/40 px-3 py-2 text-xs text-cyan-100"
            >
              <span>Хочешь маленькую подсказку?</span>
              <button
                type="button"
                onClick={onIdleHintDismiss}
                className="min-h-[44px] min-w-[44px] touch-manipulation rounded-lg bg-cyan-500/20 px-3 py-2 text-xs font-medium active:bg-cyan-500/30 [@media(hover:hover)]:hover:bg-cyan-500/30"
              >
                Скрыть
              </button>
            </motion.div>
          ) : null}
        </AnimatePresence>

        {messages.length === 0 && !loading ? (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center text-sm leading-relaxed text-slate-500"
          >
            Это не чат для готовых ответов — только вопросы, подсказки и твоё мышление.
            <br />
            <span className="text-slate-600">Начни с темы или вопроса.</span>
          </motion.p>
        ) : null}

        {visible.map((m) => (
          <MessageBubble key={m.id} role={m.role} text={m.text} />
        ))}

        {loading ? <TypingIndicator /> : null}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}

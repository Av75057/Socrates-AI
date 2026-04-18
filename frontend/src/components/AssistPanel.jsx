import { motion } from "framer-motion";

/**
 * Анти-фрустрация: уровни 1–3 по frustration_level с сервера (0 = скрыто).
 */
export default function AssistPanel({ level, loading, onExampleHint, onExplain }) {
  if (!level || level < 1) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
      className="shrink-0 border-b border-slate-800/80 bg-[#1e293b]/95 px-4 py-3"
    >
      <div className="mx-auto max-w-3xl text-sm leading-snug text-slate-300">
        {level === 1 ? (
          <p className="text-center text-slate-200">Давай чуть проще 👇</p>
        ) : null}

        {level === 2 ? (
          <div className="space-y-3">
            <p className="text-center text-slate-200">Ты не обязан знать сразу 🙂</p>
            <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
              <button
                type="button"
                disabled={loading}
                onClick={() => onExampleHint?.()}
                className="min-h-[48px] touch-manipulation rounded-xl border border-amber-500/45 bg-amber-500/15 px-4 py-3 text-sm font-semibold text-amber-100 active:bg-amber-500/25 disabled:opacity-40 [@media(hover:hover)]:hover:bg-amber-500/20"
              >
                Дай пример
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={() => onExplain?.()}
                className="min-h-[48px] touch-manipulation rounded-xl border border-rose-500/45 bg-rose-500/12 px-4 py-3 text-sm font-semibold text-rose-100 active:bg-rose-500/22 disabled:opacity-40 [@media(hover:hover)]:hover:bg-rose-500/18"
              >
                Объясни проще
              </button>
            </div>
          </div>
        ) : null}

        {level >= 3 ? (
          <div className="space-y-3">
            <p className="text-center text-slate-200">Окей, давай разберём это вместе 👇</p>
            <button
              type="button"
              disabled={loading}
              onClick={() => onExplain?.()}
              className="mx-auto flex min-h-[48px] w-full max-w-sm touch-manipulation items-center justify-center rounded-xl bg-violet-600 px-4 py-3 text-sm font-semibold text-white active:bg-violet-500 disabled:opacity-40 sm:w-auto [@media(hover:hover)]:hover:bg-violet-500"
            >
              Показать объяснение
            </button>
          </div>
        ) : null}
      </div>
    </motion.div>
  );
}

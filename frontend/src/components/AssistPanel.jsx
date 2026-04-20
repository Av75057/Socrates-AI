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
      className="shrink-0 border-b border-slate-200 bg-slate-100/95 px-4 py-3 dark:border-slate-800/80 dark:bg-[#1e293b]/95"
    >
      <div className="mx-auto max-w-3xl text-sm leading-snug text-slate-700 dark:text-slate-300">
        {level === 1 ? (
          <p className="text-center text-slate-800 dark:text-slate-200">Давай чуть проще 👇</p>
        ) : null}

        {level === 2 ? (
          <div className="space-y-3">
            <p className="text-center text-slate-800 dark:text-slate-200">Ты не обязан знать сразу 🙂</p>
            <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
              <button
                type="button"
                disabled={loading}
                onClick={() => onExampleHint?.()}
                className="min-h-[48px] touch-manipulation rounded-xl border border-amber-600/40 bg-amber-100 px-4 py-3 text-sm font-semibold text-amber-950 active:bg-amber-200 disabled:opacity-40 dark:border-amber-500/45 dark:bg-amber-500/15 dark:text-amber-100 dark:active:bg-amber-500/25 dark:[@media(hover:hover)]:hover:bg-amber-500/20 [@media(hover:hover)]:hover:bg-amber-200"
              >
                Дай пример
              </button>
              <button
                type="button"
                disabled={loading}
                onClick={() => onExplain?.()}
                className="min-h-[48px] touch-manipulation rounded-xl border border-rose-500/50 bg-rose-100 px-4 py-3 text-sm font-semibold text-rose-900 active:bg-rose-200 disabled:opacity-40 dark:border-rose-500/45 dark:bg-rose-500/12 dark:text-rose-100 dark:active:bg-rose-500/22 dark:[@media(hover:hover)]:hover:bg-rose-500/18 [@media(hover:hover)]:hover:bg-rose-200"
              >
                Объясни проще
              </button>
            </div>
          </div>
        ) : null}

        {level >= 3 ? (
          <div className="space-y-3">
            <p className="text-center text-slate-800 dark:text-slate-200">Окей, давай разберём это вместе 👇</p>
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

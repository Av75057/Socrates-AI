import { AnimatePresence, motion } from "framer-motion";

export default function DailyChallengeModal({ open, onClose, text, completed, loading }) {
  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.button
            type="button"
            aria-label="Закрыть"
            className="fixed inset-0 z-[60] bg-black/50 backdrop-blur-[1px]"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby="daily-challenge-title"
            className="fixed left-1/2 top-1/2 z-[61] w-[min(calc(100vw-2rem),24rem)] -translate-x-1/2 -translate-y-1/2 rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-600 dark:bg-slate-900"
            initial={{ opacity: 0, scale: 0.96, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.96, y: 8 }}
            transition={{ type: "spring", stiffness: 380, damping: 32 }}
          >
            <h2
              id="daily-challenge-title"
              className="flex items-center gap-2 font-display text-lg font-semibold text-slate-900 dark:text-white"
            >
              <span aria-hidden>🎯</span> Вызов дня (UTC)
            </h2>
            {loading ? (
              <p className="mt-3 text-sm text-slate-500">Загрузка…</p>
            ) : text ? (
              <>
                <p className="mt-3 text-sm leading-relaxed text-slate-800 dark:text-slate-200">{text}</p>
                <p className="mt-4 text-xs text-slate-600 dark:text-slate-400">
                  {completed
                    ? "✓ Выполнено — бонус начислен сегодня."
                    : "Выполни условие в ответе тьютору — проверка автоматическая."}
                </p>
              </>
            ) : (
              <p className="mt-3 text-sm text-slate-500">Нет активного вызова.</p>
            )}
            <button
              type="button"
              onClick={onClose}
              className="mt-5 w-full rounded-xl bg-cyan-600 py-2.5 text-sm font-medium text-white hover:bg-cyan-500"
            >
              Закрыть
            </button>
          </motion.div>
        </>
      ) : null}
    </AnimatePresence>
  );
}

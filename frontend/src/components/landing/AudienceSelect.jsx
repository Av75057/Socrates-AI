import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function AudienceSelect() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#020617] px-6 text-slate-100">
      <motion.p
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-2 text-center text-xs font-medium uppercase tracking-wider text-slate-500"
      >
        Socrates AI
      </motion.p>
      <motion.h1
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="text-center font-display text-3xl font-bold tracking-tight md:text-4xl"
      >
        Кто ты?
      </motion.h1>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.12 }}
        className="mt-3 max-w-md text-center text-sm text-slate-400"
      >
        Разные истории — разные акценты. Выбери, что ближе: интерес и игра или результат и спокойствие.
      </motion.p>

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.18 }}
        className="mt-10 flex w-full max-w-md flex-col gap-4 sm:flex-row sm:justify-center"
      >
        <Link
          to="/student"
          className="min-h-[52px] flex-1 touch-manipulation rounded-2xl bg-blue-500 px-6 py-4 text-center text-base font-semibold text-white shadow-lg shadow-blue-900/30 transition active:scale-[0.98] sm:flex-initial sm:min-w-[200px] [@media(hover:hover)]:hover:bg-blue-400"
        >
          Я ученик
        </Link>
        <Link
          to="/for-parents"
          className="min-h-[52px] flex-1 touch-manipulation rounded-2xl bg-emerald-600 px-6 py-4 text-center text-base font-semibold text-white shadow-lg shadow-emerald-900/30 transition active:scale-[0.98] sm:flex-initial sm:min-w-[200px] [@media(hover:hover)]:hover:bg-emerald-500"
        >
          Я родитель
        </Link>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.28 }}
        className="mt-12 text-center"
      >
        <Link to="/app" className="text-sm text-slate-500 underline-offset-4 hover:text-slate-400">
          Уже знаком — сразу в приложение
        </Link>
      </motion.div>
    </div>
  );
}

import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function StudentHero() {
  return (
    <section className="relative flex min-h-[88vh] flex-col items-center justify-center overflow-hidden px-6 pb-16 pt-20 text-center text-white">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.3),transparent)]"
        aria-hidden
      />
      <motion.p
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative mb-4 text-sm font-semibold uppercase tracking-wider text-blue-300"
      >
        Это не репетитор
      </motion.p>
      <motion.h1
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.06 }}
        className="relative max-w-3xl font-display text-3xl font-bold leading-tight md:text-5xl"
      >
        Тебе не будут давать ответы
      </motion.h1>
      <motion.h2
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12 }}
        className="relative mt-4 max-w-2xl text-xl font-semibold text-blue-400 md:text-2xl"
      >
        И именно поэтому ты начнёшь понимать
      </motion.h2>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.18 }}
        className="relative mt-6 max-w-lg text-slate-400"
      >
        Это как игра, но ты реально начинаешь думать — без списывания и без «выучи определение».
      </motion.p>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.22 }}
        className="relative mt-10 flex flex-wrap items-center justify-center gap-3"
      >
        <Link
          to="/app"
          className="min-h-[48px] rounded-2xl bg-blue-500 px-8 py-3 text-base font-semibold text-white shadow-lg transition active:scale-[0.98] [@media(hover:hover)]:hover:bg-blue-400"
        >
          Попробуй бесплатно
        </Link>
        <Link
          to="/"
          className="min-h-[48px] rounded-2xl border border-slate-600 px-6 py-3 text-sm font-medium text-slate-300 [@media(hover:hover)]:hover:border-slate-500"
        >
          ← Назад
        </Link>
      </motion.div>
    </section>
  );
}

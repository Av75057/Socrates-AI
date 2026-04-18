import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function ParentHero() {
  return (
    <section className="relative flex min-h-[88vh] flex-col items-center justify-center overflow-hidden px-6 pb-16 pt-20 text-center text-white">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(16,185,129,0.2),transparent)]"
        aria-hidden
      />
      <motion.h1
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative max-w-3xl font-display text-3xl font-bold leading-tight md:text-5xl"
      >
        Ваш ребёнок перестанет списывать и начнёт понимать предмет
      </motion.h1>
      <motion.p
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.08 }}
        className="relative mt-6 max-w-xl text-lg text-slate-300"
      >
        Ребёнок делает уроки, но не понимает? Мы создали систему, которая заставляет думать, а не копировать ответы.
      </motion.p>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.14 }}
        className="relative mt-10 flex flex-wrap items-center justify-center gap-3"
      >
        <Link
          to="/app"
          className="min-h-[48px] rounded-2xl bg-emerald-500 px-8 py-3 text-base font-semibold text-slate-950 shadow-lg transition active:scale-[0.98] [@media(hover:hover)]:hover:bg-emerald-400"
        >
          Проверить бесплатно
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

import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function Hero() {
  return (
    <section className="relative flex min-h-[92vh] flex-col items-center justify-center overflow-hidden px-6 pb-16 pt-24 text-center text-white">
      <div
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(59,130,246,0.25),transparent)]"
        aria-hidden
      />
      <motion.p
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-4 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1 text-xs font-medium uppercase tracking-wider text-blue-200"
      >
        Не репетитор — другой тип ИИ
      </motion.p>
      <motion.h1
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.05 }}
        className="relative max-w-4xl font-display text-4xl font-bold leading-tight tracking-tight md:text-5xl lg:text-6xl"
      >
        Нейросеть, которая{" "}
        <span className="bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent">
          отказывается давать ответы
        </span>
      </motion.h1>
      <motion.p
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.12 }}
        className="mt-6 max-w-xl text-lg text-slate-400 md:text-xl"
      >
        И именно поэтому ты наконец начинаешь понимать, а не просто копировать готовые решения.
      </motion.p>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="mt-3 text-sm font-medium text-emerald-400/90"
      >
        Твой мозг начнёт работать уже через 5 минут
      </motion.p>
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.22 }}
        className="mt-10 flex flex-wrap items-center justify-center gap-4"
      >
        <Link
          to="/app"
          className="inline-flex items-center justify-center rounded-2xl bg-blue-600 px-8 py-3.5 text-base font-semibold text-white shadow-lg shadow-blue-900/40 transition hover:scale-[1.03] hover:bg-blue-500"
        >
          Попробовать бесплатно
        </Link>
        <a
          href="#demo"
          className="rounded-2xl border border-slate-600 px-6 py-3.5 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:bg-slate-800/50"
        >
          Смотреть демо
        </a>
      </motion.div>
      <p className="mt-6 text-xs text-slate-600">Без регистрации · 3 темы в голове — и поехали</p>
    </section>
  );
}

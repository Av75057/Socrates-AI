import { motion } from "framer-motion";

const ITEMS = [
  "задаёт наводящие вопросы вместо готовых ответов",
  "тренирует причинно-следственное мышление",
  "запоминает темы и типичные ошибки",
];

export default function ParentSolution() {
  return (
    <section className="bg-[#0f172a] px-6 py-16">
      <motion.h2
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center font-display text-2xl font-bold text-white"
      >
        Как это меняет картину
      </motion.h2>
      <ul className="mx-auto mt-8 max-w-lg space-y-3 text-slate-200">
        {ITEMS.map((t, i) => (
          <motion.li
            key={t}
            initial={{ opacity: 0, x: -8 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.06 }}
            className="flex gap-3 rounded-xl border border-emerald-500/25 bg-emerald-950/20 px-4 py-3 text-sm"
          >
            <span className="text-emerald-400" aria-hidden>
              ✔
            </span>
            {t}
          </motion.li>
        ))}
      </ul>
    </section>
  );
}

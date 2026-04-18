import { motion } from "framer-motion";

const ITEMS = [
  "списывает ГДЗ и готовые разборы",
  "не понимает, зачем формула",
  "быстро забывает перед контрольной",
];

export default function ParentProblem() {
  return (
    <section className="border-y border-slate-800 bg-[#020617] px-6 py-16">
      <motion.h2
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center font-display text-2xl font-bold text-white"
      >
        Знакомо?
      </motion.h2>
      <ul className="mx-auto mt-8 max-w-lg space-y-3 text-slate-300">
        {ITEMS.map((t, i) => (
          <motion.li
            key={t}
            initial={{ opacity: 0, x: -8 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.06 }}
            className="flex gap-3 rounded-xl border border-rose-500/20 bg-rose-950/20 px-4 py-3 text-sm"
          >
            <span className="text-rose-400" aria-hidden>
              ❌
            </span>
            {t}
          </motion.li>
        ))}
      </ul>
    </section>
  );
}

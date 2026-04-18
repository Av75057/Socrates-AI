import { motion } from "framer-motion";

const STEPS = [
  { emoji: "😤", text: "Сначала бесишься" },
  { emoji: "🎮", text: "Потом втягиваешься" },
  { emoji: "💡", text: "Потом начинаешь понимать" },
];

export default function StudentExperience() {
  return (
    <section className="bg-[#0f172a] px-6 py-16">
      <motion.h2
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center font-display text-2xl font-bold text-white"
      >
        Как это обычно ощущается
      </motion.h2>
      <div className="mx-auto mt-10 flex max-w-2xl flex-col gap-4 md:flex-row md:justify-center">
        {STEPS.map((s, i) => (
          <motion.div
            key={s.text}
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.08 }}
            className="flex flex-1 items-center gap-3 rounded-2xl border border-slate-700/80 bg-slate-900/40 px-4 py-4 text-slate-200"
          >
            <span className="text-2xl" aria-hidden>
              {s.emoji}
            </span>
            <span className="text-sm font-medium leading-snug">{s.text}</span>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

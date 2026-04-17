import { motion } from "framer-motion";

const cards = [
  { title: "Понимание, а не зубрёжка", sub: "Связи в голове, а не текст в конспекте." },
  { title: "Умение думать", sub: "Вопросы сильнее готовых ответов." },
  { title: "Уверенность в знаниях", sub: "Ты можешь объяснить другу — значит, понял." },
];

export default function Benefits() {
  return (
    <section className="bg-[#0f172a] px-6 py-20 text-center text-white">
      <motion.h2
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="font-display text-3xl font-bold md:text-4xl"
      >
        Что ты получишь
      </motion.h2>
      <div className="mx-auto mt-12 grid max-w-5xl gap-6 md:grid-cols-3">
        {cards.map((c, i) => (
          <motion.div
            key={c.title}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.06 }}
            className="rounded-2xl border border-slate-800 bg-[#020617] p-6 text-left"
          >
            <p className="font-semibold text-white">{c.title}</p>
            <p className="mt-2 text-sm text-slate-400">{c.sub}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

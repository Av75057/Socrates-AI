import { motion } from "framer-motion";

const items = [
  {
    title: "Ты копируешь ответы",
    text: "ChatGPT выдаёт готовое — мозг отдыхает.",
  },
  {
    title: "Тебе сразу дают решение",
    text: "Нет пространства, чтобы самому «догнать» идею.",
  },
  {
    title: "Ты не думаешь сам",
    text: "Понимание не строится, если не было трения.",
  },
];

export default function Problem() {
  return (
    <section className="border-t border-slate-800/80 bg-[#020617] px-6 py-20 text-center text-white">
      <motion.h2
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="font-display text-3xl font-bold md:text-4xl"
      >
        Почему ты не понимаешь тему?
      </motion.h2>
      <p className="mx-auto mt-4 max-w-2xl text-slate-400">
        Ты не «тупой» — тебе просто слишком часто дают ответы.{" "}
        <span className="text-slate-300">Ты не понимаешь, потому что тебе дают ответы.</span>
      </p>
      <div className="mx-auto mt-12 grid max-w-5xl gap-6 md:grid-cols-3">
        {items.map((item, i) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.08 }}
            className="rounded-2xl border border-slate-800 bg-[#0f172a] p-6 text-left shadow-lg"
          >
            <p className="font-semibold text-white">{item.title}</p>
            <p className="mt-2 text-sm text-slate-400">{item.text}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}

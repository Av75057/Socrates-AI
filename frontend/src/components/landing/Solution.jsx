import { motion } from "framer-motion";

const steps = [
  "Ты задаёшь тему или вопрос",
  "ИИ не выдаёт решение — только вопросы и направление",
  "Ты формулируешь мысли своими словами",
  "Впервые понимаешь, а не заучиваешь",
];

export default function Solution() {
  return (
    <section className="bg-[#0f172a] px-6 py-20 text-center text-white">
      <motion.h2
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="font-display text-3xl font-bold md:text-4xl"
      >
        Как это работает
      </motion.h2>
      <p className="mx-auto mt-4 max-w-xl text-slate-400">
        ИИ, который не даёт списывать — и именно поэтому ты начинаешь понимать.
      </p>
      <div className="mx-auto mt-12 max-w-lg space-y-4 text-left text-lg text-slate-300">
        {steps.map((line, i) => (
          <motion.p
            key={line}
            initial={{ opacity: 0, x: -12 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.06 }}
            className={`flex gap-3 ${i === 3 ? "font-semibold text-blue-300" : ""}`}
          >
            <span className="text-slate-600">{i + 1}.</span>
            {line}
          </motion.p>
        ))}
      </div>
    </section>
  );
}

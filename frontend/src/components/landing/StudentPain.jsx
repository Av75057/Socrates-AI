import { motion } from "framer-motion";

export default function StudentPain() {
  return (
    <section className="border-y border-slate-800 bg-[#0f172a] px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto max-w-2xl text-center"
      >
        <p className="text-lg font-medium text-slate-200 md:text-xl">
          Ты не тупой.
        </p>
        <p className="mt-3 text-slate-400">
          Тебе просто всегда давали готовые решения — и мозг привык не включаться.
        </p>
      </motion.div>
    </section>
  );
}

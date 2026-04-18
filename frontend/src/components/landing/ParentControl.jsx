import { motion } from "framer-motion";

export default function ParentControl() {
  return (
    <section className="border-t border-slate-800 bg-[#0f172a] px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto max-w-2xl rounded-2xl border border-emerald-500/30 bg-emerald-950/20 px-6 py-8 text-center"
      >
        <p className="text-sm font-semibold uppercase tracking-wider text-emerald-300">Контроль</p>
        <h2 className="mt-2 font-display text-2xl font-bold text-white">Вы видите прогресс ребёнка</h2>
        <p className="mt-3 text-slate-400">
          Темы, типичные ошибки, этапы разбора — в одном интерфейсе рядом с диалогом. Не магия «чёрного ящика», а
          прозрачная траектория.
        </p>
      </motion.div>
    </section>
  );
}

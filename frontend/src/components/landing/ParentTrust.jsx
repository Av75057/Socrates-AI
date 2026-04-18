import { motion } from "framer-motion";

const ITEMS = ["школа и домашние темы", "подготовка к контрольным и экзаменам", "самостоятельное углубление без списывания"];

export default function ParentTrust() {
  return (
    <section className="bg-[#020617] px-6 py-16">
      <motion.h2
        initial={{ opacity: 0, y: 8 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="text-center font-display text-xl font-bold text-white md:text-2xl"
      >
        Подходит для
      </motion.h2>
      <ul className="mx-auto mt-8 flex max-w-2xl flex-col gap-3 sm:flex-row sm:flex-wrap sm:justify-center">
        {ITEMS.map((t, i) => (
          <motion.li
            key={t}
            initial={{ opacity: 0, scale: 0.98 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.05 }}
            className="rounded-xl border border-slate-700 bg-slate-900/50 px-4 py-3 text-center text-sm text-slate-300 sm:min-w-[200px]"
          >
            ✔ {t}
          </motion.li>
        ))}
      </ul>
    </section>
  );
}

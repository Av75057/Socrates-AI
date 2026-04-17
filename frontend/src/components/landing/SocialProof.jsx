import { motion } from "framer-motion";

export default function SocialProof() {
  return (
    <section className="border-t border-slate-800/80 bg-[#020617] px-6 py-16 text-center text-white">
      <motion.p
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="text-sm uppercase tracking-wider text-slate-500"
      >
        Ранний доступ
      </motion.p>
      <p className="mx-auto mt-3 max-w-xl text-slate-300">
        Студенты и взрослые пробуют формат «вопросы вместо ответов» — без списывания и без воды.
      </p>
      <div className="mx-auto mt-8 flex max-w-2xl flex-wrap justify-center gap-8 text-sm text-slate-500">
        <div>
          <p className="text-2xl font-bold text-slate-200">MVP</p>
          <p>живой продукт</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-slate-200">0₽</p>
          <p>на старте</p>
        </div>
        <div>
          <p className="text-2xl font-bold text-slate-200">5+ мин</p>
          <p>средняя сессия</p>
        </div>
      </div>
    </section>
  );
}

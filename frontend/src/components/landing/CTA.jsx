import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function CTA() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-blue-600 to-indigo-800 px-6 py-20 text-center text-white">
      <div className="pointer-events-none absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'0.06\'%3E%3Cpath d=\'M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-50" />
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative mx-auto max-w-2xl"
      >
        <h2 className="font-display text-3xl font-bold md:text-4xl">Попробуй бесплатно</h2>
        <p className="mt-4 text-lg text-blue-100/90">3 темы без регистрации — зайди и начни диалог.</p>
        <Link
          to="/app"
          className="mt-8 inline-flex rounded-2xl bg-slate-950 px-10 py-4 text-base font-semibold text-white shadow-xl transition hover:scale-[1.03] hover:bg-slate-900"
        >
          Начать
        </Link>
      </motion.div>
    </section>
  );
}

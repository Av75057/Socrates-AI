import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function LandingCta({ variant = "student" }) {
  const isStudent = variant === "student";
  return (
    <section
      className={`relative overflow-hidden px-6 py-20 text-center text-white ${
        isStudent
          ? "bg-gradient-to-br from-blue-600 to-indigo-900"
          : "bg-gradient-to-br from-emerald-700 to-slate-900"
      }`}
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.07'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E\")",
        }}
      />
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="relative mx-auto max-w-2xl"
      >
        <h2 className="font-display text-3xl font-bold md:text-4xl">
          {isStudent ? "Попробуй бесплатно" : "Проверить бесплатно"}
        </h2>
        <p className="mt-4 text-lg text-white/85">
          {isStudent
            ? "Зайди в чат и выбери тему — без регистрации."
            : "Посмотрите, как ребёнок отвечает своими словами, а не копирует."}
        </p>
        <Link
          to="/app"
          className="mt-8 inline-flex min-h-[52px] items-center justify-center rounded-2xl bg-slate-950 px-10 py-4 text-base font-semibold text-white shadow-xl transition active:scale-[0.98] [@media(hover:hover)]:hover:bg-slate-900"
        >
          {isStudent ? "Погнали" : "Открыть демо"}
        </Link>
      </motion.div>
    </section>
  );
}

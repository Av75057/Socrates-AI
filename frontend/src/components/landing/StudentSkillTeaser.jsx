import { motion } from "framer-motion";

const NODES = [
  { label: "Сила", st: "done" },
  { label: "Ускорение", st: "open" },
  { label: "Импульс", st: "lock" },
];

export default function StudentSkillTeaser() {
  return (
    <section className="bg-[#020617] px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        className="mx-auto max-w-3xl text-center"
      >
        <h2 className="font-display text-2xl font-bold text-white md:text-3xl">Открывай темы как уровни в игре</h2>
        <p className="mt-3 text-slate-400">Skill tree, опыт и память — чтобы было ощущение прокачки, а не урока.</p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          {NODES.map((n) => (
            <div
              key={n.label}
              className={`min-w-[7rem] rounded-xl border px-4 py-3 text-sm font-medium ${
                n.st === "done"
                  ? "border-emerald-500/50 bg-emerald-950/40 text-emerald-100"
                  : n.st === "open"
                    ? "border-blue-500/50 bg-blue-950/40 text-blue-100"
                    : "border-slate-700 bg-slate-900/50 text-slate-500"
              }`}
            >
              {n.st === "done" ? "✔ " : n.st === "lock" ? "🔒 " : "◐ "}
              {n.label}
            </div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}

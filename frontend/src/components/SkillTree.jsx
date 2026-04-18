import { motion } from "framer-motion";

const STYLES = {
  completed: "border-emerald-500/50 bg-emerald-950/40 text-emerald-100",
  in_progress: "border-amber-500/50 bg-amber-950/35 text-amber-100",
  available: "border-blue-500/50 bg-blue-950/35 text-blue-100",
  locked: "border-slate-700/80 bg-slate-900/50 text-slate-500",
};

export default function SkillTree({ skillTree, className = "" }) {
  const trackTitle = skillTree?.track_title || "Навыки";
  const done = skillTree?.completed ?? 0;
  const total = skillTree?.total ?? 0;
  const nodes = Array.isArray(skillTree?.nodes) ? skillTree.nodes : [];

  if (!nodes.length) {
    return (
      <div
        className={`rounded-xl border border-dashed border-slate-700/60 p-3 text-center text-xs text-slate-500 ${className}`}
      >
        Дерево навыков загрузится после диалога с сервером
      </div>
    );
  }

  return (
    <div className={`rounded-xl border border-slate-700/60 bg-slate-900/30 p-3 ${className}`}>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          🌳 {trackTitle}
        </p>
        <p className="text-[11px] tabular-nums text-slate-400">
          {done}/{total} тем
        </p>
      </div>

      <div className="-mx-1 flex gap-2 overflow-x-auto pb-1 pt-0.5">
        {nodes.map((node) => {
          const st = node.status || "locked";
          const cls = STYLES[st] || STYLES.locked;
          return (
            <motion.div
              key={`${node.id}-${st}`}
              layout
              initial={{ scale: 0.97, opacity: 0.85 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
              className={`min-w-[9.5rem] shrink-0 rounded-xl border px-3 py-2.5 text-xs ${cls}`}
            >
              <div className="font-semibold leading-tight">{node.title}</div>
              <div className="mt-1 text-[10px] uppercase tracking-wide opacity-80">
                {st === "completed" && "🟢 Готово"}
                {st === "in_progress" && "🟡 В процессе"}
                {st === "available" && "🔵 Доступно"}
                {st === "locked" && "⚫ Закрыто"}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}

import { motion } from "framer-motion";
import { skillTreeTopicMismatch } from "../utils/subjectTrack.js";

const STYLES = {
  completed:
    "border-emerald-600/40 bg-emerald-100 text-emerald-900 dark:border-emerald-500/50 dark:bg-emerald-950/40 dark:text-emerald-100",
  in_progress:
    "border-amber-600/40 bg-amber-100 text-amber-900 dark:border-amber-500/50 dark:bg-amber-950/35 dark:text-amber-100",
  available:
    "border-blue-600/40 bg-blue-100 text-blue-900 dark:border-blue-500/50 dark:bg-blue-950/35 dark:text-blue-100",
  locked:
    "border-slate-300 bg-slate-100 text-slate-600 dark:border-slate-700/80 dark:bg-slate-900/50 dark:text-slate-500",
};

export default function SkillTree({ skillTree, topic = "", className = "" }) {
  const trackTitle = skillTree?.track_title || "Навыки";
  const done = skillTree?.completed ?? 0;
  const total = skillTree?.total ?? 0;
  const rawNodes = Array.isArray(skillTree?.nodes) ? skillTree.nodes : [];
  const mismatch = skillTreeTopicMismatch(topic, skillTree);
  const nodes = mismatch ? [] : rawNodes;

  if (mismatch) {
    return (
      <div
        className={`rounded-xl border border-dashed border-amber-600/50 bg-amber-50 p-3 text-center text-xs text-amber-950 dark:border-amber-700/50 dark:bg-amber-950/20 dark:text-amber-100/90 ${className}`}
      >
        Тема «{(topic || "").trim() || "…"}» не совпадает с картой навыков на сервере. Отправьте ещё одно
        сообщение — обновится математика или физика.
      </div>
    );
  }

  if (!nodes.length) {
    return (
      <div
        className={`rounded-xl border border-dashed border-slate-300 p-3 text-center text-xs text-slate-600 dark:border-slate-700/60 dark:text-slate-500 ${className}`}
      >
        Дерево навыков загрузится после диалога с сервером
      </div>
    );
  }

  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white/70 p-3 dark:border-slate-700/60 dark:bg-slate-900/30 ${className}`}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          🌳 {trackTitle}
        </p>
        <p className="text-[11px] tabular-nums text-slate-500 dark:text-slate-400">
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

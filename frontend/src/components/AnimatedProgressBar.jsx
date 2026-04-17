import { motion } from "framer-motion";
import { MAX_STEPS } from "../constants/progress.js";

export default function AnimatedProgressBar({ attempts, pulseKey }) {
  const pct = Math.min(100, (Math.min(Math.max(attempts, 0), MAX_STEPS) / MAX_STEPS) * 100);

  return (
    <div className="w-full">
      <div className="mb-1 flex justify-between text-[11px] text-slate-500">
        <span>Прогресс</span>
        <span className="tabular-nums text-slate-400">
          {Math.min(attempts, MAX_STEPS)}/{MAX_STEPS}
        </span>
      </div>
      <div className="relative h-3 overflow-hidden rounded-full bg-slate-800/90 ring-1 ring-slate-700/50">
        <motion.div
          key={pulseKey}
          className="h-full rounded-full bg-gradient-to-r from-emerald-500 via-cyan-500 to-blue-500 shadow-[0_0_12px_rgba(34,211,238,0.45)]"
          initial={{ width: 0 }}
          animate={{
            width: `${pct}%`,
            scale: [1, 1.04, 1],
          }}
          transition={{
            width: { duration: 0.45, ease: "easeOut" },
            scale: { duration: 0.35, ease: "easeOut" },
          }}
        />
      </div>
    </div>
  );
}

import { motion } from "framer-motion";
import AnimatedProgressBar from "../AnimatedProgressBar.jsx";
import TutorAvatar from "../TutorAvatar.jsx";
import { getThinkingLevel } from "../../utils/feedbackHeuristics.js";

const TIPS = [
  "Один вопрос лучше, чем готовый ответ.",
  "Если трудно — это как раз рост.",
  "Свяжи новое с примером из жизни.",
];

function MindMapVisual({ topic, attempts }) {
  const center = topic?.trim() || "Тема";
  const nodes = [
    { id: "a", label: "Сила", show: attempts >= 1 },
    { id: "b", label: "Масса", show: attempts >= 2 },
    { id: "c", label: "Ускорение", show: attempts >= 3 },
  ];

  return (
    <div className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-3">
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-slate-500">Mind-map</p>
      <div className="flex flex-col items-center gap-1 text-xs">
        <motion.div
          layout
          className="rounded-lg border border-cyan-500/40 bg-[#1e293b] px-3 py-1.5 font-medium text-cyan-100"
        >
          {center.length > 20 ? `${center.slice(0, 18)}…` : center}
        </motion.div>
        <div className="text-slate-600">↓</div>
        <div className="flex flex-wrap justify-center gap-2">
          {nodes.map((n) => (
            <motion.div
              key={n.id}
              initial={false}
              animate={{
                opacity: n.show ? 1 : 0.35,
                scale: n.show ? 1 : 0.96,
              }}
              className={`rounded-md border px-2 py-1 ${
                n.show ? "border-emerald-500/50 text-emerald-100" : "border-slate-700 text-slate-600"
              }`}
            >
              {n.label}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function SidePanel({
  attempts,
  xp,
  streak,
  topic,
  avatarMood,
  whisperIndex,
  progressPulseKey,
}) {
  const level = getThinkingLevel(attempts);

  return (
    <aside className="flex max-h-[100dvh] w-full flex-col gap-4 overflow-y-auto border-t border-slate-800/80 bg-[#0f172a] p-4 lg:w-[30%] lg:min-w-[260px] lg:max-w-md lg:border-l lg:border-t-0">
      <TutorAvatar mood={avatarMood} whisperIndex={whisperIndex} />

      <div className="rounded-xl border border-slate-700/50 bg-slate-900/30 p-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Уровень</p>
        <p className="mt-1 text-sm font-semibold text-slate-200">{level.label}</p>
      </div>

      <AnimatedProgressBar attempts={attempts} pulseKey={progressPulseKey} />

      <div className="grid grid-cols-2 gap-2">
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/40 p-3 text-center">
          <p className="text-[10px] uppercase text-slate-500">XP</p>
          <motion.p
            key={xp}
            initial={{ scale: 1.2 }}
            animate={{ scale: 1 }}
            className="text-lg font-bold tabular-nums text-cyan-300"
          >
            {xp}
          </motion.p>
        </div>
        <div className="rounded-xl border border-slate-700/50 bg-slate-900/40 p-3 text-center">
          <p className="text-[10px] uppercase text-slate-500">Серия</p>
          <p className="text-lg font-bold text-orange-200">
            {streak > 0 ? (
              <>
                <span aria-hidden>🔥</span> {streak}
              </>
            ) : (
              <span className="text-slate-600">—</span>
            )}
          </p>
          <p className="mt-0.5 text-[10px] text-slate-600">сильных ответов подряд</p>
        </div>
      </div>

      <MindMapVisual topic={topic} attempts={attempts} />

      <div className="rounded-xl border border-dashed border-slate-700/60 p-3">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Подсказки UX</p>
        <ul className="mt-2 space-y-1.5 text-xs text-slate-500">
          {TIPS.map((t) => (
            <li key={t}>· {t}</li>
          ))}
        </ul>
      </div>
    </aside>
  );
}

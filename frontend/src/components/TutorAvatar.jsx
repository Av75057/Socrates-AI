import { motion } from "framer-motion";

const MOODS = {
  neutral: { emoji: "🙂", ring: "ring-slate-600/50", glow: "shadow-slate-900/40" },
  almost: { emoji: "😏", ring: "ring-amber-400/60", glow: "shadow-amber-500/25" },
  fire: { emoji: "🔥", ring: "ring-orange-400/60", glow: "shadow-orange-500/30" },
  doubt: { emoji: "🤨", ring: "ring-slate-500/60", glow: "shadow-slate-600/30" },
};

const WHISPERS = [
  "Интересно…",
  "Хм…",
  "А если подумать так?",
  "Попробуй связать с тем, что уже знаешь.",
];

export default function TutorAvatar({ mood = "neutral", whisperIndex = 0 }) {
  const m = MOODS[mood] || MOODS.neutral;
  const whisper = WHISPERS[whisperIndex % WHISPERS.length];

  return (
    <div className="flex flex-col items-center gap-2 text-center">
      <motion.div
        key={mood}
        initial={{ scale: 0.85, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 400, damping: 24 }}
        className={`flex h-16 w-16 items-center justify-center rounded-full bg-slate-200 text-3xl shadow-lg ring-2 dark:bg-[#1e293b] ${m.ring} ${m.glow}`}
      >
        {m.emoji}
      </motion.div>
      <p className="text-[11px] italic leading-snug text-slate-500">&ldquo;{whisper}&rdquo;</p>
    </div>
  );
}

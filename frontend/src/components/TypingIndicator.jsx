import { motion } from "framer-motion";

const dot = {
  animate: {
    y: [0, -5, 0],
    opacity: [0.5, 1, 0.5],
  },
  transition: { duration: 0.6, repeat: Infinity, ease: "easeInOut" },
};

export default function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-start"
    >
      <div className="flex items-center gap-3 rounded-2xl rounded-bl-md border border-slate-600/50 bg-[#1e293b] px-4 py-3 text-sm text-slate-300 shadow-inner shadow-black/20">
        <span className="flex gap-1.5" aria-hidden>
          {[0, 1, 2].map((i) => (
            <motion.span
              key={i}
              className="inline-block h-2 w-2 rounded-full bg-cyan-400"
              animate={dot.animate}
              transition={{
                ...dot.transition,
                delay: i * 0.15,
              }}
            />
          ))}
        </span>
        <span className="text-slate-200">Думаю…</span>
      </div>
    </motion.div>
  );
}

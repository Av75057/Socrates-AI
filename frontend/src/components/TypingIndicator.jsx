import { motion } from "framer-motion";

export default function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex w-full gap-2"
      aria-live="polite"
      aria-label="Тьютор печатает"
    >
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-lg dark:bg-emerald-900/50"
        aria-hidden
      >
        🧠
      </div>
      <div className="flex items-center gap-1 rounded-[18px] rounded-bl-md border border-slate-200/80 bg-[#f0f0f0] px-4 py-3 dark:border-slate-600/50 dark:bg-[#2d2d2d]">
        <span className="h-2 w-2 animate-bounce-dot rounded-full bg-slate-500 dark:bg-slate-400" />
        <span className="h-2 w-2 animate-bounce-dot-delay-1 rounded-full bg-slate-500 dark:bg-slate-400" />
        <span className="h-2 w-2 animate-bounce-dot-delay-2 rounded-full bg-slate-500 dark:bg-slate-400" />
      </div>
    </motion.div>
  );
}

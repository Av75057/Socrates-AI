import { motion } from "framer-motion";

export default function TypingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex justify-start"
      aria-hidden
    >
      <div className="flex gap-1 rounded-2xl rounded-bl-md border border-slate-600/50 bg-[#1e293b] px-4 py-3">
        <span className="h-2 w-2 animate-bounce-dot rounded-full bg-slate-400" />
        <span className="h-2 w-2 animate-bounce-dot-delay-1 rounded-full bg-slate-400" />
        <span className="h-2 w-2 animate-bounce-dot-delay-2 rounded-full bg-slate-400" />
      </div>
    </motion.div>
  );
}

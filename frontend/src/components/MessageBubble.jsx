import { motion } from "framer-motion";

export default function MessageBubble({ role, text }) {
  const isUser = role === "user";
  return (
    <motion.div
      layout
      initial={
        isUser
          ? { opacity: 0, x: 28, filter: "blur(4px)" }
          : { opacity: 0, y: 14, filter: "blur(4px)" }
      }
      animate={{ opacity: 1, x: 0, y: 0, filter: "blur(0px)" }}
      transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-xl sm:max-w-[min(80%,42rem)] sm:text-base ${
          isUser
            ? "rounded-br-md bg-[#2563eb] text-white"
            : "rounded-bl-md border border-slate-200 bg-slate-100 text-slate-900 dark:border-slate-600/50 dark:bg-[#1e293b] dark:text-slate-100"
        }`}
      >
        {!isUser ? (
          <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-400/90">
            Socrates
          </div>
        ) : null}
        <div className="whitespace-pre-wrap break-words">{text}</div>
      </div>
    </motion.div>
  );
}

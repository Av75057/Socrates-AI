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
        className={`max-w-[min(100%,42rem)] rounded-2xl px-4 py-3 text-base leading-relaxed shadow-xl ${
          isUser
            ? "rounded-br-md bg-[#2563eb] text-white"
            : "rounded-bl-md border border-slate-600/50 bg-[#1e293b] text-slate-100"
        }`}
      >
        {!isUser ? (
          <div className="mb-1.5 text-[10px] font-semibold uppercase tracking-wider text-emerald-400/90">
            Socrates
          </div>
        ) : null}
        <div className="whitespace-pre-wrap">{text}</div>
      </div>
    </motion.div>
  );
}

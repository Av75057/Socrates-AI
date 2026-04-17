import { useState } from "react";
import { motion } from "framer-motion";

export default function InputBox({
  onSend,
  loading,
  canSend,
  onRequestHint,
  onGiveUp,
  onUserActivity,
}) {
  const [value, setValue] = useState("");

  const submit = () => {
    const t = value.trim();
    if (!t || loading || !canSend()) return;
    onUserActivity?.();
    onSend(t);
    setValue("");
  };

  return (
    <div className="border-t border-slate-800/80 bg-[#0f172a]/95 px-4 py-3 backdrop-blur">
      <div className="mx-auto flex max-w-3xl flex-col gap-2">
        <div className="flex flex-wrap gap-2">
          <motion.button
            type="button"
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => {
              onUserActivity?.();
              onRequestHint();
            }}
            className="inline-flex items-center gap-1.5 rounded-xl border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs font-semibold text-amber-100 hover:bg-amber-500/20 disabled:opacity-40"
          >
            <span aria-hidden>🧠</span>
            Дай подсказку
          </motion.button>
          <motion.button
            type="button"
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => {
              onUserActivity?.();
              onGiveUp();
            }}
            className="inline-flex items-center gap-1.5 rounded-xl border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-xs font-semibold text-rose-100 hover:bg-rose-500/20 disabled:opacity-40"
          >
            <span aria-hidden>🚨</span>
            Объясни нормально
          </motion.button>
        </div>
        <div className="flex gap-2">
          <textarea
            rows={2}
            value={value}
            onChange={(e) => {
              onUserActivity?.();
              setValue(e.target.value);
            }}
            onFocus={() => onUserActivity?.()}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Сформулируй мысль своими словами…"
            disabled={loading}
            className="min-h-[56px] flex-1 resize-y rounded-xl border border-slate-600/80 bg-[#1e293b] px-3 py-2.5 text-base text-slate-100 placeholder:text-slate-600 focus:border-blue-500/60 focus:outline-none focus:ring-2 focus:ring-blue-500/25 disabled:opacity-60"
          />
          <motion.button
            type="button"
            disabled={loading || !value.trim() || !canSend()}
            whileHover={{ scale: loading || !value.trim() ? 1 : 1.02 }}
            whileTap={{ scale: 0.97 }}
            onClick={submit}
            className="self-end rounded-xl bg-[#2563eb] px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-blue-900/30 hover:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-40"
          >
            Отправить
          </motion.button>
        </div>
        <p className="text-[11px] text-slate-600">
          Enter — отправить · Shift+Enter — новая строка · пауза между отправками ~0.8 с
        </p>
      </div>
    </div>
  );
}

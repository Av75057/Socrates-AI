import { AnimatePresence, motion } from "framer-motion";

export default function XpFloater({ amount, show }) {
  return (
    <AnimatePresence>
      {show ? (
        <motion.div
          key={amount}
          initial={{ opacity: 0, y: 12, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ type: "spring", stiffness: 420, damping: 28 }}
          className="pointer-events-none absolute right-4 top-24 z-20 rounded-full border border-emerald-500/40 bg-emerald-500/15 px-3 py-1 text-sm font-bold text-emerald-200 shadow-lg shadow-emerald-900/30"
        >
          +{amount} XP
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}

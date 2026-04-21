import { AnimatePresence, motion } from "framer-motion";
import { Link } from "react-router-dom";
import { X } from "lucide-react";

const linkCls =
  "block rounded-lg px-3 py-3 text-sm font-medium text-slate-800 active:bg-slate-100 dark:text-slate-100 dark:active:bg-slate-800";

export default function MobileMenu({ open, onClose, isAdmin, isEducator, loggedIn }) {
  return (
    <AnimatePresence>
      {open ? (
        <>
          <motion.button
            type="button"
            aria-label="Закрыть меню"
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-[1px] lg:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.nav
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", stiffness: 320, damping: 32 }}
            className="fixed inset-y-0 right-0 z-50 flex w-[min(100%,20rem)] flex-col border-l border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-[#0f172a] lg:hidden"
          >
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
              <span className="font-display text-sm font-semibold text-slate-900 dark:text-white">Меню</span>
              <button
                type="button"
                onClick={onClose}
                className="rounded-lg p-2 text-slate-600 active:bg-slate-100 dark:text-slate-300 dark:active:bg-slate-800"
                aria-label="Закрыть"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3">
              <Link to="/app" className={linkCls} onClick={onClose}>
                Чат
              </Link>
              {loggedIn ? (
                <>
                  <Link to="/profile" className={linkCls} onClick={onClose}>
                    Профиль
                  </Link>
                  <Link to="/profile/history" className={linkCls} onClick={onClose}>
                    История
                  </Link>
                  <Link to="/profile/skills" className={linkCls} onClick={onClose}>
                    Навыки
                  </Link>
                  <Link to="/profile/settings" className={linkCls} onClick={onClose}>
                    Настройки
                  </Link>
                </>
              ) : (
                <Link to="/login" className={linkCls} onClick={onClose}>
                  Войти
                </Link>
              )}
              {isAdmin ? (
                <Link to="/admin" className={linkCls} onClick={onClose}>
                  Админка
                </Link>
              ) : null}
              {isEducator ? (
                <Link to="/educator" className={linkCls} onClick={onClose}>
                  Панель учителя
                </Link>
              ) : null}
            </div>
          </motion.nav>
        </>
      ) : null}
    </AnimatePresence>
  );
}

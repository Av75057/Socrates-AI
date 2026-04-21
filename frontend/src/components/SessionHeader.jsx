import { useState } from "react";
import { Link } from "react-router-dom";
import { ChevronDown, Menu } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useAuth } from "../contexts/AuthContext.jsx";
import ThemeToggle from "./ThemeToggle.jsx";
import MobileMenu from "./MobileMenu.jsx";

export default function SessionHeader({
  topic,
  onNewSession,
  xp = 0,
  streak = 0,
  wisdomSlot = null,
  pedagogySlot = null,
  statusSlot = null,
  /** Иконка вызова дня на узком экране (до lg), открывает модалку */
  dailyChallengeHeaderSlot = null,
}) {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const isAdmin = String(user?.role || "").toLowerCase() === "admin";
  const isEducator = ["educator", "admin"].includes(String(user?.role || "").toLowerCase());

  return (
    <>
      <header className="shrink-0 border-b border-slate-200 bg-white/95 px-2 py-2 backdrop-blur dark:border-slate-800/90 dark:bg-[#0f172a]/95 sm:px-4 sm:py-3">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-1.5 sm:gap-3">
              <button
                type="button"
                className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 active:bg-slate-100 lg:hidden dark:border-slate-600 dark:bg-slate-800/80 dark:text-slate-200 dark:active:bg-slate-700"
                aria-label="Открыть меню"
                onClick={() => setMobileOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </button>
              <Link
                to="/app"
                data-tour="welcome"
                className="inline-flex min-h-[44px] min-w-0 items-center gap-2 rounded-lg px-1 py-1 text-slate-800 dark:text-slate-100"
              >
                <span className="text-xl" aria-hidden>
                  🦉
                </span>
                <span className="font-display text-sm font-bold tracking-tight sm:text-base">Socrates-AI</span>
              </Link>
              <nav className="hidden items-center gap-1 text-xs font-medium text-slate-600 lg:flex dark:text-slate-400">
                <Link
                  to="/app"
                  className="rounded-lg px-2 py-1.5 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                >
                  Чат
                </Link>
                <Link
                  to="/profile"
                  className="rounded-lg px-2 py-1.5 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                >
                  Профиль
                </Link>
                <Link
                  to="/profile/history"
                  className="rounded-lg px-2 py-1.5 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                >
                  История
                </Link>
                <Link
                  to="/profile/skills"
                  className="rounded-lg px-2 py-1.5 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                >
                  Навыки
                </Link>
                <Link
                  to="/profile/settings"
                  className="rounded-lg px-2 py-1.5 hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-slate-800 dark:hover:text-slate-100"
                >
                  Настройки
                </Link>
                {isEducator ? (
                  <Link
                    to="/educator"
                    className="rounded-lg px-2 py-1.5 text-violet-800 hover:bg-violet-100 dark:text-violet-300 dark:hover:bg-violet-950/50"
                  >
                    Учитель
                  </Link>
                ) : null}
                {isAdmin ? (
                  <Link
                    to="/admin"
                    className="rounded-lg px-2 py-1.5 text-amber-800 hover:bg-amber-100 dark:text-amber-300 dark:hover:bg-amber-950/50"
                  >
                    Админка
                  </Link>
                ) : null}
              </nav>
              {wisdomSlot}
              {pedagogySlot}
              <span className="text-xs tabular-nums text-slate-500 lg:hidden">
                XP <span className="text-cyan-600 dark:text-cyan-300">{xp}</span>
                <span className="mx-1.5 text-slate-300 dark:text-slate-700">·</span>
                {streak > 0 ? (
                  <>
                    <span aria-hidden>🔥</span> {streak}
                  </>
                ) : (
                  <span className="text-slate-400 dark:text-slate-600">серия —</span>
                )}
              </span>
            </div>
            <div className="mt-0.5 flex flex-wrap items-baseline gap-2 sm:mt-1">
              <h1 className="font-display text-base font-bold tracking-tight text-slate-900 sm:text-lg dark:text-white">
                Диалог с наставником
              </h1>
              <span className="hidden rounded-full bg-slate-200/90 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-500 sm:inline dark:bg-slate-800/80 dark:text-slate-500">
                обучающая игра
              </span>
            </div>
            <p className="mt-0.5 truncate text-xs text-slate-600 sm:text-sm sm:mt-1 dark:text-slate-400">
              {topic ? (
                <>
                  <span className="text-slate-500 dark:text-slate-500">Тема: </span>
                  <span className="text-slate-800 dark:text-slate-200">{topic}</span>
                </>
              ) : (
                <span className="text-slate-500">Задай тему: «Хочу изучить …»</span>
              )}
            </p>
            {statusSlot ? <div className="mt-1">{statusSlot}</div> : null}
          </div>
          <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
            {dailyChallengeHeaderSlot}
            <ThemeToggle />
            {user ? (
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setUserMenuOpen((o) => !o)}
                  className="flex min-h-[44px] items-center gap-1 rounded-xl border border-slate-200 bg-white px-2 py-1.5 text-left text-xs font-medium text-slate-800 active:bg-slate-50 dark:border-slate-600 dark:bg-slate-800/90 dark:text-slate-100 dark:active:bg-slate-800"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-cyan-100 text-[11px] font-semibold text-cyan-900 dark:bg-cyan-900/50 dark:text-cyan-100">
                    {(user.full_name || user.email || "?").trim().slice(0, 2).toUpperCase()}
                  </span>
                  <ChevronDown className="hidden h-4 w-4 text-slate-500 sm:block" />
                </button>
                <AnimatePresence>
                  {userMenuOpen ? (
                    <>
                      <button
                        type="button"
                        aria-label="Закрыть меню"
                        className="fixed inset-0 z-30"
                        onClick={() => setUserMenuOpen(false)}
                      />
                      <motion.div
                        initial={{ opacity: 0, y: -6 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -6 }}
                        transition={{ duration: 0.15 }}
                        className="absolute right-0 top-full z-40 mt-1 min-w-[12rem] rounded-xl border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-600 dark:bg-slate-900"
                      >
                        <Link
                          to="/profile"
                          className="block px-4 py-2.5 text-sm text-slate-800 hover:bg-slate-50 dark:text-slate-100 dark:hover:bg-slate-800"
                          onClick={() => setUserMenuOpen(false)}
                        >
                          Профиль
                        </Link>
                        <Link
                          to="/profile/settings"
                          className="block px-4 py-2.5 text-sm text-slate-800 hover:bg-slate-50 dark:text-slate-100 dark:hover:bg-slate-800"
                          onClick={() => setUserMenuOpen(false)}
                        >
                          Настройки
                        </Link>
                        <button
                          type="button"
                          className="w-full px-4 py-2.5 text-left text-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/40"
                          onClick={() => {
                            setUserMenuOpen(false);
                            logout();
                          }}
                        >
                          Выйти
                        </button>
                      </motion.div>
                    </>
                  ) : null}
                </AnimatePresence>
              </div>
            ) : (
              <Link
                to="/login"
                className="rounded-xl border border-cyan-600/40 bg-cyan-50 px-3 py-2 text-xs font-medium text-cyan-950 hover:bg-cyan-100 dark:border-cyan-500/40 dark:bg-cyan-950/40 dark:text-cyan-100 dark:hover:bg-cyan-900/50"
              >
                Войти
              </Link>
            )}
            <button
              type="button"
              onClick={onNewSession}
              className="min-h-[44px] shrink-0 touch-manipulation rounded-xl border border-slate-300 px-3 py-2.5 text-xs font-medium text-slate-700 active:bg-slate-100 [@media(hover:hover)]:hover:border-slate-400 [@media(hover:hover)]:hover:bg-slate-100 sm:min-h-0 sm:py-2 dark:border-slate-600/80 dark:text-slate-300 dark:active:bg-slate-800/80 dark:[@media(hover:hover)]:hover:border-slate-500 dark:[@media(hover:hover)]:hover:bg-slate-800/80"
            >
              Новая сессия
            </button>
          </div>
        </div>
      </header>
      <MobileMenu
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        isAdmin={isAdmin}
        isEducator={isEducator}
        loggedIn={!!user}
      />
    </>
  );
}

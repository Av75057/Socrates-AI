import { useEffect, useState } from "react";
import ShareModal from "../sharing/ShareModal.jsx";

export default function AchievementsModal({ open, onClose, catalog, unlockedIds }) {
  const [shareAch, setShareAch] = useState(null);

  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  const unlocked = new Set(unlockedIds || []);

  return (
    <>
      <div
        className="fixed inset-0 z-[90] flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm dark:bg-black/60"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ach-modal-title"
        onClick={onClose}
      >
        <div
          className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-slate-200 bg-white p-5 shadow-2xl sm:p-6 dark:border-slate-700 dark:bg-[#0f172a] dark:shadow-black/50"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-start justify-between gap-3">
            <h2 id="ach-modal-title" className="font-display text-xl font-bold text-slate-900 dark:text-white">
              Достижения
            </h2>
            <button
              type="button"
              className="rounded-lg px-2 py-1 text-slate-500 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
              onClick={onClose}
            >
              ✕
            </button>
          </div>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">Собирай очки мудрости и открывай награды.</p>

          <ul className="mt-5 grid gap-3 sm:grid-cols-1">
            {(catalog || []).map((a) => {
              const ok = unlocked.has(a.id);
              return (
                <li
                  key={a.id}
                  className={`flex gap-3 rounded-xl border px-4 py-3 ${
                    ok
                      ? "border-amber-400/60 bg-amber-50 dark:border-amber-500/35 dark:bg-amber-950/25"
                      : "border-slate-200 bg-slate-50 opacity-90 dark:border-slate-700 dark:bg-slate-900/40 dark:opacity-80"
                  }`}
                >
                  <span className="text-2xl leading-none" aria-hidden>
                    {ok ? "🏅" : "🔒"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="font-display font-semibold text-slate-900 dark:text-slate-100">{a.name}</p>
                    <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">{a.description}</p>
                    <p className="mt-2 text-xs font-medium text-amber-700 dark:text-amber-400/90">+{a.reward_points} WP</p>
                    {ok ? (
                      <button
                        type="button"
                        className="mt-2 text-xs font-semibold text-cyan-700 underline hover:text-cyan-600 dark:text-cyan-400"
                        onClick={() => setShareAch(a)}
                      >
                        Поделиться
                      </button>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </div>

      {shareAch ? (
        <ShareModal
          open
          onClose={() => setShareAch(null)}
          variant="achievement"
          headline={shareAch.name}
          subline={shareAch.description}
          wisdomPoints={shareAch.reward_points}
        />
      ) : null}
    </>
  );
}

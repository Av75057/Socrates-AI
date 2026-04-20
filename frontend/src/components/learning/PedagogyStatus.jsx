import { useCallback, useEffect, useRef, useState } from "react";
import { getUserPedagogy } from "../../api/userApi.js";
import { useAuth } from "../../contexts/AuthContext.jsx";

export default function PedagogyStatus() {
  const { user } = useAuth();
  const [ped, setPed] = useState(null);
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  const load = useCallback(() => {
    if (!user) return;
    getUserPedagogy()
      .then(setPed)
      .catch(() => {});
  }, [user]);

  useEffect(() => {
    if (!user) {
      setPed(null);
      return;
    }
    load();
  }, [user, load]);

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === "visible") load();
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, [load]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("click", onDoc);
    return () => document.removeEventListener("click", onDoc);
  }, [open]);

  if (!user || !ped) return null;

  const diff = Math.max(1, Math.min(5, Number(ped.current_difficulty) || 1));
  const counts = ped.fallacy_counts && typeof ped.fallacy_counts === "object" ? ped.fallacy_counts : {};
  const entries = Object.entries(counts).filter(([k, v]) => k && Number(v) > 0);

  return (
    <div className="relative" ref={wrapRef}>
      <button
        type="button"
        title="Текущий уровень адаптации. Чем глубже твои ответы, тем выше сложность."
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-0.5 rounded-lg border border-slate-200 bg-white/90 px-2 py-1 text-[11px] text-slate-700 shadow-sm dark:border-slate-600 dark:bg-slate-800/90 dark:text-slate-200"
      >
        <span className="mr-1 text-slate-500 dark:text-slate-400">уровень</span>
        {[1, 2, 3, 4, 5].map((i) => (
          <span
            key={i}
            className={
              i <= diff ? "text-amber-500 drop-shadow-sm dark:text-amber-400" : "text-slate-300 dark:text-slate-600"
            }
            aria-hidden
          >
            ★
          </span>
        ))}
      </button>
      {open ? (
        <div className="absolute right-0 z-50 mt-1 w-64 rounded-lg border border-slate-200 bg-white p-3 text-left text-xs shadow-lg dark:border-slate-600 dark:bg-slate-900">
          <p className="font-medium text-slate-800 dark:text-slate-100">Частота ошибок (всего)</p>
          {entries.length === 0 ? (
            <p className="mt-2 text-slate-500 dark:text-slate-400">Пока нет зафиксированных типов.</p>
          ) : (
            <ul className="mt-2 max-h-40 space-y-1 overflow-y-auto text-slate-700 dark:text-slate-300">
              {entries
                .sort((a, b) => Number(b[1]) - Number(a[1]))
                .map(([k, v]) => (
                  <li key={k} className="flex justify-between gap-2 tabular-nums">
                    <span className="truncate">{k}</span>
                    <span className="text-slate-500 dark:text-slate-400">{v}</span>
                  </li>
                ))}
            </ul>
          )}
        </div>
      ) : null}
    </div>
  );
}

function formatWhen(value) {
  if (!value) return "";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleString();
}

export default function ConversationList({ items, activeId, loading, onSelect }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white/80 p-3 dark:border-slate-700/50 dark:bg-slate-900/30">
      <div className="flex items-center justify-between gap-2">
        <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Последние диалоги</p>
        {loading ? <span className="text-[10px] text-slate-400 dark:text-slate-500">обновляю…</span> : null}
      </div>
      <div className="mt-3 space-y-2">
        {items.map((item) => {
          const active = item.id === activeId;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect?.(item.id)}
              className={`block w-full rounded-xl border px-3 py-2 text-left transition-colors ${
                active
                  ? "border-cyan-500/60 bg-cyan-50 text-cyan-950 dark:border-cyan-500/50 dark:bg-cyan-950/40 dark:text-cyan-100"
                  : "border-slate-200 bg-white text-slate-800 [@media(hover:hover)]:hover:border-slate-300 [@media(hover:hover)]:hover:bg-slate-50 dark:border-slate-700/70 dark:bg-slate-950/40 dark:text-slate-200 dark:[@media(hover:hover)]:hover:bg-slate-800/60"
              }`}
            >
              <p className="line-clamp-2 text-sm font-medium">{item.title || "Без названия"}</p>
              <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                {item.message_count || 0} сообщ. · {formatWhen(item.last_updated_at)}
              </p>
            </button>
          );
        })}
        {!loading && items.length === 0 ? (
          <p className="rounded-lg border border-dashed border-slate-300 px-3 py-2 text-xs text-slate-500 dark:border-slate-700 dark:text-slate-500">
            После первого сообщения здесь появится история.
          </p>
        ) : null}
      </div>
    </section>
  );
}

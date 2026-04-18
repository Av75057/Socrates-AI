const DEPTH_RU = { low: "низкая", medium: "средняя", high: "высокая" };
const LOGIC_RU = { weak: "слабее связи", partial: "частично", strong: "причинно-следственно" };
const CONF_RU = { low: "с сомнениями", medium: "умеренная", high: "уверенная" };

function BarRow({ label, filled, total = 3 }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-24 shrink-0 text-[10px] text-slate-500">{label}</span>
      <div className="flex gap-0.5">
        {Array.from({ length: total }, (_, i) => (
          <span
            key={i}
            className={`h-2 w-4 rounded-sm ${i < filled ? "bg-emerald-500/80" : "bg-slate-700/80"}`}
          />
        ))}
      </div>
    </div>
  );
}

function depthFilled(depth) {
  if (depth === "high") return 3;
  if (depth === "medium") return 2;
  return 1;
}

function logicFilled(logic) {
  if (logic === "strong") return 3;
  if (logic === "partial") return 2;
  return 1;
}

function confFilled(conf) {
  if (conf === "high") return 3;
  if (conf === "medium") return 2;
  return 1;
}

export default function ThinkingPanel({ profile, className = "" }) {
  const p = profile && typeof profile === "object" ? profile : {};
  const depth = p.depth || "medium";
  const logic = p.logic || "partial";
  const confidence = p.confidence || "medium";
  const samples = typeof p.samples === "number" ? p.samples : 0;
  const avgSteps = p.avg_steps_to_explain;

  return (
    <div className={`rounded-xl border border-slate-700/60 bg-slate-900/30 p-3 ${className}`}>
      <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
        🧠 Как ты мыслишь
      </p>
      <p className="mt-1 text-[11px] text-slate-600">
        {samples > 0
          ? `Скользящее среднее по последним ${Math.min(samples, 5)} репликам (эвристика, не диагноз)`
          : "Профиль обновится после нескольких твоих ответов в чате"}
      </p>

      <div className="mt-3 space-y-2 text-xs text-slate-300">
        <div>
          <span className="text-slate-500">Глубина:</span>{" "}
          <span className="text-slate-200">{DEPTH_RU[depth] || depth}</span>
        </div>
        <BarRow label="рост" filled={depthFilled(depth)} />

        <div className="pt-1">
          <span className="text-slate-500">Логика:</span>{" "}
          <span className="text-slate-200">{LOGIC_RU[logic] || logic}</span>
        </div>
        <BarRow label="связи" filled={logicFilled(logic)} />

        <div className="pt-1">
          <span className="text-slate-500">Уверенность:</span>{" "}
          <span className="text-slate-200">{CONF_RU[confidence] || confidence}</span>
        </div>
        <BarRow label="тон" filled={confFilled(confidence)} />
      </div>

      {avgSteps != null ? (
        <p className="mt-3 border-t border-slate-800/80 pt-2 text-[11px] text-slate-500">
          Среднее шагов до разбора:{" "}
          <span className="tabular-nums text-slate-300">{avgSteps}</span>
        </p>
      ) : null}
    </div>
  );
}

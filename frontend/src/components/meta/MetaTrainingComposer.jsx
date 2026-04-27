import { useState } from "react";

const PHASE_PLACEHOLDERS = {
  orientation: "Сформулируй вопрос к тезису, лучше с явным скрытым допущением…",
  exploration: "Назови рамку и объясни, почему она полезна…",
  sparring: "Атакуй тезис вопросом о предпосылке, противоречии или альтернативе…",
  reflection: "Сформулируй свой вердикт, степень уверенности и границы незнания…",
  completed: "Сессия завершена.",
};

export default function MetaTrainingComposer({
  phase,
  loading,
  onSend,
  onSwitchFrame,
  onAdvancePhase,
  onEnd,
}) {
  const [text, setText] = useState("");
  const [confidence, setConfidence] = useState("Низкая");
  const disabled = loading || phase === "completed";

  const submit = async (kind) => {
    const value = text.trim();
    if (kind === "send") {
      if (!value) return;
      await onSend(value);
      setText("");
      return;
    }
    if (kind === "frame") {
      if (!value) return;
      await onSwitchFrame(value);
      setText("");
      return;
    }
    if (kind === "end") {
      await onEnd(value, confidence);
      setText("");
    }
  };

  return (
    <div className="border-t border-slate-200 bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.12),_transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.96),rgba(241,245,249,0.96))] px-3 py-3 sm:px-4 dark:border-slate-800 dark:bg-[radial-gradient(circle_at_top,_rgba(6,182,212,0.14),_transparent_36%),linear-gradient(180deg,rgba(15,23,42,0.92),rgba(2,6,23,0.98))]">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={disabled}
        placeholder={PHASE_PLACEHOLDERS[phase] || PHASE_PLACEHOLDERS.orientation}
        rows={4}
        className="w-full resize-none rounded-2xl border border-slate-300 bg-white/90 px-4 py-3 text-sm text-slate-900 outline-none ring-0 transition placeholder:text-slate-400 focus:border-cyan-500 dark:border-slate-700 dark:bg-slate-950/70 dark:text-slate-100 dark:placeholder:text-slate-500"
      />
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button
          type="button"
          disabled={disabled || !text.trim()}
          onClick={() => void submit("send")}
          className="rounded-xl bg-cyan-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50 hover:bg-cyan-500"
        >
          Отправить
        </button>
        <button
          type="button"
          disabled={disabled || !text.trim()}
          onClick={() => void submit("frame")}
          className="rounded-xl border border-amber-400 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-900 disabled:opacity-50 hover:bg-amber-100 dark:border-amber-600/50 dark:bg-amber-950/40 dark:text-amber-100"
        >
          Сменить рамку
        </button>
        <button
          type="button"
          disabled={loading || phase === "completed"}
          onClick={() => void onAdvancePhase()}
          className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 disabled:opacity-50 hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Следующая фаза
        </button>
        <select
          value={confidence}
          onChange={(e) => setConfidence(e.target.value)}
          disabled={loading}
          className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700 outline-none dark:border-slate-700 dark:bg-slate-900/80 dark:text-slate-200"
        >
          <option>Низкая</option>
          <option>Средняя</option>
          <option>Высокая</option>
        </select>
        <button
          type="button"
          disabled={loading}
          onClick={() => void submit("end")}
          className="rounded-xl border border-emerald-400 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-900 disabled:opacity-50 hover:bg-emerald-100 dark:border-emerald-600/50 dark:bg-emerald-950/40 dark:text-emerald-100"
        >
          Завершить
        </button>
      </div>
    </div>
  );
}

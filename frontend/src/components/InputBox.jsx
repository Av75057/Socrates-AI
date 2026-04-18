import { useState } from "react";

const BTN =
  "min-h-[48px] touch-manipulation rounded-xl px-3 py-2.5 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-40";

export default function InputBox({
  userType = "lazy",
  onSend,
  loading,
  canSend,
  onRequestHint,
  onRequestExample,
  onGiveUp,
  onQuickDontKnow,
  onUserActivity,
}) {
  const [value, setValue] = useState("");
  const ut = ["lazy", "anxious", "thinker"].includes(userType) ? userType : "lazy";

  const submit = () => {
    const t = value.trim();
    if (!t || loading || !canSend()) return;
    onUserActivity?.();
    onSend(t);
    setValue("");
  };

  const sendLine = (text) => {
    if (loading || !canSend()) return;
    onUserActivity?.();
    onSend(text);
  };

  const sendPreset = (text) => {
    if (loading || !canSend()) return;
    onUserActivity?.();
    if (text === "Не знаю") onQuickDontKnow?.();
    if (text === "Дай пример") {
      onRequestExample?.();
      return;
    }
    onSend(text);
  };

  const rowNeutral =
    "border border-slate-600/70 bg-[#0f172a] text-slate-200 active:bg-slate-800 [@media(hover:hover)]:hover:border-slate-500";
  const rowAmber =
    "border border-amber-500/45 bg-amber-500/15 font-semibold text-amber-100 active:bg-amber-500/25 [@media(hover:hover)]:hover:bg-amber-500/20";
  const rowRose =
    "border border-rose-500/45 bg-rose-500/12 font-semibold text-rose-100 active:bg-rose-500/22 [@media(hover:hover)]:hover:bg-rose-500/18";

  return (
    <div className="input-dock z-20 shrink-0 border-t border-slate-800 bg-[#020617]/98 px-3 pt-3 backdrop-blur max-lg:fixed max-lg:bottom-0 max-lg:left-0 max-lg:right-0 lg:relative lg:px-4">
      <div className="mx-auto flex max-w-3xl flex-col gap-3">
        <div className="grid grid-cols-2 gap-2">
          {ut === "lazy" ? (
            <>
              <button
                type="button"
                disabled={loading || !canSend()}
                onClick={() => sendLine("Ок, попробую ответить своими словами")}
                className={`${BTN} ${rowNeutral}`}
              >
                Попробую
              </button>
              <button
                type="button"
                disabled={loading || !canSend()}
                onClick={() => sendPreset("Не знаю")}
                className={`${BTN} ${rowNeutral}`}
              >
                Не знаю
              </button>
            </>
          ) : null}

          {ut === "anxious" ? (
            <>
              <button
                type="button"
                disabled={loading || !canSend()}
                onClick={() => sendLine("Я попробую объяснить, как понимаю")}
                className={`${BTN} ${rowNeutral}`}
              >
                Я попробую объяснить
              </button>
              <button
                type="button"
                disabled={loading || !canSend()}
                onClick={() => {
                  onUserActivity?.();
                  onRequestExample?.();
                }}
                className={`${BTN} ${rowNeutral}`}
              >
                Дай пример
              </button>
            </>
          ) : null}

          {ut === "thinker" ? (
            <>
              <button
                type="button"
                disabled={loading || !canSend()}
                onClick={() => sendLine("Усложни вопрос — хочу копнуть глубже")}
                className={`${BTN} ${rowNeutral}`}
              >
                Усложни
              </button>
              <button
                type="button"
                disabled={loading || !canSend()}
                onClick={() => sendLine("Дай небольшую задачу на размышление")}
                className={`${BTN} ${rowNeutral}`}
              >
                Дай задачу
              </button>
            </>
          ) : null}
        </div>

        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            disabled={loading}
            onClick={() => {
              onUserActivity?.();
              onRequestHint();
            }}
            className={`${BTN} ${rowAmber}`}
          >
            Подсказка
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={() => {
              onUserActivity?.();
              onGiveUp();
            }}
            className={`${BTN} ${rowRose}`}
          >
            Объясни проще
          </button>
        </div>

        <div className="flex gap-2">
          <textarea
            rows={1}
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
            placeholder="Напиши ответ…"
            disabled={loading}
            className="min-h-[48px] max-h-[8rem] flex-1 resize-none rounded-xl border border-slate-600/80 bg-[#0f172a] px-4 py-3 text-base leading-snug text-white placeholder:text-slate-500 focus:border-blue-500/60 focus:outline-none focus:ring-2 focus:ring-blue-500/25 disabled:opacity-60"
          />
          <button
            type="button"
            disabled={loading || !value.trim() || !canSend()}
            onClick={submit}
            aria-label="Отправить"
            className="flex h-[48px] min-w-[48px] shrink-0 touch-manipulation items-center justify-center self-end rounded-xl bg-blue-500 px-4 text-lg font-semibold text-white active:bg-blue-600 disabled:cursor-not-allowed disabled:opacity-40 [@media(hover:hover)]:hover:bg-blue-600"
          >
            →
          </button>
        </div>

        <p className="hidden pb-1 text-[11px] text-slate-600 sm:block">
          Enter — отправить · Shift+Enter — новая строка · пауза ~0.8 с
        </p>
      </div>
    </div>
  );
}

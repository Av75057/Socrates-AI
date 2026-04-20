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
  onInputFocus,
  topBar = null,
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
    "border border-slate-300 bg-white text-slate-800 active:bg-slate-100 [@media(hover:hover)]:hover:border-slate-400 dark:border-slate-600/70 dark:bg-[#0f172a] dark:text-slate-200 dark:active:bg-slate-800 dark:[@media(hover:hover)]:hover:border-slate-500";
  const rowAmber =
    "border border-amber-600/40 bg-amber-100 font-semibold text-amber-950 active:bg-amber-200 [@media(hover:hover)]:hover:bg-amber-200 dark:border-amber-500/45 dark:bg-amber-500/15 dark:text-amber-100 dark:active:bg-amber-500/25 dark:[@media(hover:hover)]:hover:bg-amber-500/20";
  const rowRose =
    "border border-rose-500/50 bg-rose-100 font-semibold text-rose-900 active:bg-rose-200 [@media(hover:hover)]:hover:bg-rose-200 dark:border-rose-500/45 dark:bg-rose-500/12 dark:text-rose-100 dark:active:bg-rose-500/22 dark:[@media(hover:hover)]:hover:bg-rose-500/18";

  return (
    <div
      data-tour="chat-input"
      className="input-dock z-20 shrink-0 border-t border-slate-200 bg-slate-50/98 px-3 pt-3 backdrop-blur max-lg:fixed max-lg:bottom-0 max-lg:left-0 max-lg:right-0 lg:relative lg:px-4 dark:border-slate-800 dark:bg-[#020617]/98"
    >
      <div className="mx-auto flex max-w-3xl flex-col gap-3">
        {topBar ? (
          <div className="flex flex-wrap items-center gap-2 border-b border-slate-200/90 pb-2 dark:border-slate-800/70">
            {topBar}
          </div>
        ) : null}
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
            onFocus={() => {
              onUserActivity?.();
              onInputFocus?.();
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="Напиши ответ…"
            disabled={loading}
            className="min-h-[48px] max-h-[8rem] flex-1 resize-none rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm leading-snug text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/25 disabled:opacity-60 sm:text-base dark:border-slate-600/80 dark:bg-[#0f172a] dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-500/60"
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

        <p className="hidden pb-1 text-[11px] text-slate-500 sm:block dark:text-slate-600">
          Enter — отправить · Shift+Enter — новая строка · пауза ~0.8 с
        </p>
      </div>
    </div>
  );
}

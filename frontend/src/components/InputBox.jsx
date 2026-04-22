import { useState } from "react";
import {
  BookOpen,
  ClipboardList,
  GraduationCap,
  HelpCircle,
  Lightbulb,
  ListChecks,
  MessageCircle,
  Sparkles,
} from "lucide-react";
import ActionButtonsRow from "./chat/ActionButtonsRow.jsx";

function buildQuickActions({
  ut,
  sendLine,
  sendPreset,
  onUserActivity,
  onRequestHint,
  onRequestExample,
  onGiveUp,
}) {
  const hintBtn = {
    key: "hint",
    label: "Подсказка",
    title: "Попросить подсказку у тьютора",
    icon: <Lightbulb className="shrink-0" strokeWidth={2} />,
    variant: "amber",
    needsSendGate: false,
    onClick: () => {
      onUserActivity?.();
      onRequestHint();
    },
  };
  const simplerBtn = {
    key: "simpler",
    label: "Объясни проще",
    title: "Переформулировать вопрос проще",
    icon: <BookOpen className="shrink-0" strokeWidth={2} />,
    variant: "rose",
    needsSendGate: false,
    onClick: () => {
      onUserActivity?.();
      onGiveUp();
    },
  };

  if (ut === "lazy") {
    return [
      {
        key: "try",
        label: "Попробую",
        icon: <Sparkles className="shrink-0" strokeWidth={2} />,
        variant: "neutral",
        onClick: () => sendLine("Ок, попробую ответить своими словами"),
      },
      {
        key: "dont",
        label: "Не знаю",
        icon: <HelpCircle className="shrink-0" strokeWidth={2} />,
        variant: "neutral",
        onClick: () => sendPreset("Не знаю"),
      },
      hintBtn,
      simplerBtn,
    ];
  }
  if (ut === "anxious") {
    return [
      {
        key: "try-exp",
        label: "Я попробую объяснить",
        icon: <MessageCircle className="shrink-0" strokeWidth={2} />,
        variant: "neutral",
        onClick: () => sendLine("Я попробую объяснить, как понимаю"),
      },
      {
        key: "example",
        label: "Дай пример",
        icon: <GraduationCap className="shrink-0" strokeWidth={2} />,
        variant: "neutral",
        onClick: () => {
          onUserActivity?.();
          onRequestExample?.();
        },
      },
      hintBtn,
      simplerBtn,
    ];
  }
  return [
    {
      key: "harder",
      label: "Усложни",
      icon: <ListChecks className="shrink-0" strokeWidth={2} />,
      variant: "neutral",
      onClick: () => sendLine("Усложни вопрос — хочу копнуть глубже"),
    },
    {
      key: "task",
      label: "Дай задачу",
      icon: <ClipboardList className="shrink-0" strokeWidth={2} />,
      variant: "neutral",
      onClick: () => sendLine("Дай небольшую задачу на размышление"),
    },
    hintBtn,
    simplerBtn,
  ];
}

export default function InputBox({
  userType = "lazy",
  onSend,
  loading,
  interruptibleLoading = false,
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
  const blockedByLoading = loading && !interruptibleLoading;

  const submit = () => {
    const t = value.trim();
    if (!t || blockedByLoading || !canSend()) return;
    onUserActivity?.();
    onSend(t);
    setValue("");
  };

  const sendLine = (text) => {
    if (blockedByLoading || !canSend()) return;
    onUserActivity?.();
    onSend(text);
  };

  const sendPreset = (text) => {
    if (blockedByLoading || !canSend()) return;
    onUserActivity?.();
    if (text === "Не знаю") onQuickDontKnow?.();
    if (text === "Дай пример") {
      onRequestExample?.();
      return;
    }
    onSend(text);
  };

  const quickActions = buildQuickActions({
    ut,
    sendLine,
    sendPreset,
    onUserActivity,
    onRequestHint,
    onRequestExample,
    onGiveUp,
  });

  return (
    <div
      data-tour="chat-input"
      className="input-dock z-20 shrink-0 border-t border-slate-200 bg-slate-50/98 px-3 pt-2 backdrop-blur max-lg:fixed max-lg:bottom-0 max-lg:left-0 max-lg:right-0 lg:relative lg:px-4 dark:border-slate-800 dark:bg-[#020617]/98"
    >
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-2">
        {topBar ? (
          <div className="flex flex-wrap items-center gap-2 border-b border-slate-200/90 pb-1.5 dark:border-slate-800/70">
            {topBar}
          </div>
        ) : null}

        <ActionButtonsRow
          actions={quickActions}
          loading={loading}
          canSend={canSend}
          interruptibleLoading={interruptibleLoading}
        />

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
            disabled={blockedByLoading}
            className="min-h-[48px] max-h-[8rem] flex-1 resize-none rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm leading-snug text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/25 disabled:opacity-60 sm:text-base dark:border-slate-600/80 dark:bg-[#0f172a] dark:text-white dark:placeholder:text-slate-500 dark:focus:border-blue-500/60"
          />
          <button
            type="button"
            disabled={blockedByLoading || !value.trim() || !canSend()}
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

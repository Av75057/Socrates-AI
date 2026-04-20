import { useCallback, useEffect, useRef, useState } from "react";
import { Joyride, EVENTS, STATUS } from "react-joyride";
import { updateSettings } from "../api/userApi.js";

function skillsTarget() {
  const d = document.querySelector('[data-tour="skills-desktop"]');
  const m = document.querySelector('[data-tour="skills-mobile"]');
  const pick = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 ? el : null;
  };
  return pick(d) || pick(m) || d || m || document.body;
}

const steps = [
  {
    target: '[data-tour="welcome"]',
    title: "Добро пожаловать",
    content:
      "Добро пожаловать в Socrates-AI! Я буду задавать наводящие вопросы, чтобы ты сам пришёл к выводу.",
    placement: "bottom",
  },
  {
    target: '[data-tour="chat-input"]',
    title: "Чат",
    content:
      "Здесь ты вводишь свои мысли. Не бойся ошибаться — я укажу на логические ошибки мягко.",
    placement: "top",
  },
  {
    target: skillsTarget,
    title: "Навыки",
    content: "Каждый твой ответ прокачивает конкретные навыки. Следи за прогрессом в профиле.",
    placement: "bottom",
  },
  {
    target: '[data-tour="wisdom"]',
    title: "Очки и достижения",
    content: "За активность и глубину ты получаешь очки мудрости. Открывай достижения.",
    placement: "bottom",
  },
  {
    target: '[data-tour="resume"]',
    title: "Продолжение обучения",
    content:
      "Ты всегда можешь вернуться к последнему диалогу и продолжить с того места, где остановился.",
    placement: "bottom",
  },
];

export default function OnboardingTour({ enabled, onFinished }) {
  const [run, setRun] = useState(false);
  const finishedRef = useRef(false);

  useEffect(() => {
    if (!enabled) {
      setRun(false);
      finishedRef.current = false;
      return undefined;
    }
    const t = window.setTimeout(() => setRun(true), 500);
    return () => window.clearTimeout(t);
  }, [enabled]);

  const handleEvent = useCallback(
    (data) => {
      const done =
        data.type === EVENTS.TOUR_END ||
        data.status === STATUS.FINISHED ||
        data.status === STATUS.SKIPPED;
      if (!done || finishedRef.current) return;
      finishedRef.current = true;
      setRun(false);
      void updateSettings({ has_seen_onboarding: true }).catch(() => {});
      onFinished?.();
    },
    [onFinished],
  );

  if (!enabled) return null;

  return (
    <Joyride
      run={run}
      continuous
      showProgress
      showSkipButton
      scrollToFirstStep
      steps={steps}
      onEvent={handleEvent}
      locale={{
        back: "Назад",
        close: "Закрыть",
        last: "Готово",
        next: "Далее",
        nextWithProgress: "Далее ({current} из {total})",
        open: "Открыть",
        skip: "Пропустить",
      }}
      styles={{
        options: {
          primaryColor: "#0a7cff",
          textColor: "#0f172a",
          overlayColor: "rgba(15, 23, 42, 0.55)",
          zIndex: 10050,
        },
        tooltip: {
          borderRadius: 16,
        },
        tooltipContainer: {
          textAlign: "left",
        },
        buttonNext: {
          borderRadius: 10,
        },
        buttonBack: {
          color: "#64748b",
        },
      }}
    />
  );
}

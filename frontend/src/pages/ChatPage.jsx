import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ChatWindow from "../components/ChatWindow.jsx";
import InputBox from "../components/InputBox.jsx";
import ModeIndicator from "../components/ModeIndicator.jsx";
import SessionHeader from "../components/SessionHeader.jsx";
import SidePanel from "../components/side/SidePanel.jsx";
import XpFloater from "../components/XpFloater.jsx";
import { useChatStore } from "../store/useChatStore.js";
import {
  isShortAnswer,
  isStrongAnswer,
} from "../utils/feedbackHeuristics.js";
import {
  shouldShowAlmostUnderstood,
  shouldShowVeryClose,
} from "../utils/learningHints.js";
import { getChatUrl } from "../config/api.js";
import AssistPanel from "../components/AssistPanel.jsx";
import UserStateBadge from "../components/UserStateBadge.jsx";
import { bumpUxMetric, recordProfileTime, resetProfileClock } from "../utils/uxMetrics.js";

async function postChat(sessionId, message, action) {
  const res = await fetch(getChatUrl(), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message, action }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return res.json();
}

function deriveAvatarMood({ microFeedback, feedback, simplerBanner }) {
  if (simplerBanner) return "doubt";
  if (microFeedback === "short") return "doubt";
  if (microFeedback === "good") return "fire";
  if (feedback && (feedback.includes("близко") || feedback.includes("почти"))) return "almost";
  return "neutral";
}

export default function ChatPage() {
  const messages = useChatStore((s) => s.messages);
  const mode = useChatStore((s) => s.mode);
  const loading = useChatStore((s) => s.loading);
  const attempts = useChatStore((s) => s.attempts);
  const frustration = useChatStore((s) => s.frustration);
  const frustrationLevel = useChatStore((s) => s.frustrationLevel);
  const userType = useChatStore((s) => s.userType);
  const topic = useChatStore((s) => s.topic);
  const sessionId = useChatStore((s) => s.sessionId);
  const xp = useChatStore((s) => s.xp);
  const streak = useChatStore((s) => s.streak);
  const dontKnowCount = useChatStore((s) => s.dontKnowCount);

  const setFromServer = useChatStore((s) => s.setFromServer);
  const addMessage = useChatStore((s) => s.addMessage);
  const setLoading = useChatStore((s) => s.setLoading);
  const canSend = useChatStore((s) => s.canSend);
  const markSent = useChatStore((s) => s.markSent);
  const resetSession = useChatStore((s) => s.resetSession);
  const recordTurnOutcome = useChatStore((s) => s.recordTurnOutcome);
  const resetDontKnowCount = useChatStore((s) => s.resetDontKnowCount);

  const [feedback, setFeedback] = useState(null);
  const [microFeedback, setMicroFeedback] = useState(null);
  const [simplerBanner, setSimplerBanner] = useState(false);
  const [idleHint, setIdleHint] = useState(false);
  const [xpToast, setXpToast] = useState(false);

  const lastActivityRef = useRef(Date.now());

  const bumpActivity = useCallback(() => {
    lastActivityRef.current = Date.now();
    setIdleHint(false);
  }, []);

  useEffect(() => {
    if (!feedback) return undefined;
    const t = setTimeout(() => setFeedback(null), 9000);
    return () => clearTimeout(t);
  }, [feedback]);

  useEffect(() => {
    if (!microFeedback) return undefined;
    const t = setTimeout(() => setMicroFeedback(null), 5000);
    return () => clearTimeout(t);
  }, [microFeedback]);

  useEffect(() => {
    const id = setInterval(() => {
      if (loading) return;
      if (messages.length === 0) return;
      if (Date.now() - lastActivityRef.current > 10000) {
        setIdleHint(true);
      }
    }, 1000);
    return () => clearInterval(id);
  }, [loading, messages.length]);

  useEffect(() => {
    if (dontKnowCount >= 3) setSimplerBanner(true);
  }, [dontKnowCount]);

  useEffect(() => {
    document.body.classList.add("chat-route-lock");
    return () => document.body.classList.remove("chat-route-lock");
  }, []);

  useEffect(() => {
    const onLeave = () => bumpUxMetric("tabAway");
    window.addEventListener("beforeunload", onLeave);
    return () => window.removeEventListener("beforeunload", onLeave);
  }, []);

  useEffect(() => {
    const onVis = () => {
      if (document.visibilityState === "hidden") bumpUxMetric("chatBackgrounded");
    };
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  useEffect(() => {
    if (userType) recordProfileTime(userType);
  }, [userType]);

  const run = useCallback(
    async (message, action = "none") => {
      if (!canSend()) return;
      markSent();
      bumpActivity();

      const trimmed = message.trim();
      if (action === "none" && trimmed) {
        addMessage("user", trimmed);
      } else if (action === "hint") {
        addMessage("user", trimmed || "Дай подсказку");
        resetDontKnowCount();
        setSimplerBanner(false);
      } else if (action === "give_up") {
        addMessage("user", "Объясни нормально");
        resetDontKnowCount();
        setSimplerBanner(false);
      }

      setFeedback(null);
      setMicroFeedback(null);
      setLoading(true);
      try {
        const data = await postChat(sessionId, trimmed, action);
        addMessage("assistant", data.reply);
        setFromServer(data);

        recordTurnOutcome({ userText: trimmed, action });

        const dk = useChatStore.getState().dontKnowCount;
        if (dk >= 3) setSimplerBanner(true);

        const veryClose = shouldShowVeryClose({
          action,
          attempts: data.attempts,
          mode: data.mode,
        });
        const almost = shouldShowAlmostUnderstood({
          action,
          userText: trimmed,
          attempts: data.attempts,
          frustration: data.frustration,
          mode: data.mode,
        });
        const goodAttemptBanner =
          action === "none" &&
          trimmed &&
          (data.frustration_level ?? 0) >= 1 &&
          trimmed.length < 28;

        if (veryClose) {
          setFeedback("Ты очень близко 👀");
        } else if (almost) {
          setFeedback("Ты почти понял 👀");
        } else if (goodAttemptBanner) {
          setFeedback("Хорошая попытка. Давай докрутим 👇");
        }

        if (action === "none" && trimmed) {
          const skipShortMicro = veryClose || almost || goodAttemptBanner;
          if (!skipShortMicro && isShortAnswer(trimmed, action)) setMicroFeedback("short");
          else if (isStrongAnswer(trimmed, action)) setMicroFeedback("good");
        }

        setXpToast(true);
        setTimeout(() => setXpToast(false), 1400);
      } catch (e) {
        const msg =
          e instanceof TypeError
            ? "Не удаётся связаться с сервером. Запусти бэкенд: cd backend && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000. Если открываешь собранный фронт без прокси — в frontend/.env задай VITE_API_URL=http://127.0.0.1:8000"
            : e.message;
        addMessage("assistant", `Ошибка: ${msg}`);
      } finally {
        setLoading(false);
      }
    },
    [
      addMessage,
      bumpActivity,
      canSend,
      markSent,
      recordTurnOutcome,
      resetDontKnowCount,
      sessionId,
      setFromServer,
      setLoading,
    ],
  );

  const onSend = (text) => run(text, "none");
  const onRequestHint = () => {
    bumpUxMetric("hintButtonClicks");
    run("", "hint");
  };
  const onRequestExample = () => {
    bumpUxMetric("exampleHintClicks");
    run("Дай пример", "hint");
  };
  const onGiveUp = () => {
    bumpUxMetric("giveUpClicks");
    run("", "give_up");
  };

  const onNewSession = () => {
    if (confirm("Начать новую сессию? Прогресс этой темы сбросится.")) {
      setFeedback(null);
      setMicroFeedback(null);
      setSimplerBanner(false);
      setIdleHint(false);
      setXpToast(false);
      resetProfileClock();
      resetSession();
    }
  };

  const avatarMood = useMemo(
    () =>
      deriveAvatarMood({
        microFeedback,
        feedback,
        simplerBanner,
      }),
    [microFeedback, feedback, simplerBanner],
  );

  return (
    <div className="relative flex h-[100dvh] max-h-[100dvh] flex-col overflow-hidden bg-[#0f172a] font-sans text-slate-100">
      <XpFloater amount={5} show={xpToast} />
      <SessionHeader topic={topic} onNewSession={onNewSession} xp={xp} streak={streak} />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col lg:flex-row">
        <div className="flex min-h-0 min-w-0 flex-1 flex-col lg:flex-[7_1_0%]">
          <ModeIndicator mode={mode} attempts={attempts} frustration={frustration} />
          <UserStateBadge type={userType} />
          <AssistPanel
            level={frustrationLevel}
            loading={loading}
            onExampleHint={onRequestExample}
            onExplain={onGiveUp}
          />
          <ChatWindow
            messages={messages}
            loading={loading}
            feedback={feedback}
            microFeedback={microFeedback}
            simplerBanner={simplerBanner}
            idleHint={idleHint}
            assistLevel={frustrationLevel}
            onIdleHintDismiss={() => {
              setIdleHint(false);
              bumpActivity();
            }}
          />
          <InputBox
            userType={userType}
            onSend={onSend}
            loading={loading}
            canSend={canSend}
            onRequestHint={onRequestHint}
            onRequestExample={onRequestExample}
            onGiveUp={onGiveUp}
            onQuickDontKnow={() => bumpUxMetric("dontKnowQuick")}
            onUserActivity={bumpActivity}
          />
        </div>

        <SidePanel
          attempts={attempts}
          xp={xp}
          streak={streak}
          topic={topic}
          avatarMood={avatarMood}
          whisperIndex={attempts}
          progressPulseKey={attempts}
        />
      </div>
    </div>
  );
}

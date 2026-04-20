import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Link } from "react-router-dom";
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
import { apiFetch, getToken } from "../api/client.js";
import {
  createConversation,
  deleteMessage,
  fetchConversation,
  fetchMemoryProfile,
  fetchSettings,
  getRecommendation,
  updateMessage,
} from "../api/userApi.js";
import ResumeLearningWidget from "../components/learning/ResumeLearningWidget.jsx";
import PedagogyStatus from "../components/learning/PedagogyStatus.jsx";
import { getMemoryUserId } from "../config/memoryUser.js";
import { useAuth } from "../contexts/AuthContext.jsx";
import AssistPanel from "../components/AssistPanel.jsx";
import UserStateBadge from "../components/UserStateBadge.jsx";
import UserMemoryPanel from "../components/UserMemoryPanel.jsx";
import SkillTree from "../components/SkillTree.jsx";
import ThinkingPanel from "../components/ThinkingPanel.jsx";
import WisdomPointsBadge from "../components/gamification/WisdomPointsBadge.jsx";
import AchievementsModal from "../components/gamification/AchievementsModal.jsx";
import DailyChallengeWidget from "../components/gamification/DailyChallengeWidget.jsx";
import GamificationToastHost from "../components/gamification/GamificationToastHost.jsx";
import {
  fetchAchievementsCatalog,
  fetchDailyChallenge,
  fetchDailyChallengeMe,
  fetchGamificationProgress,
  fetchGamificationProgressMe,
  postGamificationAction,
} from "../api/gamificationApi.js";
import { fetchPedagogyState, postPedagogyHint, postPedagogyMode } from "../api/pedagogyApi.js";
import TutorModeSelector from "../components/pedagogy/TutorModeSelector.jsx";
import DifficultyIndicator from "../components/pedagogy/DifficultyIndicator.jsx";
import FallacyNotification from "../components/pedagogy/FallacyNotification.jsx";
import HintButton from "../components/pedagogy/HintButton.jsx";
import { buildConnectionErrorHint } from "../utils/connectionErrorHint.js";
import { bumpUxMetric, recordProfileTime, resetProfileClock } from "../utils/uxMetrics.js";
import { parseDbMessageId } from "../utils/messageId.js";
import OnboardingTour from "../components/OnboardingTour.jsx";

function messagesFromNewConversation(c) {
  const t = (c.opening_message || "").trim();
  if (!t) return [];
  return [
    {
      id:
        typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : `open_${c.id}_${Date.now()}`,
      role: "assistant",
      text: t,
      createdAt: Date.now(),
    },
  ];
}

async function postChat(sessionId, message, action, conversationId) {
  const payload = {
    session_id: sessionId,
    message,
    action,
    memory_user_id: getMemoryUserId(),
  };
  if (conversationId != null) payload.conversation_id = conversationId;
  const res = await apiFetch("/chat", {
    method: "POST",
    body: JSON.stringify(payload),
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
  const { user: authUser } = useAuth();
  const setActiveConversation = useChatStore((s) => s.setActiveConversation);
  const conversationId = useChatStore((s) => s.conversationId);
  const messages = useChatStore((s) => s.messages);
  const mode = useChatStore((s) => s.mode);
  const loading = useChatStore((s) => s.loading);
  const attempts = useChatStore((s) => s.attempts);
  const frustration = useChatStore((s) => s.frustration);
  const frustrationLevel = useChatStore((s) => s.frustrationLevel);
  const userType = useChatStore((s) => s.userType);
  const memory = useChatStore((s) => s.memory);
  const skillTree = useChatStore((s) => s.skillTree);
  const topic = useChatStore((s) => s.topic);
  const sessionId = useChatStore((s) => s.sessionId);
  const xp = useChatStore((s) => s.xp);
  const streak = useChatStore((s) => s.streak);
  const gamificationPublic = useChatStore((s) => s.gamificationPublic);
  const dontKnowCount = useChatStore((s) => s.dontKnowCount);

  const setFromServer = useChatStore((s) => s.setFromServer);
  const addMessage = useChatStore((s) => s.addMessage);
  const patchLastExchangeMessageIds = useChatStore((s) => s.patchLastExchangeMessageIds);
  const updateMessageText = useChatStore((s) => s.updateMessageText);
  const removeMessagesFromId = useChatStore((s) => s.removeMessagesFromId);
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
  const [skillToast, setSkillToast] = useState(null);
  const [dailyCh, setDailyCh] = useState(null);
  const [achCatalog, setAchCatalog] = useState([]);
  const [achOpen, setAchOpen] = useState(false);
  const [gamToasts, setGamToasts] = useState([]);
  const [wisdomBump, setWisdomBump] = useState(0);
  const [gamificationLoaded, setGamificationLoaded] = useState(false);
  const [tutorMode, setTutorMode] = useState("friendly");
  const [pedDifficulty, setPedDifficulty] = useState(1);
  const [fallacyNotice, setFallacyNotice] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [pedagogyIntro, setPedagogyIntro] = useState(false);
  const [accountSettings, setAccountSettings] = useState(null);
  const chatScrollRef = useRef(null);

  const lastActivityRef = useRef(Date.now());

  const bumpActivity = useCallback(() => {
    lastActivityRef.current = Date.now();
    setIdleHint(false);
  }, []);

  const pushGamToast = useCallback((text, kind = "points") => {
    const id =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `gt_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    setGamToasts((t) => [...t, { id, kind, text }]);
    setTimeout(() => {
      setGamToasts((t) => t.filter((x) => x.id !== id));
    }, 5000);
  }, []);

  const dismissGamToast = useCallback((id) => {
    setGamToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const handleTutorModeChange = useCallback(
    async (m) => {
      setTutorMode(m);
      const res = await postPedagogyMode(sessionId, m);
      if (res && typeof res.difficulty_level === "number") setPedDifficulty(res.difficulty_level);
    },
    [sessionId],
  );

  const handlePedagogyHint = useCallback(async () => {
    if (loading || !canSend()) return;
    bumpActivity();
    const msgs = useChatStore.getState().messages;
    const lastUser = [...msgs].reverse().find((m) => m.role === "user")?.text ?? "";
    const res = await postPedagogyHint(sessionId, topic, lastUser);
    if (res?.hint) {
      addMessage("assistant", res.hint);
      if (typeof res.difficulty_level === "number") setPedDifficulty(res.difficulty_level);
    }
  }, [sessionId, topic, loading, canSend, bumpActivity, addMessage]);

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

  /** Для аккаунта прогресс общий: не перезагружать при смене диалога (иначе мигание и гонки с API). Гость — привязка к sessionId. */
  const gamificationReloadKey =
    authUser?.id != null ? `auth:${authUser.id}` : `guest:${sessionId}`;

  useLayoutEffect(() => {
    useChatStore.getState().mergeGamificationFromPersisted();
  }, [sessionId, conversationId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setGamificationLoaded(false);
      const sid = useChatStore.getState().sessionId;
      const authed = !!getToken();
      const [p, dc, cat] = await Promise.all([
        authed ? fetchGamificationProgressMe() : fetchGamificationProgress(sid),
        authed ? fetchDailyChallengeMe() : fetchDailyChallenge(sid),
        fetchAchievementsCatalog(),
      ]);
      if (cancelled) return;
      if (p) {
        useChatStore.getState().applyGamificationProgress(p);
      }
      if (authed) {
        useChatStore.getState().mergeGamificationFromPersisted();
      }
      setDailyCh(dc);
      setAchCatalog(Array.isArray(cat) ? cat : []);
      setGamificationLoaded(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [gamificationReloadKey]);

  /**
   * При смене диалога перечитать общий прогресс по JWT (не зависит от session_key).
   * Важно: /app без PrivateRoute — authUser может ещё грузиться, а токен уже есть;
   * если ждать только authUser, панель временно уходит в «attempts» и выглядит как сброс.
   */
  useEffect(() => {
    if (!getToken()) return;
    let cancelled = false;
    (async () => {
      const p = await fetchGamificationProgressMe();
      if (cancelled || !p) return;
      useChatStore.getState().applyGamificationProgress(p);
      useChatStore.getState().mergeGamificationFromPersisted();
    })();
    return () => {
      cancelled = true;
    };
  }, [conversationId, sessionId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const s = await fetchPedagogyState(sessionId);
      if (cancelled || !s) return;
      if (s.mode) setTutorMode(s.mode);
      if (typeof s.difficulty_level === "number") setPedDifficulty(s.difficulty_level);
    })();
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    if (!authUser) {
      setRecommendation(null);
      return;
    }
    let cancelled = false;
    setRecommendationLoading(true);
    getRecommendation()
      .then((r) => {
        if (!cancelled) setRecommendation(r);
      })
      .catch(() => {
        if (!cancelled) setRecommendation(null);
      })
      .finally(() => {
        if (!cancelled) setRecommendationLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [authUser]);

  useEffect(() => {
    if (!authUser) return;
    if (!localStorage.getItem("socrates_pedagogy_intro_v1")) {
      setPedagogyIntro(true);
    }
  }, [authUser]);

  useEffect(() => {
    if (!authUser) {
      setAccountSettings(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const s = await fetchSettings();
        if (!cancelled) setAccountSettings(s);
      } catch {
        if (!cancelled) setAccountSettings(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [authUser?.id]);

  /** Память тьютора в Redis привязана к аккаунту, не к диалогу — подтягиваем при смене чата и при JWT без ожидания authUser. */
  useEffect(() => {
    if (!getToken()) return;
    let cancelled = false;
    (async () => {
      try {
        const mp = await fetchMemoryProfile();
        if (cancelled || !mp?.user_type) return;
        useChatStore.getState().hydrateTutorMemoryFromProfile(mp);
      } catch {
        /* нет сети или старый API */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [conversationId, sessionId, authUser?.id]);

  /** После F5: подтянуть сообщения диалога, если в сторе уже есть conversationId. */
  useEffect(() => {
    if (!authUser || !conversationId) return;
    if (useChatStore.getState().messages.length > 0) return;
    let cancelled = false;
    (async () => {
      try {
        const detail = await fetchConversation(conversationId);
        if (cancelled) return;
        const sk = detail.session_key;
        if (useChatStore.getState().sessionId !== sk) {
          localStorage.setItem("socrates_session_id", sk);
          localStorage.setItem(
            "socrates_chat_resume",
            JSON.stringify({ conversationId, sessionKey: sk }),
          );
        }
        const initial = (detail.messages || []).map((m) => ({
          id: `db-${m.id}`,
          role: m.role === "tutor" ? "assistant" : "user",
          text: m.content,
          createdAt: m.created_at ? new Date(m.created_at).getTime() : Date.now(),
        }));
        useChatStore.setState({
          sessionId: sk,
          messages: initial,
          topic: (detail.title || "").trim() || useChatStore.getState().topic,
        });
      } catch {
        useChatStore.getState().clearResume();
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [authUser, conversationId]);

  useEffect(() => {
    if (!skillToast) return undefined;
    const t = setTimeout(() => setSkillToast(null), 5200);
    return () => clearTimeout(t);
  }, [skillToast]);

  const refreshRecommendation = useCallback(async () => {
    if (!authUser) return;
    try {
      const r = await getRecommendation();
      setRecommendation(r);
    } catch {
      /* ignore */
    }
  }, [authUser]);

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
      const attemptsBefore = useChatStore.getState().attempts;
      try {
        const data = await postChat(
          sessionId,
          trimmed,
          action,
          useChatStore.getState().conversationId,
        );
        addMessage("assistant", data.reply);
        setFromServer(data);
        if (
          data.persisted_user_message_id != null &&
          data.persisted_assistant_message_id != null
        ) {
          patchLastExchangeMessageIds({
            userId: data.persisted_user_message_id,
            assistantId: data.persisted_assistant_message_id,
          });
        }

        if (data.pedagogy) {
          setTutorMode(data.pedagogy.mode || "friendly");
          setPedDifficulty(data.pedagogy.difficulty_level ?? 1);
          if (data.pedagogy.fallacy?.has_fallacy) {
            setFallacyNotice(data.pedagogy.fallacy);
          } else {
            setFallacyNotice(null);
          }
        }

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

        const ev = data.skill_tree?.events;
        if (ev?.completed?.length) {
          bumpUxMetric("skillNodeCompleted");
          const t = ev.completed[0];
          setSkillToast(`Ты разобрался с темой «${t.title}» 🎉 Готов перейти к следующей?`);
        } else if (ev?.unlocked?.length) {
          bumpUxMetric("skillNodeUnlocked");
          const t = ev.unlocked[0];
          setSkillToast(`Новая тема открыта: «${t.title}» 🔓`);
        }

        const msgForGame =
          trimmed ||
          (action === "hint" ? "Дай подсказку" : action === "give_up" ? "Объясни нормально" : "");
        if (msgForGame || action !== "none") {
          const gam = await postGamificationAction(sessionId, "user_response", {
            user_message: msgForGame,
            action,
            attempts_before: attemptsBefore,
          });
          if (gam?.progress) {
            useChatStore.getState().applyGamificationProgress(gam.progress);
            setWisdomBump((k) => k + 1);
          }
          if (gam?.toasts?.length) {
            for (const line of gam.toasts) {
              const kind = line.includes("Достижение") ? "achievement" : "points";
              pushGamToast(line, kind);
            }
          }
        }
        const dc = authUser ? await fetchDailyChallengeMe() : await fetchDailyChallenge(sessionId);
        if (dc) setDailyCh(dc);

        if (authUser) void refreshRecommendation();
      } catch (e) {
        const msg =
          e instanceof TypeError
            ? `Не удаётся связаться с сервером. ${buildConnectionErrorHint()}`
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
      pushGamToast,
      authUser,
      refreshRecommendation,
      patchLastExchangeMessageIds,
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
      setFallacyNotice(null);
      resetProfileClock();
      void postGamificationAction(sessionId, "new_dialog", {});
      resetSession();
    }
  };

  const onNewAccountDialog = async () => {
    if (!authUser) return;
    try {
      const c = await createConversation();
      setFeedback(null);
      setMicroFeedback(null);
      setSimplerBanner(false);
      setIdleHint(false);
      setFallacyNotice(null);
      resetProfileClock();
      setActiveConversation(c.id, c.session_key, messagesFromNewConversation(c));
      void postGamificationAction(c.session_key, "new_dialog", {});
      try {
        const r = await getRecommendation();
        setRecommendation(r);
      } catch {
        /* ignore */
      }
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось создать диалог");
    }
  };

  const onResumeLastDialog = useCallback(async () => {
    const last = recommendation?.last_conversation;
    if (!last?.id) return;
    try {
      const detail = await fetchConversation(last.id);
      const initial = (detail.messages || []).map((m) => ({
        id: `db-${m.id}`,
        role: m.role === "tutor" ? "assistant" : "user",
        text: m.content,
        createdAt: m.created_at ? new Date(m.created_at).getTime() : Date.now(),
      }));
      setFeedback(null);
      setMicroFeedback(null);
      setSimplerBanner(false);
      setIdleHint(false);
      setFallacyNotice(null);
      resetProfileClock();
      setActiveConversation(detail.id, detail.session_key, initial);
      await refreshRecommendation();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось открыть диалог");
    }
  }, [recommendation, refreshRecommendation, setActiveConversation]);

  const onNewRecommendedDialog = useCallback(async () => {
    const title = (recommendation?.recommended_topic || "").trim() || "Новая тема";
    try {
      const c = await createConversation(title);
      setFeedback(null);
      setMicroFeedback(null);
      setSimplerBanner(false);
      setIdleHint(false);
      setFallacyNotice(null);
      resetProfileClock();
      setActiveConversation(c.id, c.session_key, messagesFromNewConversation(c));
      void postGamificationAction(c.session_key, "new_dialog", {});
      await refreshRecommendation();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось создать диалог");
    }
  }, [recommendation, refreshRecommendation, setActiveConversation]);

  const dismissPedagogyIntro = useCallback(() => {
    localStorage.setItem("socrates_pedagogy_intro_v1", "1");
    setPedagogyIntro(false);
  }, []);

  const handleEditMessage = useCallback(
    async (messageId, text) => {
      if (!authUser) return;
      const id = parseDbMessageId(messageId);
      if (id == null) return;
      try {
        await updateMessage(id, text);
        updateMessageText(messageId, text);
      } catch (e) {
        alert(e instanceof Error ? e.message : "Не удалось сохранить");
      }
    },
    [authUser, updateMessageText],
  );

  const handleDeleteMessage = useCallback(
    async (messageId) => {
      if (!authUser) return;
      if (!window.confirm("Удалить это сообщение и все последующие?")) return;
      const id = parseDbMessageId(messageId);
      if (id == null) return;
      try {
        await deleteMessage(id);
        removeMessagesFromId(messageId);
      } catch (e) {
        alert(e instanceof Error ? e.message : "Не удалось удалить");
      }
    },
    [authUser, removeMessagesFromId],
  );

  const scrollChatToBottom = useCallback(() => {
    const el = chatScrollRef.current;
    if (!el) return;
    requestAnimationFrame(() => {
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    });
  }, []);

  const showTypingFromSettings = accountSettings?.show_typing_indicator !== false;

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
    <div className="relative flex h-[100dvh] max-h-[100dvh] flex-col overflow-hidden bg-slate-100 font-sans text-slate-900 dark:bg-[#0f172a] dark:text-slate-100">
      <GamificationToastHost items={gamToasts} onDismiss={dismissGamToast} />
      <AchievementsModal
        open={achOpen}
        onClose={() => setAchOpen(false)}
        catalog={achCatalog}
        unlockedIds={gamificationPublic?.achievements}
      />
      <XpFloater amount={5} show={xpToast} />
      {skillToast ? (
        <div className="pointer-events-none fixed left-0 right-0 top-[3.25rem] z-30 flex justify-center px-3 sm:top-16">
          <div className="max-w-lg rounded-xl border border-violet-400/50 bg-violet-100 px-4 py-2.5 text-center text-sm text-violet-900 shadow-lg shadow-violet-900/10 dark:border-violet-500/40 dark:bg-violet-950/95 dark:text-violet-100 dark:shadow-black/30">
            {skillToast}
          </div>
        </div>
      ) : null}
      <SessionHeader
        topic={topic}
        onNewSession={onNewSession}
        xp={xp}
        streak={streak}
        pedagogySlot={<PedagogyStatus />}
        wisdomSlot={
          <div data-tour="wisdom">
            <WisdomPointsBadge
              points={gamificationPublic?.wisdom_points ?? 0}
              level={gamificationPublic?.level ?? 1}
              onClick={() => setAchOpen(true)}
              bumpSignal={wisdomBump}
            />
          </div>
        }
      />
      {!authUser ? (
        <div className="mx-4 mt-2 rounded-lg border border-amber-500/50 bg-amber-50 px-3 py-2 text-center text-xs text-amber-950 dark:border-amber-600/40 dark:bg-amber-950/30 dark:text-amber-100/95">
          <Link to="/login" className="font-medium text-amber-800 underline dark:text-amber-300">
            Войдите
          </Link>
          , чтобы сохранять историю диалогов в аккаунте.
        </div>
      ) : null}
      {authUser && pedagogyIntro ? (
        <div className="mx-4 mt-2 rounded-lg border border-cyan-400/40 bg-cyan-50/90 px-3 py-2 text-xs text-cyan-950 dark:border-cyan-700/50 dark:bg-cyan-950/40 dark:text-cyan-100/90">
          <p>
            Я буду отслеживать твои навыки, чтобы стать персональным наставником. Уровни и ошибки — в разделе
            «Навыки» и «Педагогика» в профиле.
          </p>
          <button
            type="button"
            onClick={dismissPedagogyIntro}
            className="mt-2 font-medium text-cyan-800 underline dark:text-cyan-300"
          >
            Понятно
          </button>
        </div>
      ) : null}
      {authUser ? (
        <div data-tour="resume">
          <ResumeLearningWidget
            data={recommendation}
            loading={recommendationLoading}
            onContinueLast={onResumeLastDialog}
            onNewRecommended={onNewRecommendedDialog}
          />
        </div>
      ) : null}
      {authUser ? (
        <div className="mx-4 mt-2 flex flex-wrap items-center justify-center gap-3 text-xs text-slate-600 dark:text-slate-400">
          <Link to="/profile" className="text-cyan-700 hover:underline dark:text-cyan-400">
            Профиль
          </Link>
          <Link to="/profile/history" className="text-cyan-700 hover:underline dark:text-cyan-400">
            История
          </Link>
          {String(authUser.role || "").toLowerCase() === "admin" ? (
            <Link to="/admin" className="text-amber-700 hover:underline dark:text-amber-400">
              Админ-панель
            </Link>
          ) : null}
          <button
            type="button"
            onClick={onNewAccountDialog}
            className="rounded-md border border-slate-300 px-2 py-1 text-slate-700 hover:bg-slate-200 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            Новый диалог (сохранить в аккаунте)
          </button>
          {conversationId != null ? (
            <span className="text-slate-500 dark:text-slate-500">Диалог #{conversationId}</span>
          ) : (
            <span className="text-amber-800 dark:text-amber-400/90">
              Гостевой Redis-сессия — нажмите, чтобы вести диалог в БД
            </span>
          )}
        </div>
      ) : null}
      <DailyChallengeWidget
        text={dailyCh?.challenge_text}
        completed={!!dailyCh?.completed}
        loading={!gamificationLoaded}
      />
      <FallacyNotification fallacy={fallacyNotice} onDismiss={() => setFallacyNotice(null)} />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col lg:flex-row">
        <div className="flex min-h-0 min-w-0 flex-1 flex-col lg:flex-[7_1_0%]">
          <ModeIndicator mode={mode} attempts={attempts} frustration={frustration} />
          <UserStateBadge type={userType} />
          <UserMemoryPanel memory={memory} className="mx-4 mt-0 lg:hidden" />
          <div className="mx-4 lg:hidden" data-tour="skills-mobile">
            <SkillTree skillTree={skillTree} topic={topic} />
          </div>
          <ThinkingPanel profile={memory.thinking_profile} className="mx-4 lg:hidden" />
          <AssistPanel
            level={frustrationLevel}
            loading={loading}
            onExampleHint={onRequestExample}
            onExplain={onGiveUp}
          />
          <ChatWindow
            ref={chatScrollRef}
            messages={messages}
            loading={loading}
            feedback={feedback}
            microFeedback={microFeedback}
            simplerBanner={simplerBanner}
            idleHint={idleHint}
            assistLevel={frustrationLevel}
            userLabel={authUser?.full_name || authUser?.email || "Я"}
            canEditMessages={!!authUser}
            onEditMessage={handleEditMessage}
            onDeleteMessage={handleDeleteMessage}
            showTypingIndicator={showTypingFromSettings}
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
            onInputFocus={scrollChatToBottom}
            topBar={
              <>
                <TutorModeSelector
                  value={tutorMode}
                  onChange={handleTutorModeChange}
                  disabled={loading}
                />
                <DifficultyIndicator level={pedDifficulty} />
                <HintButton
                  visible={tutorMode === "friendly" || pedDifficulty > 2}
                  disabled={loading || !canSend()}
                  onClick={handlePedagogyHint}
                />
              </>
            }
          />
        </div>

        <SidePanel
          attempts={attempts}
          xp={xp}
          streak={streak}
          topic={topic}
          memory={memory}
          skillTree={skillTree}
          avatarMood={avatarMood}
          whisperIndex={attempts}
          progressPulseKey={attempts}
          accountGamification={!!getToken()}
          gamificationPublic={gamificationPublic}
        />
      </div>
      <OnboardingTour
        enabled={!!authUser && !!accountSettings && accountSettings.has_seen_onboarding === false}
        onFinished={() =>
          setAccountSettings((s) => (s ? { ...s, has_seen_onboarding: true } : s))
        }
      />
    </div>
  );
}

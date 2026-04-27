import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
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
  fetchMyAssignment,
  fetchMemoryProfile,
  fetchSettings,
  getRecommendation,
  listConversations,
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
import DailyChallengeCompact from "../components/gamification/DailyChallengeCompact.jsx";
import DailyChallengeModal from "../components/gamification/DailyChallengeModal.jsx";
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
import { bumpUxMetric, recordProfileTime, resetProfileClock } from "../utils/uxMetrics.js";
import { parseDbMessageId } from "../utils/messageId.js";
import OnboardingTour from "../components/OnboardingTour.jsx";
import ConversationList from "../components/chat/ConversationList.jsx";
import { useSSE } from "../hooks/useSSE.js";
import TopicCard from "../components/topics/TopicCard.jsx";
import { listTopics, startTopic } from "../api/topicsApi.js";
import MetaTrainingPanel from "../components/meta/MetaTrainingPanel.jsx";
import MetaTrainingComposer from "../components/meta/MetaTrainingComposer.jsx";
import {
  advanceMetaTrainingPhase,
  endMetaTraining,
  fetchMetaTrainingStatus,
  postMetaTrainingMessage,
  startMetaTraining,
  switchMetaTrainingFrame,
} from "../api/metaTrainingApi.js";

const META_PHASE_ROLE = {
  orientation: "Навигатор по вопросам",
  exploration: "Навигатор по рамкам",
  sparring: "Защитник тезиса",
  reflection: "Зеркало рефлексии",
  completed: "Итоговый разбор",
};

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

function messagesFromTopicStart(data) {
  const t = (data.opening_message || data.first_message || "").trim();
  if (!t) return [];
  return [
    {
      id:
        typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : `topic_${data.conversation_id}_${Date.now()}`,
      role: "assistant",
      text: t,
      createdAt: Date.now(),
    },
  ];
}

function PremiumTopicsModal({ open, onClose }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4">
      <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl dark:bg-slate-900">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-amber-600 dark:text-amber-300">
          Premium-тема
        </p>
        <h2 className="mt-3 font-display text-2xl font-bold text-slate-950 dark:text-white">
          Для этой темы нужен Pro
        </h2>
        <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
          Открой premium-библиотеку тем и расширенные сценарии обсуждений.
        </p>
        <div className="mt-6 flex gap-3">
          <Link
            to="/pricing"
            className="inline-flex flex-1 items-center justify-center rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-medium text-amber-950 hover:bg-amber-400"
          >
            Перейти к Pro
          </Link>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex flex-1 items-center justify-center rounded-xl border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}

function buildChatPayload(
  sessionId,
  message,
  action,
  conversationId,
  clientMessageId = null,
  assignmentId = null,
) {
  const payload = {
    session_id: sessionId,
    message,
    action,
    memory_user_id: getMemoryUserId(),
  };
  if (conversationId != null) payload.conversation_id = conversationId;
  if (clientMessageId) payload.client_message_id = clientMessageId;
  if (assignmentId != null) payload.assignment_id = assignmentId;
  return payload;
}

async function postChat(
  sessionId,
  message,
  action,
  conversationId,
  clientMessageId = null,
  assignmentId = null,
) {
  const res = await apiFetch("/chat", {
    method: "POST",
    body: JSON.stringify(
      buildChatPayload(
        sessionId,
        message,
        action,
        conversationId,
        clientMessageId,
        assignmentId,
      ),
    ),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || res.statusText);
  }
  return res.json();
}

const OFFLINE_QUEUE_KEY = "socrates_pending_chat_v1";

function readPendingTurns() {
  try {
    const raw = localStorage.getItem(OFFLINE_QUEUE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writePendingTurns(items) {
  try {
    localStorage.setItem(OFFLINE_QUEUE_KEY, JSON.stringify(items));
  } catch {
    /* ignore */
  }
}

function enqueuePendingTurn(item) {
  const next = [...readPendingTurns(), item];
  writePendingTurns(next);
  return next;
}

function removePendingTurn(clientMessageId) {
  const next = readPendingTurns().filter((item) => item.clientMessageId !== clientMessageId);
  writePendingTurns(next);
  return next;
}

function pendingTurnsForSession(sessionId) {
  return readPendingTurns().filter((item) => item.sessionId === sessionId);
}

function createClientMessageId() {
  return typeof crypto !== "undefined" && crypto.randomUUID
    ? crypto.randomUUID()
    : `turn_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}

function buildUserBubbleText(trimmed, action) {
  if (action === "none" && trimmed) return trimmed;
  if (action === "hint") return trimmed || "Дай подсказку";
  if (action === "give_up") return "Объясни нормально";
  return trimmed;
}

function normalizeConversationMessages(detail) {
  return (detail.messages || []).map((m) => ({
    id: `db-${m.id}`,
    role: m.role === "tutor" ? "assistant" : "user",
    text: m.content,
    createdAt: m.created_at ? new Date(m.created_at).getTime() : Date.now(),
  }));
}

function normalizeMetaMessages(items) {
  return (items || []).map((item) => {
    const prefix =
      item.role === "assistant" ? `[${META_PHASE_ROLE[item.phase] || "Meta"}] ` : "";
    return {
      id: item.id,
      role: item.role,
      text: `${prefix}${item.text}`,
      createdAt: item.created_at ? new Date(item.created_at).getTime() : Date.now(),
    };
  });
}

function SaveStatusBadge({ status }) {
  if (!status) return null;
  const tone =
    status.kind === "saved"
      ? "border-emerald-300/70 bg-emerald-50 text-emerald-800 dark:border-emerald-500/30 dark:bg-emerald-950/30 dark:text-emerald-200"
      : status.kind === "queued"
        ? "border-amber-300/70 bg-amber-50 text-amber-900 dark:border-amber-500/30 dark:bg-amber-950/30 dark:text-amber-200"
        : status.kind === "saving"
          ? "border-cyan-300/70 bg-cyan-50 text-cyan-900 dark:border-cyan-500/30 dark:bg-cyan-950/30 dark:text-cyan-200"
          : "border-rose-300/70 bg-rose-50 text-rose-900 dark:border-rose-500/30 dark:bg-rose-950/30 dark:text-rose-200";
  return <span className={`inline-flex rounded-full border px-2 py-0.5 text-[11px] font-medium ${tone}`}>{status.text}</span>;
}

function deriveAvatarMood({ microFeedback, feedback, simplerBanner }) {
  if (simplerBanner) return "doubt";
  if (microFeedback === "short") return "doubt";
  if (microFeedback === "good") return "fire";
  if (feedback && (feedback.includes("близко") || feedback.includes("почти"))) return "almost";
  return "neutral";
}

export default function ChatPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user: authUser } = useAuth();
  const setActiveConversation = useChatStore((s) => s.setActiveConversation);
  const bindConversation = useChatStore((s) => s.bindConversation);
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
  const updateMessageMeta = useChatStore((s) => s.updateMessageMeta);
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
  const [dailyModalOpen, setDailyModalOpen] = useState(false);
  const [conversationItems, setConversationItems] = useState([]);
  const [conversationListLoading, setConversationListLoading] = useState(false);
  const [assignmentBanner, setAssignmentBanner] = useState(null);
  const [topicSuggestions, setTopicSuggestions] = useState([]);
  const [topicSuggestionsLoading, setTopicSuggestionsLoading] = useState(false);
  const [topicUpgradeOpen, setTopicUpgradeOpen] = useState(false);
  const [startingTopicId, setStartingTopicId] = useState(null);
  const [saveStatus, setSaveStatus] = useState(() => {
    const pending = pendingTurnsForSession(useChatStore.getState().sessionId).length;
    return pending > 0 ? { kind: "queued", text: `Локально сохранено: ${pending}` } : null;
  });
  const [metaSession, setMetaSession] = useState(null);
  const [metaMessages, setMetaMessages] = useState([]);
  const [metaLoading, setMetaLoading] = useState(false);
  const [metaDetectedQuestionType, setMetaDetectedQuestionType] = useState(null);
  const [metaDetectedQuestionHint, setMetaDetectedQuestionHint] = useState(null);
  const [metaDetectedAssumptionHint, setMetaDetectedAssumptionHint] = useState(null);
  const [metaDiversityHint, setMetaDiversityHint] = useState(null);
  const chatScrollRef = useRef(null);
  const syncQueueRef = useRef(false);
  const streamingMessageIdRef = useRef(null);
  const streamRequestIdRef = useRef(0);
  const streamStartedRef = useRef(false);
  const { send: sendStream, cancel: cancelStream, streaming: streamInFlight } = useSSE("/api/chat/message/stream");

  const lastActivityRef = useRef(Date.now());
  const metaMode = searchParams.get("mode") === "meta";

  const applyMetaPayload = useCallback((payload) => {
    if (!payload || typeof payload !== "object") return;
    const session = payload.session || null;
    setMetaSession(session);
    setMetaMessages(normalizeMetaMessages(payload.messages || []));
    const nextType =
      session?.phase === "orientation" ? payload.detected_question_type || null : null;
    const latestQuestion =
      session?.phase === "orientation" && Array.isArray(session?.questions) && session.questions.length > 0
        ? session.questions[session.questions.length - 1]
        : null;
    setMetaDetectedQuestionType(nextType);
    setMetaDetectedQuestionHint(nextType ? null : null);
    setMetaDetectedAssumptionHint(nextType ? latestQuestion?.assumption || null : null);
    const questions = Array.isArray(session?.questions) ? session.questions : [];
    const recentTypes = questions
      .slice(-3)
      .map((item) => String(item?.question_type || "").trim())
      .filter(Boolean);
    const lastTwoSame =
      recentTypes.length >= 2 && recentTypes[recentTypes.length - 1] === recentTypes[recentTypes.length - 2];
    const seenTypes = new Set(recentTypes);
    let nextDiversityHint = null;
    if (session?.phase === "orientation" && lastTwoSame) {
      const currentType = recentTypes[recentTypes.length - 1];
      if (currentType === "factual") {
        nextDiversityHint = "Ты дважды подряд идёшь в фактологию. Попробуй теперь концептуальный или мета-вопрос: не «что это», а «в каком смысле это считается знанием?»";
      } else if (currentType === "conceptual") {
        nextDiversityHint = "Ты держишься в концептуальной рамке. Попробуй провокационный ход: какое допущение в тезисе можно атаковать?";
      } else if (currentType === "provocative") {
        nextDiversityHint = "Ты хорошо атакуешь основания. Теперь попробуй мета-вопрос: по каким критериям вообще проверять этот тезис?";
      } else if (currentType === "meta") {
        nextDiversityHint = "Ты уже смотришь на правила знания. Теперь попробуй сменить оптику и задать более предметный концептуальный или провокационный вопрос.";
      }
    } else if (session?.phase === "orientation" && seenTypes.size >= 2 && questions.length >= 3) {
      nextDiversityHint = "Типы вопросов уже начали различаться. Попробуй добрать ещё один тип, которого пока не хватает, чтобы карта была шире.";
    }
    setMetaDiversityHint(nextDiversityHint);
  }, []);

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

  useEffect(() => () => cancelStream(), [cancelStream]);

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

  useEffect(() => {
    if (!metaMode) {
      setMetaSession(null);
      setMetaMessages([]);
      setMetaDetectedQuestionType(null);
      setMetaDetectedQuestionHint(null);
      setMetaDetectedAssumptionHint(null);
      setMetaDiversityHint(null);
      return;
    }
    let cancelled = false;
    setMetaLoading(true);
    fetchMetaTrainingStatus(sessionId)
      .then((payload) => {
        if (!cancelled) applyMetaPayload(payload);
      })
      .catch((error) => {
        if (cancelled) return;
        if (error?.status === 404) {
          setMetaSession(null);
          setMetaMessages([]);
        }
      })
      .finally(() => {
        if (!cancelled) setMetaLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [applyMetaPayload, metaMode, sessionId]);

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

  useEffect(() => {
    let cancelled = false;
    setTopicSuggestionsLoading(true);
    listTopics({ limit: 4, offset: 0, sort: "popular" })
      .then((data) => {
        if (!cancelled) setTopicSuggestions(Array.isArray(data?.items) ? data.items : []);
      })
      .catch(() => {
        if (!cancelled) setTopicSuggestions([]);
      })
      .finally(() => {
        if (!cancelled) setTopicSuggestionsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [authUser?.id]);

  /** После F5 или по ?conversation=: подтянуть сообщения выбранного диалога. */
  useEffect(() => {
    if (!authUser) return;
    if (useChatStore.getState().messages.length > 0) return;
    const urlConversationId = Number(searchParams.get("conversation"));
    const targetId =
      Number.isFinite(urlConversationId) && urlConversationId > 0 ? urlConversationId : conversationId;
    if (!targetId) return;
    let cancelled = false;
    (async () => {
      try {
        const detail = await fetchConversation(targetId);
        if (cancelled) return;
        setActiveConversation(detail.id, detail.session_key, normalizeConversationMessages(detail));
      } catch {
        useChatStore.getState().clearResume();
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [authUser, conversationId, searchParams, setActiveConversation]);

  useEffect(() => {
    if (!skillToast) return undefined;
    const t = setTimeout(() => setSkillToast(null), 5200);
    return () => clearTimeout(t);
  }, [skillToast]);

  useEffect(() => {
    const pending = pendingTurnsForSession(sessionId).length;
    if (pending > 0) {
      setSaveStatus({ kind: "queued", text: `Локально сохранено: ${pending}` });
    } else if (saveStatus?.kind === "queued") {
      setSaveStatus(null);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!authUser) {
      setConversationItems([]);
      return;
    }
    let cancelled = false;
    setConversationListLoading(true);
    listConversations(0, 12)
      .then((rows) => {
        if (!cancelled) setConversationItems(Array.isArray(rows) ? rows : []);
      })
      .catch(() => {
        if (!cancelled) setConversationItems([]);
      })
      .finally(() => {
        if (!cancelled) setConversationListLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [authUser?.id, conversationId, messages.length]);

  useEffect(() => {
    const urlConversationId = Number(searchParams.get("conversation"));
    if (conversationId != null) {
      if (urlConversationId !== conversationId) {
        const next = new URLSearchParams(searchParams);
        next.set("conversation", String(conversationId));
        setSearchParams(next, { replace: true });
      }
      return;
    }
    if (!Number.isFinite(urlConversationId) || urlConversationId <= 0) {
      return;
    }
    const next = new URLSearchParams(searchParams);
    next.delete("conversation");
    setSearchParams(next, { replace: true });
  }, [conversationId, searchParams, setSearchParams]);

  useEffect(() => {
    const assignmentId = Number(searchParams.get("assignment"));
    if (!authUser || !Number.isFinite(assignmentId) || assignmentId <= 0) {
      setAssignmentBanner(null);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const assignment = await fetchMyAssignment(assignmentId);
        if (!cancelled) setAssignmentBanner(assignment);
      } catch {
        if (!cancelled) setAssignmentBanner(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [authUser, searchParams]);

  const refreshRecommendation = useCallback(async () => {
    if (!authUser) return;
    try {
      const r = await getRecommendation();
      setRecommendation(r);
    } catch {
      /* ignore */
    }
  }, [authUser]);

  const openConversationById = useCallback(
    async (id) => {
      const detail = await fetchConversation(id);
      setFeedback(null);
      setMicroFeedback(null);
      setSimplerBanner(false);
      setIdleHint(false);
      setFallacyNotice(null);
      resetProfileClock();
      setActiveConversation(detail.id, detail.session_key, normalizeConversationMessages(detail));
    },
    [setActiveConversation],
  );

  const clearStreamingPlaceholder = useCallback(() => {
    if (!streamingMessageIdRef.current) return;
    removeMessagesFromId(streamingMessageIdRef.current);
    streamingMessageIdRef.current = null;
    streamStartedRef.current = false;
  }, [removeMessagesFromId]);

  const executeTurn = useCallback(
    async (turn, { fromQueue = false } = {}) => {
      const trimmed = (turn.message || "").trim();
      const effectiveSessionId = turn.sessionId || useChatStore.getState().sessionId;
      const effectiveConversationId =
        turn.conversationId ?? useChatStore.getState().conversationId;
      const attemptsBefore = useChatStore.getState().attempts;
      const requestId = streamRequestIdRef.current + 1;
      streamRequestIdRef.current = requestId;

      if (!fromQueue) {
        cancelStream();
        clearStreamingPlaceholder();
      }

      setLoading(true);
      setSaveStatus({
        kind: "saving",
        text: fromQueue ? "Синхронизирую…" : "Сохраняю…",
      });
      try {
        const payload = buildChatPayload(
          effectiveSessionId,
          trimmed,
          turn.action,
          effectiveConversationId,
          turn.clientMessageId,
          turn.assignmentId,
        );
        const data = fromQueue
          ? await postChat(
              effectiveSessionId,
              trimmed,
              turn.action,
              effectiveConversationId,
              turn.clientMessageId,
              turn.assignmentId,
            )
          : await sendStream(payload, {
              onMeta: (meta) => {
                if (requestId !== streamRequestIdRef.current) return;
                if (meta?.conversation_id != null && meta?.session_key) {
                  bindConversation(meta.conversation_id, meta.session_key);
                }
              },
              onChunk: (chunk) => {
                if (requestId !== streamRequestIdRef.current || typeof chunk !== "string") return;
                if (!streamingMessageIdRef.current) {
                  streamingMessageIdRef.current = addMessage("assistant", chunk, {
                    streaming: true,
                  });
                } else {
                  const current = useChatStore
                    .getState()
                    .messages.find((m) => m.id === streamingMessageIdRef.current);
                  updateMessageText(
                    streamingMessageIdRef.current,
                    `${current?.text || ""}${chunk}`,
                  );
                }
                streamStartedRef.current = true;
              },
            });
        if (!data) {
          throw new Error("Streaming completed without a final payload.");
        }
        if (!fromQueue && requestId !== streamRequestIdRef.current) {
          return null;
        }
        if (data.conversation_id != null && data.session_key) {
          bindConversation(data.conversation_id, data.session_key);
        }
        if (streamingMessageIdRef.current) {
          updateMessageText(streamingMessageIdRef.current, data.reply);
          updateMessageMeta(streamingMessageIdRef.current, { streaming: false });
        } else {
          addMessage("assistant", data.reply);
        }
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
        streamingMessageIdRef.current = null;
        streamStartedRef.current = false;
        removePendingTurn(turn.clientMessageId);

        if (data.pedagogy) {
          setTutorMode(data.pedagogy.mode || "friendly");
          setPedDifficulty(data.pedagogy.difficulty_level ?? 1);
          if (data.pedagogy.fallacy?.has_fallacy) {
            setFallacyNotice(data.pedagogy.fallacy);
          } else {
            setFallacyNotice(null);
          }
        }

        recordTurnOutcome({ userText: trimmed, action: turn.action });

        const dk = useChatStore.getState().dontKnowCount;
        if (dk >= 3) setSimplerBanner(true);

        const veryClose = shouldShowVeryClose({
          action: turn.action,
          attempts: data.attempts,
          mode: data.mode,
        });
        const almost = shouldShowAlmostUnderstood({
          action: turn.action,
          userText: trimmed,
          attempts: data.attempts,
          frustration: data.frustration,
          mode: data.mode,
        });
        const goodAttemptBanner =
          turn.action === "none" &&
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

        if (turn.action === "none" && trimmed) {
          const skipShortMicro = veryClose || almost || goodAttemptBanner;
          if (!skipShortMicro && isShortAnswer(trimmed, turn.action)) setMicroFeedback("short");
          else if (isStrongAnswer(trimmed, turn.action)) setMicroFeedback("good");
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

        const msgForGame = buildUserBubbleText(trimmed, turn.action);
        if (msgForGame || turn.action !== "none") {
          const gam = await postGamificationAction(effectiveSessionId, "user_response", {
            user_message: msgForGame,
            action: turn.action,
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

        const dc = authUser ? await fetchDailyChallengeMe() : await fetchDailyChallenge(effectiveSessionId);
        if (dc) setDailyCh(dc);
        if (authUser) void refreshRecommendation();

        const pendingLeft = pendingTurnsForSession(effectiveSessionId).length;
        setSaveStatus(
          pendingLeft > 0
            ? { kind: "queued", text: `Локально сохранено: ${pendingLeft}` }
            : { kind: "saved", text: "Сохранено" },
        );
        return data;
      } catch (e) {
        if (e?.name === "AbortError") {
          if (requestId === streamRequestIdRef.current) {
            clearStreamingPlaceholder();
          }
          return null;
        }
        if (e instanceof TypeError) {
          if (!fromQueue) {
            enqueuePendingTurn({
              ...turn,
              conversationId: effectiveConversationId,
              sessionId: effectiveSessionId,
              assignmentId: turn.assignmentId ?? null,
            });
            setSaveStatus({
              kind: "queued",
              text: `Локально сохранено: ${pendingTurnsForSession(effectiveSessionId).length}`,
            });
            return null;
          }
          setSaveStatus({
            kind: "queued",
            text: `Жду сеть. В очереди: ${pendingTurnsForSession(effectiveSessionId).length}`,
          });
          if (requestId === streamRequestIdRef.current) {
            clearStreamingPlaceholder();
          }
          return null;
        }
        const msg = e instanceof Error ? e.message : "Ошибка сервера";
        if (requestId === streamRequestIdRef.current) {
          clearStreamingPlaceholder();
        }
        if (!fromQueue && requestId === streamRequestIdRef.current) {
          addMessage("assistant", `Ошибка: ${msg}`);
        }
        if (requestId === streamRequestIdRef.current) {
          setSaveStatus({ kind: "error", text: "Не сохранено" });
        }
        return null;
      } finally {
        if (requestId === streamRequestIdRef.current) {
          streamStartedRef.current = false;
          setLoading(false);
        }
      }
    },
    [
      addMessage,
      authUser,
      bindConversation,
      cancelStream,
      clearStreamingPlaceholder,
      patchLastExchangeMessageIds,
      pushGamToast,
      recordTurnOutcome,
      refreshRecommendation,
      setFromServer,
      setLoading,
      sendStream,
      updateMessageMeta,
      updateMessageText,
    ],
  );

  const flushPendingTurns = useCallback(async () => {
    if (syncQueueRef.current) return;
    if (!navigator.onLine) return;
    const currentSessionId = useChatStore.getState().sessionId;
    const queue = pendingTurnsForSession(currentSessionId);
    if (queue.length === 0) return;
    syncQueueRef.current = true;
    try {
      for (const item of queue) {
        const ok = await executeTurn(item, { fromQueue: true });
        if (!ok) break;
      }
    } finally {
      syncQueueRef.current = false;
      const pendingLeft = pendingTurnsForSession(useChatStore.getState().sessionId).length;
      if (pendingLeft > 0) {
        setSaveStatus({ kind: "queued", text: `Локально сохранено: ${pendingLeft}` });
      }
    }
  }, [executeTurn]);

  const run = useCallback(
    async (message, action = "none") => {
      if (!canSend()) return;
      markSent();
      bumpActivity();

      const trimmed = message.trim();
      const userText = buildUserBubbleText(trimmed, action);
      const clientMessageId = createClientMessageId();

      if (userText) {
        addMessage("user", userText, { id: `local-${clientMessageId}` });
      }
      if (action !== "none") {
        resetDontKnowCount();
        setSimplerBanner(false);
      }

      setFeedback(null);
      setMicroFeedback(null);

      await executeTurn({
        message: trimmed,
        action,
        clientMessageId,
        sessionId: useChatStore.getState().sessionId,
        conversationId: useChatStore.getState().conversationId,
        assignmentId: Number(searchParams.get("assignment")) || null,
      });
    },
    [addMessage, bumpActivity, canSend, executeTurn, markSent, resetDontKnowCount, searchParams],
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

  useEffect(() => {
    void flushPendingTurns();
  }, [flushPendingTurns, sessionId]);

  useEffect(() => {
    const onOnline = () => {
      void flushPendingTurns();
    };
    window.addEventListener("online", onOnline);
    return () => window.removeEventListener("online", onOnline);
  }, [flushPendingTurns]);

  const onNewSession = () => {
    if (confirm("Начать новую сессию? Прогресс этой темы сбросится.")) {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.delete("conversation");
        return next;
      });
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
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.delete("conversation");
        return next;
      });
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
      await openConversationById(last.id);
      await refreshRecommendation();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось открыть диалог");
    }
  }, [openConversationById, recommendation, refreshRecommendation]);

  const onNewRecommendedDialog = useCallback(async () => {
    const title = (recommendation?.recommended_topic || "").trim() || "Новая тема";
    try {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        next.delete("conversation");
        return next;
      });
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
  }, [recommendation, refreshRecommendation, setActiveConversation, setSearchParams]);

  const handleStartTopic = useCallback(
    async (topic) => {
      if (!authUser) {
        navigate("/login", { state: { from: "/app" } });
        return;
      }
      if (topic.is_premium && !topic.can_start) {
        setTopicUpgradeOpen(true);
        return;
      }
      setStartingTopicId(topic.id);
      try {
        const started = await startTopic(topic.id);
        const next = new URLSearchParams(searchParams);
        next.set("conversation", String(started.conversation_id));
        setSearchParams(next);
        setFeedback(null);
        setMicroFeedback(null);
        setSimplerBanner(false);
        setIdleHint(false);
        setFallacyNotice(null);
        resetProfileClock();
        setActiveConversation(
          started.conversation_id,
          started.session_key,
          messagesFromTopicStart(started),
        );
        void postGamificationAction(started.session_key, "new_dialog", {});
        await refreshRecommendation();
      } catch (e) {
        if (e?.status === 402) {
          setTopicUpgradeOpen(true);
        } else {
          alert(e instanceof Error ? e.message : "Не удалось начать тему");
        }
      } finally {
        setStartingTopicId(null);
      }
    },
    [authUser, navigate, refreshRecommendation, searchParams, setActiveConversation, setSearchParams],
  );

  const dismissPedagogyIntro = useCallback(() => {
    localStorage.setItem("socrates_pedagogy_intro_v1", "1");
    setPedagogyIntro(false);
  }, []);

  const openMetaMode = useCallback(() => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.set("mode", "meta");
      return next;
    });
  }, [setSearchParams]);

  const exitMetaMode = useCallback(() => {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev);
      next.delete("mode");
      return next;
    });
    setMetaSession(null);
    setMetaMessages([]);
    setMetaDetectedQuestionType(null);
    setMetaDetectedQuestionHint(null);
    setMetaDetectedAssumptionHint(null);
    setMetaDiversityHint(null);
  }, [setSearchParams]);

  const handleMetaStart = useCallback(async () => {
    setMetaLoading(true);
    try {
      openMetaMode();
      const payload = await startMetaTraining(sessionId);
      applyMetaPayload(payload);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось запустить мета-тренировку");
    } finally {
      setMetaLoading(false);
    }
  }, [applyMetaPayload, openMetaMode, sessionId]);

  const handleMetaSend = useCallback(async (text) => {
    setMetaLoading(true);
    try {
      const payload = await postMetaTrainingMessage(sessionId, text);
      applyMetaPayload(payload);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось отправить сообщение");
    } finally {
      setMetaLoading(false);
    }
  }, [applyMetaPayload, sessionId]);

  const handleMetaSwitchFrame = useCallback(async (text) => {
    setMetaLoading(true);
    try {
      const payload = await switchMetaTrainingFrame(sessionId, text);
      applyMetaPayload(payload);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось сменить рамку");
    } finally {
      setMetaLoading(false);
    }
  }, [applyMetaPayload, sessionId]);

  const handleMetaAdvancePhase = useCallback(async () => {
    setMetaLoading(true);
    try {
      const payload = await advanceMetaTrainingPhase(sessionId);
      applyMetaPayload(payload);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось переключить фазу");
    } finally {
      setMetaLoading(false);
    }
  }, [applyMetaPayload, sessionId]);

  const handleMetaEnd = useCallback(async (summary, confidence) => {
    setMetaLoading(true);
    try {
      const payload = await endMetaTraining(sessionId, summary, confidence);
      applyMetaPayload(payload);
      const progress = authUser ? await fetchGamificationProgressMe() : await fetchGamificationProgress(sessionId);
      if (progress) {
        useChatStore.getState().applyGamificationProgress(progress);
        setWisdomBump((k) => k + 1);
      }
    } catch (e) {
      alert(e instanceof Error ? e.message : "Не удалось завершить мета-тренировку");
    } finally {
      setMetaLoading(false);
    }
  }, [applyMetaPayload, authUser, sessionId]);

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
      <PremiumTopicsModal open={topicUpgradeOpen} onClose={() => setTopicUpgradeOpen(false)} />
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
        statusSlot={<SaveStatusBadge status={saveStatus} />}
        dailyChallengeHeaderSlot={
          gamificationLoaded && dailyCh?.challenge_text ? (
            <button
              type="button"
              onClick={() => setDailyModalOpen(true)}
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-violet-400/50 bg-violet-50 text-lg lg:hidden dark:border-violet-600/50 dark:bg-violet-950/50"
              aria-label="Вызов дня"
              title="Вызов дня"
            >
              <span aria-hidden>🎯</span>
            </button>
          ) : null
        }
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
      {assignmentBanner ? (
        <div className="mx-4 mt-2 rounded-xl border border-violet-400/40 bg-violet-50/90 px-4 py-3 text-sm text-violet-950 dark:border-violet-700/50 dark:bg-violet-950/30 dark:text-violet-100">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-medium">{assignmentBanner.title}</p>
              <p className="mt-1 text-violet-900/80 dark:text-violet-100/80">{assignmentBanner.prompt}</p>
            </div>
            {messages.length === 0 ? (
              <button
                type="button"
                onClick={() => run(assignmentBanner.prompt, "none")}
                className="rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-500"
              >
                Начать задание
              </button>
            ) : null}
          </div>
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
      {!metaMode || !metaSession ? (
        <MetaTrainingPanel
          session={metaSession}
          onStart={handleMetaStart}
          onExit={exitMetaMode}
          loading={metaLoading}
          detectedQuestionType={metaDetectedQuestionType}
          detectedQuestionHint={metaDetectedQuestionHint}
          detectedAssumptionHint={metaDetectedAssumptionHint}
          diversityHint={metaDiversityHint}
        />
      ) : null}
      {!metaMode ? (
        <div className="mx-4 mt-3 rounded-3xl border border-slate-200 bg-white/90 p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900/45">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-700 dark:text-cyan-300">
                Популярные темы
              </p>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                Быстрый старт для осмысленного разговора, если не хочется придумывать тему с нуля.
              </p>
            </div>
            <Link to="/topics" className="text-sm font-medium text-cyan-700 underline dark:text-cyan-400">
              Вся библиотека
            </Link>
          </div>
          {topicSuggestionsLoading ? (
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, idx) => (
                <div
                  key={idx}
                  className="h-48 animate-pulse rounded-3xl border border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950/40"
                />
              ))}
            </div>
          ) : topicSuggestions.length > 0 ? (
            <div className="mt-4 grid gap-3 lg:grid-cols-4">
              {topicSuggestions.map((topic) => (
                <TopicCard
                  key={topic.id}
                  topic={topic}
                  compact
                  starting={startingTopicId === topic.id}
                  onStart={handleStartTopic}
                  onOpen={() => navigate("/topics")}
                />
              ))}
            </div>
          ) : null}
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
          <Link to="/topics" className="text-cyan-700 hover:underline dark:text-cyan-400">
            Темы
          </Link>
          {String(authUser.role || "").toLowerCase() === "admin" ? (
            <Link to="/admin" className="text-amber-700 hover:underline dark:text-amber-400">
              Админ-панель
            </Link>
          ) : null}
          {["admin", "educator"].includes(String(authUser.role || "").toLowerCase()) ? (
            <Link to="/admin/topics" className="text-amber-700 hover:underline dark:text-amber-400">
              Управление темами
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
      <FallacyNotification fallacy={fallacyNotice} onDismiss={() => setFallacyNotice(null)} />

      <div className="flex min-h-0 min-w-0 flex-1 flex-col lg:flex-row">
        <div className="flex min-h-0 min-w-0 flex-1 flex-col lg:min-w-[400px]">
          {metaMode && metaSession ? (
            <MetaTrainingPanel
              session={metaSession}
              onStart={handleMetaStart}
              onExit={exitMetaMode}
              loading={metaLoading}
              detectedQuestionType={metaDetectedQuestionType}
              detectedQuestionHint={metaDetectedQuestionHint}
              detectedAssumptionHint={metaDetectedAssumptionHint}
              diversityHint={metaDiversityHint}
              compact
            />
          ) : null}
          {!metaMode ? <ModeIndicator mode={mode} attempts={attempts} frustration={frustration} /> : null}
          {!metaMode ? <UserStateBadge type={userType} /> : null}
          {!metaMode ? <UserMemoryPanel memory={memory} className="mx-4 mt-0 lg:hidden" /> : null}
          {!metaMode ? (
            <div className="mx-4 lg:hidden" data-tour="skills-mobile">
              <SkillTree skillTree={skillTree} topic={topic} />
            </div>
          ) : null}
          {!metaMode ? <ThinkingPanel profile={memory.thinking_profile} className="mx-4 lg:hidden" /> : null}
          {!metaMode ? (
            <AssistPanel
              level={frustrationLevel}
              loading={loading}
              onExampleHint={onRequestExample}
              onExplain={onGiveUp}
              conversationKey={conversationId != null ? `conversation_${conversationId}` : `session_${sessionId}`}
            />
          ) : null}
          <ChatWindow
            ref={chatScrollRef}
            messages={metaMode ? metaMessages : messages}
            loading={metaMode ? metaLoading : loading}
            feedback={feedback}
            microFeedback={microFeedback}
            simplerBanner={simplerBanner}
            idleHint={idleHint}
            assistLevel={frustrationLevel}
            userLabel={authUser?.full_name || authUser?.email || "Я"}
            canEditMessages={!!authUser}
            onEditMessage={handleEditMessage}
            onDeleteMessage={handleDeleteMessage}
            showTypingIndicator={showTypingFromSettings && !streamStartedRef.current}
            onIdleHintDismiss={() => {
              setIdleHint(false);
              bumpActivity();
            }}
          />
          {metaMode ? (
            <MetaTrainingComposer
              phase={metaSession?.phase || "orientation"}
              loading={metaLoading}
              onSend={handleMetaSend}
              onSwitchFrame={handleMetaSwitchFrame}
              onAdvancePhase={handleMetaAdvancePhase}
              onEnd={handleMetaEnd}
            />
          ) : (
            <InputBox
              userType={userType}
              onSend={onSend}
              loading={loading}
              interruptibleLoading={streamInFlight}
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
          )}
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
          conversationListSlot={
            authUser ? (
              <ConversationList
                items={conversationItems}
                activeId={conversationId}
                loading={conversationListLoading}
                onSelect={(id) => {
                  const next = new URLSearchParams(searchParams);
                  next.set("conversation", String(id));
                  setSearchParams(next);
                  void openConversationById(id);
                }}
              />
            ) : null
          }
          dailyChallengeSlot={
            <DailyChallengeCompact
              text={dailyCh?.challenge_text}
              completed={!!dailyCh?.completed}
              loading={!gamificationLoaded}
              onOpenDetails={() => setDailyModalOpen(true)}
            />
          }
        />
      </div>
      <DailyChallengeModal
        open={dailyModalOpen}
        onClose={() => setDailyModalOpen(false)}
        text={dailyCh?.challenge_text}
        completed={!!dailyCh?.completed}
        loading={!gamificationLoaded}
      />
      <OnboardingTour
        enabled={!!authUser && !!accountSettings && accountSettings.has_seen_onboarding === false}
        onFinished={() =>
          setAccountSettings((s) => (s ? { ...s, has_seen_onboarding: true } : s))
        }
      />
    </div>
  );
}

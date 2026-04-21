import { create } from "zustand";

import { getToken } from "../api/client.js";
import { fetchMemoryProfile } from "../api/userApi.js";

/** Последний диалог в БД: после F5 восстанавливаем session_key и геймификацию/педагогику из Redis. */
const RESUME_KEY = "socrates_chat_resume";

/** Снимок геймификации (аккаунт с JWT): переживает смену диалога и размонтирование чата. */
const GAMIFICATION_LS = "socrates_gamification_public_v1";

export const XP_PER_ATTEMPT = 5;

function readGamificationSnapshot() {
  try {
    const raw = localStorage.getItem(GAMIFICATION_LS);
    if (!raw) return null;
    const o = JSON.parse(raw);
    if (!o || typeof o !== "object") return null;
    const wisdom_points = Number(o.wisdom_points);
    const level = Number(o.level);
    const total_user_turns = Number(o.total_user_turns);
    const logic_good_streak = Number(o.logic_good_streak);
    const achievements = Array.isArray(o.achievements) ? o.achievements : [];
    if (!Number.isFinite(wisdom_points) && !Number.isFinite(total_user_turns)) return null;
    return {
      wisdom_points: Number.isFinite(wisdom_points) ? wisdom_points : 0,
      level: Number.isFinite(level) && level >= 1 ? level : 1,
      achievements,
      total_user_turns: Number.isFinite(total_user_turns) ? total_user_turns : 0,
      logic_good_streak: Number.isFinite(logic_good_streak) ? logic_good_streak : 0,
    };
  } catch {
    return null;
  }
}

function writeGamificationSnapshot(snap) {
  try {
    if (snap && typeof snap === "object") {
      localStorage.setItem(GAMIFICATION_LS, JSON.stringify(snap));
    }
  } catch {
    /* ignore */
  }
}

function clearGamificationSnapshot() {
  try {
    localStorage.removeItem(GAMIFICATION_LS);
  } catch {
    /* ignore */
  }
}

function readResumeSync() {
  try {
    const raw = localStorage.getItem(RESUME_KEY);
    if (!raw) return { conversationId: null, sessionKey: null };
    const o = JSON.parse(raw);
    const conversationId = Number(o.conversationId);
    const sessionKey = typeof o.sessionKey === "string" ? o.sessionKey : null;
    if (Number.isFinite(conversationId) && conversationId > 0 && sessionKey) {
      return { conversationId, sessionKey };
    }
  } catch {
    /* ignore */
  }
  return { conversationId: null, sessionKey: null };
}

function getOrCreateSessionId(resumeSessionKey) {
  const k = "socrates_session_id";
  if (resumeSessionKey) {
    localStorage.setItem(k, resumeSessionKey);
    return resumeSessionKey;
  }
  let id = localStorage.getItem(k);
  if (!id) {
    id =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `sess_${Date.now()}_${Math.random().toString(36).slice(2)}`;
    localStorage.setItem(k, id);
  }
  return id;
}

const _resume = readResumeSync();
const _initialSessionId = getOrCreateSessionId(_resume.sessionKey);
const _storedGamification = getToken() ? readGamificationSnapshot() : null;
const _initialXp = _storedGamification
  ? _storedGamification.total_user_turns * XP_PER_ATTEMPT
  : 0;
const _initialStreak = _storedGamification ? _storedGamification.logic_good_streak : 0;

const EMPTY_MEMORY = {
  topics: [],
  mistakes: [],
  progress: {},
  user_type: "lazy",
  skill_status: {},
  thinking_profile: {},
};

function _normalizeUserType(raw, fallback = "lazy") {
  if (typeof raw === "string" && ["lazy", "anxious", "thinker"].includes(raw)) return raw;
  return fallback;
}

/**
 * Ответ /chat для аккаунта иногда приходит с пустыми topics/mistakes или без полей (undefined → [] в старом коде).
 * Память в Redis общая на user.id — не затираем накопленное при смене диалога и гонках с refresh.
 */
function mergeAuthMemoryFromChatPayload(prev, incoming) {
  const p = prev && typeof prev === "object" ? prev : { ...EMPTY_MEMORY };
  const inc = incoming && typeof incoming === "object" ? incoming : null;
  if (!inc) return { ...p };

  const pickList = (key) => {
    const pi = inc[key];
    const pp = p[key];
    const havePrev = Array.isArray(pp) && pp.length > 0;
    if (!Array.isArray(pi)) return havePrev ? pp : [];
    if (pi.length > 0) return pi;
    return havePrev ? pp : pi;
  };

  const prevProg = p.progress && typeof p.progress === "object" ? p.progress : {};
  const incProg = inc.progress && typeof inc.progress === "object" ? inc.progress : null;
  const progress = incProg ? { ...prevProg, ...incProg } : prevProg;

  const ut = _normalizeUserType(inc.user_type, _normalizeUserType(p.user_type));

  const prevSk = p.skill_status && typeof p.skill_status === "object" ? p.skill_status : {};
  const incSk = inc.skill_status && typeof inc.skill_status === "object" ? inc.skill_status : {};
  const skill_status = { ...prevSk, ...incSk };

  const prevTp =
    p.thinking_profile && typeof p.thinking_profile === "object" ? p.thinking_profile : {};
  const incTp =
    inc.thinking_profile && typeof inc.thinking_profile === "object" ? inc.thinking_profile : {};
  const thinking_profile = { ...prevTp, ...incTp };

  return {
    topics: pickList("topics"),
    mistakes: pickList("mistakes"),
    progress,
    user_type: ut,
    skill_status,
    thinking_profile,
  };
}

export const useChatStore = create((set, get) => ({
  messages: [],
  mode: "question",
  loading: false,
  attempts: 0,
  frustration: 0,
  frustrationLevel: 0,
  userType: "lazy",
  memory: { ...EMPTY_MEMORY },
  skillTree: null,
  topic: "",
  lastSendAt: 0,
  sessionId: _initialSessionId,
  /** ID диалога в БД (только для авторизованных) */
  conversationId: _resume.conversationId,

  xp: _initialXp,
  streak: _initialStreak,
  dontKnowCount: 0,
  /** Снимок /gamification/progress + localStorage при JWT (правая панель не «падает» при смене диалога). */
  gamificationPublic: _storedGamification,

  clearGamification: () => {
    clearGamificationSnapshot();
    set({
      gamificationPublic: null,
      xp: 0,
      streak: 0,
    });
  },

  /**
   * Подтянуть долговременную память тьютора с /users/me/memory-profile (аккаунт).
   * Поля, которых нет в ответе (старый бэкенд), не затираем.
   */
  hydrateTutorMemoryFromProfile: (mp) => {
    if (!mp || typeof mp !== "object") return;
    const rawUt = mp.user_type;
    if (typeof rawUt !== "string" || !["lazy", "anxious", "thinker"].includes(rawUt)) return;
    set((s) => ({
      userType: rawUt,
      memory: {
        topics: Array.isArray(mp.topics) ? mp.topics : s.memory.topics,
        mistakes: Array.isArray(mp.mistakes) ? mp.mistakes : s.memory.mistakes,
        progress:
          mp.progress && typeof mp.progress === "object" ? mp.progress : s.memory.progress,
        user_type: rawUt,
        skill_status:
          mp.skill_status && typeof mp.skill_status === "object"
            ? mp.skill_status
            : s.memory.skill_status,
        thinking_profile:
          mp.thinking_profile && typeof mp.thinking_profile === "object"
            ? mp.thinking_profile
            : s.memory.thinking_profile,
      },
    }));
  },

  /** Долговременная память из Redis (аккаунт) — тот же источник, что в /chat. */
  refreshTutorMemoryFromServer: async () => {
    if (!getToken()) return;
    try {
      const mp = await fetchMemoryProfile();
      if (mp && typeof mp === "object" && mp.user_type) {
        get().hydrateTutorMemoryFromProfile(mp);
      }
    } catch {
      /* сеть / 401 */
    }
  },

  /**
   * Слить стор и localStorage по максимуму (JWT).
   * Раньше при truthy, но нулевом gamificationPublic гидратация не срабатывала — панель «обнулялась».
   */
  mergeGamificationFromPersisted: () => {
    if (!getToken()) return;
    const ls = readGamificationSnapshot();
    const cur = get().gamificationPublic;
    const empty = {
      wisdom_points: 0,
      level: 1,
      achievements: [],
      total_user_turns: 0,
      logic_good_streak: 0,
    };
    const a = { ...empty, ...(cur && typeof cur === "object" ? cur : {}) };
    const b = { ...empty, ...(ls && typeof ls === "object" ? ls : {}) };
    const merged = {
      wisdom_points: Math.max(a.wisdom_points, b.wisdom_points),
      total_user_turns: Math.max(a.total_user_turns, b.total_user_turns),
      logic_good_streak: Math.max(a.logic_good_streak, b.logic_good_streak),
      achievements: [...new Set([...(a.achievements || []), ...(b.achievements || [])])],
    };
    merged.level = Math.max(1, Math.floor(merged.wisdom_points / 150) + 1);
    writeGamificationSnapshot(merged);
    set({
      gamificationPublic: merged,
      xp: merged.total_user_turns * XP_PER_ATTEMPT,
      streak: merged.logic_good_streak,
    });
  },

  setFromServer: (payload) =>
    set((s) => {
      const authed = !!getToken();
      let memory = s.memory;
      if (payload.memory && typeof payload.memory === "object") {
        memory = authed
          ? mergeAuthMemoryFromChatPayload(s.memory, payload.memory)
          : {
              topics: Array.isArray(payload.memory.topics) ? payload.memory.topics : [],
              mistakes: Array.isArray(payload.memory.mistakes) ? payload.memory.mistakes : [],
              progress:
                payload.memory.progress && typeof payload.memory.progress === "object"
                  ? payload.memory.progress
                  : {},
              user_type: _normalizeUserType(payload.memory.user_type),
              skill_status:
                payload.memory.skill_status && typeof payload.memory.skill_status === "object"
                  ? payload.memory.skill_status
                  : {},
              thinking_profile:
                payload.memory.thinking_profile &&
                typeof payload.memory.thinking_profile === "object"
                  ? payload.memory.thinking_profile
                  : {},
            };
      }
      return {
        mode: payload.mode,
        attempts: payload.attempts,
        frustration: payload.frustration,
        frustrationLevel:
          typeof payload.frustration_level === "number"
            ? payload.frustration_level
            : Math.min(3, payload.frustration ?? 0),
        userType:
          payload.user_type && ["lazy", "anxious", "thinker"].includes(payload.user_type)
            ? payload.user_type
            : "lazy",
        memory,
        skillTree:
          payload.skill_tree && typeof payload.skill_tree === "object"
            ? payload.skill_tree
            : s.skillTree,
        topic: payload.topic || "",
      };
    }),

  /**
   * Локально только «не знаю»; XP и streak берутся из Redis геймификации (см. applyGamificationProgressToStore).
   */
  recordTurnOutcome: ({ userText, action }) => {
    const text = (userText || "").trim();
    const low = text.toLowerCase();
    const isDontKnow = action === "none" && /не знаю|хз|без понятия/.test(low);

    set((s) => {
      let dontKnowCount = s.dontKnowCount;
      if (action === "none" && text && isDontKnow) {
        dontKnowCount += 1;
      }
      return { dontKnowCount };
    });
  },

  /** Синхронизация геймификации с бэкендом (для аккаунта — общий прогресс независимо от session_id). */
  applyGamificationProgress: (p) => {
    if (!p || typeof p !== "object") return;
    const authed = !!getToken();
    const ls = authed ? readGamificationSnapshot() : null;
    const cur = get().gamificationPublic;
    let turns = Number(p.total_user_turns);
    let lg = Number(p.logic_good_streak);
    let wp = Number(p.wisdom_points);
    if (authed) {
      const curTurns = cur && typeof cur === "object" ? Number(cur.total_user_turns) || 0 : 0;
      const curLg = cur && typeof cur === "object" ? Number(cur.logic_good_streak) || 0 : 0;
      const curWp = cur && typeof cur === "object" ? Number(cur.wisdom_points) || 0 : 0;
      const lsTurns = ls && typeof ls === "object" ? Number(ls.total_user_turns) || 0 : 0;
      const lsLg = ls && typeof ls === "object" ? Number(ls.logic_good_streak) || 0 : 0;
      const lsWp = ls && typeof ls === "object" ? Number(ls.wisdom_points) || 0 : 0;
      turns = Math.max(Number.isFinite(turns) ? turns : 0, curTurns, lsTurns);
      lg = Math.max(Number.isFinite(lg) ? lg : 0, curLg, lsLg);
      wp = Math.max(Number.isFinite(wp) ? wp : 0, curWp, lsWp);
    } else {
      turns = Number.isFinite(turns) ? turns : 0;
      lg = Number.isFinite(lg) ? lg : 0;
      wp = Number.isFinite(wp) ? wp : 0;
    }
    const lvl = Math.max(1, Math.floor(wp / 150) + 1);
    const achP = Array.isArray(p.achievements) ? p.achievements : [];
    const achC = authed && cur && typeof cur === "object" && Array.isArray(cur.achievements)
      ? cur.achievements
      : [];
    const achLs = authed && ls && typeof ls === "object" && Array.isArray(ls.achievements)
      ? ls.achievements
      : [];
    const achievements =
      authed ? [...new Set([...achLs, ...achC, ...achP])] : [...achP];
    const snap = {
      wisdom_points: wp,
      level: lvl,
      achievements,
      total_user_turns: turns,
      logic_good_streak: lg,
    };
    if (authed) {
      writeGamificationSnapshot(snap);
    }
    set({
      xp: turns * XP_PER_ATTEMPT,
      streak: lg,
      gamificationPublic: snap,
    });
  },

  resetDontKnowCount: () => set({ dontKnowCount: 0 }),

  addMessage: (role, text, meta = {}) => {
    const id =
      meta.id ||
      (typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : `m_${Date.now()}_${Math.random().toString(36).slice(2)}`);
    const createdAt = meta.createdAt ?? Date.now();
    set((s) => ({
      messages: [
        ...s.messages,
        {
          id,
          role,
          text,
          createdAt,
        },
      ],
    }));
    return id;
  },

  /** После POST /chat: привязать id сообщений из БД к последней паре user+assistant. */
  patchLastExchangeMessageIds: ({ userId, assistantId }) =>
    set((s) => {
      const msgs = [...s.messages];
      const isAssistant = (r) => r === "assistant" || r === "tutor";
      for (let i = msgs.length - 1; i >= 0; i--) {
        if (isAssistant(msgs[i].role)) {
          msgs[i] = { ...msgs[i], id: `db-${assistantId}` };
          if (i > 0 && msgs[i - 1].role === "user") {
            msgs[i - 1] = { ...msgs[i - 1], id: `db-${userId}` };
          }
          break;
        }
      }
      return { messages: msgs };
    }),

  updateMessageText: (messageId, text) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === messageId ? { ...m, text } : m)),
    })),

  /** Удалить сообщение с данным id и все ниже (уже после ответа сервера). */
  removeMessagesFromId: (messageId) =>
    set((s) => {
      const idx = s.messages.findIndex((m) => m.id === messageId);
      if (idx < 0) return s;
      return { messages: s.messages.slice(0, idx) };
    }),

  setLoading: (loading) => set({ loading }),

  resetSession: () => {
    localStorage.removeItem("socrates_session_id");
    localStorage.removeItem(RESUME_KEY);
    const loggedIn = !!getToken();
    const keepGam = loggedIn ? get().gamificationPublic : null;
    const keepXp = loggedIn ? get().xp : 0;
    const keepStreak = loggedIn ? get().streak : 0;
    if (!loggedIn) {
      clearGamificationSnapshot();
    }
    set({
      messages: [],
      mode: "question",
      attempts: 0,
      frustration: 0,
      frustrationLevel: 0,
      userType: "lazy",
      topic: "",
      sessionId: getOrCreateSessionId(null),
      xp: loggedIn ? keepXp : 0,
      streak: loggedIn ? keepStreak : 0,
      gamificationPublic: loggedIn ? keepGam : null,
      dontKnowCount: 0,
      memory: { ...EMPTY_MEMORY },
      skillTree: null,
      conversationId: null,
    });
  },

  /** Выход из аккаунта: не тянуть чужой диалог в гостевой сессии. */
  clearResume: () => {
    localStorage.removeItem(RESUME_KEY);
    set({ conversationId: null });
  },

  canSend: () => {
    const now = Date.now();
    return !get().loading && now - get().lastSendAt > 800;
  },

  markSent: () => set({ lastSendAt: Date.now() }),

  /**
   * Привязать чат к диалогу в БД (session_key = sessionId для Redis).
   * @param {number|null} conversationId
   * @param {string} sessionId
   * @param {{ id: string, role: string, text: string }[]} [initialMessages]
   */
  setActiveConversation: (conversationId, sessionId, initialMessages = []) => {
    localStorage.setItem("socrates_session_id", sessionId);
    if (conversationId != null) {
      localStorage.setItem(
        RESUME_KEY,
        JSON.stringify({ conversationId, sessionKey: sessionId }),
      );
    } else {
      localStorage.removeItem(RESUME_KEY);
    }
    set((s) => ({
      conversationId,
      sessionId,
      messages: initialMessages,
      mode: "question",
      attempts: 0,
      frustration: 0,
      frustrationLevel: 0,
      topic: "",
      skillTree: null,
      memory: s.memory,
    }));
    if (getToken()) {
      get().mergeGamificationFromPersisted();
      if (conversationId != null) {
        void get().refreshTutorMemoryFromServer();
      }
    }
  },

  bindConversation: (conversationId, sessionId) => {
    localStorage.setItem("socrates_session_id", sessionId);
    if (conversationId != null) {
      localStorage.setItem(
        RESUME_KEY,
        JSON.stringify({ conversationId, sessionKey: sessionId }),
      );
    } else {
      localStorage.removeItem(RESUME_KEY);
    }
    set({ conversationId, sessionId });
  },
}));

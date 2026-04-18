import { create } from "zustand";

function getOrCreateSessionId() {
  const k = "socrates_session_id";
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

const XP_PER_ATTEMPT = 5;

export const useChatStore = create((set, get) => ({
  messages: [],
  mode: "question",
  loading: false,
  attempts: 0,
  frustration: 0,
  frustrationLevel: 0,
  userType: "lazy",
  topic: "",
  lastSendAt: 0,
  sessionId: getOrCreateSessionId(),

  xp: 0,
  streak: 0,
  dontKnowCount: 0,

  setFromServer: (payload) =>
    set({
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
      topic: payload.topic || "",
    }),

  /** После успешного ответа API: XP, streak, счётчик «не знаю». */
  recordTurnOutcome: ({ userText, action }) => {
    const text = (userText || "").trim();
    const low = text.toLowerCase();
    const isDontKnow = action === "none" && /не знаю|хз|без понятия/.test(low);
    const isShort = action === "none" && text.length > 0 && text.length < 15;
    const isStrong = action === "none" && text.length >= 35;

    set((s) => {
      let streak = s.streak;
      let dontKnowCount = s.dontKnowCount;

      if (action === "none" && text) {
        if (isDontKnow) {
          dontKnowCount += 1;
          streak = 0;
        } else if (isShort) {
          streak = 0;
        } else if (isStrong) {
          streak += 1;
        }
      } else if (action === "hint" || action === "give_up") {
        streak = Math.max(0, streak);
      }

      return {
        xp: s.xp + XP_PER_ATTEMPT,
        streak,
        dontKnowCount,
      };
    });
  },

  resetDontKnowCount: () => set({ dontKnowCount: 0 }),

  addMessage: (role, text) =>
    set((s) => ({
      messages: [
        ...s.messages,
        {
          id:
            typeof crypto !== "undefined" && crypto.randomUUID
              ? crypto.randomUUID()
              : `m_${Date.now()}_${Math.random().toString(36).slice(2)}`,
          role,
          text,
        },
      ],
    })),

  setLoading: (loading) => set({ loading }),

  resetSession: () => {
    localStorage.removeItem("socrates_session_id");
    set({
      messages: [],
      mode: "question",
      attempts: 0,
      frustration: 0,
      frustrationLevel: 0,
      userType: "lazy",
      topic: "",
      sessionId: getOrCreateSessionId(),
      xp: 0,
      streak: 0,
      dontKnowCount: 0,
    });
  },

  canSend: () => {
    const now = Date.now();
    return !get().loading && now - get().lastSendAt > 800;
  },

  markSent: () => set({ lastSendAt: Date.now() }),
}));

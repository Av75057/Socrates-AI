import { create } from "zustand";
import NetInfo from "@react-native-community/netinfo";
import { ChatMessage, ConversationSummary } from "../types";
import { fetchConversation, listConversations } from "../api/user";
import { postChat } from "../api/chat";
import { loadJson, saveJson } from "../services/storage";

const OFFLINE_QUEUE_KEY = "mobile_chat_queue";
const RECENT_MESSAGES_KEY = "mobile_recent_messages";

type PendingTurn = {
  sessionId: string;
  conversationId?: number | null;
  clientMessageId: string;
  message: string;
  assignmentId?: number | null;
};

type ChatState = {
  sessionId: string;
  conversationId: number | null;
  conversationTitle: string;
  messages: ChatMessage[];
  conversations: ConversationSummary[];
  loading: boolean;
  offline: boolean;
  bootstrap: () => Promise<void>;
  setConversation: (conversationId: number | null, sessionId: string, messages?: ChatMessage[]) => void;
  openConversation: (conversationId: number) => Promise<void>;
  startNewConversation: () => void;
  appendMessage: (message: ChatMessage) => void;
  sendMessage: (text: string, assignmentId?: number | null) => Promise<void>;
  loadConversations: () => Promise<void>;
  flushQueue: () => Promise<void>;
};

function randomId(prefix: string) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2)}`;
}

export const useChatStore = create<ChatState>((set, get) => ({
  sessionId: randomId("sess"),
  conversationId: null,
  conversationTitle: "Новый диалог",
  messages: [],
  conversations: [],
  loading: false,
  offline: false,
  bootstrap: async () => {
    const net = await NetInfo.fetch();
    set({ offline: !net.isConnected });
    const cached = await loadJson<ChatMessage[]>(RECENT_MESSAGES_KEY, []);
    if (cached.length) set({ messages: cached });
  },
  setConversation: (conversationId, sessionId, messages = []) => {
    set({ conversationId, sessionId, messages });
    void saveJson(RECENT_MESSAGES_KEY, messages.slice(-50));
  },
  openConversation: async (conversationId) => {
    const detail = await fetchConversation(conversationId);
    const messages = (detail.messages || []).map((m: any) => ({
      id: `db-${m.id}`,
      role: m.role === "tutor" ? "assistant" : "user",
      text: m.content,
      createdAt: m.created_at ? new Date(m.created_at).getTime() : Date.now()
    })) as ChatMessage[];
    set({
      conversationId: detail.id,
      sessionId: detail.session_key,
      conversationTitle: detail.title || "Диалог",
      messages
    });
    await saveJson(RECENT_MESSAGES_KEY, messages.slice(-50));
  },
  startNewConversation: () => {
    const sessionId = randomId("sess");
    set({
      sessionId,
      conversationId: null,
      conversationTitle: "Новый диалог",
      messages: []
    });
    void saveJson(RECENT_MESSAGES_KEY, []);
  },
  appendMessage: (message) => {
    const next = [...get().messages, message].slice(-50);
    set({ messages: next });
    void saveJson(RECENT_MESSAGES_KEY, next);
  },
  loadConversations: async () => {
    try {
      const conversations = await listConversations();
      set({ conversations });
    } catch {
      set({ conversations: [] });
    }
  },
  sendMessage: async (text, assignmentId = null) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    const clientMessageId = randomId("client");
    const userMessage: ChatMessage = {
      id: clientMessageId,
      role: "user",
      text: trimmed,
      createdAt: Date.now()
    };
    get().appendMessage(userMessage);
    const state = await NetInfo.fetch();
    if (!state.isConnected) {
      const queue = await loadJson<PendingTurn[]>(OFFLINE_QUEUE_KEY, []);
      queue.push({
        sessionId: get().sessionId,
        conversationId: get().conversationId,
        clientMessageId,
        message: trimmed,
        assignmentId
      });
      await saveJson(OFFLINE_QUEUE_KEY, queue);
      set({ offline: true });
      get().appendMessage({
        id: randomId("offline"),
        role: "assistant",
        text: "Нет соединения. Сообщение сохранено и будет отправлено при восстановлении сети.",
        createdAt: Date.now()
      });
      return;
    }
    set({ loading: true, offline: false });
    try {
      const data = await postChat({
        session_id: get().sessionId,
        conversation_id: get().conversationId,
        client_message_id: clientMessageId,
        message: trimmed,
        action: "none",
        assignment_id: assignmentId
      });
      if (data?.conversation_id && data?.session_key) {
        set({
          conversationId: data.conversation_id,
          sessionId: data.session_key,
          conversationTitle: data.topic || "Диалог"
        });
      }
      get().appendMessage({
        id: randomId("assistant"),
        role: "assistant",
        text: data.reply,
        createdAt: Date.now()
      });
      await get().loadConversations();
    } finally {
      set({ loading: false });
    }
  },
  flushQueue: async () => {
    const state = await NetInfo.fetch();
    if (!state.isConnected) {
      set({ offline: true });
      return;
    }
    const queue = await loadJson<PendingTurn[]>(OFFLINE_QUEUE_KEY, []);
    if (!queue.length) return;
    for (const item of queue) {
      const data = await postChat({
        session_id: item.sessionId,
        conversation_id: item.conversationId,
        client_message_id: item.clientMessageId,
        message: item.message,
        action: "none",
        assignment_id: item.assignmentId
      });
      if (data?.reply) {
        get().appendMessage({
          id: randomId("assistant"),
          role: "assistant",
          text: data.reply,
          createdAt: Date.now()
        });
      }
    }
    await saveJson(OFFLINE_QUEUE_KEY, []);
    set({ offline: false });
  }
}));

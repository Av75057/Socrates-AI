export type UserRole = "user" | "admin" | "educator";

export type AuthUser = {
  id: number;
  email: string;
  full_name?: string | null;
  avatar_url?: string | null;
  role: UserRole;
  is_active: boolean;
};

export type SubscriptionInfo = {
  plan: string;
  status: string;
  is_pro: boolean;
  current_period_end?: string | null;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  createdAt: number;
  pending?: boolean;
};

export type ConversationSummary = {
  id: number;
  title: string;
  started_at: string;
  last_updated_at: string;
  message_count: number;
  session_key: string;
};

export type AssignmentLite = {
  id: number;
  title: string;
  prompt: string;
  due_date?: string | null;
  class_name?: string;
  educator_name?: string;
};

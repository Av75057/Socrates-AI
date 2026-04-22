import { create } from "zustand";
import { loginRequest, registerRequest } from "../api/auth";
import { fetchMe } from "../api/user";
import { saveToken, loadToken } from "../services/storage";
import { AuthUser } from "../types";

type AuthState = {
  user: AuthUser | null;
  token: string | null;
  loading: boolean;
  hydrate: () => Promise<void>;
  login: (email: string, password: string) => Promise<AuthUser>;
  register: (email: string, password: string, fullName: string) => Promise<AuthUser>;
  refreshUser: () => Promise<void>;
  logout: () => Promise<void>;
};

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  loading: true,
  hydrate: async () => {
    const token = await loadToken();
    if (!token) {
      set({ token: null, user: null, loading: false });
      return;
    }
    try {
      const user = await fetchMe();
      set({ token, user, loading: false });
    } catch {
      await saveToken(null);
      set({ token: null, user: null, loading: false });
    }
  },
  login: async (email, password) => {
    const data = await loginRequest(email, password);
    await saveToken(data.access_token);
    set({ token: data.access_token, user: data.user, loading: false });
    return data.user;
  },
  register: async (email, password, fullName) => {
    const data = await registerRequest(email, password, fullName);
    await saveToken(data.access_token);
    set({ token: data.access_token, user: data.user, loading: false });
    return data.user;
  },
  refreshUser: async () => {
    const user = await fetchMe();
    set({ user });
  },
  logout: async () => {
    await saveToken(null);
    set({ token: null, user: null });
  }
}));

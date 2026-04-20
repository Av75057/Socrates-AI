import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  clearToken,
  loginRequest,
  persistToken,
  registerRequest,
} from "../api/authApi.js";
import { getToken } from "../api/client.js";
import { fetchMe } from "../api/userApi.js";
import { useChatStore } from "../store/useChatStore.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const t = getToken();
    if (!t) {
      setUser(null);
      useChatStore.getState().clearResume();
      useChatStore.getState().clearGamification();
      return;
    }
    const me = await fetchMe();
    if (me) setUser(me);
    else {
      clearToken();
      setUser(null);
      useChatStore.getState().clearGamification();
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const t = getToken();
        if (!t) {
          useChatStore.getState().clearResume();
          useChatStore.getState().clearGamification();
          return;
        }
        const me = await fetchMe();
        if (!cancelled && me) setUser(me);
        else if (!cancelled) {
          clearToken();
          setUser(null);
          useChatStore.getState().clearResume();
          useChatStore.getState().clearGamification();
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await loginRequest(email, password);
    useChatStore.getState().clearGamification();
    persistToken(data.access_token);
    setUser(data.user);
    return data;
  }, []);

  const register = useCallback(async (email, password, full_name) => {
    const data = await registerRequest(email, password, full_name);
    useChatStore.getState().clearGamification();
    persistToken(data.access_token);
    setUser(data.user);
    return data;
  }, []);

  const logout = useCallback(() => {
    clearToken();
    setUser(null);
    useChatStore.getState().clearResume();
    useChatStore.getState().clearGamification();
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      logout,
      register,
      refreshUser,
    }),
    [user, loading, login, logout, register, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

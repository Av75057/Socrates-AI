import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { fetchSettings, updateSettings } from "../api/userApi.js";
import { useAuth } from "./AuthContext.jsx";

export const THEME_STORAGE_KEY = "socrates_theme";

function getInitialTheme() {
  try {
    const t = localStorage.getItem(THEME_STORAGE_KEY);
    if (t === "light" || t === "dark") return t;
  } catch {
    /* ignore */
  }
  if (typeof window !== "undefined" && window.matchMedia("(prefers-color-scheme: dark)").matches) {
    return "dark";
  }
  return "light";
}

/** @param {"light" | "dark"} theme */
export function applyDomTheme(theme) {
  const root = document.documentElement;
  if (theme === "dark") root.classList.add("dark");
  else root.classList.remove("dark");
}

const ThemeContext = createContext(null);

export function ThemeProvider({ children }) {
  const { user } = useAuth();
  const [theme, setThemeState] = useState(() => getInitialTheme());

  const setTheme = useCallback((next) => {
    const t = next === "light" ? "light" : "dark";
    setThemeState(t);
    try {
      localStorage.setItem(THEME_STORAGE_KEY, t);
    } catch {
      /* ignore */
    }
    applyDomTheme(t);
    if (user) {
      void updateSettings({ theme: t }).catch(() => {});
    }
  }, [user]);

  useEffect(() => {
    applyDomTheme(theme);
  }, [theme]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    (async () => {
      try {
        const s = await fetchSettings();
        if (cancelled || !s?.theme) return;
        if (s.theme === "light" || s.theme === "dark") {
          setThemeState(s.theme);
          try {
            localStorage.setItem(THEME_STORAGE_KEY, s.theme);
          } catch {
            /* ignore */
          }
          applyDomTheme(s.theme);
        }
      } catch {
        /* offline */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user?.id]);

  const value = useMemo(() => ({ theme, setTheme }), [theme, setTheme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used within ThemeProvider");
  return ctx;
}

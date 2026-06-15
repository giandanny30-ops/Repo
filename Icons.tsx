import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from "react";

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");
const TOKEN_KEY = "gianni_panel_token";

interface AuthCtx {
  isAuthenticated: boolean;
  isLoading: boolean;
  devMode: boolean;
  login: (password: string) => Promise<string | null>;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx | null>(null);

function patchFetch(token: string) {
  const orig: typeof fetch = (window as any).__origFetch__ ?? window.fetch.bind(window);
  (window as any).__origFetch__ = orig;
  window.fetch = (input, init?) => {
    const headers = new Headers(init?.headers);
    headers.set("Authorization", `Bearer ${token}`);
    return orig(input, { ...init, headers });
  };
}

function restoreFetch() {
  const orig = (window as any).__origFetch__;
  if (orig) { window.fetch = orig; (window as any).__origFetch__ = undefined; }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [devMode, setDevMode] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    // Use original fetch (no token header yet) to call verify
    const origFetch: typeof fetch = (window as any).__origFetch__ ?? window.fetch.bind(window);
    const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};
    origFetch(`${BASE}/api/auth/verify`, { headers })
      .then(async (r) => {
        const body = await r.json().catch(() => ({ ok: false }));
        if (r.ok && body.ok) {
          if (token) patchFetch(token);
          setDevMode(!!body.devMode);
          setIsAuthenticated(true);
        } else {
          localStorage.removeItem(TOKEN_KEY);
          restoreFetch();
          setIsAuthenticated(false);
        }
      })
      .catch(() => setIsAuthenticated(false))
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (password: string): Promise<string | null> => {
    const origFetch: typeof fetch = (window as any).__origFetch__ ?? window.fetch.bind(window);
    try {
      const r = await origFetch(`${BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      });
      const body = await r.json().catch(() => ({}));
      if (!r.ok) return body.error ?? "Pogrešna lozinka.";
      const { token, devMode: dm } = body as { token: string; devMode: boolean };
      localStorage.setItem(TOKEN_KEY, token);
      patchFetch(token);
      setDevMode(dm);
      setIsAuthenticated(true);
      return null;
    } catch {
      return "Greška pri prijavi — provjeri konekciju.";
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    restoreFetch();
    setIsAuthenticated(false);
    setDevMode(false);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, isLoading, devMode, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be inside AuthProvider");
  return ctx;
}

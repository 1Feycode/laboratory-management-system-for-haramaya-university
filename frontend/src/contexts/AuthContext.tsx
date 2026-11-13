import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { clearAccessToken } from "../services/api";
import { restoreSession, signIn, signOut } from "../services/auth";
import type { AuthUser } from "../types/auth";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: AuthUser | null;
  status: AuthStatus;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    let active = true;
    const expireSession = () => {
      clearAccessToken();
      setUser(null);
      setStatus("unauthenticated");
    };

    window.addEventListener("auth:expired", expireSession);
    restoreSession()
      .then((session) => {
        if (active) {
          setUser(session.user);
          setStatus("authenticated");
        }
      })
      .catch(() => {
        clearAccessToken();
        if (active) setStatus("unauthenticated");
      });

    return () => {
      active = false;
      window.removeEventListener("auth:expired", expireSession);
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const session = await signIn(email, password);
    setUser(session.user);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    try {
      await signOut();
    } finally {
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  const value = useMemo(
    () => ({ user, status, login, logout }),
    [user, status, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

import api, {
  clearAccessToken,
  refreshAuthSession,
  setAccessToken,
} from "./api";
import type { AuthSession } from "../types/auth";

export async function signIn(
  email: string,
  password: string,
): Promise<AuthSession> {
  const form = new URLSearchParams({ username: email, password });
  const response = await api.post<AuthSession>("/api/v1/auth/login", form, {
    withCredentials: true,
  });
  setAccessToken(response.data.access_token);
  return response.data;
}

export async function restoreSession(): Promise<AuthSession> {
  return refreshAuthSession();
}

export async function signOut(): Promise<void> {
  try {
    await api.post("/api/v1/auth/logout");
  } finally {
    clearAccessToken();
  }
}

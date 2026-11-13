import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";
import type { AuthSession } from "../types/auth";

declare module "axios" {
  export interface InternalAxiosRequestConfig {
    authRetry?: boolean;
  }
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000",
  timeout: 10000,
  withCredentials: true,
  headers: {
    Accept: "application/json",
  },
});

let accessToken: string | null = null;
let refreshInFlight: Promise<AuthSession> | null = null;

export function setAccessToken(token: string): void {
  accessToken = token;
}

export function clearAccessToken(): void {
  accessToken = null;
}

export function refreshAuthSession(): Promise<AuthSession> {
  if (!refreshInFlight) {
    refreshInFlight = axios
      .post<AuthSession>(
        `${api.defaults.baseURL}/api/v1/auth/refresh`,
        null,
        { withCredentials: true, timeout: 10000 },
      )
      .then(({ data }) => {
        setAccessToken(data.access_token);
        return data;
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config;
    const isAuthEndpoint = request?.url?.includes("/api/v1/auth/");
    if (
      error.response?.status !== 401 ||
      !request ||
      request.authRetry ||
      isAuthEndpoint
    ) {
      return Promise.reject(error);
    }

    request.authRetry = true;
    try {
      const session = await refreshAuthSession();
      request.headers.Authorization = `Bearer ${session.access_token}`;
      return api(request);
    } catch (refreshError) {
      clearAccessToken();
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("auth:expired"));
      }
      return Promise.reject(refreshError);
    }
  },
);

export default api;

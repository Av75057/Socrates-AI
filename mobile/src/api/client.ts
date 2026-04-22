import axios from "axios";
import { API_URL } from "../config";
import { loadToken } from "../services/storage";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 20000
});

api.interceptors.request.use(async (config) => {
  const token = await loadToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function apiErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    if (!error.response) {
      return `Network error. Cannot reach ${API_URL}. In development, run the backend on 0.0.0.0:8000 and open the app through Expo on the same network.`;
    }
    return (
      error.response?.data?.detail ||
      error.response?.data ||
      error.message ||
      "Request failed"
    );
  }
  return error instanceof Error ? error.message : "Unknown error";
}

export function resolveApiUrl(path?: string | null) {
  if (!path) return null;
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

import { api } from "./client";
import { AuthUser } from "../types";

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: AuthUser;
};

export async function loginRequest(email: string, password: string) {
  const { data } = await api.post<AuthResponse>("/auth/login", { email, password });
  return data;
}

export async function registerRequest(email: string, password: string, fullName: string) {
  const { data } = await api.post<AuthResponse>("/auth/register", {
    email,
    password,
    full_name: fullName || null
  });
  return data;
}

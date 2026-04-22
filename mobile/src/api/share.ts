import { api } from "./client";

export async function fetchPublicShare(slug: string) {
  const { data } = await api.get(`/public/share/${encodeURIComponent(slug)}`);
  return data;
}

"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function getSupabaseAccessToken(): Promise<string> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) {
    redirect("/login");
  }
  return session.access_token;
}

export async function connectProviderAction(formData: FormData) {
  const provider = String(formData.get("provider") ?? "");
  if (!provider) return;

  const token = await getSupabaseAccessToken();

  const response = await fetch(`${BACKEND_URL}/providers/${provider}/authorize`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Backend authorize failed (${response.status}): ${text}`);
  }

  const { authorize_url } = (await response.json()) as { authorize_url: string };
  redirect(authorize_url);
}

export async function syncProviderAction(formData: FormData) {
  const provider = String(formData.get("provider") ?? "");
  const days = Number(formData.get("days") ?? 30);
  if (!provider) return;

  const token = await getSupabaseAccessToken();

  await fetch(`${BACKEND_URL}/providers/${provider}/sync?days=${days}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  redirect("/dashboard/connections?provider=" + provider + "&status=synced");
}

export async function disconnectProviderAction(formData: FormData) {
  const provider = String(formData.get("provider") ?? "");
  if (!provider) return;

  const token = await getSupabaseAccessToken();

  await fetch(`${BACKEND_URL}/providers/${provider}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  redirect("/dashboard/connections?provider=" + provider + "&status=disconnected");
}

export type ConnectionStatus = {
  provider: string;
  connected: boolean;
  provider_user_id: string | null;
  expires_at: string | null;
  scope: string | null;
};

export async function getConnectionStatus(provider: string): Promise<ConnectionStatus | null> {
  try {
    const token = await getSupabaseAccessToken();
    const response = await fetch(`${BACKEND_URL}/providers/${provider}/status`, {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!response.ok) return null;
    return (await response.json()) as ConnectionStatus;
  } catch {
    return null;
  }
}

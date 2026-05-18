"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function getAccessToken(): Promise<string> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) redirect("/login");
  return session.access_token;
}

export async function approveOAuthAction(formData: FormData) {
  const body = {
    client_id: String(formData.get("client_id") ?? ""),
    redirect_uri: String(formData.get("redirect_uri") ?? ""),
    state: String(formData.get("state") ?? ""),
    scope: String(formData.get("scope") ?? "mcp"),
    code_challenge: String(formData.get("code_challenge") ?? "") || null,
    code_challenge_method: String(formData.get("code_challenge_method") ?? "S256"),
  };

  const token = await getAccessToken();
  const response = await fetch(`${BACKEND_URL}/oauth/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`OAuth approve failed (${response.status}): ${text}`);
  }
  const { redirect_url } = (await response.json()) as { redirect_url: string };
  redirect(redirect_url);
}

export async function denyOAuthAction(formData: FormData) {
  const redirectUri = String(formData.get("redirect_uri") ?? "");
  const state = String(formData.get("state") ?? "");
  const sep = redirectUri.includes("?") ? "&" : "?";
  const params = new URLSearchParams({ error: "access_denied" });
  if (state) params.set("state", state);
  redirect(`${redirectUri}${sep}${params.toString()}`);
}

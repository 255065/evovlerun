"use server";

import { revalidatePath } from "next/cache";
import { createClient } from "@/lib/supabase/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function getToken(): Promise<string> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) {
    throw new Error("Not authenticated");
  }
  return session.access_token;
}

export type KeySummary = {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
};

export type InstallSnippets = {
  claude_desktop_config_snippet: string;
  macos_install_script: string;
  mcp_server_path: string;
  claude_config_file_path: string;
};

export type CreateKeyResult = {
  id: string;
  name: string;
  key: string;
  key_prefix: string;
  install: InstallSnippets;
};

export async function listKeys(): Promise<KeySummary[]> {
  const token = await getToken();
  const response = await fetch(`${BACKEND_URL}/mcp-keys`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) return [];
  return (await response.json()) as KeySummary[];
}

export type CreateKeyState = {
  error: string | null;
  newKey: CreateKeyResult | null;
};

export async function createKeyAction(
  _prev: CreateKeyState,
  formData: FormData,
): Promise<CreateKeyState> {
  const name = String(formData.get("name") ?? "").trim();
  if (!name) return { error: "Giv nøglen et navn.", newKey: null };

  const token = await getToken();
  const response = await fetch(`${BACKEND_URL}/mcp-keys`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) {
    return { error: `Kunne ikke oprette nøgle (${response.status})`, newKey: null };
  }
  const data = (await response.json()) as CreateKeyResult;
  revalidatePath("/dashboard/mcp");
  return { error: null, newKey: data };
}

export async function revokeKeyAction(formData: FormData): Promise<void> {
  const id = String(formData.get("id") ?? "");
  if (!id) return;
  const token = await getToken();
  await fetch(`${BACKEND_URL}/mcp-keys/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  revalidatePath("/dashboard/mcp");
}

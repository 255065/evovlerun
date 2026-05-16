"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function getToken(): Promise<string> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) redirect("/login");
  return session.access_token;
}

export type GarminConnectState = {
  error: string | null;
  needsMfa: boolean;
  pendingToken: string | null;
};

const initialState: GarminConnectState = { error: null, needsMfa: false, pendingToken: null };

export async function garminConnectAction(
  _prev: GarminConnectState,
  formData: FormData,
): Promise<GarminConnectState> {
  const username = String(formData.get("username") ?? "").trim();
  const password = String(formData.get("password") ?? "");
  if (!username || !password) {
    return { ...initialState, error: "Udfyld både email og password." };
  }

  const token = await getToken();
  const response = await fetch(`${BACKEND_URL}/providers/garmin/credential-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ username, password }),
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    return { ...initialState, error: `Login fejlede (${response.status}): ${text}` };
  }

  const data = (await response.json()) as { status: string; pending_token: string | null };

  if (data.status === "mfa_required") {
    return { error: null, needsMfa: true, pendingToken: data.pending_token };
  }

  redirect("/dashboard/connections?provider=garmin&status=connected");
}

export async function garminMfaAction(
  _prev: GarminConnectState,
  formData: FormData,
): Promise<GarminConnectState> {
  const pendingToken = String(formData.get("pending_token") ?? "");
  const mfaCode = String(formData.get("mfa_code") ?? "").trim();
  if (!pendingToken || !mfaCode) {
    return {
      error: "Mangler MFA-kode.",
      needsMfa: true,
      pendingToken: pendingToken || null,
    };
  }

  const token = await getToken();
  const response = await fetch(`${BACKEND_URL}/providers/garmin/mfa-submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ pending_token: pendingToken, mfa_code: mfaCode }),
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    return {
      error: `MFA fejlede (${response.status}): ${text}`,
      needsMfa: true,
      pendingToken,
    };
  }

  redirect("/dashboard/connections?provider=garmin&status=connected");
}

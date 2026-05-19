"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export type OnboardingPayload = {
  goal: string;
  goal_detail: Record<string, string> | null;
  weekly_sessions: number;
  weekly_hours: number;
  training_style: "structured" | "freeflow" | "adaptive" | "hybrid";
  preferred_ai_coach: "claude" | "gpt" | "gemini";
};

/**
 * Persist the wizard answers to `profiles`, mark the user onboarded, then
 * either hand them off to Strava OAuth (if they haven't connected yet) or
 * drop them on the dashboard. The Strava connect step lives at the very end
 * because the rest of the flow is metadata-only — we want the user to see
 * their answers saved even if they bail on the OAuth handoff.
 */
export async function finishOnboardingAction(formData: FormData) {
  const supabase = await createClient();
  const [{ data: userData }, { data: sessionData }] = await Promise.all([
    supabase.auth.getUser(),
    supabase.auth.getSession(),
  ]);
  const user = userData.user;
  const session = sessionData.session;

  if (!user || !session) {
    redirect("/login");
  }

  // Parse the wizard payload out of the form. The wizard serialises the full
  // answer set as a single JSON blob so we don't have to enumerate every
  // field by name on the server side.
  let payload: OnboardingPayload;
  try {
    payload = JSON.parse(String(formData.get("payload") ?? "{}"));
  } catch {
    throw new Error("Invalid onboarding payload");
  }

  const { error } = await supabase
    .from("profiles")
    .update({
      onboarding_goal: payload.goal,
      onboarding_goal_detail: payload.goal_detail,
      weekly_sessions: payload.weekly_sessions,
      weekly_hours: payload.weekly_hours,
      training_style: payload.training_style,
      preferred_ai_coach: payload.preferred_ai_coach,
      onboarded_at: new Date().toISOString(),
    })
    .eq("id", user.id);

  if (error) {
    // Surface the error to the client so the wizard can show it instead of
    // silently swallowing — onboarding answers are worth a retry.
    throw new Error(`Could not save onboarding: ${error.message}`);
  }

  // Skip the Strava handoff if they already connected (e.g. they came back
  // to finish onboarding after a partial run). Just drop them on the
  // dashboard.
  const connectStrava = String(formData.get("connect_strava") ?? "0") === "1";
  if (!connectStrava) {
    redirect("/dashboard");
  }

  // Kick off Strava OAuth. The backend returns an authorize_url that the
  // browser must navigate to — Strava callbacks land on
  // /dashboard/connections, where the success banner takes over.
  const response = await fetch(`${BACKEND_URL}/providers/strava/authorize`, {
    method: "POST",
    headers: { Authorization: `Bearer ${session.access_token}` },
    cache: "no-store",
  });

  if (!response.ok) {
    // If Strava authorize fails, we still want the user to see their
    // onboarding-complete state — drop them on connections with a hint.
    redirect("/dashboard/connections?status=authorize_failed&provider=strava");
  }

  const { authorize_url } = (await response.json()) as { authorize_url: string };
  redirect(authorize_url);
}

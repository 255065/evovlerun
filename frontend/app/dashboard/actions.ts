"use server";

import { createClient } from "@/lib/supabase/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

/** Get a Supabase access token for the current request — auth-gated by middleware. */
async function getToken(): Promise<string | null> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

async function backendGet<T>(path: string): Promise<T | null> {
  const token = await getToken();
  if (!token) return null;
  try {
    const res = await fetch(`${BACKEND_URL}${path}`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

// ---- Types ---------------------------------------------------------------
export type ActivitySummary = {
  latest: {
    started_at: string;
    sport: string;
    distance_m: number | null;
    duration_seconds: number;
    avg_pace_s_per_km: number | null;
  } | null;
  week: { activities: number; km: number; hours: number };
} | null;

export type PlannedSession = {
  scheduled_date: string;
  session_type: string;
  sport: string;
  duration_min: number | null;
  distance_m: number | null;
  description: string | null;
  intensity_zones: Record<string, unknown> | null;
  rationale: string | null;
  status: string;
};

export type PlanBlueprint = {
  total_weeks: number;
  phases: { name: string; week_count: number; weekly_volume_hours: number; weekly_intensity_focus: string; rationale: string }[];
  weekly_template: Record<string, string>;
  guiding_principles: string[];
  key_metrics_to_track: string[];
  auto_adapt_triggers?: string[];
};

export type CurrentPlan = {
  active: boolean;
  plan_id?: string;
  race_type?: string;
  race_date?: string;
  target_time_seconds?: number | null;
  philosophy?: string;
  current_phase?: string;
  weeks?: number;
  blueprint?: PlanBlueprint;
  next_14_days?: PlannedSession[];
};

export type Profile = {
  id: string;
  email: string | null;
  full_name: string | null;
  date_of_birth: string | null;
  sex: "male" | "female" | "other" | null;
  height_cm: number | null;
  weight_kg: number | null;
  primary_sport: string | null;
  experience_level: string | null;
  resting_hr: number | null;
  max_hr: number | null;
  preferred_philosophy: string | null;
};

// ---- Loaders -------------------------------------------------------------
export async function loadCurrentPlan(): Promise<CurrentPlan | null> {
  return backendGet<CurrentPlan>("/training/plan/current");
}

/** Profile is read straight from Supabase (RLS-protected) — no backend hop needed. */
export async function loadProfile(): Promise<Profile | null> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return null;
  const { data } = await supabase.from("profiles").select("*").eq("id", user.id).maybeSingle();
  return data as Profile | null;
}

/** Most recent daily wellness — pulled directly from Supabase. */
export async function loadLatestRecovery(): Promise<{
  metric_date: string;
  hrv_rmssd: number | null;
  resting_hr: number | null;
  sleep_minutes: number | null;
  sleep_score: number | null;
  readiness_score: number | null;
  body_battery: number | null;
  stress_avg: number | null;
} | null> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return null;
  const { data } = await supabase
    .from("daily_metrics")
    .select(
      "metric_date, hrv_rmssd, resting_hr, sleep_minutes, sleep_score, readiness_score, body_battery, stress_avg",
    )
    .eq("user_id", user.id)
    .order("metric_date", { ascending: false })
    .limit(1)
    .maybeSingle();
  return data;
}

/** Latest workout + trailing-7-day totals — read directly from Supabase (RLS). */
export async function loadActivitySummary(): Promise<ActivitySummary> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return null;

  const { data: latest } = await supabase
    .from("workouts")
    .select("started_at, sport, distance_m, duration_seconds, avg_pace_s_per_km")
    .eq("user_id", user.id)
    .order("started_at", { ascending: false })
    .limit(1)
    .maybeSingle();

  const since = new Date(Date.now() - 7 * 864e5).toISOString();
  const { data: rows } = await supabase
    .from("workouts")
    .select("distance_m, duration_seconds")
    .eq("user_id", user.id)
    .gte("started_at", since);

  const weekRows = (rows ?? []) as { distance_m: number | null; duration_seconds: number | null }[];
  const meters = weekRows.reduce((sum, r) => sum + (r.distance_m ?? 0), 0);
  const seconds = weekRows.reduce((sum, r) => sum + (r.duration_seconds ?? 0), 0);

  return {
    latest: (latest as NonNullable<ActivitySummary>["latest"]) ?? null,
    week: {
      activities: weekRows.length,
      km: meters / 1000,
      hours: seconds / 3600,
    },
  };
}

// ---- Mutations -----------------------------------------------------------
export async function updateProfile(patch: Partial<Profile>): Promise<{ ok: boolean; error?: string }> {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) return { ok: false, error: "Not authenticated" };
  const allowed: Partial<Profile> = {
    full_name: patch.full_name,
    date_of_birth: patch.date_of_birth,
    sex: patch.sex,
    height_cm: patch.height_cm,
    weight_kg: patch.weight_kg,
    primary_sport: patch.primary_sport,
    experience_level: patch.experience_level,
    resting_hr: patch.resting_hr,
    max_hr: patch.max_hr,
    preferred_philosophy: patch.preferred_philosophy,
  };
  // Strip undefined so we don't blank fields the user didn't touch.
  const clean: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(allowed)) {
    if (v !== undefined && v !== "") clean[k] = v;
  }
  const { error } = await supabase.from("profiles").update(clean).eq("id", user.id);
  if (error) return { ok: false, error: error.message };
  return { ok: true };
}

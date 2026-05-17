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
export type FitnessPoint = {
  snapshot_date: string;
  ctl: number | null;
  atl: number | null;
  tsb: number | null;
  acwr: number | null;
};

export type FitnessTimeline = {
  days: number;
  points: FitnessPoint[];
};

export type LimiterCall = {
  available: boolean;
  detected_at?: string;
  primary_limiter?: string;
  secondary_limiter?: string | null;
  confidence?: number;
  recommended_focus?: string | null;
  key_observations?: string[];
  supporting_data_points?: string[];
  physiology_explanation?: string | null;
  alternative_considered?: string | null;
};

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
export async function loadFitnessTimeline(days = 90): Promise<FitnessTimeline | null> {
  return backendGet<FitnessTimeline>(`/performance/timeline?days=${days}`);
}

export async function loadLatestLimiter(): Promise<LimiterCall | null> {
  return backendGet<LimiterCall>("/limiter/latest");
}

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

// ---- Mutations -----------------------------------------------------------
export async function runLimiterAnalysis(): Promise<{ ok: boolean; error?: string }> {
  const token = await getToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  const res = await fetch(`${BACKEND_URL}/limiter/analyze`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    return { ok: false, error: `${res.status}: ${await res.text()}` };
  }
  return { ok: true };
}

export async function generatePlan(input: {
  race_type: string;
  race_date: string;
  target_time_seconds?: number;
  philosophy: string;
  expand_first_n_weeks?: number;
}): Promise<{ ok: boolean; plan_id?: string; error?: string }> {
  const token = await getToken();
  if (!token) return { ok: false, error: "Not authenticated" };
  const res = await fetch(`${BACKEND_URL}/training/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(input),
    cache: "no-store",
  });
  if (!res.ok) {
    return { ok: false, error: `${res.status}: ${await res.text()}` };
  }
  const data = (await res.json()) as { plan_id: string };
  return { ok: true, plan_id: data.plan_id };
}

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

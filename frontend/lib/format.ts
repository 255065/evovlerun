/** Shared formatting helpers across the dashboard. */

export function fmtPace(secondsPerKm: number | null | undefined): string {
  if (!secondsPerKm) return "—";
  const m = Math.floor(secondsPerKm / 60);
  const s = Math.round(secondsPerKm % 60);
  return `${m}:${s.toString().padStart(2, "0")}/km`;
}

export function fmtDuration(seconds: number | null | undefined): string {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h) return `${h}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function fmtDistance(meters: number | null | undefined): string {
  if (!meters) return "—";
  if (meters < 1000) return `${meters} m`;
  return `${(meters / 1000).toFixed(2)} km`;
}

const LIMITER_LABELS: Record<string, string> = {
  aerobic_capacity: "Aerob kapacitet",
  lactate_threshold: "Lactate threshold",
  muscular_endurance: "Muskulær udholdenhed",
  running_economy: "Løbeøkonomi",
  anaerobic_capacity: "Anaerob kapacitet",
  recovery: "Restitution",
  neuromuscular: "Neuromuskulær",
};

export function fmtLimiter(slug: string | null | undefined): string {
  if (!slug) return "—";
  return LIMITER_LABELS[slug] ?? slug.replaceAll("_", " ");
}

const SESSION_TYPE_LABELS: Record<string, string> = {
  easy: "Easy",
  long: "Long run",
  tempo: "Tempo",
  threshold: "Threshold",
  intervals: "Intervals",
  vo2max: "VO2max",
  fartlek: "Fartlek",
  hills: "Bakketræning",
  recovery: "Recovery",
  race: "Race",
  strength: "Styrke",
  cross_training: "Cross-training",
  rest: "Hvile",
};

export function fmtSessionType(slug: string | null | undefined): string {
  if (!slug) return "—";
  return SESSION_TYPE_LABELS[slug] ?? slug;
}

const DAYS_DA = ["Søn", "Man", "Tir", "Ons", "Tor", "Fre", "Lør"];

export function fmtWeekday(iso: string): string {
  const d = new Date(iso);
  return DAYS_DA[d.getDay()];
}

export function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("da-DK", { day: "numeric", month: "short" });
}

export function acwrZone(acwr: number | null | undefined): {
  label: string;
  tone: "success" | "warn" | "danger" | "info";
} {
  if (acwr == null) return { label: "Ingen data", tone: "info" };
  if (acwr < 0.8) return { label: "Detraining / undertrained", tone: "warn" };
  if (acwr <= 1.3) return { label: "Optimal sweet spot", tone: "success" };
  if (acwr <= 1.5) return { label: "Forhøjet skaderisiko", tone: "warn" };
  return { label: "Høj skaderisiko", tone: "danger" };
}

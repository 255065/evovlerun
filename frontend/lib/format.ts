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
  aerobic_capacity: "Aerobic capacity",
  lactate_threshold: "Lactate threshold",
  muscular_endurance: "Muscular endurance",
  running_economy: "Running economy",
  anaerobic_capacity: "Anaerobic capacity",
  recovery: "Recovery",
  neuromuscular: "Neuromuscular",
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
  hills: "Hills",
  recovery: "Recovery",
  race: "Race",
  strength: "Strength",
  cross_training: "Cross-training",
  rest: "Rest",
};

export function fmtSessionType(slug: string | null | undefined): string {
  if (!slug) return "—";
  return SESSION_TYPE_LABELS[slug] ?? slug;
}

const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

export function fmtWeekday(iso: string): string {
  const d = new Date(iso);
  return DAYS[d.getDay()];
}

export function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

/** Coarse "x ago" label for sync timestamps. Null → "never". */
export function fmtRelative(iso: string | null | undefined): string {
  if (!iso) return "never";
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  if (days < 30) return `${days}d ago`;
  return fmtDate(iso);
}

export function acwrZone(acwr: number | null | undefined): {
  label: string;
  tone: "success" | "warn" | "danger" | "info";
} {
  if (acwr == null) return { label: "No data", tone: "info" };
  if (acwr < 0.8) return { label: "Detraining / undertrained", tone: "warn" };
  if (acwr <= 1.3) return { label: "Optimal sweet spot", tone: "success" };
  if (acwr <= 1.5) return { label: "Elevated injury risk", tone: "warn" };
  return { label: "High injury risk", tone: "danger" };
}

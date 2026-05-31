import type { LatestActivity } from "./actions";
import { fmtDistance, fmtDuration, fmtPace } from "@/lib/format";
import { decodePolyline, polylineToSvgPath } from "@/lib/polyline";

const MAP_W = 560;
const MAP_H = 200;

/**
 * Strava-style latest-activity card. Reproduces the public activity layout
 * (athlete header, title, distance/pace/time, route trace, kudos) from the
 * fields Strava stores in raw_payload. Note: the "Local Legend" badge is a
 * Strava-app leaderboard feature with no API surface, so it isn't shown.
 */
export function LatestActivityCard({
  latest,
  athleteName,
}: {
  latest: LatestActivity;
  athleteName: string;
}) {
  const routePath = latest.summary_polyline
    ? polylineToSvgPath(decodePolyline(latest.summary_polyline), MAP_W, MAP_H)
    : null;

  const subtitle = [fmtDateTime(latest.started_at), latest.device_name, latest.location]
    .filter(Boolean)
    .join(" · ");

  const initial = (athleteName.trim()[0] ?? "A").toUpperCase();

  return (
    <div className="overflow-hidden rounded-2xl border border-neutral-200/70 bg-white/70">
      {/* Athlete header */}
      <div className="flex items-center gap-3 px-5 pt-5">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-[#fc4c02] text-[16px] font-semibold text-white">
          {initial}
        </div>
        <div className="min-w-0">
          <div className="text-[15px] font-semibold tracking-[-0.005em]">{athleteName}</div>
          <div className="truncate text-[12.5px] text-neutral-500">{subtitle}</div>
        </div>
      </div>

      {/* Title + stats */}
      <div className="px-5 pt-4">
        <h3 className="text-[22px] font-semibold tracking-[-0.015em]">
          {latest.name ?? capitalize(latest.sport)}
        </h3>
        <div className="mt-3 flex flex-wrap items-end gap-x-8 gap-y-3">
          <Stat label="Distance" value={fmtDistance(latest.distance_m)} />
          {latest.avg_pace_s_per_km != null && (
            <Stat label="Pace" value={fmtPace(latest.avg_pace_s_per_km)} />
          )}
          <Stat label="Time" value={fmtDuration(latest.duration_seconds)} />
          {latest.elevation_gain_m != null && latest.elevation_gain_m > 0 && (
            <Stat label="Elevation" value={`${Math.round(latest.elevation_gain_m)} m`} />
          )}
          {latest.achievement_count != null && latest.achievement_count > 0 && (
            <Stat label="Achievements" value={`🏆 ${latest.achievement_count}`} />
          )}
        </div>
      </div>

      {/* Route trace */}
      {routePath && (
        <div className="mt-4 bg-neutral-100">
          <svg
            viewBox={`0 0 ${MAP_W} ${MAP_H}`}
            className="h-auto w-full"
            preserveAspectRatio="xMidYMid meet"
            role="img"
            aria-label="Activity route"
          >
            <path
              d={routePath}
              fill="none"
              stroke="#fc4c02"
              strokeWidth={3}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      )}

      {/* Kudos footer */}
      <div className="flex items-center gap-2 px-5 py-4 text-[13px] text-neutral-600">
        <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor" aria-hidden>
          <path d="M2 21h4V9H2v12zM23 10c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z" />
        </svg>
        <span>{latest.kudos_count ?? 0} kudos</span>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[10px] uppercase tracking-[0.15em] text-neutral-500">
        {label}
      </div>
      <div className="mt-0.5 text-[20px] font-semibold tracking-[-0.02em] leading-none">
        {value}
      </div>
    </div>
  );
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, " ");
}

function fmtDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

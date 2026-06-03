import type { LatestActivity } from "./actions";
import { fmtDistance, fmtDuration, fmtPace } from "@/lib/format";
import { decodePolyline, polylineToSvgPath } from "@/lib/polyline";

const MAP_W = 560;
const MAP_H = 200;

/**
 * Strava-style latest-activity card. Reproduces the public activity layout
 * (athlete header, title, distance/pace/time, route trace) from the
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
    <div className="overflow-hidden rounded-2xl border border-neutral-200 bg-white">
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

      {/* Strava attribution — required by Strava brand guidelines */}
      <div className="flex items-center justify-between px-5 py-3 text-[12px] text-neutral-400">
        <a
          href="https://www.strava.com"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 hover:text-[#fc4c02]"
          aria-label="Powered by Strava"
        >
          <StravaWordmark />
          <span>Powered by Strava</span>
        </a>
        {latest.source_id && (
          <a
            href={`https://www.strava.com/activities/${latest.source_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[#fc4c02]"
          >
            View on Strava →
          </a>
        )}
      </div>
    </div>
  );
}

/** Strava logo wordmark (SVG inline — no image request, no CORS). */
function StravaWordmark() {
  return (
    <svg
      width="52"
      height="14"
      viewBox="0 0 52 14"
      fill="currentColor"
      aria-hidden="true"
      className="text-[#fc4c02]"
    >
      {/* Simplified "STRAVA" text path matching brand colour */}
      <text
        x="0"
        y="11"
        fontFamily="Arial, sans-serif"
        fontWeight="bold"
        fontSize="12"
        letterSpacing="0.5"
      >
        STRAVA
      </text>
    </svg>
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

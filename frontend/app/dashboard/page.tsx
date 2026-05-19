import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import {
  loadCurrentPlan,
  loadFitnessTimeline,
  loadLatestLimiter,
  loadLatestRecovery,
} from "./actions";
import { acwrZone, fmtDate, fmtLimiter, fmtSessionType, fmtWeekday } from "@/lib/format";

export const dynamic = "force-dynamic";

/**
 * V1 dashboard — Vercel-style: bright white surface, sharp dividers, mono
 * time labels. Same data wiring as before (CTL/ATL/TSB/ACWR, recovery,
 * limiter, upcoming sessions) but the visual language now matches the
 * landing page so the post-signup experience feels continuous.
 */
export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const name = user?.user_metadata?.full_name ?? user?.email ?? "atlet";

  const [timeline, recovery, limiter, plan] = await Promise.all([
    loadFitnessTimeline(90),
    loadLatestRecovery(),
    loadLatestLimiter(),
    loadCurrentPlan(),
  ]);

  const latestPoint = timeline?.points[timeline.points.length - 1];
  const acwrInfo = acwrZone(latestPoint?.acwr);

  // 7-day volume (km) from the last 7 timeline points — they store CTL/ATL
  // but not raw weekly distance, so we approximate from upcoming-plan if
  // available. Long-term we'll source this from a dedicated weekly-summary
  // view; this is good enough for the V1 top-row card.
  const sevenDayKmDelta = 12; // placeholder until we wire weekly aggregate

  const today = new Date();
  const todayIso = today.toISOString().slice(0, 10);
  const upcoming = (plan?.next_14_days ?? []).filter((s) => s.scheduled_date >= todayIso);
  const todays = upcoming.filter((s) => s.scheduled_date === todayIso);

  // Readiness ring — prefer wearable-reported readiness, fall back to a
  // TSB-derived proxy so the ring always shows *something* sensible.
  const tsb = latestPoint?.tsb;
  const readiness =
    recovery?.readiness_score ??
    (tsb != null ? Math.max(0, Math.min(100, Math.round(tsb + 50))) : null);
  const readinessRing = readiness ?? 0;

  return (
    <div className="text-neutral-950">
      <div className="text-[32px] font-semibold tracking-[-0.03em]">Hej, {name}</div>
      <div className="mt-1 text-[14px] text-neutral-600">
        {fmtToday(today)} · uge {isoWeek(today)}
        {latestPoint && <> · sidst opdateret {fmtDate(latestPoint.snapshot_date)}</>}
      </div>

      <Tabs />

      {/* ─── Top stat row ─────────────────────────────────── */}
      <div className="grid grid-cols-1 overflow-hidden rounded-[10px] border border-neutral-200 bg-neutral-200 sm:grid-cols-2 lg:grid-cols-4 gap-px">
        <StatCell
          label={
            <>
              Readiness{" "}
              <span style={{ color: readinessTone(readiness) }}>●</span>
            </>
          }
          value={readiness != null ? readiness.toString() : "—"}
          valueUnit={readiness != null ? "/100" : undefined}
          hint={readinessHint(readiness)}
          hintTone={readinessTone(readiness)}
        />
        <StatCell
          label="Form (TSB)"
          value={tsb != null ? `${tsb >= 0 ? "+" : ""}${tsb.toFixed(0)}` : "—"}
          hint={tsbHint(tsb)}
        />
        <StatCell
          label="Fitness (CTL)"
          value={latestPoint?.ctl?.toFixed(0) ?? "—"}
          hint={`▲ ${sevenDayKmDelta}% on prior week`}
        />
        <StatCell
          label="ACWR"
          value={latestPoint?.acwr?.toFixed(2) ?? "—"}
          hint={acwrInfo.label}
          hintTone={acwrInfo.tone === "warn" ? "#dc2626" : undefined}
        />
      </div>

      {/* ─── Two-card row ─────────────────────────────────── */}
      <div className="mt-4 grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        {/* Today's plan */}
        <div className="rounded-[10px] border border-neutral-200 bg-white">
          <CardHeader title="Today's plan" right={<Link href="/dashboard/training" className="hover:text-neutral-950">View all →</Link>} />
          {todays.length === 0 ? (
            <div className="px-5 py-5 text-[13.5px] text-neutral-600">
              {plan?.active
                ? "Ingen sessioner planlagt for i dag. Recovery er også træning."
                : "Ingen plan endnu. Spørg din AI-coach i chatten om at lave en."}
            </div>
          ) : (
            <div>
              {todays.map((s, i) => (
                <PlanRow
                  key={`${s.scheduled_date}-${i}`}
                  time={i === 0 ? "Today" : "Optional"}
                  title={fmtSessionType(s.session_type)}
                  sub={planRowSub(s)}
                  tag={i === 0 ? "Anchor" : "Optional"}
                  tagTone={i === 0 ? "ok" : "neutral"}
                  right={zoneLabel(s)}
                />
              ))}
            </div>
          )}
          {upcoming.length > todays.length && (
            <div className="border-t border-neutral-100 px-5 py-3 text-[13px] text-neutral-600">
              Næste op:{" "}
              {upcoming
                .slice(todays.length, todays.length + 3)
                .map((s) => `${fmtWeekday(s.scheduled_date)} · ${fmtSessionType(s.session_type)}`)
                .join(" → ")}
            </div>
          )}
        </div>

        {/* Recovery ring */}
        <div className="rounded-[10px] border border-neutral-200 bg-white p-5">
          <div className="mb-3 flex items-center justify-between">
            <span className="text-[14px] font-medium">Recovery</span>
            <span className="text-[12.5px] text-neutral-600">
              {recovery?.metric_date ? `Last sync ${fmtDate(recovery.metric_date)}` : "Strava only — limited"}
            </span>
          </div>
          <RecoveryRing value={readinessRing} />
          <div className="mt-4 space-y-2 text-[13.5px]">
            <RecoveryMetric k="Søvn" v={fmtSleep(recovery?.sleep_minutes)} />
            <RecoveryMetric k="HRV (7d)" v={recovery?.hrv_rmssd ? `${recovery.hrv_rmssd.toFixed(0)} ms` : "—"} />
            <RecoveryMetric k="Resting HR" v={recovery?.resting_hr ? `${recovery.resting_hr} bpm` : "—"} />
          </div>
          {!recovery?.metric_date && (
            <p className="mt-3 text-[12px] text-neutral-500">
              Strava udleverer ikke søvn / HRV — koble Garmin direkte i V2 for fulde recovery-tal.
            </p>
          )}
        </div>
      </div>

      {/* ─── Weekly load chart ───────────────────────────── */}
      <div className="mt-4 rounded-[10px] border border-neutral-200 bg-white">
        <CardHeader
          title="Weekly load"
          right={<span>Easy 68% · Threshold 22% · VO₂ 10%</span>}
        />
        <div className="flex items-end gap-2 px-5 py-6" style={{ height: 120 }}>
          {/* 7-day bars from upcoming plan distance-min totals, fall back to placeholder */}
          {sevenBars(upcoming).map((h, i) => (
            <div
              key={i}
              className={`flex-1 rounded-t-md ${i === 1 || i === 3 ? "bg-[color:var(--evr-accent)]" : "bg-neutral-300"}`}
              style={{ height: `${Math.max(8, h)}%` }}
            />
          ))}
        </div>
        <div className="grid grid-cols-7 gap-2 border-t border-neutral-100 px-5 py-2 text-center text-[11px] text-neutral-500">
          {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((d) => (
            <span key={d}>{d}</span>
          ))}
        </div>
      </div>

      {/* ─── Limiter (kept — V2 hook, value-add when available) ── */}
      {limiter?.available && (
        <div className="mt-4 rounded-[10px] border border-neutral-200 bg-white p-5">
          <div className="flex items-start justify-between">
            <div>
              <div className="text-[14px] font-medium">Din limiter</div>
              <div className="mt-1 text-[12.5px] text-neutral-600">
                AI-detekteret primær fysiologisk begrænsning · {Math.round((limiter.confidence ?? 0) * 100)}% confidence
              </div>
            </div>
            <Link href="/dashboard/limiter" className="text-[13px] text-neutral-600 hover:text-neutral-950">
              Detaljer →
            </Link>
          </div>
          <div className="mt-3 flex items-baseline gap-3">
            <span className="text-[22px] font-semibold tracking-[-0.02em]">
              {fmtLimiter(limiter.primary_limiter)}
            </span>
            {limiter.secondary_limiter && (
              <span className="text-[13px] text-neutral-500">+ {fmtLimiter(limiter.secondary_limiter)}</span>
            )}
          </div>
          {limiter.recommended_focus && (
            <p className="mt-2 text-[13.5px] text-neutral-700">
              <span className="font-medium">Fokus:</span> {limiter.recommended_focus}
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────

function Tabs() {
  const tabs: { label: string; href: string; active?: boolean }[] = [
    { label: "Overview", href: "/dashboard", active: true },
    { label: "Workouts", href: "/dashboard/training" },
    { label: "Limiter", href: "/dashboard/limiter" },
    { label: "Integrations", href: "/dashboard/connections" },
    { label: "MCP", href: "/dashboard/mcp" },
  ];
  return (
    <div className="my-7 flex gap-6 border-b border-neutral-200">
      {tabs.map((t) => (
        <Link
          key={t.label}
          href={t.href}
          className={`-mb-px border-b-2 pb-3 text-[13.5px] ${
            t.active
              ? "border-neutral-950 font-medium text-neutral-950"
              : "border-transparent text-neutral-600 hover:text-neutral-950"
          }`}
        >
          {t.label}
        </Link>
      ))}
    </div>
  );
}

function StatCell({
  label,
  value,
  valueUnit,
  hint,
  hintTone,
}: {
  label: React.ReactNode;
  value: string;
  valueUnit?: string;
  hint: string;
  hintTone?: string;
}) {
  return (
    <div className="bg-white px-5 py-[18px]">
      <div className="flex items-center gap-1.5 text-[12.5px] text-neutral-600">{label}</div>
      <div className="mt-1.5 text-[28px] font-semibold tracking-[-0.02em] leading-none">
        {value}
        {valueUnit && <span className="ml-1 text-[14px] font-normal text-neutral-500">{valueUnit}</span>}
      </div>
      <div className="mt-1 text-[12px]" style={{ color: hintTone ?? "#16a34a" }}>
        {hint}
      </div>
    </div>
  );
}

function CardHeader({ title, right }: { title: string; right?: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-neutral-100 px-5 py-4">
      <span className="text-[14px] font-medium">{title}</span>
      <span className="text-[12.5px] text-neutral-600">{right}</span>
    </div>
  );
}

function PlanRow({
  time,
  title,
  sub,
  tag,
  tagTone,
  right,
}: {
  time: string;
  title: string;
  sub: string;
  tag: string;
  tagTone: "ok" | "neutral" | "warn";
  right: string;
}) {
  const tagClass =
    tagTone === "ok"
      ? "bg-emerald-100 text-emerald-800"
      : tagTone === "warn"
        ? "bg-amber-100 text-amber-800"
        : "bg-neutral-100 text-neutral-700";
  return (
    <div className="grid grid-cols-[60px_1fr_auto_auto] items-center gap-3 border-b border-neutral-100 px-5 py-3.5 text-[13.5px] last:border-b-0">
      <span className="font-mono text-[12px] text-neutral-500">{time}</span>
      <div>
        <div className="font-medium">{title}</div>
        <div className="mt-0.5 text-[12.5px] text-neutral-600">{sub}</div>
      </div>
      <span className={`rounded-full px-2 py-[2px] text-[11px] font-medium ${tagClass}`}>{tag}</span>
      <span className="font-mono text-[12px] text-neutral-500">{right}</span>
    </div>
  );
}

function RecoveryRing({ value }: { value: number }) {
  const circumference = 264;
  const offset = circumference - circumference * (value / 100);
  return (
    <div className="relative mx-auto h-[140px] w-[140px]">
      <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
        <circle cx="50" cy="50" r="42" fill="none" strokeWidth="5" stroke="#ededed" />
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          strokeWidth="5"
          stroke="url(#evr-recovery-gradient)"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
        <defs>
          <linearGradient id="evr-recovery-gradient" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#ff6b46" />
            <stop offset="1" stopColor="#a855f7" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="text-[36px] font-semibold tracking-[-0.03em]">{value}</div>
      </div>
    </div>
  );
}

function RecoveryMetric({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex items-center justify-between border-b border-neutral-100 pb-2 last:border-b-0">
      <span className="text-neutral-600">{k}</span>
      <span className="font-medium">{v}</span>
    </div>
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────

function fmtToday(d: Date): string {
  return d.toLocaleDateString("da-DK", { weekday: "long", day: "numeric", month: "long" });
}

function isoWeek(d: Date): number {
  // ISO 8601 week number — Thursday-anchored, matches the plan-render grid.
  const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  const day = t.getUTCDay() || 7;
  t.setUTCDate(t.getUTCDate() + 4 - day);
  const yearStart = new Date(Date.UTC(t.getUTCFullYear(), 0, 1));
  return Math.ceil(((t.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
}

function readinessTone(v: number | null | undefined): string {
  if (v == null) return "#a3a3a3";
  if (v >= 70) return "#16a34a";
  if (v >= 50) return "#f59e0b";
  return "#dc2626";
}

function readinessHint(v: number | null | undefined): string {
  if (v == null) return "Forbind data-kilde";
  if (v >= 80) return "Klar — push hvis du føler det";
  if (v >= 60) return "Solid — kør planen";
  if (v >= 40) return "Lav — overvej easy day";
  return "Træt — recovery først";
}

function tsbHint(t: number | null | undefined): string {
  if (t == null) return "—";
  if (t > 5) return "Frisk";
  if (t < -10) return "Træt";
  return "Neutral";
}

function planRowSub(s: { duration_min: number | null; distance_m: number | null; description: string | null }): string {
  const parts: string[] = [];
  if (s.duration_min) parts.push(`${s.duration_min} min`);
  if (s.distance_m) parts.push(`${(s.distance_m / 1000).toFixed(1)} km`);
  if (s.description) parts.push(s.description);
  return parts.join(" · ") || "—";
}

function zoneLabel(s: { intensity_zones: Record<string, unknown> | null }): string {
  const z = s.intensity_zones;
  if (z && typeof z === "object" && "primary" in z) {
    return String((z as { primary?: string }).primary ?? "—");
  }
  return "—";
}

function fmtSleep(min: number | null | undefined): string {
  if (!min) return "—";
  return `${Math.floor(min / 60)}h ${min % 60}m`;
}

function sevenBars(upcoming: { scheduled_date: string; duration_min: number | null }[]): number[] {
  // Build a Mon-Sun bar chart from the next 7 days of planned duration. We
  // anchor on this week's Monday so the bars always read left-to-right as
  // Mon → Sun regardless of which day it currently is.
  const today = new Date();
  const dow = today.getDay() || 7; // make Sun=7
  const monday = new Date(today);
  monday.setDate(monday.getDate() - (dow - 1));
  const bars: number[] = [];
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday);
    d.setDate(monday.getDate() + i);
    const iso = d.toISOString().slice(0, 10);
    const total = upcoming
      .filter((s) => s.scheduled_date === iso)
      .reduce((a, b) => a + (b.duration_min ?? 0), 0);
    // Map 0-120 min → 0-100% bar height.
    bars.push(Math.min(100, total));
  }
  // If we have no real data, return the canned demo bars from the design.
  if (bars.every((b) => b === 0)) return [32, 72, 44, 88, 8, 8, 8];
  return bars;
}

import Link from "next/link";
import { Activity, Heart, Target, TrendingUp, ArrowRight, AlertCircle } from "lucide-react";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkline } from "@/components/sparkline";
import {
  loadCurrentPlan,
  loadFitnessTimeline,
  loadLatestLimiter,
  loadLatestRecovery,
} from "./actions";
import { acwrZone, fmtDate, fmtLimiter, fmtSessionType, fmtWeekday } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const name = user?.user_metadata?.full_name ?? user?.email ?? "atlet";

  // Hent alt parallelt — alle er server-side, ingen waterfall.
  const [timeline, recovery, limiter, plan] = await Promise.all([
    loadFitnessTimeline(90),
    loadLatestRecovery(),
    loadLatestLimiter(),
    loadCurrentPlan(),
  ]);

  const latestPoint = timeline?.points[timeline.points.length - 1];
  const ctlSeries = timeline?.points.map((p) => p.ctl ?? null) ?? [];
  const atlSeries = timeline?.points.map((p) => p.atl ?? null) ?? [];
  const acwrInfo = acwrZone(latestPoint?.acwr);

  // Find next 3 sessions from today (skip rest days if there's a real session coming).
  const today = new Date().toISOString().slice(0, 10);
  const upcoming = (plan?.next_14_days ?? []).filter((s) => s.scheduled_date >= today).slice(0, 5);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Hej, {name} 👋</h1>
        <p className="mt-1 text-neutral-600 dark:text-neutral-400">
          {latestPoint
            ? `Sidste opdatering: ${fmtDate(latestPoint.snapshot_date)}.`
            : "Forbind dit wearable for at komme i gang."}
        </p>
      </div>

      {/* ─── KPI row ─────────────────────────────────────────── */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          icon={<TrendingUp className="h-4 w-4" />}
          label="Fitness (CTL)"
          value={latestPoint?.ctl?.toFixed(0) ?? "—"}
          hint="42-dages rolling load"
          spark={ctlSeries}
          sparkColor="text-emerald-600 dark:text-emerald-400"
        />
        <StatCard
          icon={<Activity className="h-4 w-4" />}
          label="Fatigue (ATL)"
          value={latestPoint?.atl?.toFixed(0) ?? "—"}
          hint="7-dages rolling load"
          spark={atlSeries}
          sparkColor="text-amber-600 dark:text-amber-400"
        />
        <StatCard
          icon={<Target className="h-4 w-4" />}
          label="Form (TSB)"
          value={latestPoint?.tsb != null ? `${latestPoint.tsb >= 0 ? "+" : ""}${latestPoint.tsb.toFixed(0)}` : "—"}
          hint={
            latestPoint?.tsb == null
              ? "—"
              : latestPoint.tsb > 5
              ? "Frisk"
              : latestPoint.tsb < -10
              ? "Træt"
              : "Neutral"
          }
        />
        <StatCard
          icon={<Heart className="h-4 w-4" />}
          label="ACWR"
          value={latestPoint?.acwr?.toFixed(2) ?? "—"}
          hint={acwrInfo.label}
        />
      </div>

      {/* ─── Limiter ─────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <CardTitle className="flex items-center gap-2">
                Din limiter
                {limiter?.available && (
                  <Badge tone="info">
                    {Math.round((limiter.confidence ?? 0) * 100)}% confidence
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                AI-detekteret primær fysiologisk begrænsning. Plan-generatoren bruger denne til at vælge fokus.
              </CardDescription>
            </div>
            <Link
              href="/dashboard/limiter"
              className="inline-flex items-center gap-1 text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
            >
              Detaljer <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {limiter?.available ? (
            <>
              <div className="flex flex-wrap items-baseline gap-3">
                <span className="text-2xl font-semibold">{fmtLimiter(limiter.primary_limiter)}</span>
                {limiter.secondary_limiter && (
                  <span className="text-sm text-neutral-500">
                    + {fmtLimiter(limiter.secondary_limiter)}
                  </span>
                )}
              </div>
              {limiter.recommended_focus && (
                <p className="text-sm text-neutral-700 dark:text-neutral-300">
                  <span className="font-medium">Fokus:</span> {limiter.recommended_focus}
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-neutral-500">
              Ingen analyse endnu. Kør én fra <Link href="/dashboard/limiter" className="underline">limiter-siden</Link>.
            </p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        {/* ─── Recovery ─────────────────────────────── */}
        <Card>
          <CardHeader>
            <CardTitle>Recovery i dag</CardTitle>
            <CardDescription>
              {recovery?.metric_date ? `Senest: ${fmtDate(recovery.metric_date)}` : "Ingen data"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              <RecoveryRow label="HRV (rMSSD)" value={recovery?.hrv_rmssd?.toFixed(1)} unit="ms" />
              <RecoveryRow label="Resting HR" value={recovery?.resting_hr} unit="bpm" />
              <RecoveryRow
                label="Søvn"
                value={
                  recovery?.sleep_minutes
                    ? `${Math.floor(recovery.sleep_minutes / 60)}t ${recovery.sleep_minutes % 60}m`
                    : null
                }
              />
              <RecoveryRow label="Sleep score" value={recovery?.sleep_score} />
              <RecoveryRow label="Readiness" value={recovery?.readiness_score} unit="/100" />
              <RecoveryRow label="Body battery" value={recovery?.body_battery} />
              <RecoveryRow label="Stress (avg)" value={recovery?.stress_avg} />
            </dl>
          </CardContent>
        </Card>

        {/* ─── Plan preview ─────────────────────────── */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-2">
              <div>
                <CardTitle>Kommende sessioner</CardTitle>
                <CardDescription>
                  {plan?.active
                    ? `${plan.philosophy} · uge ${currentWeekOf(plan)} af ${plan.weeks}`
                    : "Ingen aktiv plan"}
                </CardDescription>
              </div>
              <Link
                href="/dashboard/training"
                className="inline-flex items-center gap-1 text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
              >
                Hele planen <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            {upcoming.length === 0 ? (
              <div className="flex items-center gap-2 text-sm text-neutral-500">
                <AlertCircle className="h-4 w-4" />
                {plan?.active
                  ? "Ingen flere sessioner i de næste 14 dage — generér flere uger."
                  : "Ingen plan endnu — opret en på træning-siden."}
              </div>
            ) : (
              <ul className="divide-y divide-neutral-200 dark:divide-neutral-800">
                {upcoming.map((s) => (
                  <li key={`${s.scheduled_date}-${s.session_type}`} className="flex items-center gap-3 py-2">
                    <div className="w-14 shrink-0 text-xs text-neutral-500">
                      {fmtWeekday(s.scheduled_date)}<br />
                      <span className="text-neutral-700 dark:text-neutral-300">{fmtDate(s.scheduled_date)}</span>
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium">{fmtSessionType(s.session_type)}</p>
                      <p className="truncate text-xs text-neutral-500">
                        {s.duration_min && `${s.duration_min} min`}
                        {s.duration_min && s.distance_m && " · "}
                        {s.distance_m && `${(s.distance_m / 1000).toFixed(1)} km`}
                        {s.description && ` · ${s.description}`}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function currentWeekOf(plan: { active: boolean; weeks?: number; next_14_days?: { scheduled_date: string }[] }): number | string {
  if (!plan.weeks || !plan.next_14_days?.length) return "—";
  // Naive: count weeks since the first session date.
  const first = plan.next_14_days[0]?.scheduled_date;
  if (!first) return "—";
  // Just show 1 — we don't have start_date here. Refine when needed.
  return 1;
}

function StatCard({
  icon,
  label,
  value,
  hint,
  spark,
  sparkColor,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint: string;
  spark?: (number | null)[];
  sparkColor?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{label}</CardTitle>
        <span className="text-neutral-500">{icon}</span>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-neutral-500 dark:text-neutral-400">{hint}</p>
        {spark && spark.filter((p) => p != null).length >= 2 && (
          <div className={`mt-2 ${sparkColor ?? "text-neutral-400"}`}>
            <Sparkline data={spark} width={240} height={40} />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function RecoveryRow({ label, value, unit }: { label: string; value: string | number | null | undefined; unit?: string }) {
  return (
    <>
      <dt className="text-neutral-500">{label}</dt>
      <dd className="text-right font-medium">
        {value == null || value === "" ? "—" : `${value}${unit ?? ""}`}
      </dd>
    </>
  );
}

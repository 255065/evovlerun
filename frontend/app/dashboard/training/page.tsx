import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { loadCurrentPlan } from "../actions";
import { fmtDate, fmtSessionType, fmtWeekday } from "@/lib/format";
import { PlanGeneratorForm } from "./plan-form";

export const dynamic = "force-dynamic";

export default async function TrainingPage() {
  const plan = await loadCurrentPlan();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[36px] font-semibold tracking-[-0.025em]">Training</h1>
        <p className="mt-1 text-[14px] text-neutral-600">
          Set a race goal and let the AI build a periodized plan based on your fitness and limiter.
        </p>
      </div>

      {plan?.active ? <ActivePlanView plan={plan} /> : <PlanGeneratorForm />}
    </div>
  );
}

function ActivePlanView({ plan }: { plan: NonNullable<Awaited<ReturnType<typeof loadCurrentPlan>>> }) {
  const bp = plan.blueprint;
  return (
    <div className="space-y-6">
      {/* Header card */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <CardTitle className="text-2xl">
                {plan.race_type?.replace("_", " ")} ·{" "}
                <span className="text-neutral-500">{plan.philosophy}</span>
              </CardTitle>
              <CardDescription className="mt-1">
                {plan.weeks} uger · Race / milestone: {plan.race_date}
              </CardDescription>
            </div>
            <Badge tone="success">{plan.current_phase ?? "—"}</Badge>
          </div>
        </CardHeader>
        {bp?.guiding_principles && bp.guiding_principles.length > 0 && (
          <CardContent>
            <p className="mb-2 text-sm font-medium">Guiding principles</p>
            <ul className="space-y-1 text-sm text-neutral-700 dark:text-neutral-300">
              {bp.guiding_principles.map((p, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-neutral-400">•</span>
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        )}
      </Card>

      {/* Phases */}
      {bp?.phases && bp.phases.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Faser</CardTitle>
            <CardDescription>Den overordnede struktur AI'en valgte</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {bp.phases.map((p, i) => (
                <div
                  key={i}
                  className="rounded-md border border-neutral-200 p-3 dark:border-neutral-800"
                >
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <p className="font-medium capitalize">{p.name}</p>
                    <p className="text-xs text-neutral-500">
                      {p.week_count} uger · {p.weekly_volume_hours} t/uge
                    </p>
                  </div>
                  <p className="mt-1 text-xs text-neutral-600 dark:text-neutral-400">
                    {p.weekly_intensity_focus}
                  </p>
                  <p className="mt-2 text-xs text-neutral-500">
                    <em>Hvorfor:</em> {p.rationale}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upcoming sessions */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Kommende sessioner</CardTitle>
          <CardDescription>De næste 14 dage med rationale per session</CardDescription>
        </CardHeader>
        <CardContent>
          {(plan.next_14_days ?? []).length === 0 ? (
            <p className="text-sm text-neutral-500">
              Ingen sessioner genereret endnu — kør generatoren igen for at expand'e flere uger.
            </p>
          ) : (
            <ul className="divide-y divide-neutral-200 dark:divide-neutral-800">
              {(plan.next_14_days ?? []).map((s, idx) => {
                const isRest = s.session_type === "rest";
                return (
                  <li key={`${s.scheduled_date}-${idx}`} className="py-3">
                    <div className="flex items-start gap-3">
                      <div className="w-14 shrink-0 text-xs text-neutral-500">
                        <span className="font-medium text-neutral-700 dark:text-neutral-300">
                          {fmtWeekday(s.scheduled_date)}
                        </span>
                        <br />
                        {fmtDate(s.scheduled_date)}
                      </div>
                      <div className="min-w-0 flex-1 space-y-1">
                        <div className="flex flex-wrap items-baseline gap-2">
                          <span className={`font-medium ${isRest ? "text-neutral-500" : ""}`}>
                            {fmtSessionType(s.session_type)}
                          </span>
                          {s.duration_min && (
                            <span className="text-xs text-neutral-500">{s.duration_min} min</span>
                          )}
                          {s.distance_m && (
                            <span className="text-xs text-neutral-500">
                              {(s.distance_m / 1000).toFixed(1)} km
                            </span>
                          )}
                        </div>
                        {s.description && (
                          <p className="text-sm text-neutral-700 dark:text-neutral-300">
                            {s.description}
                          </p>
                        )}
                        {s.rationale && (
                          <p className="text-xs text-neutral-500">
                            <em>Hvorfor:</em> {s.rationale}
                          </p>
                        )}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Auto-adapt triggers */}
      {bp?.auto_adapt_triggers && bp.auto_adapt_triggers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Adapt-triggers</CardTitle>
            <CardDescription>
              Forhold der vil få planen til at justere sig
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="space-y-1 text-sm text-neutral-700 dark:text-neutral-300">
              {bp.auto_adapt_triggers.map((t, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-neutral-400">•</span>
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Regenerate */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Ny plan</CardTitle>
          <CardDescription>
            Overskriv den nuværende. Den gamle markeres &quot;paused&quot; men slettes ikke.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <PlanGeneratorForm />
        </CardContent>
      </Card>
    </div>
  );
}

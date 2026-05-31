import Link from "next/link";
import { loadCurrentPlan } from "../actions";
import { fmtDate, fmtSessionType, fmtWeekday } from "@/lib/format";

export const dynamic = "force-dynamic";

/**
 * Training page — read-only view of the plan the chat assistant saved.
 *
 * V1 has no in-app plan generator. The assistant (Claude / ChatGPT /
 * Gemini, via the EvolveRun MCP connector) writes plans and persists
 * them through `save-training-plan`. This page just renders whatever
 * is active, plus an empty state when nothing is.
 */
export default async function TrainingPage() {
  const plan = await loadCurrentPlan();

  return (
    <div className="space-y-8 pb-16">
      <div>
        <h1 className="text-[36px] font-semibold tracking-[-0.025em]">Training</h1>
        <p className="mt-1 text-[14px] text-neutral-600">
          The active plan your AI coach saved through the EvolveRun connector.
        </p>
      </div>

      {plan?.active ? <ActivePlan plan={plan} /> : <EmptyState />}
    </div>
  );
}

export function EmptyState() {
  return (
    <div className="rounded-2xl border border-neutral-200/70 bg-white/70 p-8 text-center">
      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-neutral-500">
        No plan yet
      </div>
      <h2 className="mt-3 text-[20px] font-semibold tracking-[-0.01em]">
        Create a training plan with your chatbot
      </h2>
      <p className="mx-auto mt-3 max-w-md text-[14.5px] text-neutral-700">
        EvolveRun doesn&apos;t generate plans in the app. Ask your connected AI coach —
        Claude, ChatGPT, or Gemini — through the EvolveRun connector to build a plan and
        save it. Once saved, it shows up here automatically.
      </p>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-4">
        <a
          href="https://claude.ai"
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center rounded-md bg-neutral-950 px-4 py-2 text-[13px] font-medium text-white"
        >
          Open Claude
        </a>
        <Link
          href="/dashboard/mcp"
          className="text-[13px] text-[color:var(--evr-accent)] hover:underline"
        >
          Set up the connector
        </Link>
      </div>
    </div>
  );
}

function ActivePlan({ plan }: { plan: NonNullable<Awaited<ReturnType<typeof loadCurrentPlan>>> }) {
  const bp = plan.blueprint;
  return (
    <div className="space-y-8">
      <div className="rounded-2xl border border-neutral-200/70 bg-white/70 p-6">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-neutral-500">
              Active plan
            </div>
            <div className="mt-1 text-[20px] font-semibold capitalize tracking-[-0.01em]">
              {plan.race_type?.replace(/_/g, " ")}
              {plan.philosophy && <span className="text-neutral-500"> · {plan.philosophy}</span>}
            </div>
            <div className="mt-1 text-[13px] text-neutral-600">
              {plan.weeks} weeks{plan.race_date && ` · target ${plan.race_date}`}
            </div>
          </div>
          {plan.current_phase && (
            <span className="rounded-full bg-emerald-100 px-2.5 py-[3px] text-[11px] font-medium text-emerald-800">
              {plan.current_phase}
            </span>
          )}
        </div>

        {bp?.guiding_principles && bp.guiding_principles.length > 0 && (
          <div className="mt-5">
            <div className="font-mono text-[10.5px] uppercase tracking-[0.15em] text-neutral-500">
              Guiding principles
            </div>
            <ul className="mt-2 space-y-1 text-[13.5px] text-neutral-700">
              {bp.guiding_principles.map((p, i) => (
                <li key={i} className="flex gap-2">
                  <span className="text-neutral-400">•</span>
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="rounded-2xl border border-neutral-200/70 bg-white/70 p-6">
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-neutral-500">
          Next 14 days
        </div>
        {(plan.next_14_days ?? []).length === 0 ? (
          <p className="mt-4 text-[13.5px] text-neutral-600">
            No sessions in the next 14 days. Ask your AI coach to extend the plan.
          </p>
        ) : (
          <ul className="mt-4 divide-y divide-neutral-200/60">
            {(plan.next_14_days ?? []).map((s, idx) => {
              const isRest = s.session_type === "rest";
              return (
                <li key={`${s.scheduled_date}-${idx}`} className="py-3.5">
                  <div className="flex items-start gap-4">
                    <div className="w-16 shrink-0 font-mono text-[11px] text-neutral-500">
                      <span className="block text-[13px] font-medium text-neutral-800">
                        {fmtWeekday(s.scheduled_date)}
                      </span>
                      {fmtDate(s.scheduled_date)}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <span className={`text-[14.5px] font-medium ${isRest ? "text-neutral-500" : ""}`}>
                          {fmtSessionType(s.session_type)}
                        </span>
                        {s.duration_min && (
                          <span className="text-[12px] text-neutral-500">{s.duration_min} min</span>
                        )}
                        {s.distance_m && (
                          <span className="text-[12px] text-neutral-500">
                            {(s.distance_m / 1000).toFixed(1)} km
                          </span>
                        )}
                      </div>
                      {s.description && (
                        <p className="mt-1 text-[13.5px] text-neutral-700">{s.description}</p>
                      )}
                      {s.rationale && (
                        <p className="mt-1 text-[12.5px] text-neutral-500">{s.rationale}</p>
                      )}
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

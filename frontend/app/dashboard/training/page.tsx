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
        <h1 className="evr-headline text-[clamp(34px,4.5vw,48px)] tracking-[-0.03em]">Training</h1>
        <p className="mt-2 text-[15px] text-[#5f564d]">
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
  const sessions = plan.next_14_days ?? [];
  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-[#1a1612]/10 bg-[#fbf8f1] p-6">
      <div className="text-[12px] font-semibold uppercase tracking-[0.18em] text-[#dc6b3f]">
        Next 14 days
      </div>
      {sessions.length === 0 ? (
        <p className="mt-4 text-[13.5px] text-[#6b6259]">
          No sessions in the next 14 days. Ask your AI coach to extend the plan.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-[#1a1612]/10 text-[#8a7f74]">
                <Th className="w-28">Day</Th>
                <Th className="w-32">Session</Th>
                <Th className="w-20">Duration</Th>
                <Th className="w-20">Distance</Th>
                <Th>Details</Th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((s, idx) => {
                const isRest = s.session_type === "rest";
                return (
                  <tr
                    key={`${s.scheduled_date}-${idx}`}
                    className="border-b border-[#1a1612]/8 align-top last:border-0"
                  >
                    <td className="py-3 pr-3">
                      <span className="block text-[13px] font-medium text-[#1a1612]">
                        {fmtWeekday(s.scheduled_date)}
                      </span>
                      <span className="font-mono text-[11px] text-[#8a7f74]">
                        {fmtDate(s.scheduled_date)}
                      </span>
                    </td>
                    <td className="py-3 pr-3">
                      <span
                        className={`text-[14px] font-medium ${isRest ? "text-[#8a7f74]" : ""}`}
                      >
                        {fmtSessionType(s.session_type)}
                      </span>
                    </td>
                    <td className="py-3 pr-3 text-[13px] text-[#6b6259]">
                      {s.duration_min ? `${s.duration_min} min` : "—"}
                    </td>
                    <td className="py-3 pr-3 text-[13px] text-[#6b6259]">
                      {s.distance_m ? `${(s.distance_m / 1000).toFixed(1)} km` : "—"}
                    </td>
                    <td className="py-3 text-[13px] text-[#4b423a]">
                      {s.description ? <span>{s.description}</span> : <span className="text-[#a89e92]">—</span>}
                      {s.rationale && (
                        <p className="mt-1 text-[12px] text-[#8a7f74]">{s.rationale}</p>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      </div>
      <p className="px-1 text-[13.5px] text-[#5f564d]">
        Want to change your training plan?{" "}
        <Link
          href="/dashboard/mcp"
          className="font-medium text-[#dc6b3f] hover:underline"
        >
          Ask your AI coach →
        </Link>
      </p>
    </div>
  );
}

function Th({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <th
      className={`pb-2 pr-3 font-mono text-[10.5px] font-medium uppercase tracking-[0.15em] text-[#8a7f74] ${className}`}
    >
      {children}
    </th>
  );
}

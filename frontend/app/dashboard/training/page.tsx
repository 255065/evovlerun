import Link from "next/link";
import { loadCurrentPlan, type PlannedSession } from "../actions";
import { fmtSessionType, fmtDistance, fmtDate } from "@/lib/format";

export const dynamic = "force-dynamic";

type SearchParams = { week?: string };

/**
 * Training page — read-only view of the plan the chat assistant saved.
 *
 * V1 has no in-app plan generator. The assistant (Claude / ChatGPT /
 * Gemini, via the EvolveRun MCP connector) writes plans through
 * `save-training-plan`. This page renders the schedule one week at a time
 * (paged via ?week=<offset>), plus an empty state when nothing is saved.
 */
export default async function TrainingPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const { week: weekParam } = await searchParams;
  const weekOffset = Number.parseInt(weekParam ?? "0", 10) || 0;

  const plan = await loadCurrentPlan();

  if (!plan?.active) {
    return (
      <>
        <Header subtitle="Your AI coach hasn't saved a plan yet." />
        <div className="mt-10">
          <EmptyState />
        </div>
      </>
    );
  }

  const week = buildWeek(plan.next_14_days ?? [], weekOffset);
  const rangeLabel = `${fmtDate(week[0].iso)} — ${fmtDate(week[6].iso)}`;
  const weekLabel = `${weekOffset === 0 ? "This week · " : ""}${rangeLabel}`;

  return (
    <>
      <div className="flex items-end justify-between gap-6">
        <div>
          {/* Week navigation */}
          <div className="flex items-center gap-3">
            <WeekArrow href={`/dashboard/training?week=${weekOffset - 1}`} label="Previous week" dir="prev" />
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-neutral-500">
              {weekLabel}
            </div>
            <WeekArrow href={`/dashboard/training?week=${weekOffset + 1}`} label="Next week" dir="next" />
          </div>
          <h1 className="evr-headline mt-3 text-[clamp(40px,6vw,56px)] leading-[1] tracking-[-0.03em]">
            Training plan
          </h1>
        </div>
        <a
          href="https://claude.ai"
          target="_blank"
          rel="noreferrer"
          className="hidden rounded-lg bg-neutral-950 px-4 py-2.5 text-[13.5px] font-medium text-white hover:bg-neutral-800 md:inline-flex"
        >
          Regenerate with AI →
        </a>
      </div>

      {/* Week schedule */}
      <div className="mt-10 font-mono text-[11px] uppercase tracking-[0.18em] text-neutral-500">
        Schedule
      </div>
      <div className="mt-4 overflow-hidden rounded-2xl border border-neutral-200 bg-white">
        {week.map((d, i) => (
          <SessionRow key={d.iso} day={d} divider={i > 0} />
        ))}
      </div>
    </>
  );
}

function Header({ subtitle }: { subtitle: string }) {
  return (
    <div>
      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-neutral-500">
        Training plan
      </div>
      <h1 className="evr-headline mt-3 text-[clamp(40px,6vw,56px)] leading-[1] tracking-[-0.03em]">
        Training plan
      </h1>
      <p className="mt-4 max-w-xl text-[15px] text-neutral-600">{subtitle}</p>
    </div>
  );
}

export function EmptyState() {
  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-8 text-center">
      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-neutral-500">
        No plan yet
      </div>
      <h2 className="mt-3 text-[20px] font-semibold tracking-[-0.01em]">
        Create a training plan with your chatbot
      </h2>
      <p className="mx-auto mt-3 max-w-md text-[14.5px] text-neutral-600">
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
        <Link href="/dashboard/mcp" className="text-[13px] font-medium text-[#dc6b3f] hover:underline">
          Set up the connector
        </Link>
      </div>
    </div>
  );
}

// ─── Week model ────────────────────────────────────────────────────

type DaySlot = { iso: string; weekday: string; date: string; sessions: PlannedSession[] };

const WEEKDAY_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

function isoLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Mon–Sun of (current week + weekOffset); each day holds all its sessions. */
function buildWeek(sessions: PlannedSession[], weekOffset: number): DaySlot[] {
  const byDate = new Map<string, PlannedSession[]>();
  for (const s of sessions) {
    const arr = byDate.get(s.scheduled_date) ?? [];
    arr.push(s);
    byDate.set(s.scheduled_date, arr);
  }

  const now = new Date();
  const dow = now.getDay(); // 0 Sun … 6 Sat
  const mondayOffset = dow === 0 ? -6 : 1 - dow;
  const monday = new Date(now);
  monday.setDate(now.getDate() + mondayOffset + weekOffset * 7);

  const week: DaySlot[] = [];
  for (let i = 0; i < 7; i++) {
    const date = new Date(monday);
    date.setDate(monday.getDate() + i);
    const iso = isoLocal(date);
    week.push({
      iso,
      weekday: WEEKDAY_SHORT[date.getDay()],
      date: fmtDate(iso),
      sessions: byDate.get(iso) ?? [],
    });
  }
  return week;
}

type LovableType = "Easy" | "Quality" | "Long" | "Rest" | "Recovery" | "Strength" | "Swim";

function lovableType(t: string): LovableType {
  if (t === "long") return "Long";
  if (["tempo", "threshold", "intervals", "vo2max", "fartlek", "hills", "race"].includes(t)) return "Quality";
  if (t === "strength") return "Strength";
  if (t === "cross_training") return "Swim";
  if (t === "recovery") return "Recovery";
  return "Easy";
}

const TYPE_COLORS: Record<LovableType, { bg: string; text: string }> = {
  Easy: { bg: "#e8f0e6", text: "#3d6b34" },
  Quality: { bg: "#fde2d4", text: "#a13e1a" },
  Long: { bg: "#e4ddf5", text: "#4a3a8a" },
  Recovery: { bg: "#dfeef0", text: "#2e6b75" },
  Strength: { bg: "#e6e8ef", text: "#404a63" },
  Swim: { bg: "#d8e8fb", text: "#2456a6" },
  Rest: { bg: "#f0ece4", text: "#6b6356" },
};

/** The real activity name to show — cross_training in this plan is swimming. */
function sessionTitle(sessionType: string): string {
  if (sessionType === "cross_training") return "Swimming";
  return fmtSessionType(sessionType);
}

// ─── Sub-components ────────────────────────────────────────────────

function WeekArrow({ href, label, dir }: { href: string; label: string; dir: "prev" | "next" }) {
  return (
    <Link
      href={href}
      aria-label={label}
      className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-neutral-300 text-neutral-600 transition hover:bg-neutral-100 hover:text-neutral-950"
    >
      {dir === "prev" ? "←" : "→"}
    </Link>
  );
}

function SessionRow({ day, divider }: { day: DaySlot; divider: boolean }) {
  const rest = TYPE_COLORS.Rest;
  return (
    <div
      className={`grid grid-cols-[80px_1fr] gap-4 px-5 py-4 sm:grid-cols-[90px_1fr] ${
        divider ? "border-t border-neutral-200" : ""
      }`}
    >
      <div>
        <div className="text-[14px] font-semibold">{day.weekday}</div>
        <div className="text-[12px] text-neutral-500">{day.date}</div>
      </div>
      <div className="space-y-3">
        {day.sessions.length === 0 ? (
          <div className="flex items-center gap-2">
            <span
              className="rounded-full px-2.5 py-[3px] text-[11px] font-medium"
              style={{ background: rest.bg, color: rest.text }}
            >
              Rest
            </span>
            <span className="text-[13px] text-neutral-500">No session scheduled.</span>
          </div>
        ) : (
          day.sessions.map((s, i) => <SessionItem key={i} session={s} />)
        )}
      </div>
    </div>
  );
}

function SessionItem({ session }: { session: PlannedSession }) {
  const type = lovableType(session.session_type);
  const c = TYPE_COLORS[type];
  const title = sessionTitle(session.session_type);
  const distance = session.distance_m ? fmtDistance(session.distance_m) : null;
  const duration = session.duration_min ? `${session.duration_min} min` : null;
  const meta = [distance, duration].filter(Boolean).join(" · ");

  return (
    <div>
      <div className="flex flex-wrap items-center gap-2">
        <span
          className="rounded-full px-2.5 py-[3px] text-[11px] font-medium"
          style={{ background: c.bg, color: c.text }}
        >
          {type}
        </span>
        <span className="text-[14.5px] font-semibold">{title}</span>
        {meta && <span className="text-[12.5px] text-neutral-500">· {meta}</span>}
      </div>
      {session.description && (
        <div className="mt-1 text-[12.5px] leading-relaxed text-neutral-500">{session.description}</div>
      )}
    </div>
  );
}

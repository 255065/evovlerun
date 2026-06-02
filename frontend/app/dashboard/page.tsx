import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { loadActivitySummary } from "./actions";
import {
  connectProviderAction,
  disconnectProviderAction,
  getConnectionStatus,
  syncProviderAction,
} from "./connections/actions";
import { CopyButton } from "./copy-button";
import { LatestActivityCard } from "./latest-activity-card";

export const dynamic = "force-dynamic";

const QUICK_PROMPTS = [
  "How did this week compare to last?",
  "Am I ready for tomorrow's long run?",
  "Plan my next 7 days around a tempo Tuesday.",
  "Why was last Saturday's long run so hard?",
  "Am I training polarized or stuck in the grey zone?",
  "Write me a 12-week marathon plan based on my last 3 months of data.",
];

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const athleteName = (user?.user_metadata?.full_name ?? "").trim() || "Athlete";
  const firstName = athleteName.split(" ")[0] || "athlete";

  const [strava, summary] = await Promise.all([
    getConnectionStatus("strava"),
    loadActivitySummary(),
  ]);

  const connected = strava?.connected ?? false;
  const latest = summary?.latest ?? null;
  const week = summary?.week ?? { activities: 0, km: 0, hours: 0 };

  return (
    <>
      <h1 className="evr-headline text-[clamp(40px,6vw,64px)] leading-[1] tracking-[-0.03em]">
        Dashboard
      </h1>
      <p className="mt-4 text-[15px] text-neutral-600">
        Welcome back, <span className="capitalize">{firstName}</span>.
      </p>

      {/* Connected sources */}
      <SectionLabel className="mt-16">Connected sources</SectionLabel>
      <Row
        icon={
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#fc5200]">
            <svg viewBox="0 0 24 24" className="h-6 w-6" fill="#fff">
              <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169" />
            </svg>
          </div>
        }
        title="Strava"
        desc={
          connected
            ? "Synced — webhook listening for new activities"
            : "Not connected — link Strava to sync your runs"
        }
        right={
          connected ? (
            <div className="flex items-center gap-4">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-[12px] font-medium text-emerald-700">
                Synced
              </span>
              <form action={syncProviderAction}>
                <input type="hidden" name="provider" value="strava" />
                <input type="hidden" name="days" value="30" />
                <button type="submit" className="text-[13px] text-neutral-500 hover:text-neutral-950">
                  Sync
                </button>
              </form>
              <form action={disconnectProviderAction}>
                <input type="hidden" name="provider" value="strava" />
                <button type="submit" className="text-[13px] text-neutral-500 hover:text-neutral-950">
                  Disconnect
                </button>
              </form>
            </div>
          ) : (
            <form action={connectProviderAction}>
              <input type="hidden" name="provider" value="strava" />
              <button
                type="submit"
                className="rounded-md bg-neutral-950 px-3.5 py-1.5 text-[13px] font-medium text-white hover:bg-neutral-800"
              >
                Connect
              </button>
            </form>
          )
        }
      />

      {/* AI coach */}
      <SectionHeader label="AI coach" action="Open setup" href="/dashboard/mcp" />
      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
        <CoachCard name="Claude" tagline="Considered, careful with nuance" logo={<ClaudeLogo />} bg="#fde2d4" />
        <CoachCard name="ChatGPT" tagline="Versatile, fast, broad" logo={<ChatGPTLogo />} bg="#d6f0e2" />
      </div>

      {/* Latest activity */}
      <SectionLabel className="mt-16">Latest activity</SectionLabel>
      <div className="mt-4">
        {latest ? (
          <LatestActivityCard latest={latest} athleteName={athleteName} />
        ) : (
          <div className="rounded-2xl border border-neutral-200 bg-white px-5 py-6 text-[13.5px] text-neutral-500">
            No activities yet. Your latest run will appear here once Strava finishes its first sync.
          </div>
        )}
      </div>

      {/* This week */}
      <SectionLabel className="mt-16">This week</SectionLabel>
      <div className="mt-4 grid grid-cols-3 gap-4">
        <StatCard label="Activities" value={String(week.activities)} />
        <StatCard label="Total km" value={week.km.toFixed(1)} />
        <StatCard label="Total hours" value={week.hours.toFixed(1)} />
      </div>

      {/* Quick prompts */}
      <SectionHeader label="Quick prompts" action="Connector setup" href="/dashboard/mcp" />
      <p className="mt-4 text-[15px] text-neutral-700">
        Copy any of these into Claude.ai, ChatGPT, or Gemini once the EvolveRun connector is attached.
      </p>
      <div className="mt-6 space-y-3">
        {QUICK_PROMPTS.map((p) => (
          <div
            key={p}
            className="flex items-center justify-between gap-4 rounded-2xl border border-neutral-200 bg-white px-5 py-3"
          >
            <div className="text-[14.5px] text-neutral-800">{p}</div>
            <CopyButton text={p} />
          </div>
        ))}
      </div>
    </>
  );
}

// ─── Sub-components ────────────────────────────────────────────────

function SectionLabel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`font-mono text-[11px] uppercase tracking-[0.18em] text-neutral-500 ${className}`}>
      {children}
    </div>
  );
}

function SectionHeader({ label, action, href }: { label: string; action: string; href: string }) {
  return (
    <div className="mt-16 flex items-end justify-between">
      <SectionLabel>{label}</SectionLabel>
      <Link href={href} className="text-[13px] font-medium text-[#dc6b3f] hover:underline">
        {action}
      </Link>
    </div>
  );
}

function Row({
  icon,
  title,
  desc,
  right,
}: {
  icon: React.ReactNode;
  title: string;
  desc: string;
  right: React.ReactNode;
}) {
  return (
    <div className="mt-4 flex items-center justify-between rounded-2xl border border-neutral-200 bg-white px-5 py-4">
      <div className="flex items-center gap-4">
        {icon}
        <div>
          <div className="text-[15px] font-semibold">{title}</div>
          <div className="text-[13px] text-neutral-600">{desc}</div>
        </div>
      </div>
      {right}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-neutral-200 bg-white p-5">
      <div className="font-mono text-[10.5px] uppercase tracking-[0.16em] text-neutral-500">{label}</div>
      <div className="mt-2 text-[28px] font-semibold tracking-[-0.02em]">{value}</div>
    </div>
  );
}

function CoachCard({
  name,
  tagline,
  logo,
  bg,
}: {
  name: string;
  tagline: string;
  logo: React.ReactNode;
  bg: string;
}) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-neutral-200 bg-white px-5 py-5">
      <div className="flex items-center gap-4">
        <div className="flex h-12 w-12 items-center justify-center rounded-xl" style={{ background: bg }}>
          {logo}
        </div>
        <div>
          <div className="text-[15.5px] font-semibold">{name}</div>
          <div className="text-[13px] text-neutral-600">{tagline}</div>
        </div>
      </div>
      <Link
        href="/dashboard/mcp"
        className="rounded-md border border-neutral-300 bg-white px-3.5 py-1.5 text-[13px] font-medium text-neutral-950 hover:bg-neutral-50"
      >
        Add
      </Link>
    </div>
  );
}

function ClaudeLogo() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="#cc785c">
      <path d="M4.2 18.6 9 6h2.4l4.8 12.6h-2.3l-1.1-3h-5l-1.1 3H4.2Zm4.5-4.9h3.5L10.5 9 8.7 13.7Zm8.7 4.9V6h2.2v12.6h-2.2Z" />
    </svg>
  );
}

function ChatGPTLogo() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="#10a37f" strokeWidth="1.6">
      <path
        d="M21.55 10.36a5.45 5.45 0 0 0-.47-4.48 5.52 5.52 0 0 0-5.94-2.65A5.49 5.49 0 0 0 6.7 4.51a5.46 5.46 0 0 0-3.65 2.65 5.52 5.52 0 0 0 .68 6.48 5.45 5.45 0 0 0 .47 4.48 5.52 5.52 0 0 0 5.94 2.65 5.48 5.48 0 0 0 4.13 1.84 5.5 5.5 0 0 0 5.25-3.81 5.46 5.46 0 0 0 3.65-2.65 5.52 5.52 0 0 0-.62-6.79Z"
        fill="#10a37f"
        fillOpacity="0.12"
      />
      <path d="m9 9.5 3-1.7 3 1.7v3.4L12 14.6 9 12.9V9.5Z" />
    </svg>
  );
}

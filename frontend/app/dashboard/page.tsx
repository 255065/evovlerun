import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import {
  loadActivitySummary,
  loadCurrentPlan,
} from "./actions";
import { fmtRelative } from "@/lib/format";
import {
  connectProviderAction,
  disconnectProviderAction,
  getConnectionStatus,
  syncProviderAction,
} from "./connections/actions";
import { CopyButton } from "./copy-button";
import { LatestActivityCard } from "./latest-activity-card";

export const dynamic = "force-dynamic";

/**
 * Chirona-style dashboard:
 *   - Connected sources (Strava — the only V1 provider)
 *   - AI coaches (Claude / ChatGPT / Gemini connector links)
 *   - Latest activity (most recent workout from Strava)
 *   - This week (trailing-7-day activity / km / hours totals)
 *   - Quick prompts the user can fire into their chat connector
 *
 * No dense data tables, no nested cards. Each section is a single,
 * scannable block on the warm-beige surface.
 */
export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const athleteName = (user?.user_metadata?.full_name ?? "").trim() || "Athlete";
  const fullName = athleteName.split(" ")[0] || "athlete";

  const [strava, activity, plan] = await Promise.all([
    getConnectionStatus("strava"),
    loadActivitySummary(),
    loadCurrentPlan(),
  ]);

  const latest = activity?.latest ?? null;
  const week = activity?.week ?? { activities: 0, km: 0, hours: 0 };
  const todayIso = new Date().toISOString().slice(0, 10);
  const today = plan?.next_14_days?.find((s) => s.scheduled_date === todayIso);

  return (
    <div className="space-y-12 pb-16">
      <div>
        <h1 className="evr-headline text-[clamp(36px,5vw,52px)] tracking-[-0.03em]">Dashboard</h1>
        <p className="mt-2 text-[15px] text-[#5f564d]">
          Welcome back, {fullName}.
        </p>
      </div>

      {/* ─── Connected sources ───────────────────────────────── */}
      <Section
        eyebrow="Connected sources"
        right={
          strava?.connected ? <SyncNowButton /> : <ConnectStravaButton />
        }
      >
        <SourceRow
          name="Strava"
          subtitle={
            strava?.connected
              ? `Last synced ${fmtRelative(strava.last_sync_at)}`
              : "Not connected"
          }
          connected={strava?.connected ?? false}
          color="#fc4c02"
          icon={
            <svg viewBox="0 0 24 24" className="h-6 w-6" fill="currentColor">
              <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169" />
            </svg>
          }
        />
      </Section>

      {/* ─── AI coach ────────────────────────────────────────── */}
      <Section
        eyebrow="AI coach"
        right={<Link href="/dashboard/mcp" className="text-[13px] text-[color:var(--evr-accent)] hover:underline">Open setup</Link>}
      >
        <div className="space-y-2">
          <CoachRow
            name="Claude"
            subtitle="Considered, careful with nuance"
            color="#d97757"
          />
          <CoachRow
            name="ChatGPT"
            subtitle="Versatile, fast, broad"
            color="#10a37f"
          />
          <CoachRow
            name="Gemini"
            subtitle="Multimodal, web-aware"
            color="#4285f4"
          />
        </div>
      </Section>

      {/* ─── Latest activity ─────────────────────────────────── */}
      <Section
        eyebrow="Latest activity"
        right={
          strava?.connected && (
            <span className="text-[12px] text-[#7a7168]">
              Synced {fmtRelative(strava.last_sync_at)}
            </span>
          )
        }
      >
        {latest === null ? (
          <div className="rounded-2xl border border-[#1a1612]/10 bg-[#fbf8f1] p-4">
            <p className="text-[13.5px] text-[#6b6259]">
              We&apos;ll show your latest activity once Strava has finished its first sync.
            </p>
          </div>
        ) : (
          <LatestActivityCard latest={latest} athleteName={athleteName} />
        )}
      </Section>

      {/* ─── This week ───────────────────────────────────────── */}
      <Section eyebrow="This week">
        <div className="rounded-2xl border border-[#1a1612]/10 bg-[#fbf8f1] p-4">
          {week.activities === 0 ? (
            <p className="text-[13.5px] text-[#6b6259]">No activities in the last 7 days.</p>
          ) : (
            <div className="grid grid-cols-3 gap-x-8 gap-y-2">
              <LoadStat label="Activities" value={String(week.activities)} />
              <LoadStat label="Total km" value={week.km.toFixed(1)} />
              <LoadStat label="Total hours" value={week.hours.toFixed(1)} />
            </div>
          )}
        </div>

        {today && (
          <div className="mt-5 rounded-xl border border-[#dc6b3f]/25 bg-[#dc6b3f]/8 p-4">
            <div className="font-mono text-[11px] uppercase tracking-widest text-[#9e4728]">
              Today
            </div>
            <div className="mt-1 text-[15px] font-medium">{capitalize(today.session_type)}</div>
            <div className="text-[13px] text-[#7a4225]">
              {planRowSub(today)}
            </div>
          </div>
        )}
      </Section>

      {/* ─── Quick prompts ───────────────────────────────────── */}
      <Section
        eyebrow="Quick prompts"
        right={<Link href="/dashboard/mcp" className="text-[13px] text-[color:var(--evr-accent)] hover:underline">Connector setup</Link>}
      >
        <p className="mb-4 text-[13px] text-[#6b6259]">
          Copy any of these into Claude.ai, ChatGPT, or Gemini once the EvolveRun connector is attached.
        </p>
        <div className="space-y-2">
          {QUICK_PROMPTS.map((p) => (
            <PromptRow key={p} text={p} />
          ))}
        </div>
      </Section>
    </div>
  );

  /** Inline server-action button — keeps the file self-contained */
  function ConnectStravaButton() {
    return (
      <form action={connectProviderAction}>
        <input type="hidden" name="provider" value="strava" />
        <button
          type="submit"
          className="text-[13px] text-[color:var(--evr-accent)] hover:underline"
        >
          Connect
        </button>
      </form>
    );
  }

  /** Manual re-sync — pulls the last 30 days from Strava (webhook is the
   *  automatic path; this is the "I just finished, refresh now" escape hatch). */
  function SyncNowButton() {
    return (
      <form action={syncProviderAction}>
        <input type="hidden" name="provider" value="strava" />
        <input type="hidden" name="days" value="30" />
        <button
          type="submit"
          className="text-[13px] text-[color:var(--evr-accent)] hover:underline"
        >
          Sync now
        </button>
      </form>
    );
  }
}

// ─── Sub-components ────────────────────────────────────────────────

function Section({
  eyebrow,
  right,
  children,
}: {
  eyebrow: string;
  right?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section>
      <div className="mb-3 flex items-center justify-between">
        <span className="text-[12px] font-semibold uppercase tracking-[0.18em] text-[#dc6b3f]">
          {eyebrow}
        </span>
        {right}
      </div>
      {children}
    </section>
  );
}

function SourceRow({
  name,
  subtitle,
  connected,
  color,
  icon,
}: {
  name: string;
  subtitle: string;
  connected: boolean;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-[#1a1612]/10 bg-[#fbf8f1] p-4">
      <div
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-white"
        style={{ background: color }}
      >
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[15px] font-semibold tracking-[-0.005em]">{name}</div>
        <div className="truncate text-[12.5px] text-[#6b6259]">{subtitle}</div>
      </div>
      {connected ? (
        <span className="rounded-full bg-emerald-100 px-2.5 py-[3px] text-[11px] font-medium text-emerald-800">
          Synced
        </span>
      ) : (
        <span className="rounded-full bg-[#1a1612]/8 px-2.5 py-[3px] text-[11px] font-medium text-[#7a7168]">
          Not connected
        </span>
      )}
      {connected && (
        <form action={disconnectProviderAction}>
          <input type="hidden" name="provider" value="strava" />
          <button type="submit" className="text-[12.5px] text-[#7a7168] hover:text-[#1a1612]">
            Disconnect
          </button>
        </form>
      )}
    </div>
  );
}

function CoachRow({ name, subtitle, color }: { name: string; subtitle: string; color: string }) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-[#1a1612]/10 bg-[#fbf8f1] p-4">
      <div
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
        style={{ background: color + "22", color }}
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
          <path d="M12 3 L13 11 L21 12 L13 13 L12 21 L11 13 L3 12 L11 11 Z" />
        </svg>
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[15px] font-semibold tracking-[-0.005em]">{name}</div>
        <div className="truncate text-[12.5px] text-[#6b6259]">{subtitle}</div>
      </div>
      <Link
        href="/dashboard/mcp"
        className="text-[12.5px] text-[color:var(--evr-accent)] hover:underline"
      >
        Setup →
      </Link>
    </div>
  );
}

function LoadStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="font-mono text-[10.5px] uppercase tracking-[0.15em] text-[#8a7f74]">{label}</div>
      <div className="mt-1 text-[28px] font-semibold tracking-[-0.02em] leading-none">{value}</div>
    </div>
  );
}

/**
 * Quick prompt row — copy-to-clipboard button. Client-side so we can show
 * a "Copied" confirmation without a roundtrip. Server-rendered shell, but
 * the button itself is a client island via the <CopyButton> below.
 */
function PromptRow({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-[#1a1612]/10 bg-[#fbf8f1] px-4 py-3">
      <p className="flex-1 text-[14px] text-[#4b423a]">{text}</p>
      <CopyButton text={text} />
    </div>
  );
}

const QUICK_PROMPTS = [
  "How did this week compare to last?",
  "Am I ready for tomorrow's long run?",
  "Plan my next 7 days around a tempo Tuesday.",
  "Why was last Saturday's long run so hard?",
  "Am I training polarized or stuck in the grey zone?",
  "Write me a 12-week marathon plan based on my last 3 months of data.",
];

// ─── Helpers ─────────────────────────────────────────────────────

function planRowSub(s: {
  duration_min: number | null;
  distance_m: number | null;
  description: string | null;
}): string {
  const parts: string[] = [];
  if (s.duration_min) parts.push(`${s.duration_min} min`);
  if (s.distance_m) parts.push(`${(s.distance_m / 1000).toFixed(1)} km`);
  if (s.description) parts.push(s.description);
  return parts.join(" · ") || "—";
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1).replace(/_/g, " ");
}

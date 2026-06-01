import Link from "next/link";
import { Reveal, Stagger, StaggerItem } from "./_motion/reveal";
import { CountUp } from "./_motion/count-up";
import { HeroBackground } from "./_motion/hero-background";
import { GrowBar } from "./_motion/grow-bar";

type SearchParams = { deleted?: string };

const CONNECTOR_URL = "https://evovlerun-production.up.railway.app/mcp";

export default async function LandingPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  return (
    <main className="min-h-screen bg-[#f5f0e8] text-[#1a1612]">
      {params.deleted === "1" && (
        <div className="border-b border-emerald-200 bg-emerald-50 px-6 py-3 text-center text-[13.5px] text-emerald-900">
          Your account and all data have been deleted. Thanks for trying EvolveRun.
        </div>
      )}
      <Nav />
      <Hero />
      <ProofBar />
      <PaceTrendDemo />
      <HowItWorks />
      <Pricing />
      <Footer />
    </main>
  );
}

function Nav() {
  return (
    <header className="sticky top-0 z-40 border-b border-[#1a1612]/10 bg-[#f5f0e8]/88 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4 sm:px-8">
        <Link href="/" className="flex items-center gap-2 text-[15px] font-semibold">
          <Brandmark />
          EvolveRun
        </Link>
        <nav className="hidden items-center gap-7 text-[13.5px] text-[#5f564d] md:flex">
          <a href="#how-it-works" className="hover:text-[#1a1612]">
            How it works
          </a>
          <a href="#integrations" className="hover:text-[#1a1612]">
            Integrations
          </a>
          <a href="#pricing" className="hover:text-[#1a1612]">
            Pricing
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="hidden text-[13.5px] text-[#5f564d] hover:text-[#1a1612] sm:inline">
            Login
          </Link>
          <Link
            href="/signup"
            className="rounded-full bg-[#1a1612] px-4 py-2 text-[13px] font-medium text-white shadow-sm transition hover:bg-[#2b251f]"
          >
            Get started
          </Link>
        </div>
      </div>
    </header>
  );
}

function Brandmark() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
      <path d="M3 5 H17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path
        d="M3 12 Q9 8 15 12 T21 12"
        stroke="#dc6b3f"
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
      <path d="M3 19 H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function Hero() {
  return (
    <section className="evr-warm-wash relative overflow-hidden">
      <HeroBackground />
      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-20 sm:px-8 sm:pt-24 lg:grid-cols-[1fr_0.95fr] lg:pb-24">
        <Stagger>
          <StaggerItem>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-[#dc6b3f]/30 bg-gradient-to-r from-[#dc6b3f]/12 to-[#fc4c02]/8 px-3 py-1.5 text-[12.5px] font-medium text-[#9e4728]">
              <span aria-hidden>★</span>
              Launching on Product Hunt today
            </div>
          </StaggerItem>
          <StaggerItem>
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-[#1a1612]/10 bg-white/55 px-3 py-1.5 text-[13px] text-[#5f564d]">
              <span className="evr-pulse h-2 w-2 rounded-full bg-[#fc4c02]" />
              Understand your training with AI
            </div>
          </StaggerItem>
          <StaggerItem>
            <h1 className="evr-headline max-w-[12ch] text-[clamp(46px,7.5vw,84px)] leading-[0.96] tracking-[-0.05em]">
              Connect Strava to <span className="text-[#dc6b3f]">ChatGPT &amp; Claude</span>
            </h1>
          </StaggerItem>
          <StaggerItem>
            <p className="mt-6 text-[20px] font-medium text-[#1a1612] sm:text-[22px]">
              Understand your training with AI.
            </p>
          </StaggerItem>
          <StaggerItem>
            <p className="mt-5 max-w-xl text-[17px] leading-relaxed text-[#5f564d] sm:text-[18px]">
              EvolveRun turns your Strava history into a secure connector for the AI you already use.
              Ask Claude or ChatGPT about your runs, splits, fatigue, and weekly load — no exports, no
              new dashboard to learn.
            </p>
          </StaggerItem>
          <StaggerItem>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="evr-lift inline-flex h-12 items-center justify-center rounded-full bg-[#1a1612] px-6 text-[14.5px] font-medium text-white shadow-sm transition hover:bg-[#2b251f]"
              >
                Get started
              </Link>
              <a
                href="#how-it-works"
                className="evr-lift inline-flex h-12 items-center justify-center rounded-full border border-[#1a1612]/12 bg-white/50 px-6 text-[14.5px] font-medium text-[#1a1612] transition hover:bg-white"
              >
                See how it works
              </a>
            </div>
          </StaggerItem>
          <StaggerItem>
            <p className="mt-5 max-w-lg text-[12.5px] leading-relaxed text-[#7a7168]">
              Works with Garmin, Apple Watch, Polar, COROS, Suunto, Wahoo and anything that syncs to
              Strava.
            </p>
          </StaggerItem>
        </Stagger>

        <Reveal delay={0.25} y={24} className="relative">
          <PaceTrendChat animated />
        </Reveal>
      </div>
    </section>
  );
}

/** Static chat-window mockup: user asks about easy-run pace trends, Claude
 * answers using EvolveRun tools and shows the Jan–March progression. Reused
 * in the hero (right column). No client state — faithful static markup. */
function PaceTrendChat({ animated = false }: { animated?: boolean }) {
  return (
    <div className="evr-card-hover overflow-hidden rounded-[24px] border border-[#1a1612]/10 bg-[#fbf8f1] shadow-2xl shadow-[#1a1612]/15">
      <div className="flex items-center gap-2 border-b border-[#1a1612]/10 px-4 py-3">
        <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
        <span className="h-3 w-3 rounded-full bg-[#ffbd2e]" />
        <span className="h-3 w-3 rounded-full bg-[#28c840]" />
        <span className="ml-3 text-[12px] text-[#7a7168]">claude.ai · EvolveRun connected</span>
      </div>
      <div className="space-y-4 p-5 sm:p-6">
        <ChatBubble who="You">
          How has my easy-run pace trended since January?
        </ChatBubble>
        <ToolCall name="get-period-summary" detail="Jan–Mar · easy runs" />
        <ToolCall name="get-run-splits" detail="pace + heart rate" />
        <ChatBubble who="Claude" muted>
          Your easy pace has steadily improved from January to March while heart rate has come down
          slightly. Aerobic efficiency is improving — you are holding the same effort at a lower
          heart rate.
        </ChatBubble>
        <div className="grid gap-3 sm:grid-cols-2">
          <Insight label="Easy pace" fromValue={323} toValue={308} mode="pace" unit="/km" tone="good" animated={animated} />
          <Insight label="Avg HR" fromValue={149} toValue={145} mode="int" unit="bpm" tone="good" animated={animated} />
        </div>
        <div className="rounded-2xl border border-[#dc6b3f]/25 bg-[#dc6b3f]/8 p-4">
          <p className="text-[13.5px] leading-relaxed text-[#7a4225]">
            Conclusion: aerobic efficiency improving — same pace at lower HR.
          </p>
          {animated && (
            <div className="mt-3">
              <GrowBar pct={82} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function PaceTrendDemo() {
  return (
    <section id="integrations" className="mx-auto grid max-w-7xl gap-10 px-5 py-24 sm:px-8 lg:grid-cols-[0.86fr_1.14fr]">
      <Reveal>
        <div className="text-[13px] font-semibold uppercase tracking-[0.18em] text-[#dc6b3f]">
          See it in your chat
        </div>
        <h2 className="evr-headline mt-4 max-w-lg text-[clamp(36px,5vw,58px)] tracking-[-0.04em]">
          Ask. EvolveRun answers from your real data.
        </h2>
        <p className="mt-5 max-w-xl text-[16.5px] leading-relaxed text-[#5f564d]">
          The analysis happens inside the AI you already use. EvolveRun gives Claude and ChatGPT a
          small set of reliable tools over your Strava history — recent activities, splits, and
          period summaries — so the answers are grounded in your training, not generic advice.
        </p>
        <div className="mt-8 grid gap-3">
          <ValueLine title="Connect Strava" body="One OAuth connection imports your activities and keeps syncing." />
          <ValueLine title="Add the connector" body="Add EvolveRun as a custom connector inside Claude, ChatGPT, or Gemini." />
          <ValueLine title="Ask questions" body="Pace trends, fatigue, weekly load, race prep — answered from your data." />
        </div>
      </Reveal>

      <Reveal delay={0.12} y={24} className="relative">
        <PaceTrendChat animated />
      </Reveal>
    </section>
  );
}

function ProofBar() {
  const items = [
    "Activities",
    "Routes",
    "Splits",
    "Heart rate",
    "Power",
    "Pace",
    "Elevation",
    "Training plans",
  ];

  const platforms = [
    "Garmin",
    "Apple Watch",
    "Polar",
    "COROS",
    "Suunto",
    "Wahoo",
    "Claude",
    "ChatGPT",
    "Gemini",
  ];

  return (
    <section className="border-y border-[#1a1612]/10 bg-white/38">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-px px-5 py-5 text-center sm:grid-cols-4 sm:px-8 lg:grid-cols-8">
        {items.map((item) => (
          <div key={item} className="px-3 py-3 text-[12.5px] font-medium text-[#5f564d]">
            {item}
          </div>
        ))}
      </div>
      <div className="overflow-hidden border-t border-[#1a1612]/10 py-3 [mask-image:linear-gradient(to_right,transparent,black_12%,black_88%,transparent)]">
        <div className="evr-marquee gap-10 pr-10">
          {[...platforms, ...platforms].map((p, i) => (
            <span
              key={`${p}-${i}`}
              className="shrink-0 text-[12px] font-medium uppercase tracking-[0.14em] text-[#8a7f74]"
            >
              {p}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}

function ValueLine({ title, body }: { title: string; body: string }) {
  return (
    <div className="flex gap-3">
      <span className="mt-1 h-2 w-2 rounded-full bg-[#dc6b3f]" />
      <div>
        <div className="text-[15px] font-semibold">{title}</div>
        <p className="mt-1 text-[14px] leading-relaxed text-[#6b6259]">{body}</p>
      </div>
    </div>
  );
}

function ChatBubble({
  who,
  muted,
  children,
}: {
  who: string;
  muted?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className={muted ? "rounded-2xl bg-white/70 p-4" : "rounded-2xl bg-[#1a1612] p-4 text-white"}>
      <div className={muted ? "text-[11px] font-semibold text-[#8a7f74]" : "text-[11px] font-semibold text-white/55"}>
        {who}
      </div>
      <p className={muted ? "mt-1 text-[14px] leading-relaxed text-[#4b423a]" : "mt-1 text-[14px] leading-relaxed text-white/88"}>
        {children}
      </p>
    </div>
  );
}

function ToolCall({ name, detail }: { name: string; detail: string }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-[#dc6b3f]/25 bg-[#dc6b3f]/8 px-4 py-3">
      <code className="text-[12px] font-medium text-[#9e4728]">{name}</code>
      <span className="text-[12px] text-[#7a7168]">{detail}</span>
    </div>
  );
}

function Insight({
  label,
  fromValue,
  toValue,
  mode,
  unit,
  tone,
  animated,
}: {
  label: string;
  fromValue: number;
  toValue: number;
  mode: "pace" | "int";
  unit: string;
  tone: "good" | "warn";
  animated?: boolean;
}) {
  const fmt = (n: number) =>
    mode === "pace"
      ? `${Math.floor(n / 60)}:${String(n % 60).padStart(2, "0")}`
      : String(n);

  return (
    <div className="rounded-2xl border border-[#1a1612]/10 bg-white/65 p-4">
      <div className="text-[11px] uppercase tracking-[0.16em] text-[#8a7f74]">{label}</div>
      <div className="mt-2 flex items-baseline gap-1">
        <span className="text-[24px] font-semibold tracking-[-0.04em]">
          {fmt(fromValue)} →{" "}
          {animated ? (
            <CountUp from={fromValue} to={toValue} mode={mode} />
          ) : (
            fmt(toValue)
          )}
        </span>
        <span className="text-[12px] text-[#8a7f74]">{unit}</span>
      </div>
      <div className={tone === "good" ? "mt-1 text-[12px] text-emerald-700" : "mt-1 text-[12px] text-[#b85d32]"}>
        {tone === "good" ? "improving" : "watch zone"}
      </div>
    </div>
  );
}

function HowItWorks() {
  const steps = [
    {
      n: "01",
      t: "Connect Strava via OAuth",
      d: "Authorize EvolveRun once. We import your recent activities and keep listening for new uploads.",
    },
    {
      n: "02",
      t: "Add the EvolveRun connector",
      d: "Add the EvolveRun custom connector to Claude, ChatGPT, or Gemini. No desktop JSON setup.",
    },
    {
      n: "03",
      t: "Ask about your training",
      d: "Ask questions about your training data — pace trends, fatigue, weekly load, and race prep.",
    },
  ];

  return (
    <section id="how-it-works" className="mx-auto max-w-7xl px-5 py-20 sm:px-8">
      <Reveal className="mb-10 flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <div className="text-[13px] font-semibold uppercase tracking-[0.18em] text-[#dc6b3f]">
            How it works
          </div>
          <h2 className="evr-headline mt-4 max-w-xl text-[clamp(36px,5vw,58px)] tracking-[-0.04em]">
            Three steps from Strava to answers.
          </h2>
        </div>
        <p className="max-w-md text-[15.5px] leading-relaxed text-[#5f564d]">
          EvolveRun is intentionally small. The product gets your training data into the place you
          already think: your AI chat.
        </p>
      </Reveal>
      <div className="grid gap-px overflow-hidden rounded-[24px] border border-[#1a1612]/10 bg-[#1a1612]/10 md:grid-cols-3">
        {steps.map((step, i) => (
          <Reveal key={step.n} delay={i * 0.1} className="bg-[#fbf8f1] p-7">
            <div className="font-mono text-[12px] text-[#8a7f74]">{step.n}</div>
            <h3 className="mt-5 text-[21px] font-semibold tracking-[-0.025em]">{step.t}</h3>
            <p className="mt-3 text-[14.5px] leading-relaxed text-[#62584f]">{step.d}</p>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

function Pricing() {
  return (
    <section id="pricing" className="mx-auto grid max-w-7xl items-center gap-10 px-5 py-24 sm:px-8 lg:grid-cols-[1fr_420px]">
      <Reveal>
        <div className="text-[13px] font-semibold uppercase tracking-[0.18em] text-[#dc6b3f]">
          Pricing
        </div>
        <h2 className="evr-headline mt-4 max-w-xl text-[clamp(36px,5vw,58px)] tracking-[-0.04em]">
          Simple enough to try. Useful enough to keep.
        </h2>
        <p className="mt-5 max-w-xl text-[16.5px] leading-relaxed text-[#5f564d]">
          One subscription covers Strava sync, hosted connector access, plan saving, and the
          training calendar. Bring your own Claude or ChatGPT account.
        </p>
      </Reveal>
      <Reveal delay={0.12} className="evr-card-hover rounded-[28px] border border-[#1a1612]/10 bg-[#fbf8f1] p-7 shadow-xl shadow-[#1a1612]/8">
        <div className="text-[13px] font-semibold uppercase tracking-[0.18em] text-[#8a7f74]">
          EvolveRun V1
        </div>
        <div className="mt-5 flex items-end gap-2">
          <span className="text-[58px] font-semibold leading-none tracking-[-0.06em]">€9</span>
          <span className="pb-2 text-[15px] text-[#6b6259]">/ month</span>
        </div>
        <ul className="mt-7 space-y-3 text-[14.5px] text-[#4b423a]">
          <li>Strava sync + live updates</li>
          <li>Claude / ChatGPT connector</li>
          <li>Recent activities, splits, period summaries</li>
          <li>Training plan save + calendar view</li>
        </ul>
        <Link
          href="/signup"
          className="evr-lift mt-8 inline-flex h-12 w-full items-center justify-center rounded-full bg-[#1a1612] px-6 text-[14.5px] font-medium text-white transition hover:bg-[#2b251f]"
        >
          Get started
        </Link>
        <p className="mt-4 text-center text-[12px] text-[#8a7f74]">
          Cancel anytime. No extra wearable subscription.
        </p>
      </Reveal>
    </section>
  );
}

function Footer() {
  return (
    <footer className="border-t border-[#1a1612]/10 bg-[#eee7dc]">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-5 py-12 sm:px-8 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="flex items-center gap-2 text-[15px] font-semibold">
            <Brandmark />
            EvolveRun
          </div>
          <p className="mt-3 max-w-md text-[13.5px] leading-relaxed text-[#6b6259]">
            Simple AI endurance coaching from your Strava data. MCP endpoint:{" "}
            <code className="rounded bg-white/60 px-1.5 py-0.5 text-[12px]">{CONNECTOR_URL}</code>
          </p>
          <Link
            href="/signup"
            className="mt-5 inline-flex h-11 items-center justify-center rounded-full bg-[#1a1612] px-5 text-[13.5px] font-medium text-white transition hover:bg-[#2b251f]"
          >
            Start free trial
          </Link>
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-[12.5px] text-[#6b6259]">
          <a href="#how-it-works" className="hover:text-[#1a1612]">
            How it works
          </a>
          <a href="#integrations" className="hover:text-[#1a1612]">
            Integrations
          </a>
          <a href="#pricing" className="hover:text-[#1a1612]">
            Pricing
          </a>
          <Link href="/login" className="hover:text-[#1a1612]">
            Login
          </Link>
          <a href="https://github.com/255065/evovlerun" target="_blank" rel="noreferrer" className="hover:text-[#1a1612]">
            GitHub
          </a>
          <span>© 2026 EvolveRun</span>
        </div>
      </div>
    </footer>
  );
}

import Link from "next/link";

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
      <ConnectorDemo />
      <HowItWorks />
      <PromptGrid />
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
          <a href="#demo" className="hover:text-[#1a1612]">
            Demo
          </a>
          <a href="#how-it-works" className="hover:text-[#1a1612]">
            How it works
          </a>
          <a href="#prompts" className="hover:text-[#1a1612]">
            Prompts
          </a>
          <a href="#pricing" className="hover:text-[#1a1612]">
            Pricing
          </a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="hidden text-[13.5px] text-[#5f564d] hover:text-[#1a1612] sm:inline">
            Log in
          </Link>
          <Link
            href="/signup"
            className="rounded-full bg-[#1a1612] px-4 py-2 text-[13px] font-medium text-white shadow-sm transition hover:bg-[#2b251f]"
          >
            Start free trial
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
    <section className="mx-auto grid max-w-7xl items-center gap-12 px-5 pb-20 pt-20 sm:px-8 sm:pt-24 lg:grid-cols-[1fr_0.95fr] lg:pb-24">
      <div>
        <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-[#1a1612]/10 bg-white/55 px-3 py-1.5 text-[13px] text-[#5f564d]">
          <span className="h-2 w-2 rounded-full bg-[#fc4c02]" />
          Built for Strava athletes using Claude or ChatGPT
        </div>
        <h1 className="evr-headline max-w-[10.8ch] text-[clamp(52px,8.5vw,92px)] leading-[0.95] tracking-[-0.055em]">
          Your AI coach, powered by <span className="text-[#dc6b3f]">Strava.</span>
        </h1>
        <p className="mt-7 max-w-xl text-[18px] leading-relaxed text-[#5f564d] sm:text-[19px]">
          EvolveRun turns your Strava history into a secure connector for the AI you already use.
          Ask Claude or ChatGPT about your training, splits, fatigue, weekly load, and race prep
          without exporting a single CSV.
        </p>
        <div className="mt-9 flex flex-col gap-3 sm:flex-row">
          <Link
            href="/signup"
            className="inline-flex h-12 items-center justify-center rounded-full bg-[#1a1612] px-6 text-[14.5px] font-medium text-white shadow-sm transition hover:bg-[#2b251f]"
          >
            Connect Strava
          </Link>
          <a
            href="#demo"
            className="inline-flex h-12 items-center justify-center rounded-full border border-[#1a1612]/12 bg-white/50 px-6 text-[14.5px] font-medium text-[#1a1612] transition hover:bg-white"
          >
            See what it answers
          </a>
        </div>
        <p className="mt-5 max-w-lg text-[12.5px] leading-relaxed text-[#7a7168]">
          Works through Strava with Garmin, Apple Watch, Polar, COROS, Suunto, Wahoo, Zwift and
          other devices that already sync there.
        </p>
      </div>

      <div className="relative">
        <TrainingSnapshot />
      </div>
    </section>
  );
}

function TrainingSnapshot() {
  return (
    <div className="rounded-[28px] border border-[#1a1612]/10 bg-[#1a1612] p-3 shadow-2xl shadow-[#1a1612]/15">
      <div className="rounded-[22px] bg-[#f8f4ed] p-4 sm:p-5">
        <div className="flex items-center justify-between border-b border-[#1a1612]/10 pb-4">
          <div>
            <div className="text-[12px] font-medium uppercase tracking-[0.18em] text-[#8a7f74]">
              EvolveRun connector
            </div>
            <div className="mt-1 text-[18px] font-semibold tracking-[-0.02em]">
              Training context ready
            </div>
          </div>
          <span className="rounded-full bg-[#fc4c02] px-3 py-1 text-[11px] font-semibold text-white">
            Strava
          </span>
        </div>

        <div className="mt-5 grid grid-cols-3 gap-2">
          <Metric label="Last 30 days" value="247 km" />
          <Metric label="Avg pace" value="5:18/km" />
          <Metric label="Runs" value="21" />
        </div>

        <div className="mt-5 rounded-2xl border border-[#1a1612]/10 bg-white/70 p-4">
          <div className="flex items-start gap-3">
            <div className="mt-1 h-8 w-8 rounded-full bg-[#dc6b3f]/15" />
            <div>
              <div className="text-[13px] font-semibold">Claude used 3 EvolveRun tools</div>
              <p className="mt-1 text-[13px] leading-relaxed text-[#62584f]">
                get-period-summary, get-run-splits, get-planned-workouts
              </p>
            </div>
          </div>
        </div>

        <div className="mt-3 rounded-2xl bg-[#1a1612] p-4 text-white">
          <div className="text-[12px] text-white/55">Answer preview</div>
          <p className="mt-2 text-[14px] leading-relaxed text-white/88">
            Your last two long runs show stable pace but rising HR after 75 minutes. I would keep
            Saturday aerobic, then add controlled threshold on Tuesday.
          </p>
        </div>

        <div className="mt-5 flex items-end gap-2">
          {[34, 52, 46, 63, 57, 72, 68, 78, 65, 86, 74, 82].map((h, i) => (
            <div
              key={i}
              className="flex-1 rounded-t-md bg-[#dc6b3f]"
              style={{ height: `${h}px`, opacity: 0.35 + i * 0.045 }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[#1a1612]/10 bg-white/65 p-3">
      <div className="text-[11px] text-[#7a7168]">{label}</div>
      <div className="mt-1 text-[18px] font-semibold tracking-[-0.03em]">{value}</div>
    </div>
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

  return (
    <section className="border-y border-[#1a1612]/10 bg-white/38">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-px px-5 py-5 text-center sm:grid-cols-4 sm:px-8 lg:grid-cols-8">
        {items.map((item) => (
          <div key={item} className="px-3 py-3 text-[12.5px] font-medium text-[#5f564d]">
            {item}
          </div>
        ))}
      </div>
    </section>
  );
}

function ConnectorDemo() {
  return (
    <section id="demo" className="mx-auto grid max-w-7xl gap-10 px-5 py-24 sm:px-8 lg:grid-cols-[0.86fr_1.14fr]">
      <div>
        <div className="text-[13px] font-semibold uppercase tracking-[0.18em] text-[#dc6b3f]">
          Connector-first
        </div>
        <h2 className="evr-headline mt-4 max-w-lg text-[clamp(36px,5vw,58px)] tracking-[-0.04em]">
          The analysis happens in your chat.
        </h2>
        <p className="mt-5 max-w-xl text-[16.5px] leading-relaxed text-[#5f564d]">
          We keep EvolveRun focused: secure Strava sync, clean training data, and a small MCP tool
          surface that Claude and ChatGPT can use reliably. No bloated dashboard. No fake certainty.
        </p>
        <div className="mt-8 grid gap-3">
          <ValueLine title="Less setup" body="Connect Strava once. Then connect EvolveRun inside Claude.ai or ChatGPT." />
          <ValueLine title="Better answers" body="The assistant sees your recent activities, period totals, splits, and saved plans." />
          <ValueLine title="Plan saving" body="When a plan is ready, the assistant asks before saving it to your training calendar." />
        </div>
      </div>

      <div className="overflow-hidden rounded-[24px] border border-[#1a1612]/10 bg-[#fbf8f1] shadow-xl shadow-[#1a1612]/8">
        <div className="flex items-center gap-2 border-b border-[#1a1612]/10 px-4 py-3">
          <span className="h-3 w-3 rounded-full bg-[#ff5f57]" />
          <span className="h-3 w-3 rounded-full bg-[#ffbd2e]" />
          <span className="h-3 w-3 rounded-full bg-[#28c840]" />
          <span className="ml-3 text-[12px] text-[#7a7168]">claude.ai · EvolveRun connected</span>
        </div>
        <div className="space-y-4 p-5 sm:p-6">
          <ChatBubble who="You">
            Am I training polarized or spending too much time in grey zone?
          </ChatBubble>
          <ToolCall name="get-period-summary" detail="last 8 weeks · run only" />
          <ToolCall name="get-recent-activities" detail="25 activities · pace + HR + elevation" />
          <ChatBubble who="Claude" muted>
            Your last 8 weeks look more pyramidal than polarized: about 67% easy, 24% moderate,
            and 9% hard by time. The issue is not intensity volume, it is where the moderate work
            lands: most of it appears in long-run fade and steady aerobic days.
          </ChatBubble>
          <div className="grid gap-3 sm:grid-cols-3">
            <Insight label="Easy" value="67%" tone="good" />
            <Insight label="Moderate" value="24%" tone="warn" />
            <Insight label="Hard" value="9%" tone="good" />
          </div>
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

function Insight({ label, value, tone }: { label: string; value: string; tone: "good" | "warn" }) {
  return (
    <div className="rounded-2xl border border-[#1a1612]/10 bg-white/65 p-4">
      <div className="text-[11px] uppercase tracking-[0.16em] text-[#8a7f74]">{label}</div>
      <div className="mt-2 text-[26px] font-semibold tracking-[-0.04em]">{value}</div>
      <div className={tone === "good" ? "mt-1 text-[12px] text-emerald-700" : "mt-1 text-[12px] text-[#b85d32]"}>
        {tone === "good" ? "within range" : "watch zone"}
      </div>
    </div>
  );
}

function HowItWorks() {
  const steps = [
    {
      n: "01",
      t: "Connect Strava",
      d: "We import your recent activities and keep listening for new uploads through Strava webhooks.",
    },
    {
      n: "02",
      t: "Add EvolveRun to your AI",
      d: "Claude.ai and ChatGPT can connect to the hosted MCP endpoint. No desktop JSON setup for customers.",
    },
    {
      n: "03",
      t: "Ask, analyze, save",
      d: "Ask for race prep, grey-zone analysis, long-run debriefs, or a plan. Save plans back to EvolveRun when ready.",
    },
  ];

  return (
    <section id="how-it-works" className="mx-auto max-w-7xl px-5 py-20 sm:px-8">
      <div className="mb-10 flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <div className="text-[13px] font-semibold uppercase tracking-[0.18em] text-[#dc6b3f]">
            How it works
          </div>
          <h2 className="evr-headline mt-4 max-w-xl text-[clamp(36px,5vw,58px)] tracking-[-0.04em]">
            A data layer, not another training app.
          </h2>
        </div>
        <p className="max-w-md text-[15.5px] leading-relaxed text-[#5f564d]">
          EvolveRun is intentionally small. The product gets your training data into the place you
          already think: your AI chat.
        </p>
      </div>
      <div className="grid gap-px overflow-hidden rounded-[24px] border border-[#1a1612]/10 bg-[#1a1612]/10 md:grid-cols-3">
        {steps.map((step) => (
          <div key={step.n} className="bg-[#fbf8f1] p-7">
            <div className="font-mono text-[12px] text-[#8a7f74]">{step.n}</div>
            <h3 className="mt-5 text-[21px] font-semibold tracking-[-0.025em]">{step.t}</h3>
            <p className="mt-3 text-[14.5px] leading-relaxed text-[#62584f]">{step.d}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function PromptGrid() {
  const prompts = [
    "What changed in my training over the last 8 weeks?",
    "Am I polarized, pyramidal, or stuck in grey zone?",
    "Write a 10-week half marathon plan around my current volume.",
    "Which recent run should I treat as my fitness benchmark?",
    "Why did my long run fade after 75 minutes?",
    "Turn this plan into a Mon-Sun calendar and ask before saving it.",
  ];

  return (
    <section id="prompts" className="border-y border-[#1a1612]/10 bg-[#1a1612] px-5 py-24 text-white sm:px-8">
      <div className="mx-auto max-w-7xl">
        <div className="max-w-2xl">
          <div className="text-[13px] font-semibold uppercase tracking-[0.18em] text-[#f0a17d]">
            Cookbook
          </div>
          <h2 className="evr-headline mt-4 text-[clamp(36px,5vw,58px)] tracking-[-0.04em]">
            Start with questions that actually move training.
          </h2>
        </div>
        <div className="mt-10 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {prompts.map((prompt) => (
            <div key={prompt} className="rounded-2xl border border-white/10 bg-white/[0.06] p-5">
              <div className="text-[12px] text-white/45">Try asking</div>
              <p className="mt-2 text-[15px] leading-relaxed text-white/88">"{prompt}"</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  return (
    <section id="pricing" className="mx-auto grid max-w-7xl items-center gap-10 px-5 py-24 sm:px-8 lg:grid-cols-[1fr_420px]">
      <div>
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
      </div>
      <div className="rounded-[28px] border border-[#1a1612]/10 bg-[#fbf8f1] p-7 shadow-xl shadow-[#1a1612]/8">
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
          className="mt-8 inline-flex h-12 w-full items-center justify-center rounded-full bg-[#1a1612] px-6 text-[14.5px] font-medium text-white transition hover:bg-[#2b251f]"
        >
          Start free trial
        </Link>
        <p className="mt-4 text-center text-[12px] text-[#8a7f74]">
          Cancel anytime. No extra wearable subscription.
        </p>
      </div>
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
        </div>
        <div className="flex flex-wrap gap-x-6 gap-y-2 text-[12.5px] text-[#6b6259]">
          <Link href="/login" className="hover:text-[#1a1612]">
            Log in
          </Link>
          <a href="#how-it-works" className="hover:text-[#1a1612]">
            How it works
          </a>
          <a href="https://github.com/255065/evovlerun" target="_blank" rel="noreferrer" className="hover:text-[#1a1612]">
            GitHub
          </a>
          <span>© {new Date().getFullYear()} EvolveRun</span>
        </div>
      </div>
    </footer>
  );
}

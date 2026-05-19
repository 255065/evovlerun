import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-neutral-950">
      <Nav />
      <Hero />
      <StatsGrid />
      <HowItWorks />
      <Footer />
    </div>
  );
}

function Nav() {
  return (
    <header className="border-b border-neutral-200">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-[18px]">
        <Link href="/" className="flex items-center gap-2 font-semibold text-[15px]">
          <Brandmark />
          EvolveRun
        </Link>
        <nav className="hidden gap-6 text-[13.5px] text-neutral-600 md:flex">
          <a href="#how-it-works" className="hover:text-neutral-950">How it works</a>
          <a href="#integrations" className="hover:text-neutral-950">Integrations</a>
          <a href="#pricing" className="hover:text-neutral-950">Pricing</a>
        </nav>
        <div className="flex items-center gap-3">
          <Link href="/login" className="text-[13.5px] text-neutral-600 hover:text-neutral-950">
            Log in
          </Link>
          <Link
            href="/signup"
            className="rounded-md bg-neutral-950 px-3.5 py-1.5 text-[13px] font-medium text-white"
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
    <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5">
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
    <section className="relative mx-auto max-w-[1200px] overflow-hidden px-8 pt-28 pb-24 text-center">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 left-1/2 -z-0 h-[600px] w-[800px] -translate-x-1/2 blur-2xl"
        style={{
          background:
            "radial-gradient(circle at 30% 50%, rgba(255,107,70,0.15), transparent 50%), radial-gradient(circle at 70% 50%, rgba(168,85,247,0.12), transparent 50%)",
        }}
      />
      <div className="relative z-10">
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white/90 py-1.5 pr-3.5 pl-1.5 text-[13px] text-neutral-600">
          <span className="rounded-full bg-neutral-950 px-2.5 py-[3px] text-[11px] font-medium tracking-wide text-white">
            v1
          </span>
          Simple AI endurance coach for Strava athletes
        </div>
        <h1
          className="mx-auto max-w-[14ch] bg-gradient-to-b from-neutral-950 to-neutral-700 bg-clip-text text-[clamp(48px,9vw,80px)] font-semibold leading-[1] tracking-[-0.045em] text-transparent"
        >
          Connect Strava.{" "}
          <em
            className="not-italic bg-gradient-to-br from-[#ff6b46] to-[#a855f7] bg-clip-text text-transparent"
          >
            Get answers.
          </em>
        </h1>
        <p className="mx-auto mt-6 max-w-[36rem] text-[18.5px] leading-relaxed text-neutral-600">
          EvolveRun connects your Strava account to Claude, ChatGPT, or Gemini — so the
          AI you already use can answer real questions about <em className="not-italic">your</em>{" "}
          training. Zone analysis, plan writing, recovery debriefs, all from your actual data.
        </p>
        <div className="mt-9 flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 rounded-lg bg-neutral-950 px-6 py-3 text-[14.5px] font-medium text-white"
          >
            Start free trial →
          </Link>
          <Link
            href="#how-it-works"
            className="inline-flex items-center gap-2 rounded-lg border border-neutral-200 bg-white px-5 py-3 text-[14.5px] text-neutral-950"
          >
            How it works ↓
          </Link>
        </div>
        <p className="mt-5 text-[12.5px] text-neutral-500">
          Works with Garmin, Apple Watch, Polar, COROS, Suunto and Wahoo — anything that auto-syncs to Strava.
        </p>
      </div>
    </section>
  );
}

function StatsGrid() {
  const cells = [
    {
      n: <>85<em className="not-italic text-[#ff6b46]">%</em></>,
      l: "of the endurance market — every device that auto-syncs to Strava is supported.",
    },
    {
      n: <>3</>,
      l: "AI coaches you can use: Claude, ChatGPT, Gemini — connected via your own account.",
    },
    {
      n: <>11</>,
      l: "MCP tools tuned for endurance data — splits, periods, plan writes, all kebab-cased.",
    },
    {
      n: <>€9<span className="text-[18px] text-neutral-500">/mo</span></>,
      l: "One simple subscription. No free tier, no surprise upsells, cancel anytime.",
    },
  ];
  return (
    <section
      id="integrations"
      className="mx-auto grid max-w-[1100px] grid-cols-2 border-t border-b border-neutral-200 px-8 py-[60px] md:grid-cols-4"
    >
      {cells.map((c, i) => (
        <div
          key={i}
          className={`px-0 py-7 ${i < cells.length - 1 ? "md:border-r md:border-neutral-200" : ""} pr-6`}
        >
          <div className="text-[36px] font-semibold tracking-[-0.03em] leading-none">{c.n}</div>
          <div className="mt-2 text-[13.5px] leading-snug text-neutral-600">{c.l}</div>
        </div>
      ))}
    </section>
  );
}

function HowItWorks() {
  const steps = [
    {
      n: "01",
      t: "Connect Strava",
      d: "One OAuth click. We pull your last 90 days and listen for new activities live. Encrypted tokens, RLS on every row.",
    },
    {
      n: "02",
      t: "Add the connector",
      d: 'In Claude.ai, ChatGPT or Gemini, "Add custom connector" → paste the link → done. Your chat now has access to your training data.',
    },
    {
      n: "03",
      t: "Ask anything",
      d: '"Write me a 12-week marathon plan." "Why was Saturday\'s long run so hard?" "Am I polarized or stuck in grey zone?" Real answers from your real data.',
    },
  ];
  return (
    <section id="how-it-works" className="mx-auto max-w-[1100px] px-8 py-24">
      <div className="mb-12 max-w-2xl">
        <div className="text-[13px] font-medium uppercase tracking-wider text-[#dc6b3f]">
          How it works
        </div>
        <h2 className="evr-headline mt-3 text-[40px] tracking-[-0.025em]">
          Three steps. <span className="evr-emphasis">No new app to learn.</span>
        </h2>
        <p className="mt-4 text-[16px] text-neutral-600">
          The AI lives in the chat you already use. EvolveRun is the data layer that makes its
          answers actually correct for you.
        </p>
      </div>
      <div className="grid gap-px overflow-hidden rounded-xl border border-neutral-200 bg-neutral-200 md:grid-cols-3">
        {steps.map((s) => (
          <div key={s.n} className="bg-white p-7">
            <div className="font-mono text-[12px] text-neutral-500">{s.n}</div>
            <div className="mt-3 text-[18px] font-semibold tracking-[-0.01em]">{s.t}</div>
            <p className="mt-2 text-[14px] leading-relaxed text-neutral-600">{s.d}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer id="pricing" className="border-t border-neutral-200 bg-neutral-50">
      <div className="mx-auto flex max-w-7xl flex-col items-center gap-6 px-8 py-16 text-center">
        <div className="flex items-center gap-2 text-[15px] font-semibold">
          <Brandmark />
          EvolveRun
        </div>
        <h3 className="evr-headline max-w-xl text-[32px] tracking-[-0.02em]">
          Ready to let your AI <span className="evr-emphasis">read your training data?</span>
        </h3>
        <Link
          href="/signup"
          className="inline-flex items-center gap-2 rounded-lg bg-neutral-950 px-6 py-3 text-[14.5px] font-medium text-white"
        >
          Start free trial →
        </Link>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-[12.5px] text-neutral-500">
          <Link href="/login" className="hover:text-neutral-950">Log in</Link>
          <a href="#how-it-works" className="hover:text-neutral-950">How it works</a>
          <a
            href="https://github.com/255065/evovlerun"
            target="_blank"
            rel="noreferrer"
            className="hover:text-neutral-950"
          >
            GitHub
          </a>
          <span>© {new Date().getFullYear()} EvolveRun</span>
        </div>
      </div>
    </footer>
  );
}

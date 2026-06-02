import Link from "next/link";
import Image from "next/image";
import { ChatDemo } from "./_motion/chat-demo";

type SearchParams = { deleted?: string };

export default async function LandingPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  return (
    <div className="min-h-screen bg-white text-neutral-950">
      {params.deleted === "1" && (
        <div className="border-b border-emerald-200 bg-emerald-50 px-6 py-3 text-center text-[13.5px] text-emerald-900">
          Your account and all data have been deleted. Thanks for trying EvolveRun.
        </div>
      )}
      <Nav />
      <Hero />
      <ChatDemo />
      <HowItWorks />
      <Footer />
    </div>
  );
}

function Brandmark({ size = 16 }: { size?: number }) {
  return (
    <Image
      src="/evr-logo.png"
      alt="EvolveRun"
      width={size}
      height={size}
      className="object-contain"
    />
  );
}

function Nav() {
  return (
    <header className="border-b border-neutral-200">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-[18px]">
        <Link href="/" className="flex items-center gap-2 text-[15px] font-semibold">
          <Brandmark />
          EvolveRun
        </Link>
        <nav className="hidden gap-6 text-[13.5px] text-neutral-600 md:flex">
          <a href="#how-it-works" className="hover:text-neutral-950">How it works</a>
          <a href="#how-it-works" className="hover:text-neutral-950">Integrations</a>
          <a href="#pricing" className="hover:text-neutral-950">Pricing</a>
        </nav>
        <div className="flex items-center gap-2">
          <Link
            href="/login"
            className="rounded-md px-3.5 py-1.5 text-[13px] font-medium text-neutral-700 hover:text-neutral-950"
          >
            Login
          </Link>
          <Link
            href="/signup"
            className="rounded-md bg-neutral-950 px-3.5 py-1.5 text-[13px] font-medium text-white"
          >
            Get started
          </Link>
        </div>
      </div>
    </header>
  );
}

function Hero() {
  return (
    <section className="relative mx-auto max-w-[1200px] overflow-hidden px-8 pt-24 pb-20">
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 left-1/2 -z-0 h-[600px] w-[800px] -translate-x-1/2 blur-2xl"
        style={{
          background:
            "radial-gradient(circle at 30% 50%, rgba(255,107,70,0.12), transparent 50%), radial-gradient(circle at 70% 50%, rgba(168,85,247,0.10), transparent 50%)",
        }}
      />
      <div className="relative z-10 grid items-center gap-12 md:grid-cols-[1.05fr_1fr]">
        <div className="text-left">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-white/90 py-1.5 pr-3.5 pl-1.5 text-[13px] text-neutral-600">
            <span className="rounded-full bg-neutral-950 px-2.5 py-[3px] text-[11px] font-medium tracking-wide text-white">
              Public Beta
            </span>
            Connect Strava to ChatGPT &amp; Claude
          </div>
          <h1 className="evr-headline bg-gradient-to-b from-neutral-950 to-neutral-700 bg-clip-text text-[clamp(40px,6.5vw,68px)] font-semibold leading-[1.02] tracking-[-0.04em] text-transparent">
            Understand your training with{" "}
            <em className="not-italic bg-gradient-to-br from-[#ff6b46] to-[#a855f7] bg-clip-text text-transparent">
              AI.
            </em>
          </h1>
          <p className="mt-6 max-w-[34rem] text-[17px] leading-relaxed text-neutral-600">
            Connect your Strava account to ChatGPT, Claude, or Gemini and get deeper
            insights into your workouts, recovery, fitness trends, and performance —
            using your real training data.
          </p>
          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="/signup"
              className="inline-flex items-center gap-2 rounded-lg bg-neutral-950 px-6 py-3 text-[14.5px] font-medium text-white"
            >
              Get started →
            </Link>
          </div>
          <p className="mt-5 text-[12.5px] text-neutral-500">
            Works with Garmin, Apple Watch, Polar, COROS, Suunto and Wahoo — anything that auto-syncs to Strava.
          </p>
        </div>

        <HeroConnector />
      </div>
    </section>
  );
}

function HeroConnector() {
  return (
    <div className="relative mx-auto h-[460px] w-full max-w-[440px]">
      <div
        aria-hidden
        className="absolute inset-0 rounded-2xl"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent 0 47px, rgba(0,0,0,0.07) 47px 48px), repeating-linear-gradient(90deg, transparent 0 47px, rgba(0,0,0,0.07) 47px 48px)",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute left-0 right-0 top-1/2 h-[120px] -translate-y-1/2 blur-2xl opacity-90"
        style={{
          background:
            "linear-gradient(90deg, rgba(138,169,255,0) 0%, rgba(138,169,255,0.55) 25%, rgba(252,82,0,0.55) 50%, rgba(138,169,255,0.55) 75%, rgba(138,169,255,0) 100%)",
        }}
      />
      <div
        aria-hidden
        className="pointer-events-none absolute left-0 right-0 top-1/2 h-[44px] -translate-y-1/2 blur-xl opacity-95"
        style={{
          background:
            "linear-gradient(90deg, rgba(252,82,0,0) 0%, rgba(252,82,0,0.7) 35%, rgba(204,120,92,0.8) 50%, rgba(252,82,0,0.7) 65%, rgba(252,82,0,0) 100%)",
        }}
      />

      <div className="absolute left-1/2 top-[40px] -translate-x-1/2">
        <div
          className="flex h-[120px] w-[120px] items-center justify-center rounded-[18px] bg-[#fc5200]"
          style={{ boxShadow: "0 24px 60px -20px rgba(252,82,0,0.55)" }}
        >
          <svg viewBox="0 0 24 24" className="h-12 w-12" fill="#fff">
            <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169" />
          </svg>
        </div>
      </div>

      <div className="absolute bottom-[40px] left-1/2 -translate-x-1/2">
        <div
          className="flex h-[120px] w-[120px] items-center justify-center rounded-[18px] bg-white"
          style={{ boxShadow: "0 24px 60px -20px rgba(204,120,92,0.55), 0 0 0 1px rgba(0,0,0,0.04)" }}
        >
          <svg viewBox="0 0 24 24" className="h-14 w-14" fill="#cc785c">
            <path d="M4.709 15.955l4.72-2.647.079-.23-.079-.128H9.2l-.79-.048-2.698-.073-2.339-.097-2.266-.122-.571-.121L0 11.784l.055-.352.48-.321.686.06 1.52.103 2.278.158 1.652.097 2.448.255h.389l.055-.157-.134-.098-.103-.097-2.358-1.596-2.552-1.688-1.336-.972-.724-.491-.364-.462-.158-1.008.656-.722.881.06.225.061.893.686 1.908 1.477 2.491 1.833.365.304.146-.103.018-.073-.164-.274-1.355-2.446-1.446-2.49-.644-1.032-.17-.619a2.97 2.97 0 01-.104-.729L6.283.134 6.696 0l.996.134.42.364.62 1.418 1.002 2.228 1.555 3.03.456.898.243.832.091.255h.158V9.01l.128-1.706.237-2.095.23-2.695.08-.76.376-.91.747-.492.584.28.48.685-.067.444-.286 1.851-.559 2.903-.364 1.942h.212l.243-.243.985-1.306 1.652-2.064.73-.82.85-.904.547-.431h1.033l.76 1.129-.34 1.166-1.064 1.347-.881 1.142-1.264 1.7-.79 1.36.073.11.188-.02 2.856-.606 1.543-.28 1.841-.315.833.388.091.395-.328.807-1.969.486-2.309.462-3.439.813-.042.03.049.061 1.549.146.662.036h1.622l3.02.225.79.522.474.638-.079.485-1.215.62-1.64-.389-3.829-.91-1.312-.329h-.182v.11l1.093 1.068 2.005 1.81 2.508 2.33.127.578-.322.455-.34-.049-2.204-1.657-.851-.747-1.926-1.62h-.128v.17l.444.649 2.345 3.521.122 1.08-.17.353-.608.213-.668-.122-1.374-1.925-1.415-2.167-1.143-1.943-.14.08-.674 7.254-.316.37-.729.28-.607-.461-.322-.747.322-1.476.389-1.924.315-1.53.286-1.9.17-.632-.012-.042-.14.018-1.434 1.967-2.18 2.945-1.726 1.845-.414.164-.717-.37.067-.662.401-.589 2.388-3.036 1.44-1.882.93-1.087-.006-.158h-.055L4.132 18.56l-1.13.146-.487-.456.061-.746.231-.243 1.908-1.312-.006.006z" />
          </svg>
        </div>
      </div>
    </div>
  );
}

function HowItWorks() {
  const steps = [
    { n: "01", t: "Connect Strava", d: "One OAuth click. We pull your last 90 days and listen for new activities live. Encrypted tokens, RLS on every row." },
    { n: "02", t: "Add the connector", d: 'In Claude.ai, ChatGPT or Gemini, "Add custom connector" → paste the link → done. Your chat now has access to your training data.' },
    { n: "03", t: "Ask anything", d: '"Write me a 12-week marathon plan." "Why was Saturday\'s long run so hard?" "Am I polarized or stuck in grey zone?" Real answers from your real data.' },
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

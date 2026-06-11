import Link from "next/link";
import Image from "next/image";
import { Brand, StepIcon, Check, StravaGlyph } from "./icons";

export function Hero() {
  return (
    <header className="hero" id="top">
      <div className="hero-bloom" aria-hidden="true"></div>
      <div className="eyebrow reveal">
        <span className="live">
          <span className="dot"></span>Now live
        </span>
        Connect Strava to Claude &amp; ChatGPT
      </div>
      <h1 className="reveal d1">
        Understand your <em className="grad-text">training with AI.</em>
      </h1>
      <p className="sub reveal d2">
        Connect your Strava account to ChatGPT or Claude and get deeper insights into your
        workouts, recovery, fitness trends, and performance — using your real training data.
      </p>
      <div className="hero-cta reveal d3">
        <Link className="btn btn-dark btn-lg" href="/signup">
          Get started <span className="arrow">→</span>
        </Link>
      </div>
      <p className="hero-note reveal d3">
        Works with Garmin, Apple Watch, Polar, COROS, Suunto and Wahoo — anything that auto-syncs to Strava.
      </p>
    </header>
  );
}

const STEPS = [
  {
    n: "01",
    t: "Connect your Strava",
    icon: "link" as const,
    d: "Link your account in one tap. Your whole history comes with you, and new workouts sync automatically.",
  },
  {
    n: "02",
    t: "Add it to your AI",
    icon: "plug" as const,
    d: "Paste one link into Claude or ChatGPT. No new app, no dashboard to learn.",
  },
  {
    n: "03",
    t: "Just ask",
    icon: "chat" as const,
    d: "Your AI now sees your runs, recovery, trends and zones. Just ask naturally — real answers, built on your data.",
  },
];

export function HowItWorks() {
  return (
    <section className="section" id="how">
      <div className="section-head reveal">
        <div className="kicker">How it works</div>
        <h2>
          The context your AI chatbot <span className="grad-text">was missing.</span>
        </h2>
        <p>
          Connect your training data once — and every conversation with your AI assistant is backed
          by your training history, load trends and recovery.
        </p>
      </div>
      <div className="steps">
        {STEPS.map((s, i) => (
          <div className={"step reveal d" + (i + 1)} key={s.n}>
            <div className="ic">
              <StepIcon kind={s.icon} />
            </div>
            <div className="n">{s.n}</div>
            <h3>{s.t}</h3>
            <p>{s.d}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export function Features() {
  return (
    <section className="section" id="features">
      <div className="section-head reveal">
        <div className="kicker">Why it&apos;s different</div>
        <h2>
          Generic AI guesses. <span className="grad-text">Yours knows.</span>
        </h2>
        <p>
          Get answers from your actual numbers — the runs you logged, the nights you slept, the
          zones you train in.
        </p>
      </div>

      <div className="bento">
        <div className="card span2 dark reveal">
          <div className="c-kicker">Works inside your chat</div>
          <h3>Bring your own coach — Claude or ChatGPT.</h3>
          <p>
            EvolveRun is a custom connector, not another subscription dashboard. It rides along
            inside the assistant you already use.
          </p>
          <div className="quote-models">
            <span className="model-chip">
              <span className="d" style={{ background: "#cc785c" }}></span>Claude
            </span>
            <span className="model-chip">
              <span className="d" style={{ background: "#10a37f" }}></span>ChatGPT
            </span>
          </div>
          <div className="conn-art" aria-hidden="true">
            <span className="conn-node strava">
              <StravaGlyph />
            </span>
            <span className="conn-flow">
              <i />
              <i />
              <i />
            </span>
            <span className="conn-node ai">
              <Image src="/claude-symbol.png" alt="Claude" width={38} height={38} />
            </span>
          </div>
        </div>

        <div className="card reveal d1">
          <div className="c-kicker">Live aerobic data</div>
          <h3>Reads the trend, not the day.</h3>
          <p>
            Pace, HR efficiency, HRV and load — tracked over months, so the advice follows your real
            adaptation curve.
          </p>
          <div className="statline">
            <span className="big grad-text">62</span>
            <span className="unit">ms HRV ↑</span>
          </div>
        </div>

        <div className="card reveal d1">
          <div className="c-kicker">Adaptive plans</div>
          <h3>Plans that re-write themselves.</h3>
          <p>
            Travel Friday? Bad sleep? The week bends around your life instead of breaking when you
            miss a session.
          </p>
          <div className="statline">
            <span className="big grad-text">∞</span>
            <span className="unit">re-plans</span>
          </div>
        </div>

        <div className="card span2 reveal d2">
          <div className="c-kicker">Private by design</div>
          <h3>Your data stays yours.</h3>
          <p>
            Encrypted tokens, row-level security on every record, and a one-click delete that wipes
            everything. We&apos;re the data layer — never the landlord.
          </p>
          <div className="sec-rows">
            <div className="sec-row">
              <Check /> OAuth-only access — we never see your password
            </div>
            <div className="sec-row">
              <Check /> Row-level security isolates every athlete&apos;s data
            </div>
            <div className="sec-row">
              <Check /> Delete your account and all data in one click
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export function CTA() {
  return (
    <section className="cta" style={{ marginTop: 40 }}>
      <div className="cta-inner reveal">
        <div className="cta-bloom" aria-hidden="true"></div>
        <h2>
          Ready to let your AI read
          <br />
          your <em className="grad-text">training data?</em>
        </h2>
        <p>Connect Strava in two minutes and ask your first real question tonight.</p>
        <Link className="btn btn-light btn-lg" href="/signup">
          Get started <span className="arrow">→</span>
        </Link>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="footer">
      <div className="footer-grid">
        <div className="footer-brand">
          <div className="nav-brand">
            <Brand size={20} /> EvolveRun
          </div>
          <p>
            The adaptive performance layer for endurance athletes. Your real training data, in the AI
            you already use.
          </p>
        </div>
        <div className="footer-cols">
          <div className="footer-col">
            <h4>Product</h4>
            <a href="#demo">Demo</a>
            <a href="#how">How it works</a>
            <a href="#features">Why it&apos;s different</a>
          </div>
          <div className="footer-col">
            <h4>Company</h4>
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <a href="https://github.com/255065/evovlerun" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
          </div>
          <div className="footer-col">
            <h4>Get started</h4>
            <Link href="/signup">Sign up</Link>
            <Link href="/login">Log in</Link>
          </div>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} EvolveRun</span>
        <span>Built for runners who want the truth.</span>
      </div>
    </footer>
  );
}

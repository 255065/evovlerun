"use client";

import { useMemo, useState } from "react";
import { finishOnboardingAction } from "./actions";

type Step = 0 | 1 | 2 | 3 | 4 | 5 | 6;

const clampStep = (n: number): Step => Math.max(0, Math.min(6, n)) as Step;

type GoalDetail = Record<string, string>;

type GoalDef = { id: string; title: string; desc: string; badge?: string };

type State = {
  goal: string | null;
  goal_detail: GoalDetail;
  weekly_sessions: number;
  weekly_hours: number;
  training_style: "structured" | "freeflow" | "adaptive" | "hybrid" | null;
  preferred_ai_coach: "claude" | "gpt" | "gemini" | null;
};

const INITIAL: State = {
  goal: null,
  goal_detail: {},
  weekly_sessions: 4,
  weekly_hours: 6,
  training_style: null,
  preferred_ai_coach: null,
};

const GOALS: GoalDef[] = [
  { id: "race", title: "Race a goal event", desc: "Marathon, gran fondo, triathlon — a date on the calendar.", badge: "MOST PICKED" },
  { id: "base", title: "Build aerobic base", desc: "More easy volume, a deeper engine, room to grow." },
  { id: "strength", title: "Get stronger", desc: "Lift heavier, move better, stay durable." },
  { id: "trail", title: "Trail & ultra", desc: "Vert, time on feet, mountain readiness." },
  { id: "triathlon", title: "Triathlon", desc: "Three sports, one weekly rhythm." },
  { id: "cycle", title: "Cycling focus", desc: "FTP, climbing, long-day stamina." },
  { id: "hybrid", title: "Hybrid athlete", desc: "Strength and endurance in the same week." },
  { id: "general", title: "General fitness", desc: "Stay consistent, feel good, no race pressure." },
];

const STYLES = [
  { id: "structured" as const, title: "Structured plan", desc: "A weekly schedule with prescribed sessions, paces, and progression." },
  { id: "freeflow" as const, title: "Free-flow", desc: "No fixed plan. Pick from suggested workouts when you want them." },
  { id: "adaptive" as const, title: "Adaptive", desc: "Plan reshapes itself around your readiness, sleep, and life." },
  { id: "hybrid" as const, title: "Hybrid", desc: "Anchor sessions you commit to, with flexible days around them." },
];

const COACHES = [
  { id: "claude" as const, name: "Claude", color: "#d97757", sub: "Considered. Careful with nuance.", sample: "Why was Tuesday's threshold so off? — Looking at your last two weeks, you slept 5h 40m the night before. Intervals weren't off; your body was." },
  { id: "gpt" as const, name: "ChatGPT", color: "#10a37f", sub: "Versatile. Fast. Broad.", sample: "Plan my week around a tempo Tuesday. — Easy 8K Mon, 6×8min @ threshold Tue, recovery 5K Wed, easy 10K Thu, off Fri, long 22K Sat, easy 6K Sun." },
  { id: "gemini" as const, name: "Gemini", color: "#4285f4", sub: "Multimodal. Searches the web.", sample: "Weather for Saturday's long run? — 14°C, light NW wind, dry. Good window for the 22K." },
];

export function OnboardingWizard({
  fullName,
  stravaConnected,
}: {
  fullName: string;
  stravaConnected: boolean;
}) {
  const [step, setStep] = useState<Step>(0);
  const [state, setState] = useState<State>(INITIAL);
  const [submitting, setSubmitting] = useState(false);

  // Skip the Strava step entirely if they connected before reaching us.
  // We still show progress as 3/5 so the count stays honest.
  const stepLabel = useMemo(() => {
    if (step === 0 || step === 6) return null;
    return `Question ${step} / 5`;
  }, [step]);

  const canContinue = useMemo(() => {
    if (step === 1) return state.goal !== null;
    if (step === 4) return state.training_style !== null;
    if (step === 5) return state.preferred_ai_coach !== null;
    return true;
  }, [step, state]);

  function next() {
    setStep((s) => clampStep(s + 1));
  }
  function back() {
    setStep((s) => clampStep(s - 1));
  }
  function goTo(s: Step) {
    setStep(s);
  }

  return (
    <div>
      {/* Progress eyebrow + step label */}
      {stepLabel && (
        <div className="mb-8 flex items-center gap-3">
          <span className="font-mono text-[11px] tracking-widest uppercase text-neutral-500">
            {stepLabel}
          </span>
          <div className="h-px flex-1 bg-neutral-300/60">
            <div
              className="h-full bg-[color:var(--evr-accent)] transition-all"
              style={{ width: `${(step / 5) * 100}%` }}
            />
          </div>
        </div>
      )}

      {step === 0 && <Hero name={fullName} onStart={() => setStep(1)} />}

      {step === 1 && (
        <GoalStep
          state={state}
          setState={setState}
          onBack={back}
          onNext={next}
          canContinue={canContinue}
        />
      )}

      {step === 2 && (
        <VolumeStep
          state={state}
          setState={setState}
          onBack={back}
          onNext={next}
        />
      )}

      {step === 3 && (
        <StravaStep
          stravaConnected={stravaConnected}
          onBack={back}
          onNext={next}
        />
      )}

      {step === 4 && (
        <StyleStep
          state={state}
          setState={setState}
          onBack={back}
          onNext={next}
          canContinue={canContinue}
        />
      )}

      {step === 5 && (
        <CoachStep
          state={state}
          setState={setState}
          onBack={back}
          onNext={next}
          canContinue={canContinue}
        />
      )}

      {step === 6 && (
        <SummaryStep
          state={state}
          stravaConnected={stravaConnected}
          submitting={submitting}
          setSubmitting={setSubmitting}
          onBack={back}
          goTo={goTo}
        />
      )}
    </div>
  );
}

// ─── Step 0 · Hero ─────────────────────────────────────────────────────

function Hero({ name, onStart }: { name: string; onStart: () => void }) {
  return (
    <div>
      <span className="inline-flex items-center gap-2 rounded-full border border-neutral-300/70 bg-white/60 px-3 py-1 text-[12px] text-neutral-700">
        <span className="h-1.5 w-1.5 rounded-full bg-[color:var(--evr-accent)]" />
        Setting up
      </span>
      <h1 className="evr-headline mt-7 text-[clamp(40px,6.5vw,64px)] tracking-[-0.025em]">
        Hej {name}. <span className="evr-emphasis">5 hurtige spørgsmål.</span>
      </h1>
      <p className="mt-5 max-w-xl text-[17px] leading-relaxed text-neutral-700">
        To minutter. Vi bruger svarene til at give chat-assistenten den kontekst, den har brug for —
        så den ikke skal gætte hver gang du spørger om en plan.
      </p>
      <div className="mt-8 flex items-center gap-4">
        <button
          onClick={onStart}
          className="inline-flex items-center gap-2 rounded-lg bg-neutral-950 px-6 py-3 text-[14.5px] font-medium text-white"
        >
          Start setup →
        </button>
        <span className="font-mono text-[12px] tracking-widest uppercase text-neutral-500">
          ≈ 2 minutes
        </span>
      </div>

      <div className="mt-16 grid grid-cols-3 gap-8 border-t border-neutral-300/60 pt-9">
        <Stat n="11" label="MCP tools" />
        <Stat n="3" label="AI coaches" />
        <Stat n={<>14<span className="text-[color:var(--evr-accent)]">+</span></>} label="Devices via Strava" />
      </div>
    </div>
  );
}

function Stat({ n, label }: { n: React.ReactNode; label: string }) {
  return (
    <div>
      <div className="text-[36px] font-semibold leading-none tracking-[-0.04em]">{n}</div>
      <div className="mt-2.5 font-mono text-[11px] tracking-widest uppercase text-neutral-500">
        {label}
      </div>
    </div>
  );
}

// ─── Step 1 · Goal ─────────────────────────────────────────────────────

function GoalStep({
  state,
  setState,
  onBack,
  onNext,
  canContinue,
}: {
  state: State;
  setState: (s: State | ((s: State) => State)) => void;
  onBack: () => void;
  onNext: () => void;
  canContinue: boolean;
}) {
  return (
    <div>
      <QuestionHeader
        title="What are you training for?"
        subtitle="Pick the goal that matters most right now. Your coach will tilt the plan toward it."
      />
      <div className="mt-8 space-y-3">
        {GOALS.map((g) => {
          const selected = state.goal === g.id;
          return (
            <button
              key={g.id}
              onClick={() => setState({ ...state, goal: g.id })}
              className={`flex w-full items-start gap-4 rounded-2xl border p-5 text-left transition ${
                selected
                  ? "border-[color:var(--evr-accent)] bg-[color:var(--evr-accent-soft)]"
                  : "border-neutral-300/70 bg-white/60 hover:border-neutral-400"
              }`}
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-[16px] font-semibold tracking-[-0.01em]">{g.title}</h3>
                  {g.badge && (
                    <span className="rounded-full bg-neutral-950 px-2 py-[2px] text-[10px] font-medium tracking-wide text-white">
                      {g.badge}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-[13.5px] text-neutral-600">{g.desc}</p>
              </div>
              <span
                className={`mt-1 inline-block h-4 w-4 shrink-0 rounded-full border ${
                  selected ? "border-[color:var(--evr-accent)] bg-[color:var(--evr-accent)]" : "border-neutral-400 bg-white"
                }`}
              />
            </button>
          );
        })}
      </div>

      {state.goal === "race" && (
        <div className="mt-6 space-y-3 rounded-2xl border border-neutral-300/70 bg-white/60 p-5">
          <Field label="What kind of event?">
            <select
              className={FIELD_CLS}
              value={state.goal_detail.eventKind ?? ""}
              onChange={(e) =>
                setState({ ...state, goal_detail: { ...state.goal_detail, eventKind: e.target.value } })
              }
            >
              <option value="">Select…</option>
              <option>Road marathon</option>
              <option>Half marathon</option>
              <option>10K / 5K</option>
              <option>Trail / ultra</option>
              <option>Gran fondo</option>
              <option>Triathlon</option>
            </select>
          </Field>
          <Field label={<>When <span className="text-neutral-500">(optional)</span></>}>
            <input
              className={FIELD_CLS}
              type="text"
              placeholder="YYYY-MM-DD"
              value={state.goal_detail.when ?? ""}
              onChange={(e) =>
                setState({ ...state, goal_detail: { ...state.goal_detail, when: e.target.value } })
              }
            />
          </Field>
          <Field label={<>Goal time <span className="text-neutral-500">(optional)</span></>}>
            <input
              className={FIELD_CLS}
              placeholder="e.g. sub-3:30, finish, or PR"
              value={state.goal_detail.goalTime ?? ""}
              onChange={(e) =>
                setState({ ...state, goal_detail: { ...state.goal_detail, goalTime: e.target.value } })
              }
            />
          </Field>
        </div>
      )}

      <FooterActions onBack={onBack} onContinue={onNext} continueDisabled={!canContinue} />
    </div>
  );
}

// ─── Step 2 · Volume ───────────────────────────────────────────────────

function VolumeStep({
  state,
  setState,
  onBack,
  onNext,
}: {
  state: State;
  setState: (s: State | ((s: State) => State)) => void;
  onBack: () => void;
  onNext: () => void;
}) {
  const sessions = state.weekly_sessions;
  const hours = state.weekly_hours;
  const load =
    sessions <= 3 ? "Light" : sessions <= 5 ? "Committed" : sessions <= 6 ? "Dedicated" : "Elite";
  const perSession = (hours / sessions).toFixed(1);
  return (
    <div>
      <QuestionHeader
        title="How often do you actually train?"
        subtitle="An honest baseline beats an ambitious one. We'll adjust as you go."
      />
      <div className="mt-8 space-y-4">
        <SliderCard
          label="Sessions per week"
          value={sessions}
          unit="days"
          min={2}
          max={10}
          onChange={(v) => setState({ ...state, weekly_sessions: v })}
        />
        <SliderCard
          label="Total hours per week"
          value={hours}
          unit="hrs"
          min={2}
          max={20}
          onChange={(v) => setState({ ...state, weekly_hours: v })}
        />
        <div className="flex items-center justify-between rounded-2xl border border-neutral-300/70 bg-white/60 px-5 py-4">
          <div>
            <div className="font-mono text-[11px] tracking-widest uppercase text-neutral-500">
              Your weekly load
            </div>
            <div className="mt-1 text-[20px] font-semibold tracking-[-0.02em]">{load}</div>
          </div>
          <div className="text-[14px] text-neutral-600">
            {sessions} × ≈{perSession}h
          </div>
        </div>
      </div>
      <FooterActions onBack={onBack} onContinue={onNext} />
    </div>
  );
}

function SliderCard({
  label,
  value,
  unit,
  min,
  max,
  onChange,
}: {
  label: string;
  value: number;
  unit: string;
  min: number;
  max: number;
  onChange: (v: number) => void;
}) {
  return (
    <div className="rounded-2xl border border-neutral-300/70 bg-white/60 p-5">
      <div className="flex items-baseline justify-between">
        <span className="text-[14px] text-neutral-700">{label}</span>
        <span className="text-[22px] font-semibold tracking-[-0.02em]">
          {value}
          <span className="ml-1 text-[12px] font-normal text-neutral-500">{unit}</span>
        </span>
      </div>
      <input
        type="range"
        className="mt-3 w-full accent-[color:var(--evr-accent)]"
        min={min}
        max={max}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </div>
  );
}

// ─── Step 3 · Strava (V1: only integration) ────────────────────────────

function StravaStep({
  stravaConnected,
  onBack,
  onNext,
}: {
  stravaConnected: boolean;
  onBack: () => void;
  onNext: () => void;
}) {
  return (
    <div>
      <QuestionHeader
        title="Where does your data live?"
        subtitle="EvolveRun reads your training from Strava. Garmin, Apple Watch, Polar, COROS, Suunto, Wahoo — they all auto-sync there, so one connection covers them all."
      />
      <div className="mt-8 rounded-2xl border border-neutral-300/70 bg-white/80 p-6">
        <div className="flex items-start gap-4">
          <div
            className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-white"
            style={{ background: "#fc4c02" }}
          >
            <svg viewBox="0 0 24 24" className="h-7 w-7" fill="currentColor">
              <path d="M15.387 17.944l-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066m-7.008-5.599l2.836 5.598h4.172L10.463 0l-7 13.828h4.169" />
            </svg>
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-[18px] font-semibold tracking-[-0.01em]">Strava</h3>
              {stravaConnected && (
                <span className="rounded-full bg-emerald-100 px-2 py-[2px] text-[11px] font-medium text-emerald-800">
                  ✓ Connected
                </span>
              )}
            </div>
            <p className="mt-1 text-[13.5px] leading-snug text-neutral-600">
              Pace, splits, heart rate, power, elevation. We sync the last 90 days on connect, then
              listen for live updates via webhook.
            </p>
            <p className="mt-3 text-[12.5px] text-neutral-500">
              We&apos;ll send you to Strava to authorize at the end. You can skip this step and
              connect later from <span className="font-mono">/dashboard/connections</span>.
            </p>
          </div>
        </div>
      </div>
      <div className="mt-4 rounded-xl border border-neutral-300/40 bg-neutral-50/50 p-4 text-[12.5px] text-neutral-500">
        <strong className="text-neutral-700">Not in V1:</strong> direct Garmin / Oura / WHOOP /
        Polar integrations. We&apos;re adding them in V2 once Strava-only proves the wedge.
      </div>
      <FooterActions onBack={onBack} onContinue={onNext} />
    </div>
  );
}

// ─── Step 4 · Style ────────────────────────────────────────────────────

function StyleStep({
  state,
  setState,
  onBack,
  onNext,
  canContinue,
}: {
  state: State;
  setState: (s: State | ((s: State) => State)) => void;
  onBack: () => void;
  onNext: () => void;
  canContinue: boolean;
}) {
  return (
    <div>
      <QuestionHeader
        title="How do you like to train?"
        subtitle="Some athletes want a fixed plan. Others want a partner. Tell us how you work best — the chat assistant will calibrate its tone."
      />
      <div className="mt-8 space-y-3">
        {STYLES.map((s) => {
          const selected = state.training_style === s.id;
          return (
            <button
              key={s.id}
              onClick={() => setState({ ...state, training_style: s.id })}
              className={`flex w-full items-start gap-4 rounded-2xl border p-5 text-left transition ${
                selected
                  ? "border-[color:var(--evr-accent)] bg-[color:var(--evr-accent-soft)]"
                  : "border-neutral-300/70 bg-white/60 hover:border-neutral-400"
              }`}
            >
              <div className="flex-1">
                <h3 className="text-[16px] font-semibold tracking-[-0.01em]">{s.title}</h3>
                <p className="mt-1 text-[13.5px] text-neutral-600">{s.desc}</p>
              </div>
              <span
                className={`mt-1 inline-block h-4 w-4 shrink-0 rounded-full border ${
                  selected ? "border-[color:var(--evr-accent)] bg-[color:var(--evr-accent)]" : "border-neutral-400 bg-white"
                }`}
              />
            </button>
          );
        })}
      </div>
      <FooterActions onBack={onBack} onContinue={onNext} continueDisabled={!canContinue} />
    </div>
  );
}

// ─── Step 5 · Coach pick ───────────────────────────────────────────────

function CoachStep({
  state,
  setState,
  onBack,
  onNext,
  canContinue,
}: {
  state: State;
  setState: (s: State | ((s: State) => State)) => void;
  onBack: () => void;
  onNext: () => void;
  canContinue: boolean;
}) {
  return (
    <div>
      <QuestionHeader
        title="Pick your AI coach."
        subtitle="Choose which assistant gets connected first. You can use the others later — all three read the same data."
      />
      <div className="mt-8 space-y-3">
        {COACHES.map((c) => {
          const selected = state.preferred_ai_coach === c.id;
          return (
            <button
              key={c.id}
              onClick={() => setState({ ...state, preferred_ai_coach: c.id })}
              className={`block w-full rounded-2xl border p-5 text-left transition ${
                selected
                  ? "border-[color:var(--evr-accent)] bg-[color:var(--evr-accent-soft)]"
                  : "border-neutral-300/70 bg-white/60 hover:border-neutral-400"
              }`}
            >
              <div className="flex items-center gap-4">
                <div
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg"
                  style={{ background: c.color + "22", color: c.color }}
                >
                  <svg viewBox="0 0 24 24" className="h-5 w-5" fill="currentColor">
                    <path d="M12 3 L13 11 L21 12 L13 13 L12 21 L11 13 L3 12 L11 11 Z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="text-[16px] font-semibold tracking-[-0.01em]">{c.name}</div>
                  <div className="text-[13px] text-neutral-600">{c.sub}</div>
                </div>
                <span
                  className={`inline-block h-4 w-4 shrink-0 rounded-full border ${
                    selected ? "border-[color:var(--evr-accent)] bg-[color:var(--evr-accent)]" : "border-neutral-400 bg-white"
                  }`}
                />
              </div>
              <div className="mt-3 rounded-xl bg-neutral-50/60 px-4 py-3 font-mono text-[11.5px] leading-relaxed whitespace-pre-wrap text-neutral-600">
                {c.sample}
              </div>
            </button>
          );
        })}
      </div>
      <FooterActions onBack={onBack} onContinue={onNext} continueDisabled={!canContinue} continueLabel="Review →" />
    </div>
  );
}

// ─── Step 6 · Summary + submit ────────────────────────────────────────

function SummaryStep({
  state,
  stravaConnected,
  submitting,
  setSubmitting,
  onBack,
  goTo,
}: {
  state: State;
  stravaConnected: boolean;
  submitting: boolean;
  setSubmitting: (b: boolean) => void;
  onBack: () => void;
  goTo: (s: Step) => void;
}) {
  const goal = GOALS.find((g) => g.id === state.goal);
  const style = STYLES.find((s) => s.id === state.training_style);
  const coach = COACHES.find((c) => c.id === state.preferred_ai_coach);

  // Wrap finishOnboardingAction so we can prevent double-submits and serialise
  // the wizard state into a single form field.
  async function submit(formData: FormData) {
    setSubmitting(true);
    try {
      await finishOnboardingAction(formData);
    } catch (err) {
      setSubmitting(false);
      // `redirect()` throws NEXT_REDIRECT which we want to propagate.
      if (err instanceof Error && err.message.includes("NEXT_REDIRECT")) throw err;
      console.error(err);
      alert("Could not save onboarding. Try again.");
    }
  }

  return (
    <div>
      <span className="font-mono text-[11px] tracking-widest uppercase text-neutral-500">
        Your setup
      </span>
      <h1 className="evr-headline mt-4 text-[clamp(36px,5.5vw,52px)] tracking-[-0.025em]">
        Looks good. <span className="evr-emphasis">Ready when you are.</span>
      </h1>
      <p className="mt-3 max-w-xl text-[16px] text-neutral-700">
        Anything off, edit it now. You can change everything later in settings.
      </p>

      <div className="mt-8 divide-y divide-neutral-300/50 rounded-2xl border border-neutral-300/70 bg-white/60">
        <SummaryRow k="Goal" v={goal?.title ?? "—"} subtitle={goal?.desc} onEdit={() => goTo(1)} />
        <SummaryRow
          k="Volume"
          v={`${state.weekly_sessions} sessions · ${state.weekly_hours} hrs/wk`}
          onEdit={() => goTo(2)}
        />
        <SummaryRow
          k="Data source"
          v={stravaConnected ? "Strava (already connected)" : "Strava (we'll connect after this)"}
          onEdit={() => goTo(3)}
        />
        <SummaryRow k="Style" v={style?.title ?? "—"} onEdit={() => goTo(4)} />
        <SummaryRow k="AI coach" v={coach?.name ?? "—"} onEdit={() => goTo(5)} />
      </div>

      <form action={submit} className="mt-8 flex items-center justify-between">
        <input
          type="hidden"
          name="payload"
          value={JSON.stringify({
            goal: state.goal,
            goal_detail: Object.keys(state.goal_detail).length ? state.goal_detail : null,
            weekly_sessions: state.weekly_sessions,
            weekly_hours: state.weekly_hours,
            training_style: state.training_style,
            preferred_ai_coach: state.preferred_ai_coach,
          })}
        />
        <input type="hidden" name="connect_strava" value={stravaConnected ? "0" : "1"} />
        <button
          type="button"
          onClick={onBack}
          className="text-[14px] text-neutral-600 hover:text-neutral-950"
        >
          ← Back
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center gap-2 rounded-lg bg-neutral-950 px-6 py-3 text-[14.5px] font-medium text-white disabled:opacity-60"
        >
          {submitting
            ? "Saving…"
            : stravaConnected
              ? "Open my dashboard →"
              : "Connect Strava → finish setup"}
        </button>
      </form>
    </div>
  );
}

function SummaryRow({
  k,
  v,
  subtitle,
  onEdit,
}: {
  k: string;
  v: string;
  subtitle?: string;
  onEdit: () => void;
}) {
  return (
    <div className="grid grid-cols-[100px_1fr_auto] items-center gap-4 px-5 py-4 text-[14px]">
      <span className="font-mono text-[11px] tracking-widest uppercase text-neutral-500">{k}</span>
      <div>
        <div className="font-medium text-neutral-900">{v}</div>
        {subtitle && <div className="text-[12.5px] text-neutral-600">{subtitle}</div>}
      </div>
      <button
        type="button"
        onClick={onEdit}
        className="text-[12.5px] text-neutral-600 underline hover:text-neutral-950"
      >
        Edit
      </button>
    </div>
  );
}

// ─── Shared bits ───────────────────────────────────────────────────────

function QuestionHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div>
      <h1 className="evr-headline text-[clamp(28px,4.5vw,40px)] tracking-[-0.025em]">{title}</h1>
      <p className="mt-3 max-w-xl text-[15.5px] leading-relaxed text-neutral-700">{subtitle}</p>
    </div>
  );
}

function FooterActions({
  onBack,
  onContinue,
  continueDisabled,
  continueLabel = "Continue →",
}: {
  onBack: () => void;
  onContinue: () => void;
  continueDisabled?: boolean;
  continueLabel?: string;
}) {
  return (
    <div className="mt-8 flex items-center justify-between">
      <button
        type="button"
        onClick={onBack}
        className="text-[14px] text-neutral-600 hover:text-neutral-950"
      >
        ← Back
      </button>
      <button
        type="button"
        onClick={onContinue}
        disabled={continueDisabled}
        className="inline-flex items-center gap-2 rounded-lg bg-neutral-950 px-6 py-3 text-[14.5px] font-medium text-white disabled:opacity-40"
      >
        {continueLabel}
      </button>
    </div>
  );
}

function Field({ label, children }: { label: React.ReactNode; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[13px] text-neutral-700">{label}</span>
      {children}
    </label>
  );
}

// Shared input/select look so the race-detail fields match the rest of the
// warm-beige wizard surface.
const FIELD_CLS =
  "w-full rounded-lg border border-neutral-300 bg-white px-3 py-2 text-[14px] outline-none focus:border-[color:var(--evr-accent)] focus:ring-2 focus:ring-[color:var(--evr-accent)]/20";

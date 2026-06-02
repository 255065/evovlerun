"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";

const EASE = [0.22, 1, 0.36, 1] as const;

// Sequence steps — each block reveals when `step` reaches its threshold.
const PROMPT = 1;
const THINKING = 2;
const TOOLS = 3;
const CHART = 4;
const SUMMARY = 5;
const MAX = SUMMARY;

const MONTHS = [
  { m: "Jan", pace: "5:23/km", bpm: 149, h: 64 },
  { m: "Feb", pace: "5:17/km", bpm: 147, h: 80 },
  { m: "Mar", pace: "5:08/km", bpm: 145, h: 98 },
];

const TOOLS_LIST = ["compare-strava-periods", "chart-easy-pace-trend", "get-coros-training-zones"];

/**
 * Landing-page chat demo — plays like a live Claude session: the prompt
 * appears, the tool chips pop in one-by-one, the bars grow up, then the
 * summary fades in. Content is always in the DOM (SSR / tests read it); the
 * timeline only drives the entrance. Reduced-motion users see it fully
 * rendered with no animation.
 */
export function ChatDemo() {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.35 });
  const [step, setStep] = useState(0);

  useEffect(() => {
    // When reduced motion is on, the fade/grow helpers below render every
    // block in its final state regardless of `step`, so the timeline is skipped.
    if (reduce || !inView || step >= MAX) return;
    const id = setTimeout(() => setStep((s) => s + 1), step === 0 ? 300 : 750);
    return () => clearTimeout(id);
  }, [reduce, inView, step]);

  // Fade-up props for a block gated on `threshold`.
  const fade = (threshold: number, delay = 0) =>
    reduce
      ? { initial: false as const, animate: { opacity: 1, y: 0 } }
      : {
          initial: { opacity: 0, y: 10 },
          animate: step >= threshold ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 },
          transition: { duration: 0.5, ease: EASE, delay },
        };

  // Vertical bar grow gated on the CHART step.
  const grow = (i: number, h: number) =>
    reduce
      ? { initial: false as const, animate: { height: `${h}%` } }
      : {
          initial: { height: 0 },
          animate: { height: step >= CHART ? `${h}%` : 0 },
          transition: { duration: 0.7, ease: EASE, delay: i * 0.15 },
        };

  return (
    <section ref={ref} className="mx-auto max-w-[760px] px-6 pb-24">
      <div className="rounded-[28px] border border-neutral-200 bg-[#f5f0e8] p-3 shadow-[0_24px_60px_-30px_rgba(60,40,20,0.35)]">
        {/* Window chrome */}
        <div className="relative flex items-center justify-center rounded-t-[20px] bg-[#ece6dc] px-4 py-2.5">
          <div className="absolute left-4 flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-neutral-300" />
            <span className="h-2.5 w-2.5 rounded-full bg-neutral-300" />
            <span className="h-2.5 w-2.5 rounded-full bg-neutral-300" />
          </div>
          <span className="font-mono text-[11px] tracking-[0.2em] text-neutral-600">CLAUDE.AI</span>
        </div>

        <div className="space-y-3 p-4 md:p-6">
          <div className="flex items-center justify-center gap-3 py-3">
            <ClaudeStar />
            <span className="evr-headline text-[28px] tracking-[-0.02em]">Afternoon</span>
          </div>

          {/* 1 — Prompt */}
          <motion.div
            {...fade(PROMPT)}
            className="rounded-2xl border border-neutral-200/80 bg-white p-5"
          >
            <p className="text-[14.5px] leading-relaxed text-neutral-900">
              Compare my easy running pace trend this year with Jan, Feb, March pace and easy HR.
            </p>
            <div className="mt-5 flex items-center justify-between">
              <span className="text-[12.5px] text-neutral-500">Sonnet 4.6</span>
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#cc785c] text-white">
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 19V5M5 12l7-7 7 7" />
                </svg>
              </span>
            </div>
          </motion.div>

          {/* 2 — Thinking */}
          <motion.div
            {...fade(THINKING)}
            className="rounded-full border border-neutral-200/80 bg-[#ece6dc]/60 px-4 py-2 text-[12.5px] text-neutral-600"
          >
            Grouping easy runs by month and comparing pace to HR efficiency
            <span className="ml-1 tracking-widest text-neutral-400">. . .</span>
          </motion.div>

          {/* 3 — Tools */}
          <motion.div
            {...fade(TOOLS)}
            className="rounded-2xl border border-neutral-200/80 bg-white p-5"
          >
            <div className="mb-4 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-[#cc785c]" />
              <span className="font-mono text-[11px] tracking-[0.18em] text-neutral-700">USING EVOLVERUN TOOLS</span>
              <span className="ml-1 rounded-full border border-[#cc785c]/40 px-2 py-[2px] font-mono text-[10px] tracking-[0.15em] text-[#cc785c]">
                EVOLVERUN
              </span>
            </div>

            <div className="flex flex-wrap gap-2.5">
              {TOOLS_LIST.map((name, i) => (
                <motion.span
                  key={name}
                  {...fade(TOOLS, i * 0.18)}
                  className="rounded-full border border-[#e7c9bb] bg-[#fdf2ec] px-3 py-1.5 font-mono text-[12px] text-[#cc785c]"
                >
                  {name}
                </motion.span>
              ))}
            </div>
          </motion.div>

          {/* 4 — Chart */}
          <motion.div
            {...fade(CHART)}
            className="rounded-2xl border border-neutral-200/80 bg-[#faf8f4] p-5"
          >
            <div className="font-mono text-[11px] tracking-[0.18em] text-neutral-500">
              JAN — MAR · PACE VS HR
            </div>

            <div className="mt-6 flex items-end gap-4" style={{ height: 180 }}>
              {MONTHS.map((col, i) => (
                <div key={col.m} className="flex h-full flex-1 flex-col items-center justify-end">
                  <div className="mb-2 text-[13px] font-medium text-neutral-700">{col.pace}</div>
                  <motion.div
                    {...grow(i, col.h)}
                    className="w-full max-w-[150px] rounded-t-[6px] bg-[#e8826b]"
                  />
                </div>
              ))}
            </div>

            <div className="mt-3 flex gap-4">
              {MONTHS.map((col) => (
                <div key={col.m} className="flex-1 text-center">
                  <div className="text-[14px] text-neutral-800">{col.m}</div>
                  <div className="mt-0.5 text-[12.5px] text-neutral-400">{col.bpm} bpm</div>
                </div>
              ))}
            </div>
          </motion.div>

          {/* 5 — Summary */}
          <motion.p
            {...fade(SUMMARY)}
            className="px-1 pt-2 text-[13.5px] leading-relaxed text-neutral-700"
          >
            Your easy-run pace improved each month while average easy HR dropped, suggesting
            cardiovascular adaptations. From 5:23/km at 149 bpm in January to 5:08/km at 145 bpm
            in March — that&apos;s faster pace with a lower heart rate. Claude grouped the easy runs
            using your training zones, compared month-by-month pace and HR, and then summarized the
            direction of change for you.
          </motion.p>
        </div>
      </div>
    </section>
  );
}

function ClaudeStar() {
  return (
    <svg viewBox="0 0 24 24" className="h-6 w-6" fill="#cc785c">
      <path d="M12 2l1.6 6.4L20 10l-6.4 1.6L12 18l-1.6-6.4L4 10l6.4-1.6L12 2z" />
    </svg>
  );
}

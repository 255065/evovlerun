"use client";

import { useEffect, useRef, useState } from "react";
import { useInView, useReducedMotion } from "framer-motion";

const EASE_OUT = (t: number) => 1 - Math.pow(1 - t, 3);

/**
 * Formats seconds-per-km as M:SS (e.g. 323 -> "5:23"). Exported for tests.
 */
export function formatPace(totalSeconds: number): string {
  const s = Math.max(0, Math.round(totalSeconds));
  const m = Math.floor(s / 60);
  const rem = s % 60;
  return `${m}:${String(rem).padStart(2, "0")}`;
}

type Mode = "pace" | "int";

/**
 * Animates a number from `from` to `to` when scrolled into view. The DOM
 * always contains a real value (starts at `to` for SSR/reduced-motion so the
 * page reads correctly without JS / in jsdom), then counts when visible.
 */
export function CountUp({
  from,
  to,
  mode = "int",
  durationMs = 1100,
  className,
}: {
  from: number;
  to: number;
  mode?: Mode;
  durationMs?: number;
  className?: string;
}) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.6 });
  // Start displayed at the target so SSR + reduced motion show the real value.
  const [value, setValue] = useState(to);

  useEffect(() => {
    // Value initialises to `to` so SSR + reduced motion show the real number.
    // Only animate on the client once the element scrolls into view; the first
    // rAF frame (t≈0) snaps to `from`, so the count-up starts there.
    if (reduce || !inView) return;
    let raf = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      setValue(from + (to - from) * EASE_OUT(t));
      if (t < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, reduce, from, to, durationMs]);

  const display = mode === "pace" ? formatPace(value) : String(Math.round(value));

  return (
    <span ref={ref} className={className}>
      {display}
    </span>
  );
}

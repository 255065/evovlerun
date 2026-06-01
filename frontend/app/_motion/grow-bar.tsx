"use client";

import { motion, useReducedMotion } from "framer-motion";

/**
 * Horizontal insight bar that grows from 0 to `pct` width when scrolled into
 * view. Reduced-motion renders it at full width immediately.
 */
export function GrowBar({
  pct,
  color = "#dc6b3f",
  delay = 0,
}: {
  pct: number;
  color?: string;
  delay?: number;
}) {
  const reduce = useReducedMotion();
  const target = `${Math.max(0, Math.min(100, pct))}%`;

  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-[#1a1612]/8">
      <motion.div
        className="h-full rounded-full"
        style={{ background: color }}
        initial={reduce ? false : { width: 0 }}
        whileInView={reduce ? undefined : { width: target }}
        animate={reduce ? { width: target } : undefined}
        viewport={{ once: true, amount: 0.6 }}
        transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1], delay }}
      />
    </div>
  );
}

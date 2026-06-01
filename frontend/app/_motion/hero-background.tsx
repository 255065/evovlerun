"use client";

/**
 * Layered warm background for the hero: a soft animated aurora glow plus a
 * fine grain texture overlay. Pure CSS (utilities in globals.css), no assets,
 * pointer-events:none so it never blocks interaction. Reduced-motion handled
 * in globals.css (.evr-aurora animation disabled).
 */
export function HeroBackground() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      <div
        className="evr-aurora"
        style={{ top: "-12%", right: "2%", width: "46%", height: "70%" }}
      />
      <div
        className="evr-aurora"
        style={{
          top: "28%",
          left: "-8%",
          width: "34%",
          height: "52%",
          animationDelay: "-7s",
          background:
            "radial-gradient(closest-side, rgba(252,76,2,0.22), transparent 72%)",
        }}
      />
      <div className="evr-grain" />
    </div>
  );
}

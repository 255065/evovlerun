import Image from "next/image";

/** EvolveRun brandmark — the bundled logo at a given pixel size. */
export function Brand({ size = 19 }: { size?: number }) {
  return <Image src="/evr-logo.png" alt="" width={size} height={size} />;
}

/** Step-card icons for "How it works" (link / plug / chat). */
export function StepIcon({ kind }: { kind: "link" | "plug" | "chat" }) {
  if (kind === "link")
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1.5 1.5" />
        <path d="M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1.5-1.5" />
      </svg>
    );
  if (kind === "plug")
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        <path d="M9 2v6M15 2v6M7 8h10v3a5 5 0 0 1-10 0V8zM12 16v6" />
      </svg>
    );
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12a8 8 0 0 1-11.3 7.3L3 21l1.7-6.7A8 8 0 1 1 21 12z" />
    </svg>
  );
}

/** Checkmark used in security rows. */
export function Check() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 6L9 17l-5-5" />
    </svg>
  );
}

/** Strava two-chevron glyph (two-tone) for the connector art. */
export function StravaGlyph() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M10.463 0 3.463 13.828h4.169l2.831-5.59 2.836 5.59h4.172L10.463 0Z" />
      <path d="m15.387 17.944-2.089-4.116h-3.065L15.387 24l5.15-10.172h-3.066l-2.084 4.116Z" opacity="0.6" />
    </svg>
  );
}

/** Floating-callout icons for the demo (activity / tool / chart / spark). */
export function CalloutIcon({ kind }: { kind: "activity" | "tool" | "chart" | "spark" }) {
  if (kind === "activity")
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 12h4l2 6 4-14 2 8h6" />
      </svg>
    );
  if (kind === "tool")
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.7 6.3a4 4 0 0 0-5.2 5.2L3 18v3h3l6.5-6.5a4 4 0 0 0 5.2-5.2l-2.7 2.7-2-2 2.4-2.4z" />
      </svg>
    );
  if (kind === "chart")
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
        <path d="M5 19V9M12 19V5M19 19v-7" />
      </svg>
    );
  return (
    <svg viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2l1.5 6L20 9.5 13.5 11 12 18l-1.5-7L4 9.5 10.5 8 12 2z" />
    </svg>
  );
}

/** Claude sunburst mark used in the chat-demo greeting. */
export function ClaudeStar() {
  return (
    <svg viewBox="0 0 30 30" fill="none" stroke="currentColor" aria-label="Claude">
      <circle cx="15" cy="15" r="2.6" fill="currentColor" stroke="none" />
      <g strokeWidth="2.5" strokeLinecap="round">
        <line x1="20" y1="15" x2="27.5" y2="15" />
        <line x1="18.54" y1="18.54" x2="23.84" y2="23.84" />
        <line x1="15" y1="20" x2="15" y2="27.5" />
        <line x1="11.46" y1="18.54" x2="6.16" y2="23.84" />
        <line x1="10" y1="15" x2="2.5" y2="15" />
        <line x1="11.46" y1="11.46" x2="6.16" y2="6.16" />
        <line x1="15" y1="10" x2="15" y2="2.5" />
        <line x1="18.54" y1="11.46" x2="23.84" y2="6.16" />
      </g>
    </svg>
  );
}

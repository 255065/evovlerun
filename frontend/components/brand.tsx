import Link from "next/link";

/**
 * Minimalist wordmark used in nav, footer, and any marketing chrome.
 * Single thin EKG-line glyph + the name in semibold — no extra noise.
 * The icon stays a hair below the cap height so it doesn't dominate.
 */
export function Brand({
  href = "/",
  className = "",
}: {
  href?: string;
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={`inline-flex items-center gap-2 text-[15px] font-semibold tracking-[-0.01em] text-[#1a1612] ${className}`}
    >
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" aria-hidden>
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
      EvolveRun
    </Link>
  );
}

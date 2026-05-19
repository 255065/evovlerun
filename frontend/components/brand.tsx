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
      className={`inline-flex items-center gap-2 text-[15px] font-semibold tracking-[-0.01em] text-neutral-950 ${className}`}
    >
      <svg viewBox="0 0 24 16" className="h-3.5 w-5" fill="none" aria-hidden>
        <path
          d="M1 8 H6 L8 3 L11 13 L14 6 L16 9 H23"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      EvolveRun
    </Link>
  );
}

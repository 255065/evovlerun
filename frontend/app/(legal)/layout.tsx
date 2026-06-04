import Link from "next/link";

// Shared chrome for the legal pages (/privacy, /terms). The `(legal)` route
// group does not affect the URL — both pages live at the root path.
export default function LegalLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white text-neutral-900">
      <header className="border-b border-neutral-200">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-6 py-5">
          <Link href="/" className="text-[15px] font-semibold">
            EvolveRun
          </Link>
          <Link href="/" className="text-[13px] text-neutral-500 hover:text-neutral-950">
            ← Back to home
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-6 py-12">{children}</main>
      <footer className="border-t border-neutral-200">
        <div className="mx-auto flex max-w-3xl flex-wrap gap-x-6 gap-y-2 px-6 py-8 text-[12.5px] text-neutral-500">
          <Link href="/privacy" className="hover:text-neutral-950">Privacy</Link>
          <Link href="/terms" className="hover:text-neutral-950">Terms</Link>
          <Link href="/login" className="hover:text-neutral-950">Log in</Link>
          <span>© {new Date().getFullYear()} EvolveRun</span>
        </div>
      </footer>
    </div>
  );
}

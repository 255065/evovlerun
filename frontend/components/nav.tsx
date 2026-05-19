import Link from "next/link";
import { logoutAction } from "@/app/(auth)/actions";
import { Brand } from "@/components/brand";

type NavProps = {
  email?: string | null;
};

/**
 * Minimal in-app nav: brand left, four items center, sign-out right.
 * Anything not in this list (limiter, connections, MCP, profile) lives
 * inside the dashboard surfaces or settings — the top chrome should
 * stay short to keep the focus on training.
 */
export function Nav({ email: _email }: NavProps) {
  return (
    <header className="border-b border-neutral-200 bg-[color:var(--evr-bg-warm)]/60 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1100px] items-center justify-between px-6">
        <Brand href="/dashboard" />
        <nav className="hidden items-center gap-7 text-[13.5px] text-neutral-700 sm:flex">
          <Link href="/dashboard" className="hover:text-neutral-950">
            Dashboard
          </Link>
          <Link href="/dashboard/training" className="hover:text-neutral-950">
            Training
          </Link>
          <Link href="/dashboard/account" className="hover:text-neutral-950">
            Account
          </Link>
        </nav>
        <form action={logoutAction}>
          <button
            type="submit"
            className="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] font-medium hover:bg-neutral-50"
          >
            Sign out
          </button>
        </form>
      </div>
    </header>
  );
}

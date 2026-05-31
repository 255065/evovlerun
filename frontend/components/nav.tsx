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
export function Nav({ email }: NavProps) {
  return (
    <header className="sticky top-0 z-40 border-b border-[#1a1612]/10 bg-[#f5f0e8]/88 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1100px] items-center justify-between px-5 sm:px-8">
        <Brand href="/dashboard" />
        <nav className="hidden items-center gap-7 text-[13.5px] text-[#5f564d] sm:flex">
          <Link href="/dashboard" className="hover:text-[#1a1612]">
            Dashboard
          </Link>
          <Link href="/dashboard/training" className="hover:text-[#1a1612]">
            Training
          </Link>
          <Link href="/dashboard/account" className="hover:text-[#1a1612]">
            Account
          </Link>
        </nav>
        <div className="flex items-center gap-4">
          {email && (
            <span className="hidden text-[12.5px] text-[#7a7168] md:inline">{email}</span>
          )}
          <form action={logoutAction}>
            <button
              type="submit"
              className="rounded-full border border-[#1a1612]/12 bg-white/55 px-4 py-2 text-[13px] font-medium text-[#1a1612] transition hover:bg-white"
            >
              Sign out
            </button>
          </form>
        </div>
      </div>
    </header>
  );
}

import Link from "next/link";
import { Activity } from "lucide-react";
import { logoutAction } from "@/app/(auth)/actions";
import { Button } from "@/components/ui/button";

type NavProps = {
  email?: string | null;
};

export function Nav({ email }: NavProps) {
  return (
    <header className="border-b border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-950">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
          <Activity className="h-5 w-5" />
          EvolveRun
        </Link>
        <nav className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
          >
            Dashboard
          </Link>
          <Link
            href="/dashboard/training"
            className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
          >
            Træning
          </Link>
          <Link
            href="/dashboard/limiter"
            className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
          >
            Limiter
          </Link>
          <Link
            href="/dashboard/connections"
            className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
          >
            Forbindelser
          </Link>
          <Link
            href="/dashboard/profile"
            className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
          >
            Profil
          </Link>
          <Link
            href="/dashboard/mcp"
            className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
          >
            MCP
          </Link>
          <Link
            href="/dashboard/account"
            className="text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white"
          >
            Account
          </Link>
          {email && (
            <span className="hidden text-sm text-neutral-500 sm:inline dark:text-neutral-400">
              {email}
            </span>
          )}
          <form action={logoutAction}>
            <Button type="submit" variant="ghost" size="sm">
              Log ud
            </Button>
          </form>
        </nav>
      </div>
    </header>
  );
}

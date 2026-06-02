"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { logoutAction } from "@/app/(auth)/actions";

/**
 * In-app top nav — Lovable "DashNav" look: brand left, three items center
 * (Dashboard / Training / Account), Sign out right. The active route is
 * highlighted from the current pathname.
 */
export function Nav() {
  const pathname = usePathname();
  const items: { href: string; label: string }[] = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/dashboard/training", label: "Training" },
    { href: "/dashboard/account", label: "Account" },
  ];

  return (
    <header className="border-b border-neutral-200/70">
      <div className="mx-auto flex max-w-[1100px] items-center justify-between px-5 py-[18px] sm:px-8">
        <Link href="/dashboard" className="flex items-center gap-2 text-[15px] font-semibold">
          <Image
            src="/evr-logo.png"
            alt=""
            width={24}
            height={24}
            className="object-contain mix-blend-multiply"
          />
          EvolveRun
        </Link>
        <nav className="hidden gap-8 text-[14px] text-neutral-700 md:flex">
          {items.map((it) => {
            const active =
              it.href === "/dashboard"
                ? pathname === "/dashboard"
                : pathname.startsWith(it.href);
            return (
              <Link
                key={it.href}
                href={it.href}
                className={active ? "font-medium text-neutral-950" : "hover:text-neutral-950"}
              >
                {it.label}
              </Link>
            );
          })}
        </nav>
        <form action={logoutAction}>
          <button
            type="submit"
            className="rounded-md border border-neutral-300 bg-white px-3.5 py-1.5 text-[13px] font-medium text-neutral-950 hover:bg-neutral-50"
          >
            Sign out
          </button>
        </form>
      </div>
    </header>
  );
}

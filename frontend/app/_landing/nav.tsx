"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brand } from "./icons";

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  const pathname = usePathname();
  const base = pathname === "/" ? "" : "/";

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 20);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  return (
    <div className="nav-wrap">
      <nav className={"nav" + (scrolled ? " scrolled" : "")}>
        <Link className="nav-brand" href="/" style={{ textDecoration: "none", color: "inherit" }}>
          <Brand /> EvolveRun
        </Link>
        <div className="nav-links">
          <a href={`${base}#demo`}>Demo</a>
          <a href={`${base}#how`}>How it works</a>
          <a href={`${base}#features`}>Why it&apos;s different</a>
          <Link href="/pricing" className={pathname === "/pricing" ? "nav-link-active" : ""}>Pricing</Link>
        </div>
        <div className="nav-cta">
          <Link className="btn btn-ghost" href="/login">
            Log in
          </Link>
          <Link className="btn btn-dark" href="/signup">
            Get started <span className="arrow">→</span>
          </Link>
        </div>
      </nav>
    </div>
  );
}

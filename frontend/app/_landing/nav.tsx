"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Brand } from "./icons";

export function Nav() {
  const [scrolled, setScrolled] = useState(false);
  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 20);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  return (
    <div className="nav-wrap">
      <nav className={"nav" + (scrolled ? " scrolled" : "")}>
        <a className="nav-brand" href="#top" style={{ textDecoration: "none", color: "inherit" }}>
          <Brand /> EvolveRun
        </a>
        <div className="nav-links">
          <a href="#demo">Demo</a>
          <a href="#how">How it works</a>
          <a href="#features">Why it&apos;s different</a>
          <a href="#pricing">Pricing</a>
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

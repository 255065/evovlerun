"use client";

import { useEffect } from "react";

// Adds `.in` to `.reveal` elements as they enter the viewport, triggering the
// CSS entrance animation. Mounted once by the landing page.
export function RevealController() {
  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>(".evr-landing .reveal"));
    const check = () => {
      const vh = window.innerHeight || 800;
      for (const el of els) {
        if (el.classList.contains("in")) continue;
        const r = el.getBoundingClientRect();
        if (r.top < vh * 0.92 && r.bottom > 0) el.classList.add("in");
      }
    };
    check();
    // a couple of deferred checks in case layout/fonts settle late
    const t1 = setTimeout(check, 120);
    const t2 = setTimeout(check, 400);
    window.addEventListener("scroll", check, { passive: true });
    window.addEventListener("resize", check);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      window.removeEventListener("scroll", check);
      window.removeEventListener("resize", check);
    };
  }, []);

  return null;
}

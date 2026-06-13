"use client";

import { useEffect } from "react";

// Adds `.in` to `.reveal` elements as they enter the viewport, triggering the
// CSS entrance animation. Mounted once by the landing page. Uses an
// IntersectionObserver so there are no per-scroll layout reads — the old
// scroll-listener + getBoundingClientRect loop forced a reflow on every scroll
// frame, which was visibly janky on phones.
export function RevealController() {
  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>(".evr-landing .reveal"));

    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            io.unobserve(entry.target);
          }
        }
      },
      // Fire a touch before the element fully enters, matching the old 0.92vh feel.
      { rootMargin: "0px 0px -8% 0px" },
    );

    for (const el of els) {
      if (!el.classList.contains("in")) io.observe(el);
    }
    return () => io.disconnect();
  }, []);

  return null;
}

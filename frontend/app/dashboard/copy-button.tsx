"use client";

import { useState } from "react";

/**
 * Click-to-copy prompt button. Shows "Copied" for 1.5s after success.
 * Falls back to a plain "Copy" if the clipboard API is unavailable
 * (rare on modern browsers, but keeps the button keyboard-accessible).
 */
export function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard unavailable — silently fail, no harm done.
    }
  }

  return (
    <button
      type="button"
      onClick={copy}
      className={`rounded-md px-3 py-1.5 text-[12.5px] font-medium transition ${
        copied
          ? "bg-emerald-100 text-emerald-800"
          : "bg-neutral-900 text-white hover:bg-neutral-800"
      }`}
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

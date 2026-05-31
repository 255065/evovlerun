"use client";

import { useState, useTransition } from "react";
import { deleteAccountAction } from "./actions";

/**
 * Inline danger-zone delete. User types "DELETE" to enable the destructive
 * button — matches Chirona's pattern. We don't pop a modal so this works
 * inside any layout without an overlay container.
 */
export function DeleteAccountButton() {
  const [typed, setTyped] = useState("");
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const matches = typed.trim() === "DELETE";

  function fire() {
    setError(null);
    startTransition(async () => {
      try {
        await deleteAccountAction();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Could not delete account");
      }
    });
  }

  return (
    <div className="space-y-3">
      <input
        type="text"
        value={typed}
        onChange={(e) => setTyped(e.target.value)}
        disabled={pending}
        className="w-full rounded-xl border border-[#1a1612]/12 bg-white/70 px-3.5 py-2 text-[13.5px] font-mono text-[#1a1612] outline-none focus:border-[#c0492a] focus:ring-2 focus:ring-[#c0492a]/30"
        placeholder="Type DELETE to confirm"
        autoComplete="off"
      />
      {error && <p className="text-[12.5px] text-[#c0492a]">{error}</p>}
      <button
        type="button"
        onClick={fire}
        disabled={!matches || pending}
        className="inline-flex items-center rounded-full bg-[#c0492a] px-5 py-2 text-[13px] font-medium text-white shadow-sm transition hover:bg-[#a83d22] disabled:cursor-not-allowed disabled:opacity-50"
      >
        {pending ? "Deleting…" : "Delete account"}
      </button>
    </div>
  );
}

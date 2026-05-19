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
        className="w-full rounded-md border border-neutral-300 bg-white px-3 py-2 text-[13.5px] font-mono outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/30"
        placeholder="Type DELETE to confirm"
        autoComplete="off"
      />
      {error && <p className="text-[12.5px] text-red-700">{error}</p>}
      <button
        type="button"
        onClick={fire}
        disabled={!matches || pending}
        className="inline-flex items-center rounded-md bg-red-600 px-4 py-2 text-[13px] font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {pending ? "Deleting…" : "Delete account"}
      </button>
    </div>
  );
}

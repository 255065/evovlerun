"use client";

import { useState, useTransition } from "react";
import { deleteAccountAction } from "./actions";

/**
 * Two-step destructive confirm: first click arms the action, second click
 * fires it. The user has to type their email to confirm — copying Stripe's
 * own pattern and removing the muscle-memory "yes" path. We don't use a
 * modal so this also works in any layout without an overlay container.
 */
export function DeleteAccountButton({ email }: { email: string }) {
  const [armed, setArmed] = useState(false);
  const [typed, setTyped] = useState("");
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const matches = typed.trim().toLowerCase() === email.trim().toLowerCase();

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

  if (!armed) {
    return (
      <button
        type="button"
        onClick={() => setArmed(true)}
        className="text-[13px] text-red-700 underline hover:text-red-900"
      >
        Slet konto permanent
      </button>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-red-200 bg-red-50 p-4">
      <div>
        <div className="text-[13.5px] font-semibold text-red-900">
          Slet konto permanent
        </div>
        <p className="mt-1 text-[12.5px] text-red-800">
          Alle dine data slettes — workouts, planer, Strava-forbindelser, profil.
          Aktivt abonnement opsiges med det samme uden refusion for den aktuelle periode.
          Dette kan ikke fortrydes.
        </p>
      </div>
      <div>
        <label className="block text-[12px] text-red-900">
          Skriv din email for at bekræfte: <span className="font-mono">{email}</span>
        </label>
        <input
          type="text"
          value={typed}
          onChange={(e) => setTyped(e.target.value)}
          disabled={pending}
          className="mt-1 w-full rounded-md border border-red-300 bg-white px-3 py-1.5 text-[13px] font-mono outline-none focus:border-red-500 focus:ring-2 focus:ring-red-500/30"
          placeholder={email}
          autoComplete="off"
        />
      </div>
      {error && <p className="text-[12.5px] text-red-900">{error}</p>}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => {
            setArmed(false);
            setTyped("");
            setError(null);
          }}
          disabled={pending}
          className="rounded-md border border-neutral-300 bg-white px-3 py-1.5 text-[13px] hover:bg-neutral-50 disabled:opacity-50"
        >
          Annullér
        </button>
        <button
          type="button"
          onClick={fire}
          disabled={!matches || pending}
          className="rounded-md bg-red-600 px-3 py-1.5 text-[13px] font-medium text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {pending ? "Sletter…" : "Slet for evigt"}
        </button>
      </div>
    </div>
  );
}

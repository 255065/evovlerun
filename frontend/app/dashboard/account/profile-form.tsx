"use client";

import { useActionState } from "react";
import { saveProfileAction, type ProfileFormState } from "./actions";

const initial: ProfileFormState = { ok: false };

/**
 * First / Last name + read-only email. The action joins the two names
 * back into the single full_name column we already store.
 */
export function ProfileForm({
  firstName,
  lastName,
  email,
}: {
  firstName: string;
  lastName: string;
  email: string;
}) {
  const [state, action, pending] = useActionState(saveProfileAction, initial);

  return (
    <form action={action} className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Field label="First name">
          <input
            name="first_name"
            defaultValue={firstName}
            autoComplete="given-name"
            className={INPUT}
          />
        </Field>
        <Field label="Last name">
          <input
            name="last_name"
            defaultValue={lastName}
            autoComplete="family-name"
            className={INPUT}
          />
        </Field>
      </div>
      <Field label="Email">
        <input
          name="email"
          value={email}
          readOnly
          className={`${INPUT} bg-neutral-100 text-neutral-500`}
        />
      </Field>

      <div className="flex items-center gap-3 pt-1">
        <button
          type="submit"
          disabled={pending}
          className="inline-flex items-center rounded-md bg-neutral-950 px-5 py-2 text-[13px] font-medium text-white shadow-sm transition hover:bg-neutral-800 disabled:opacity-60"
        >
          {pending ? "Saving…" : "Save"}
        </button>
        {state.ok && !pending && (
          <span className="text-[12.5px] text-emerald-700">Saved.</span>
        )}
        {state.error && (
          <span className="text-[12.5px] text-red-600">{state.error}</span>
        )}
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[13px] text-neutral-700">{label}</span>
      {children}
    </label>
  );
}

const INPUT =
  "w-full rounded-md border border-neutral-300 bg-white px-3.5 py-2 text-[14px] text-neutral-950 outline-none focus:border-neutral-400 focus:ring-2 focus:ring-neutral-200";

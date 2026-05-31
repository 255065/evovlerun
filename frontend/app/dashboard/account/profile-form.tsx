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
      <div className="grid grid-cols-2 gap-3">
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
          className={`${INPUT} bg-[#1a1612]/5 text-[#8a7f74]`}
        />
      </Field>

      <div className="flex items-center gap-3 pt-1">
        <button
          type="submit"
          disabled={pending}
          className="inline-flex items-center rounded-full bg-[#1a1612] px-5 py-2 text-[13px] font-medium text-white shadow-sm transition hover:bg-[#2b251f] disabled:opacity-60"
        >
          {pending ? "Saving…" : "Save"}
        </button>
        {state.ok && !pending && (
          <span className="text-[12.5px] text-emerald-700">Saved.</span>
        )}
        {state.error && (
          <span className="text-[12.5px] text-[#c0492a]">{state.error}</span>
        )}
      </div>
    </form>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-[13px] text-[#4b423a]">{label}</span>
      {children}
    </label>
  );
}

const INPUT =
  "w-full rounded-xl border border-[#1a1612]/12 bg-white/70 px-3.5 py-2 text-[14px] text-[#1a1612] outline-none focus:border-[#dc6b3f] focus:ring-2 focus:ring-[#dc6b3f]/30";

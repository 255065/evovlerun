"use client";

import { useActionState, useEffect, useRef } from "react";
import { changePasswordAction, type PasswordFormState } from "./actions";

const initial: PasswordFormState = { ok: false };

export function ChangePasswordForm() {
  const formRef = useRef<HTMLFormElement>(null);
  const [state, action, pending] = useActionState(changePasswordAction, initial);

  useEffect(() => {
    if (state.ok) formRef.current?.reset();
  }, [state.ok]);

  return (
    <form ref={formRef} action={action} className="space-y-4">
      <Field label="Current password">
        <input
          name="current_password"
          type="password"
          required
          autoComplete="current-password"
          className={INPUT}
        />
      </Field>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Field label="New password">
          <input
            name="password"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            className={INPUT}
          />
        </Field>
        <Field label="Confirm password">
          <input
            name="confirm"
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            className={INPUT}
          />
        </Field>
      </div>

      <div className="flex items-center gap-3 pt-1">
        <button
          type="submit"
          disabled={pending}
          className="inline-flex items-center rounded-md border border-neutral-300 bg-white px-5 py-2 text-[13px] font-medium text-neutral-950 transition hover:bg-neutral-50 disabled:opacity-60"
        >
          {pending ? "Updating..." : "Change password"}
        </button>
        {state.ok && !pending && (
          <span className="text-[12.5px] text-emerald-700">Password updated.</span>
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

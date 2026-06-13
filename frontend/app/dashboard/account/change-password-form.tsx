"use client";

import { useActionState, useEffect, useRef, useState } from "react";
import { changePasswordAction, type PasswordFormState } from "./actions";

const initial: PasswordFormState = { ok: false };

/**
 * "Change password" trigger + modal. The modal asks only for a new password —
 * the logged-in session authenticates the change (see changePasswordAction).
 */
export function ChangePasswordForm() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="inline-flex items-center rounded-md border border-neutral-300 bg-white px-5 py-2 text-[13px] font-medium text-neutral-950 transition hover:bg-neutral-50"
      >
        Change password
      </button>
      {open && <PasswordModal onClose={() => setOpen(false)} />}
    </>
  );
}

// Mounted only while open, so every open starts with fresh action state.
function PasswordModal({ onClose }: { onClose: () => void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [state, action, pending] = useActionState(changePasswordAction, initial);

  // Focus the field and let Escape dismiss the modal.
  useEffect(() => {
    inputRef.current?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Close shortly after a successful change.
  useEffect(() => {
    if (state.ok) {
      const t = setTimeout(onClose, 900);
      return () => clearTimeout(t);
    }
  }, [state.ok, onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-4 sm:items-center"
      onClick={onClose}
    >
      <div
        className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-[17px] font-semibold tracking-[-0.01em]">Change password</h2>
        <p className="mt-1 text-[13px] text-neutral-600">
          Enter a new password for your account.
        </p>

        <form action={action} className="mt-4 space-y-3">
          <label className="block">
            <span className="mb-1.5 block text-[13px] text-neutral-700">New password</span>
            <input
              ref={inputRef}
              name="password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              className={INPUT}
            />
          </label>

          {state.error && <p className="text-[12.5px] text-red-600">{state.error}</p>}
          {state.ok && <p className="text-[12.5px] text-emerald-700">Password updated.</p>}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="inline-flex items-center rounded-md px-4 py-2 text-[13px] font-medium text-neutral-600 transition hover:text-neutral-950"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={pending}
              className="inline-flex items-center rounded-md bg-neutral-950 px-5 py-2 text-[13px] font-medium text-white transition hover:bg-neutral-800 disabled:opacity-60"
            >
              {pending ? "Updating..." : "Update password"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const INPUT =
  "w-full rounded-md border border-neutral-300 bg-white px-3.5 py-2 text-[14px] text-neutral-950 outline-none focus:border-neutral-400 focus:ring-2 focus:ring-neutral-200";

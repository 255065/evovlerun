"use client";

import Link from "next/link";
import { useActionState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { signupAction, type AuthState } from "../actions";

const initialState: AuthState = { error: null };

export default function SignupPage() {
  const [state, formAction, pending] = useActionState(signupAction, initialState);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f0e8] px-4 text-[#1a1612]">
      <div className="w-full max-w-md">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2 text-[15px] font-semibold">
          <Brandmark />
          EvolveRun
        </Link>
        <div className="rounded-[24px] border border-[#1a1612]/10 bg-[#fbf8f1] p-8 shadow-xl shadow-[#1a1612]/8">
          <h1 className="evr-headline text-[30px] tracking-[-0.03em]">Create your account</h1>
          <p className="mt-2 text-[14.5px] text-[#5f564d]">Start your adaptive training journey.</p>
          <form action={formAction} className="mt-6 space-y-4">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full name</Label>
              <Input id="fullName" name="fullName" type="text" required autoComplete="name" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" name="email" type="email" required autoComplete="email" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password (min. 8 characters)</Label>
              <Input
                id="password"
                name="password"
                type="password"
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>
            {state.error && (
              <p className="text-sm text-red-600" role="alert">
                {state.error}
              </p>
            )}
            <Button
              type="submit"
              className="w-full bg-[#1a1612] text-white hover:bg-[#2b251f]"
              disabled={pending}
            >
              {pending ? "Creating..." : "Create account"}
            </Button>
          </form>
          <p className="mt-5 text-center text-[13.5px] text-[#6b6259]">
            Already have an account?{" "}
            <Link href="/login" className="font-medium text-[#dc6b3f] hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

function Brandmark() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
      <path d="M3 5 H17" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path
        d="M3 12 Q9 8 15 12 T21 12"
        stroke="#dc6b3f"
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
      />
      <path d="M3 19 H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

"use client";

import Link from "next/link";
import { Suspense, useActionState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginAction, type AuthState } from "../actions";

const initialState: AuthState = { error: null };

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f0e8] px-4 text-[#1a1612]">
      <div className="w-full max-w-md">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2 text-[15px] font-semibold">
          <Brandmark />
          EvolveRun
        </Link>
        <div className="rounded-[24px] border border-[#1a1612]/10 bg-[#fbf8f1] p-8 shadow-xl shadow-[#1a1612]/8">
          <h1 className="evr-headline text-[30px] tracking-[-0.03em]">Welcome back</h1>
          <p className="mt-2 text-[14.5px] text-[#5f564d]">Log in to see your coach.</p>
          {/* useSearchParams must live inside Suspense so Next.js can statically
              prerender the rest of the form without bailing out. */}
          <div className="mt-6">
            <Suspense fallback={<LoginForm fallbackRedirect="" />}>
              <SearchParamLoginForm />
            </Suspense>
          </div>
          <p className="mt-5 text-center text-[13.5px] text-[#6b6259]">
            No account?{" "}
            <Link href="/signup" className="font-medium text-[#dc6b3f] hover:underline">
              Create one
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

function SearchParamLoginForm() {
  const redirectTo = useSearchParams().get("redirect") ?? "";
  return <LoginForm fallbackRedirect={redirectTo} />;
}

function LoginForm({ fallbackRedirect }: { fallbackRedirect: string }) {
  const [state, formAction, pending] = useActionState(loginAction, initialState);
  return (
    <form action={formAction} className="space-y-4">
      <input type="hidden" name="redirect" value={fallbackRedirect} />
      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" name="email" type="email" required autoComplete="email" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input id="password" name="password" type="password" required autoComplete="current-password" />
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
        {pending ? "Logging in..." : "Log in"}
      </Button>
    </form>
  );
}

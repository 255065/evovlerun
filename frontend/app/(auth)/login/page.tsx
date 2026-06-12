"use client";

import Link from "next/link";
import Image from "next/image";
import { Suspense, useActionState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { loginAction, type AuthState } from "../actions";

const initialState: AuthState = { error: null };

export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#fbfaf7] px-4 text-neutral-950">
      <div className="w-full max-w-md">
        <Link href="/" className="mb-8 flex items-center justify-center gap-2 text-[15px] font-semibold">
          <Image src="/evr-logo.png" alt="" width={20} height={20} className="h-5 w-5" />
          EvolveRun
        </Link>
        <div className="rounded-2xl border border-neutral-200 bg-white p-8 shadow-sm">
          <h1 className="evr-headline text-[30px] tracking-[-0.03em]">Welcome back</h1>
          <p className="mt-2 text-[14.5px] text-neutral-600">Log in to see your coach.</p>
          {/* useSearchParams must live inside Suspense so Next.js can statically
              prerender the rest of the form without bailing out. */}
          <div className="mt-6">
            <Suspense fallback={<LoginForm fallbackRedirect="" />}>
              <SearchParamLoginForm />
            </Suspense>
          </div>
          <p className="mt-5 text-center text-[13.5px] text-neutral-500">
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
        <div className="flex items-center justify-between">
          <Label htmlFor="password">Password</Label>
          <Link
            href="/forgot-password"
            className="text-[13px] font-medium text-[#dc6b3f] hover:underline"
          >
            Forgot password?
          </Link>
        </div>
        <Input id="password" name="password" type="password" required autoComplete="current-password" />
      </div>
      {state.error && (
        <p className="text-sm text-red-600" role="alert">
          {state.error}
        </p>
      )}
      <Button
        type="submit"
        className="w-full bg-neutral-950 text-white hover:bg-neutral-800"
        disabled={pending}
      >
        {pending ? "Logging in..." : "Log in"}
      </Button>
    </form>
  );
}

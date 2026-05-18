"use client";

import Link from "next/link";
import { useActionState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { loginAction, type AuthState } from "../actions";

const initialState: AuthState = { error: null };

export default function LoginPage() {
  const [state, formAction, pending] = useActionState(loginAction, initialState);
  // OAuth consent + any other deep link round-trips through here; the server
  // action validates the value and falls back to /dashboard if it's unsafe.
  const next = useSearchParams().get("redirect") ?? "";

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-50 px-4 dark:bg-neutral-950">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Velkommen tilbage</CardTitle>
          <CardDescription>Log ind for at se din coach.</CardDescription>
        </CardHeader>
        <CardContent>
          <form action={formAction} className="space-y-4">
            <input type="hidden" name="redirect" value={next} />
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
            <Button type="submit" className="w-full" disabled={pending}>
              {pending ? "Logger ind..." : "Log ind"}
            </Button>
          </form>
          <p className="mt-4 text-center text-sm text-neutral-600 dark:text-neutral-400">
            Ingen konto?{" "}
            <Link href="/signup" className="font-medium underline">
              Opret en
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

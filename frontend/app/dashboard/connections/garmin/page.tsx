"use client";

import Link from "next/link";
import { useActionState } from "react";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  garminConnectAction,
  garminMfaAction,
  type GarminConnectState,
} from "./actions";

const initialState: GarminConnectState = { error: null, needsMfa: false, pendingToken: null };

export default function GarminLoginPage() {
  const [loginState, loginAction, loginPending] = useActionState(garminConnectAction, initialState);
  const [mfaState, mfaAction, mfaPending] = useActionState(garminMfaAction, initialState);

  // After login returns needsMfa, switch to MFA form.
  const state = mfaState.error || mfaState.needsMfa ? mfaState : loginState;
  const showMfa = loginState.needsMfa || mfaState.needsMfa;
  const pendingToken = loginState.pendingToken || mfaState.pendingToken;

  return (
    <div className="mx-auto max-w-md space-y-6">
      <div>
        <Link
          href="/dashboard/connections"
          className="text-sm text-neutral-600 hover:underline dark:text-neutral-400"
        >
          ← Tilbage til forbindelser
        </Link>
        <h1 className="mt-2 text-2xl font-bold tracking-tight">Forbind Garmin Connect</h1>
      </div>

      <div className="flex items-start gap-3 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm dark:border-amber-900 dark:bg-amber-950/50">
        <AlertTriangle className="h-4 w-4 shrink-0 text-amber-700 dark:text-amber-300" />
        <div className="text-amber-900 dark:text-amber-200">
          <p className="font-medium">Garmin bruger uofficielt API</p>
          <p className="mt-1">
            Vi taler med Garmin Connect&apos;s interne mobil-API via{" "}
            <code className="text-xs">python-garminconnect</code>. Det er ikke officielt
            understøttet af Garmin, og kan i teorien stoppe med at virke uden varsel.
            Dit password krypteres med Fernet før det sendes til vores server og opbevares
            ikke i klartekst.
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{showMfa ? "MFA-kode" : "Log ind på Garmin"}</CardTitle>
          <CardDescription>
            {showMfa
              ? "Indtast koden fra din authenticator-app eller SMS."
              : "Brug samme email + password som på Garmin Connect."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!showMfa ? (
            <form action={loginAction} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">Garmin-email</Label>
                <Input id="username" name="username" type="email" required autoComplete="off" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Garmin-password</Label>
                <Input id="password" name="password" type="password" required autoComplete="off" />
              </div>
              {state.error && (
                <p className="text-sm text-red-600" role="alert">
                  {state.error}
                </p>
              )}
              <Button type="submit" className="w-full" disabled={loginPending}>
                {loginPending ? "Logger ind..." : "Forbind"}
              </Button>
            </form>
          ) : (
            <form action={mfaAction} className="space-y-4">
              <input type="hidden" name="pending_token" value={pendingToken ?? ""} />
              <div className="space-y-2">
                <Label htmlFor="mfa_code">6-cifret kode</Label>
                <Input
                  id="mfa_code"
                  name="mfa_code"
                  type="text"
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={8}
                  required
                  autoFocus
                />
              </div>
              {state.error && (
                <p className="text-sm text-red-600" role="alert">
                  {state.error}
                </p>
              )}
              <Button type="submit" className="w-full" disabled={mfaPending}>
                {mfaPending ? "Bekræfter..." : "Bekræft MFA"}
              </Button>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

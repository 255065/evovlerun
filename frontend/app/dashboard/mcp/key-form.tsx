"use client";

import { useActionState, useState } from "react";
import { Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createKeyAction, type CreateKeyState } from "./actions";

const initialState: CreateKeyState = { error: null, newKey: null };

export function KeyForm() {
  const [state, formAction, pending] = useActionState(createKeyAction, initialState);
  const [copied, setCopied] = useState(false);

  async function copyKey() {
    if (!state.newKey) return;
    await navigator.clipboard.writeText(state.newKey.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-4">
      <form action={formAction} className="flex items-end gap-2">
        <div className="flex-1 space-y-2">
          <Label htmlFor="name">Navn på nøglen</Label>
          <Input id="name" name="name" placeholder="MacBook Claude Desktop" required maxLength={80} />
        </div>
        <Button type="submit" disabled={pending}>
          {pending ? "Genererer..." : "Generér"}
        </Button>
      </form>

      {state.error && (
        <p className="text-sm text-red-600" role="alert">
          {state.error}
        </p>
      )}

      {state.newKey && (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/50">
          <p className="text-sm font-medium text-emerald-900 dark:text-emerald-200">
            Nøgle oprettet ✅
          </p>
          <p className="mt-1 text-xs text-emerald-800 dark:text-emerald-300">
            Kopiér nøglen nu — vi viser den <strong>ikke igen</strong>.
          </p>
          <div className="mt-3 flex items-center gap-2">
            <code className="block flex-1 truncate rounded bg-white px-3 py-2 font-mono text-xs dark:bg-neutral-900">
              {state.newKey.key}
            </code>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={copyKey}
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copied ? "Kopieret" : "Kopiér"}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

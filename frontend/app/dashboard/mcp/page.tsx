import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { listKeys, revokeKeyAction } from "./actions";
import { KeyForm } from "./key-form";

export const dynamic = "force-dynamic";

export default async function MCPPage() {
  const keys = await listKeys();
  const activeKeys = keys.filter((k) => !k.revoked_at);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[36px] font-semibold tracking-[-0.025em]">Connector</h1>
        <p className="mt-1 text-[14px] text-neutral-600">
          Connect your training data to Claude, ChatGPT, or Gemini. You chat directly with the AI — it
          fetches the raw data, computes metrics, and gives you answers.
        </p>
      </div>

      <Card className="border-emerald-200 bg-emerald-50/50">
        <CardHeader>
          <CardTitle className="text-base">What you get</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="grid gap-2 text-sm sm:grid-cols-2">
            <li className="flex gap-2">
              <span className="text-emerald-600">✓</span>
              <span>Ask Claude or ChatGPT about any workout, split, HR zone, or period summary</span>
            </li>
            <li className="flex gap-2">
              <span className="text-emerald-600">✓</span>
              <span>Includes EvolveRun&apos;s computed metrics — CTL, ATL, TSB, ACWR</span>
            </li>
            <li className="flex gap-2">
              <span className="text-emerald-600">✓</span>
              <span>Save AI-written plans directly back to your training calendar</span>
            </li>
            <li className="flex gap-2">
              <span className="text-emerald-600">✓</span>
              <span>11 tools the assistant can call — single workouts up to 12-week trends</span>
            </li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-neutral-900 text-xs font-semibold text-white">
              1
            </span>
            Generate and install
          </CardTitle>
          <CardDescription>
            Create an API key. You&apos;ll get an auto-install script plus two manual fallbacks.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <KeyForm />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-neutral-900 text-xs font-semibold text-white">
              2
            </span>
            Your keys
            {activeKeys.length > 0 && <Badge tone="success">{activeKeys.length} active</Badge>}
          </CardTitle>
          <CardDescription>
            Revoke a key if it&apos;s compromised. You can have multiple keys active at once
            (one per device).
          </CardDescription>
        </CardHeader>
        <CardContent>
          {keys.length === 0 ? (
            <p className="text-sm text-neutral-500">
              No keys yet — create your first one above.
            </p>
          ) : (
            <ul className="divide-y divide-neutral-200">
              {keys.map((k) => {
                const isRevoked = k.revoked_at !== null;
                return (
                  <li key={k.id} className="flex items-center justify-between py-3">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium">{k.name}</p>
                      <p className="text-xs text-neutral-500">
                        <code className="font-mono">{k.key_prefix}…</code>
                        <span className="ml-2">
                          created {new Date(k.created_at).toLocaleDateString("en-GB")}
                        </span>
                        {k.last_used_at && (
                          <span className="ml-2">
                            last used {new Date(k.last_used_at).toLocaleDateString("en-GB")}
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="ml-3 flex items-center gap-2">
                      {isRevoked ? (
                        <Badge tone="warn">revoked</Badge>
                      ) : (
                        <form action={revokeKeyAction}>
                          <input type="hidden" name="id" value={k.id} />
                          <Button type="submit" variant="ghost" size="sm">
                            Revoke
                          </Button>
                        </form>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

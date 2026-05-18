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
        <h1 className="text-3xl font-bold tracking-tight">Connector</h1>
        <p className="mt-1 text-neutral-600 dark:text-neutral-400">
          Forbind dine træningsdata til Claude (og snart ChatGPT). Du chatter direkte med AI&apos;en — den henter
          rå data, beregner metrics, og giver dig svar. Ingen separat coach-app at lære.
        </p>
      </div>

      {/* Hero — what you get */}
      <Card className="border-emerald-200 bg-emerald-50/50 dark:border-emerald-900 dark:bg-emerald-950/20">
        <CardHeader>
          <CardTitle className="text-base">Hvad får du?</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="grid gap-2 text-sm sm:grid-cols-2">
            <li className="flex gap-2">
              <span className="text-emerald-600 dark:text-emerald-400">✓</span>
              <span>Spørg Claude om enhver træning, split, HR-zone, recovery-metric</span>
            </li>
            <li className="flex gap-2">
              <span className="text-emerald-600 dark:text-emerald-400">✓</span>
              <span>Inkluderer EvolveRun&apos;s beregnede metrics — CTL, VDOT, threshold, fatigue resistance</span>
            </li>
            <li className="flex gap-2">
              <span className="text-emerald-600 dark:text-emerald-400">✓</span>
              <span>Adgang til din detekterede limiter + plan med rationale</span>
            </li>
            <li className="flex gap-2">
              <span className="text-emerald-600 dark:text-emerald-400">✓</span>
              <span>20 værktøjer Claude kan kalde — fra single workout splits til 12-ugers trends</span>
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Step 1: generate + install */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-neutral-900 text-xs font-semibold text-white dark:bg-neutral-100 dark:text-neutral-900">
              1
            </span>
            Generér og install
          </CardTitle>
          <CardDescription>
            Lav en API-nøgle. Du får derefter et auto-install script og to fallback-måder at sætte den op på.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <KeyForm />
        </CardContent>
      </Card>

      {/* Existing keys management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-neutral-900 text-xs font-semibold text-white dark:bg-neutral-100 dark:text-neutral-900">
              2
            </span>
            Dine nøgler
            {activeKeys.length > 0 && <Badge tone="success">{activeKeys.length} aktive</Badge>}
          </CardTitle>
          <CardDescription>
            Tilbagekald en nøgle hvis den er kompromitteret. Du kan have flere nøgler aktive samtidigt (én pr. enhed).
          </CardDescription>
        </CardHeader>
        <CardContent>
          {keys.length === 0 ? (
            <p className="text-sm text-neutral-500">Ingen nøgler endnu — lav din første ovenfor.</p>
          ) : (
            <ul className="divide-y divide-neutral-200 dark:divide-neutral-800">
              {keys.map((k) => {
                const isRevoked = k.revoked_at !== null;
                return (
                  <li key={k.id} className="flex items-center justify-between py-3">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium">{k.name}</p>
                      <p className="text-xs text-neutral-500">
                        <code className="font-mono">{k.key_prefix}…</code>
                        <span className="ml-2">oprettet {new Date(k.created_at).toLocaleDateString("da-DK")}</span>
                        {k.last_used_at && (
                          <span className="ml-2">
                            sidst brugt {new Date(k.last_used_at).toLocaleDateString("da-DK")}
                          </span>
                        )}
                      </p>
                    </div>
                    <div className="ml-3 flex items-center gap-2">
                      {isRevoked ? (
                        <Badge tone="warn">tilbagekaldt</Badge>
                      ) : (
                        <form action={revokeKeyAction}>
                          <input type="hidden" name="id" value={k.id} />
                          <Button type="submit" variant="ghost" size="sm">
                            Tilbagekald
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

      {/* Roadmap note — sets expectations */}
      <div className="rounded-md border border-dashed border-neutral-300 bg-neutral-50/50 p-4 text-xs text-neutral-600 dark:border-neutral-700 dark:bg-neutral-900/30 dark:text-neutral-400">
        <p className="font-medium text-neutral-700 dark:text-neutral-300">På roadmappen</p>
        <p className="mt-1">
          Næste skridt: hostet HTTP MCP så install bliver one-click i Claude.ai (som Notion-connectoren) — ingen
          Terminal, ingen JSON-edits. Skipper også at kræve at repoet er klonet lokalt.
        </p>
      </div>
    </div>
  );
}

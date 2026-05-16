import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { listKeys, revokeKeyAction } from "./actions";
import { KeyForm } from "./key-form";

export default async function MCPPage() {
  const keys = await listKeys();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">MCP-forbindelse</h1>
        <p className="mt-1 text-neutral-600 dark:text-neutral-400">
          Generér en API-nøgle og forbind EvolveRun til Claude eller ChatGPT, så de kan tilgå dine data direkte.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>1. Generér en API-nøgle</CardTitle>
          <CardDescription>
            Giv nøglen et navn så du kan kende den senere (fx hvilken enhed eller AI-app der bruger den).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <KeyForm />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>2. Tilføj i Claude Desktop</CardTitle>
          <CardDescription>
            Åbn Claude Desktop&apos;s config-fil og tilføj EvolveRun som MCP-server.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <p>
            Fil-sti på macOS: <code className="rounded bg-neutral-100 px-1 py-0.5 dark:bg-neutral-800">~/Library/Application Support/Claude/claude_desktop_config.json</code>
          </p>
          <pre className="overflow-x-auto rounded-md bg-neutral-900 p-4 text-xs text-neutral-100">{`{
  "mcpServers": {
    "evolverun": {
      "command": "/Users/valdemarstoerum/dev/evolverun/backend/.venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/Users/valdemarstoerum/dev/evolverun/backend",
      "env": {
        "EVOLVERUN_API_KEY": "evr_DIN_NØGLE_HER"
      }
    }
  }
}`}</pre>
          <p>
            Genstart Claude Desktop. Spørg derefter: <em>&quot;Hvad var min sidste lange løbetur?&quot;</em>
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Eksisterende nøgler</CardTitle>
          <CardDescription>Tilbagekald en nøgle hvis den er kompromitteret eller ikke længere bruges.</CardDescription>
        </CardHeader>
        <CardContent>
          {keys.length === 0 ? (
            <p className="text-sm text-neutral-500">Ingen nøgler endnu.</p>
          ) : (
            <ul className="divide-y divide-neutral-200 dark:divide-neutral-800">
              {keys.map((k) => {
                const isRevoked = k.revoked_at !== null;
                return (
                  <li key={k.id} className="flex items-center justify-between py-3">
                    <div>
                      <p className="font-medium">{k.name}</p>
                      <p className="text-xs text-neutral-500">
                        <code className="font-mono">{k.key_prefix}…</code>
                        <span className="ml-2">oprettet {new Date(k.created_at).toLocaleDateString("da-DK")}</span>
                        {k.last_used_at && (
                          <span className="ml-2">
                            sidst brugt {new Date(k.last_used_at).toLocaleDateString("da-DK")}
                          </span>
                        )}
                        {isRevoked && <span className="ml-2 text-amber-700">tilbagekaldt</span>}
                      </p>
                    </div>
                    {!isRevoked && (
                      <form action={revokeKeyAction}>
                        <input type="hidden" name="id" value={k.id} />
                        <Button type="submit" variant="ghost" size="sm">
                          Tilbagekald
                        </Button>
                      </form>
                    )}
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

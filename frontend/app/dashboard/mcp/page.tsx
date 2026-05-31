import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { listKeys, revokeKeyAction } from "./actions";
import { KeyForm } from "./key-form";
import { CopyButton } from "../copy-button";

export const dynamic = "force-dynamic";

// Single source of truth for the public MCP endpoint. Reads the Vercel env
// at build/runtime, falls back to the canonical Railway URL from CLAUDE.md
// so the page never renders a localhost URL to a real user.
const MCP_URL =
  (process.env.NEXT_PUBLIC_BACKEND_URL && !process.env.NEXT_PUBLIC_BACKEND_URL.includes("localhost")
    ? process.env.NEXT_PUBLIC_BACKEND_URL
    : "https://evovlerun-production.up.railway.app") + "/mcp";

const SAMPLE_PROMPTS = [
  "Show my recent Strava activities",
  "Show my latest run",
  "Get the splits for my last run",
  "What's my training volume this month?",
  "Build me a 7-day training week",
];

function StepNumber({ n }: { n: number }) {
  return (
    <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-[#dc6b3f] text-xs font-semibold text-white">
      {n}
    </span>
  );
}

export default async function MCPPage() {
  const keys = await listKeys();
  const activeKeys = keys.filter((k) => !k.revoked_at);

  return (
    <div className="space-y-10">
      {/* ── Hero ──────────────────────────────────────────────────────── */}
      <div>
        <h1 className="evr-headline text-[clamp(34px,4.5vw,48px)] tracking-[-0.03em]">Connect Claude to EvolveRun</h1>
        <p className="mt-2 text-[15px] text-[#5f564d]">Three steps. Takes under a minute.</p>
        <p className="mt-3 text-sm text-[#7a7168]">
          Set up EvolveRun in Claude in your browser first, then use it anywhere you use Claude. This
          setup works best on a desktop browser.
        </p>
      </div>

      {/* ── Step 1 — Copy URL ─────────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <StepNumber n={1} />
            Copy your EvolveRun URL
          </CardTitle>
          <CardDescription>
            This is the EvolveRun MCP server URL. You&apos;ll paste it into Claude in the next step.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <label className="text-xs font-medium text-[#7a7168]">Claude MCP URL</label>
            <div className="flex items-center gap-2 rounded-xl border border-[#1a1612]/12 bg-white/60 p-2">
              <code className="flex-1 truncate font-mono text-sm text-[#1a1612]">{MCP_URL}</code>
              <CopyButton text={MCP_URL} />
            </div>
            <p className="text-xs text-[#7a7168]">
              Same URL for every user — Claude signs you into your own EvolveRun account via OAuth in
              the next step.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* ── Step 2 — Add to Claude ────────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <StepNumber n={2} />
            Add to Claude
          </CardTitle>
          <CardDescription>
            Open Claude&apos;s connector settings, click <strong>Add custom connector</strong>, paste
            the URL you just copied, and approve access when prompted.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <a
            href="https://claude.ai/settings/connectors"
            target="_blank"
            rel="noopener noreferrer"
            className={buttonVariants()}
          >
            Open Claude Connectors →
          </a>
        </CardContent>
      </Card>

      {/* ── Step 3 — Start chatting ───────────────────────────────────── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <StepNumber n={3} />
            Start chatting
          </CardTitle>
          <CardDescription>
            That&apos;s it. Ask Claude anything about your training — it now has your real Strava data
            and computed metrics (CTL, ATL, TSB, ACWR).
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {SAMPLE_PROMPTS.map((prompt) => (
              <li
                key={prompt}
                className="flex items-center justify-between gap-3 rounded-xl border border-[#1a1612]/10 bg-white/60 px-3 py-2"
              >
                <span className="truncate text-sm text-[#4b423a]">{prompt}</span>
                <CopyButton text={prompt} />
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* ── Divider ───────────────────────────────────────────────────── */}
      <div className="flex items-center gap-4 pt-2">
        <div className="h-px flex-1 bg-[#1a1612]/12" />
        <span className="text-xs uppercase tracking-wider text-[#8a7f74]">
          Other clients & API keys
        </span>
        <div className="h-px flex-1 bg-[#1a1612]/12" />
      </div>

      {/* ── Advanced: API keys (ChatGPT / Gemini / custom) ────────────── */}
      <div>
        <h2 className="text-xl font-semibold tracking-tight">Using ChatGPT, Gemini, or a custom client?</h2>
        <p className="mt-1 text-sm text-[#7a7168]">
          Claude uses OAuth automatically. For other assistants, generate a personal API key below and
          paste it into the install script — one key per device.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Generate and install</CardTitle>
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
          <CardTitle className="flex items-center gap-2 text-base">
            Your keys
            {activeKeys.length > 0 && <Badge tone="success">{activeKeys.length} active</Badge>}
          </CardTitle>
          <CardDescription>
            Revoke a key if it&apos;s compromised. You can have multiple keys active at once (one per
            device).
          </CardDescription>
        </CardHeader>
        <CardContent>
          {keys.length === 0 ? (
            <p className="text-sm text-[#7a7168]">No keys yet — create your first one above.</p>
          ) : (
            <ul className="divide-y divide-[#1a1612]/10">
              {keys.map((k) => {
                const isRevoked = k.revoked_at !== null;
                return (
                  <li key={k.id} className="flex items-center justify-between py-3">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium">{k.name}</p>
                      <p className="text-xs text-[#7a7168]">
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

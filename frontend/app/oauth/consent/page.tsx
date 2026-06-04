import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { approveOAuthAction, denyOAuthAction } from "./actions";
import { ApproveButton } from "./approve-button";

type SearchParams = {
  client_id?: string;
  client_name?: string;
  redirect_uri?: string;
  state?: string;
  scope?: string;
  code_challenge?: string;
  code_challenge_method?: string;
};

export default async function ConsentPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  // Require an authenticated user. If not logged in, send them through login
  // and bounce back here. Next.js's redirect preserves the original URL.
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) {
    const back = `/oauth/consent?${new URLSearchParams(params as Record<string, string>).toString()}`;
    redirect(`/login?redirect=${encodeURIComponent(back)}`);
  }

  if (!params.client_id || !params.redirect_uri) {
    return (
      <div className="mx-auto max-w-lg p-8">
        <p className="text-sm text-red-600">Missing client_id or redirect_uri in the request.</p>
      </div>
    );
  }

  // Use the client_name from the URL (set by the backend's /oauth/authorize from
  // the registered DB value), but cap length so a long name can't overflow the UI.
  const clientName = (params.client_name || params.client_id || "Unknown application").slice(0, 80);
  const scopes = (params.scope || "mcp").split(/\s+/);

  return (
    <div className="mx-auto flex min-h-screen max-w-xl items-center p-6">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Connect {clientName} to EvolveRun</CardTitle>
          <CardDescription>
            <span className="font-medium">{clientName}</span> is requesting access to your EvolveRun account
            ({user!.email}).
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-md border border-neutral-200 bg-neutral-50 p-3 text-sm dark:border-neutral-800 dark:bg-neutral-900">
            <p className="font-medium">This grants access to:</p>
            <ul className="mt-2 space-y-1 text-neutral-700 dark:text-neutral-300">
              <li>• Activities, splits, HR zones, pace, power</li>
              <li>• Your training plans and saved sessions</li>
              <li>• Period summaries and computed metrics</li>
              <li>• Plan-write actions when the assistant asks you to save</li>
            </ul>
            <p className="mt-3 text-xs text-neutral-500">
              Scope: <code className="font-mono">{scopes.join(" ")}</code>
            </p>
          </div>

          <p className="text-xs text-neutral-500">
            Third-party application · ID:{" "}
            <code className="font-mono">{params.client_id}</code>
          </p>

          <div className="flex gap-3 pt-2">
            <form action={approveOAuthAction} className="flex-1">
              <input type="hidden" name="client_id" value={params.client_id} />
              <input type="hidden" name="redirect_uri" value={params.redirect_uri} />
              <input type="hidden" name="state" value={params.state || ""} />
              <input type="hidden" name="scope" value={params.scope || "mcp"} />
              <input type="hidden" name="code_challenge" value={params.code_challenge || ""} />
              <input
                type="hidden"
                name="code_challenge_method"
                value={params.code_challenge_method || "S256"}
              />
              <ApproveButton />
            </form>
            <form action={denyOAuthAction}>
              <input type="hidden" name="client_id" value={params.client_id} />
              <input type="hidden" name="redirect_uri" value={params.redirect_uri} />
              <input type="hidden" name="state" value={params.state || ""} />
              <Button type="submit" variant="outline">
                Cancel
              </Button>
            </form>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

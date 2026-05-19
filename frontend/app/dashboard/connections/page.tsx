import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  connectProviderAction,
  disconnectProviderAction,
  getConnectionStatus,
  syncProviderAction,
} from "./actions";

type Provider = {
  id: string;
  name: string;
  desc: string;
  enabled: boolean;
  authMode: "oauth" | "credentials";
  warning?: string;
};

// V1: Strava is the only live integration. Garmin / Oura / Whoop / Polar all
// auto-sync to Strava, so we "inherit" them without paying Terra. Garmin's
// unofficial API has been pulled from the UI to avoid setting an expectation
// we can't keep stable — the code path still exists in the backend for V2.
const PROVIDERS: Provider[] = [
  {
    id: "strava",
    name: "Strava",
    desc: "Aktiviteter, splits, pace, HR, power, elevation. Auto-syncer fra Garmin, Apple Watch, Polar, COROS, Suunto, Wahoo og 9 mere.",
    enabled: true,
    authMode: "oauth",
  },
  {
    id: "oura",
    name: "Oura Ring",
    desc: "Sleep, HRV, readiness, body temperature.",
    enabled: false,
    authMode: "oauth",
  },
  {
    id: "whoop",
    name: "Whoop",
    desc: "Recovery, strain, sleep, workouts.",
    enabled: false,
    authMode: "oauth",
  },
];

type SearchParams = {
  provider?: string;
  status?: string;
};

export default async function ConnectionsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const banner = buildBanner(params);

  // Fetch status for each enabled provider in parallel.
  const statuses = await Promise.all(
    PROVIDERS.filter((p) => p.enabled).map(async (p) => ({
      id: p.id,
      status: await getConnectionStatus(p.id),
    })),
  );
  const statusById = Object.fromEntries(statuses.map((s) => [s.id, s.status]));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Forbindelser</h1>
        <p className="mt-1 text-neutral-600 dark:text-neutral-400">
          Forbind dine wearables. Tokens krypteres med Fernet før de gemmes.
        </p>
      </div>

      {banner && (
        <div
          className={`rounded-md border px-4 py-3 text-sm ${
            banner.tone === "ok"
              ? "border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950 dark:text-emerald-200"
              : "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900 dark:bg-amber-950 dark:text-amber-200"
          }`}
        >
          {banner.message}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {PROVIDERS.map((p) => {
          const status = statusById[p.id] ?? null;
          const isConnected = status?.connected ?? false;

          return (
            <Card key={p.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle>{p.name}</CardTitle>
                    <CardDescription className="mt-1">{p.desc}</CardDescription>
                  </div>
                  {isConnected && (
                    <span className="ml-2 inline-flex items-center rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                      forbundet
                    </span>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {p.warning && <p className="text-xs text-amber-700 dark:text-amber-300">{p.warning}</p>}

                {!p.enabled ? (
                  <Button variant="outline" disabled>
                    Kommer snart
                  </Button>
                ) : isConnected ? (
                  <div className="flex flex-wrap gap-2">
                    <form action={syncProviderAction}>
                      <input type="hidden" name="provider" value={p.id} />
                      <input type="hidden" name="days" value="30" />
                      <Button type="submit" variant="outline" size="sm">
                        Sync sidste 30 dage
                      </Button>
                    </form>
                    <form action={disconnectProviderAction}>
                      <input type="hidden" name="provider" value={p.id} />
                      <Button type="submit" variant="ghost" size="sm">
                        Frakobl
                      </Button>
                    </form>
                  </div>
                ) : p.authMode === "credentials" ? (
                  <Link href={`/dashboard/connections/${p.id}`}>
                    <Button>Forbind {p.name}</Button>
                  </Link>
                ) : (
                  <form action={connectProviderAction}>
                    <input type="hidden" name="provider" value={p.id} />
                    <Button type="submit">Forbind {p.name}</Button>
                  </form>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

function buildBanner(
  params: SearchParams,
): { tone: "ok" | "warn"; message: string } | null {
  const { provider, status } = params;
  if (!provider || !status) return null;

  if (status === "connected") {
    return { tone: "ok", message: `${capitalize(provider)} forbundet og initial sync kørt 🎉` };
  }
  if (status === "connected_no_sync") {
    return {
      tone: "warn",
      message: `${capitalize(provider)} forbundet, men første sync fejlede. Prøv "Sync sidste 30 dage" manuelt.`,
    };
  }
  if (status === "synced") {
    return { tone: "ok", message: `Sync færdig for ${capitalize(provider)}.` };
  }
  if (status === "sync_started") {
    return {
      tone: "ok",
      message: `Backfill startet for ${capitalize(provider)} — det kører i baggrunden og tager typisk 3–5 minutter. Genindlæs siden om et par minutter for at se det opdaterede dato-interval.`,
    };
  }
  if (status === "disconnected") {
    return { tone: "ok", message: `${capitalize(provider)} frakoblet.` };
  }
  if (status.startsWith("denied")) {
    return { tone: "warn", message: `Du afslog adgang på ${capitalize(provider)}.` };
  }
  return { tone: "warn", message: `Status fra ${capitalize(provider)}: ${status}` };
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

import { redirect } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { loadLatestLimiter, runLimiterAnalysis } from "../actions";
import { fmtLimiter } from "@/lib/format";

export const dynamic = "force-dynamic";

async function analyzeAction() {
  "use server";
  await runLimiterAnalysis();
  redirect("/dashboard/limiter");
}

export default async function LimiterPage() {
  const limiter = await loadLatestLimiter();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Limiter-analyse</h1>
          <p className="mt-1 text-neutral-600 dark:text-neutral-400">
            AI'en identificerer den fysiologiske faktor der begrænser dig mest lige nu — baseret på dine sidste 12 ugers data.
          </p>
        </div>
        <form action={analyzeAction}>
          <Button type="submit">Kør ny analyse</Button>
        </form>
      </div>

      {!limiter?.available ? (
        <Card>
          <CardHeader>
            <CardTitle>Ingen analyse endnu</CardTitle>
            <CardDescription>Tryk &quot;Kør ny analyse&quot; for at lave din første.</CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <>
          <Card>
            <CardHeader>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <CardTitle className="text-2xl">{fmtLimiter(limiter.primary_limiter)}</CardTitle>
                  <CardDescription className="mt-1">
                    {limiter.secondary_limiter && (
                      <>Sekundær: <strong>{fmtLimiter(limiter.secondary_limiter)}</strong> · </>
                    )}
                    Confidence: <strong>{Math.round((limiter.confidence ?? 0) * 100)}%</strong>
                  </CardDescription>
                </div>
                {limiter.detected_at && (
                  <Badge tone="info">
                    {new Date(limiter.detected_at).toLocaleString("da-DK", {
                      day: "numeric", month: "short", year: "numeric",
                      hour: "2-digit", minute: "2-digit",
                    })}
                  </Badge>
                )}
              </div>
            </CardHeader>
            {limiter.recommended_focus && (
              <CardContent>
                <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/30">
                  <p className="text-sm font-medium text-emerald-900 dark:text-emerald-200">
                    Anbefalet fokus
                  </p>
                  <p className="mt-1 text-sm text-emerald-800 dark:text-emerald-300">
                    {limiter.recommended_focus}
                  </p>
                </div>
              </CardContent>
            )}
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            {limiter.key_observations && limiter.key_observations.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Nøgleobservationer</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    {limiter.key_observations.map((o, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-neutral-400">•</span>
                        <span>{o}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {limiter.supporting_data_points && limiter.supporting_data_points.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Data-punkter</CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm font-mono text-xs">
                    {limiter.supporting_data_points.map((d, i) => (
                      <li key={i} className="flex gap-2">
                        <span className="text-neutral-400">•</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}
          </div>

          {limiter.physiology_explanation && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Fysiologi</CardTitle>
                <CardDescription>Hvorfor det er denne limiter</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-line text-sm text-neutral-700 dark:text-neutral-300">
                  {limiter.physiology_explanation}
                </p>
              </CardContent>
            </Card>
          )}

          {limiter.alternative_considered && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Alternativer overvejet</CardTitle>
                <CardDescription>Hvad AI'en også considerede, og hvorfor det blev forkastet</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-neutral-700 dark:text-neutral-300">
                  {limiter.alternative_considered}
                </p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

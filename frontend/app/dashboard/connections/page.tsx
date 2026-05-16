import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const PROVIDERS = [
  { id: "garmin", name: "Garmin Connect", desc: "Aktiviteter, HR, sleep, body battery." },
  { id: "strava", name: "Strava", desc: "Aktiviteter og social feed." },
  { id: "oura", name: "Oura Ring", desc: "Sleep, HRV, readiness." },
  { id: "whoop", name: "Whoop", desc: "Recovery, strain, sleep." },
  { id: "apple_health", name: "Apple Health", desc: "Workouts, vitals (via webhook)." },
];

export default function ConnectionsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Forbindelser</h1>
        <p className="mt-1 text-neutral-600 dark:text-neutral-400">
          Forbind dine wearables. Tokens krypteres og opbevares sikkert.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {PROVIDERS.map((p) => (
          <Card key={p.id}>
            <CardHeader>
              <CardTitle>{p.name}</CardTitle>
              <CardDescription>{p.desc}</CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="outline" disabled>
                Forbind (kommer snart)
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

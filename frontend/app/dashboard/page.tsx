import { createClient } from "@/lib/supabase/server";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Heart, Target, TrendingUp } from "lucide-react";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const name = user?.user_metadata?.full_name ?? user?.email ?? "athlete";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Hej, {name} 👋</h1>
        <p className="mt-1 text-neutral-600 dark:text-neutral-400">
          Her er din adaptive performance OS. Endnu ingen data — forbind dit wearable for at komme i gang.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={<Heart className="h-4 w-4" />} label="Resting HR" value="—" hint="Forbind Oura/Whoop" />
        <StatCard icon={<Activity className="h-4 w-4" />} label="ACWR" value="—" hint="Acute:Chronic load ratio" />
        <StatCard icon={<TrendingUp className="h-4 w-4" />} label="Fitness (CTL)" value="—" hint="42-dages rolling" />
        <StatCard icon={<Target className="h-4 w-4" />} label="Næste race" value="—" hint="Sæt et mål" />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Dagens briefing</CardTitle>
          <CardDescription>AI-genereret. Forklarer hvorfor — ikke bare hvad.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-neutral-700 dark:text-neutral-300">
            Når du har forbundet en wearable og kørt 5–7 dages data, genererer din coach den første
            briefing her. Den vil indeholde dagens anbefalede session, din readiness-score, og
            den fysiologiske begrundelse.
          </p>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Limiter Analysis</CardTitle>
            <CardDescription>Hvilken fysiologisk faktor begrænser dig mest lige nu?</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-neutral-500 dark:text-neutral-400">
              Kører hver 4. uge på fuld træningshistorik. Identificerer aerob kapacitet, økonomi,
              muskulær udholdenhed, threshold, eller recovery som primær limiter.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Træningsplan</CardTitle>
            <CardDescription>Bygges når du sætter et mål.</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-neutral-500 dark:text-neutral-400">
              Gå til <strong>Træning</strong> for at sætte et race-mål. Coach genererer en
              periodiseret plan (Base → Build → Peak → Taper) der dynamisk tilpasses din respons.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  hint,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{label}</CardTitle>
        <span className="text-neutral-500">{icon}</span>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-neutral-500 dark:text-neutral-400">{hint}</p>
      </CardContent>
    </Card>
  );
}

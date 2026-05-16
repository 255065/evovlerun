import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function TrainingPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Træningsplan</h1>
        <p className="mt-1 text-neutral-600 dark:text-neutral-400">
          Sæt et race-mål og lad coach bygge en plan.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Ingen aktiv plan</CardTitle>
          <CardDescription>Plan-builder kommer i næste iteration.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">
            Når plan-builderen er live, kan du vælge race-type (5K / 10K / halvmarathon / marathon),
            target-tid, race-dato, og foretrukken filosofi (Daniels, Pfitzinger, Norwegian, Polarized).
            Coach bygger så en periodiseret plan med ugentlig adaptation baseret på din respons.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

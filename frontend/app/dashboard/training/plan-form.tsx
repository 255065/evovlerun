"use client";

import { useActionState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { generatePlan } from "../actions";

type State = { error: string | null; ok: boolean };

const initial: State = { error: null, ok: false };

export function PlanGeneratorForm() {
  const router = useRouter();

  const [state, action, pending] = useActionState(async (_prev: State, fd: FormData): Promise<State> => {
    const race_type = String(fd.get("race_type") || "");
    const race_date = String(fd.get("race_date") || "");
    const philosophy = String(fd.get("philosophy") || "auto_hybrid");
    const target_time_seconds = fd.get("target_time_seconds")
      ? Number(fd.get("target_time_seconds"))
      : undefined;
    const expand_first_n_weeks = Number(fd.get("expand_first_n_weeks") || 4);

    if (!race_type || !race_date) {
      return { error: "Race-type og dato er påkrævet", ok: false };
    }

    const res = await generatePlan({
      race_type, race_date, philosophy, target_time_seconds, expand_first_n_weeks,
    });
    if (!res.ok) return { error: res.error ?? "Ukendt fejl", ok: false };
    router.refresh();
    return { error: null, ok: true };
  }, initial);

  return (
    <form action={action} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label htmlFor="race_type">Race-type</Label>
          <select
            id="race_type"
            name="race_type"
            required
            defaultValue="general_fitness"
            className="flex h-9 w-full rounded-md border border-neutral-200 bg-transparent px-3 py-1 text-sm dark:border-neutral-800"
          >
            <option value="5k">5K</option>
            <option value="10k">10K</option>
            <option value="half_marathon">Half marathon</option>
            <option value="marathon">Marathon</option>
            <option value="ultra">Ultra</option>
            <option value="triathlon">Triathlon</option>
            <option value="general_fitness">General fitness</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="philosophy">Filosofi</Label>
          <select
            id="philosophy"
            name="philosophy"
            defaultValue="auto_hybrid"
            className="flex h-9 w-full rounded-md border border-neutral-200 bg-transparent px-3 py-1 text-sm dark:border-neutral-800"
          >
            <option value="auto_hybrid">Auto-hybrid (lad AI'en vælge)</option>
            <option value="polarized">Polarized</option>
            <option value="norwegian">Norwegian</option>
            <option value="daniels">Daniels</option>
            <option value="pfitzinger">Pfitzinger</option>
            <option value="hansons">Hansons</option>
            <option value="lydiard">Lydiard</option>
          </select>
        </div>

        <div className="space-y-2">
          <Label htmlFor="race_date">Race-dato / milestone</Label>
          <Input
            id="race_date"
            name="race_date"
            type="date"
            required
            defaultValue={defaultRaceDate()}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="target_time_seconds">Mål-tid (sekunder, valgfri)</Label>
          <Input id="target_time_seconds" name="target_time_seconds" type="number" placeholder="fx 10800 = 3:00:00" />
        </div>

        <div className="space-y-2 sm:col-span-2">
          <Label htmlFor="expand_first_n_weeks">Antal uger at expand'e med detaljer (rest er kun blueprint)</Label>
          <Input
            id="expand_first_n_weeks"
            name="expand_first_n_weeks"
            type="number"
            min={1}
            max={12}
            defaultValue={4}
          />
          <p className="text-xs text-neutral-500">
            Genererer 1 blueprint + N ugentlige expansion-kald. Hver expansion ≈ 8000 tokens.
          </p>
        </div>
      </div>

      {state.error && (
        <p className="text-sm text-red-600" role="alert">
          {state.error}
        </p>
      )}

      <Button type="submit" disabled={pending}>
        {pending ? "Genererer plan… (kan tage 1-3 min)" : "Generér plan"}
      </Button>
    </form>
  );
}

function defaultRaceDate(): string {
  const d = new Date();
  d.setDate(d.getDate() + 7 * 12); // 12 uger ud som default
  return d.toISOString().slice(0, 10);
}

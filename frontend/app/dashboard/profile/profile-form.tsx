"use client";

import { useActionState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { updateProfile, type Profile } from "../actions";

type State = { error: string | null; saved: boolean };
const initial: State = { error: null, saved: false };

export function ProfileForm({ initial: p }: { initial: Profile | null }) {
  const router = useRouter();

  const [state, action, pending] = useActionState(async (_prev: State, fd: FormData): Promise<State> => {
    const patch: Partial<Profile> = {
      full_name: stringOrNull(fd.get("full_name")),
      date_of_birth: stringOrNull(fd.get("date_of_birth")),
      sex: (stringOrNull(fd.get("sex")) as Profile["sex"]) ?? null,
      height_cm: numberOrNull(fd.get("height_cm")),
      weight_kg: numberOrNull(fd.get("weight_kg")),
      primary_sport: stringOrNull(fd.get("primary_sport")),
      experience_level: stringOrNull(fd.get("experience_level")),
      max_hr: numberOrNull(fd.get("max_hr")),
      resting_hr: numberOrNull(fd.get("resting_hr")),
      preferred_philosophy: stringOrNull(fd.get("preferred_philosophy")),
    };
    const res = await updateProfile(patch);
    if (!res.ok) return { error: res.error ?? "Kunne ikke gemme", saved: false };
    router.refresh();
    return { error: null, saved: true };
  }, initial);

  return (
    <form action={action} className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Fulde navn" name="full_name" defaultValue={p?.full_name ?? ""} />
        <Field label="Fødselsdato" name="date_of_birth" type="date" defaultValue={p?.date_of_birth ?? ""} />

        <SelectField label="Køn" name="sex" defaultValue={p?.sex ?? ""}>
          <option value="">—</option>
          <option value="male">Mand</option>
          <option value="female">Kvinde</option>
          <option value="other">Andet</option>
        </SelectField>

        <SelectField label="Primær sport" name="primary_sport" defaultValue={p?.primary_sport ?? "running"}>
          <option value="running">Løb</option>
          <option value="cycling">Cykling</option>
          <option value="triathlon">Triathlon</option>
          <option value="swimming">Svømning</option>
        </SelectField>

        <Field label="Højde (cm)" name="height_cm" type="number" step="0.1" defaultValue={p?.height_cm?.toString() ?? ""} />
        <Field label="Vægt (kg)" name="weight_kg" type="number" step="0.1" defaultValue={p?.weight_kg?.toString() ?? ""} />

        <SelectField label="Erfaring" name="experience_level" defaultValue={p?.experience_level ?? ""}>
          <option value="">—</option>
          <option value="beginner">Begynder</option>
          <option value="intermediate">Mellem</option>
          <option value="advanced">Avanceret</option>
          <option value="elite">Elite</option>
        </SelectField>

        <SelectField label="Foretrukken filosofi" name="preferred_philosophy" defaultValue={p?.preferred_philosophy ?? ""}>
          <option value="">—</option>
          <option value="polarized">Polarized</option>
          <option value="norwegian">Norwegian</option>
          <option value="daniels">Daniels</option>
          <option value="pfitzinger">Pfitzinger</option>
          <option value="hansons">Hansons</option>
          <option value="lydiard">Lydiard</option>
          <option value="auto_hybrid">Auto-hybrid</option>
        </SelectField>
      </div>

      <div className="rounded-md border border-neutral-200 bg-neutral-50 p-4 dark:border-neutral-800 dark:bg-neutral-900/40">
        <h3 className="text-sm font-medium">Heart rate thresholds</h3>
        <p className="mt-1 text-xs text-neutral-500">
          Max HR auto-observerede fra workouts er ofte 1-3 bpm lavere end den reelle max. Overskriv hvis du kender din rigtige max HR fra en test.
        </p>
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <Field
            label="Max HR (bpm)"
            name="max_hr"
            type="number"
            min={120}
            max={225}
            defaultValue={p?.max_hr?.toString() ?? ""}
            hint="Bruges til TRIMP-beregning og HR-zoner"
          />
          <Field
            label="Resting HR (bpm)"
            name="resting_hr"
            type="number"
            min={30}
            max={100}
            defaultValue={p?.resting_hr?.toString() ?? ""}
            hint="Auto-syncet fra daily metrics"
          />
        </div>
      </div>

      {state.error && (
        <p className="text-sm text-red-600" role="alert">{state.error}</p>
      )}
      {state.saved && (
        <p className="text-sm text-emerald-600" role="status">Gemt ✓ Performance Model genberegner ved næste sync.</p>
      )}

      <Button type="submit" disabled={pending}>
        {pending ? "Gemmer…" : "Gem"}
      </Button>
    </form>
  );
}

function stringOrNull(v: FormDataEntryValue | null): string | null {
  const s = String(v ?? "").trim();
  return s ? s : null;
}

function numberOrNull(v: FormDataEntryValue | null): number | null {
  const s = String(v ?? "").trim();
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function Field({
  label, name, type = "text", defaultValue, hint, step, min, max,
}: {
  label: string; name: string; type?: string;
  defaultValue?: string; hint?: string;
  step?: string | number; min?: number; max?: number;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={name}>{label}</Label>
      <Input id={name} name={name} type={type} defaultValue={defaultValue} step={step} min={min} max={max} />
      {hint && <p className="text-xs text-neutral-500">{hint}</p>}
    </div>
  );
}

function SelectField({
  label, name, defaultValue, children,
}: {
  label: string; name: string; defaultValue?: string; children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={name}>{label}</Label>
      <select
        id={name}
        name={name}
        defaultValue={defaultValue}
        className="flex h-9 w-full rounded-md border border-neutral-200 bg-transparent px-3 py-1 text-sm dark:border-neutral-800"
      >
        {children}
      </select>
    </div>
  );
}

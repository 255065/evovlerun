import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Activity, Brain, Target, ShieldCheck } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white dark:bg-neutral-950">
      <header className="border-b border-neutral-200 dark:border-neutral-800">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <Activity className="h-5 w-5" />
            EvolveRun
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/login">
              <Button variant="ghost">Log ind</Button>
            </Link>
            <Link href="/signup">
              <Button>Kom i gang</Button>
            </Link>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-4 py-24 text-center sm:px-6 lg:px-8">
        <h1 className="text-5xl font-bold tracking-tight sm:text-6xl">
          Din adaptive AI-coach.
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-neutral-600 dark:text-neutral-400">
          EvolveRun bygger, sporer og tilpasser din træningsplan i realtid baseret på data fra
          dine wearables. Forklarende. Videnskabsbaseret. Sikkert.
        </p>
        <div className="mt-10 flex items-center justify-center gap-4">
          <Link href="/signup">
            <Button size="lg">Start gratis</Button>
          </Link>
          <Link href="#features">
            <Button variant="outline" size="lg">
              Lær mere
            </Button>
          </Link>
        </div>
      </section>

      <section id="features" className="border-t border-neutral-200 bg-neutral-50 py-24 dark:border-neutral-800 dark:bg-neutral-900">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-8 md:grid-cols-3">
            <Feature
              icon={<Brain className="h-6 w-6" />}
              title="Forklarende coaching"
              desc="Hver anbefaling kommer med en fysiologisk begrundelse — du forstår altid hvorfor."
            />
            <Feature
              icon={<Target className="h-6 w-6" />}
              title="Limiter-baseret"
              desc="Identificerer din svageste fysiologiske faktor og angriber den med præcision."
            />
            <Feature
              icon={<ShieldCheck className="h-6 w-6" />}
              title="Sikkerhed først"
              desc="ACWR-monitorering og konservativ progression. Ingen farlige load-spikes."
            />
          </div>
        </div>
      </section>
    </div>
  );
}

function Feature({ icon, title, desc }: { icon: React.ReactNode; title: string; desc: string }) {
  return (
    <div>
      <div className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-neutral-900 text-white dark:bg-white dark:text-neutral-900">
        {icon}
      </div>
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-neutral-600 dark:text-neutral-400">{desc}</p>
    </div>
  );
}

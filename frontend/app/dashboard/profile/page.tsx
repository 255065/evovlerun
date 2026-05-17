import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { loadProfile } from "../actions";
import { ProfileForm } from "./profile-form";

export const dynamic = "force-dynamic";

export default async function ProfilePage() {
  const profile = await loadProfile();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Profil</h1>
        <p className="mt-1 text-neutral-600 dark:text-neutral-400">
          Felter der bruges af Performance Model og Limiter Engine. Garmin auto-fylder de fleste — du kan override.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Atletprofil</CardTitle>
          <CardDescription>
            Max HR + resting HR driver TRIMP, hrTSS, CTL og ACWR. Forkert max HR = forkert load-beregning.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ProfileForm initial={profile} />
        </CardContent>
      </Card>
    </div>
  );
}

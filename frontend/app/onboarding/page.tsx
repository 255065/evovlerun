import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { OnboardingWizard } from "./wizard";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

export const dynamic = "force-dynamic";

/**
 * /onboarding is a one-time setup flow. Already-onboarded users bounce
 * straight to /dashboard so they don't get nagged. New users see the
 * 5-question wizard, with Q3 pre-marked as "Strava connected" if they
 * happened to connect through some other path first.
 */
export default async function OnboardingPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  const { data: profile } = await supabase
    .from("profiles")
    .select("onboarded_at, full_name")
    .eq("id", user.id)
    .single();

  if (profile?.onboarded_at) {
    redirect("/dashboard");
  }

  // Check whether Strava is already connected so Q3 can render a green
  // "connected" pill instead of a "connect now" CTA. We only need the
  // boolean — the page still works if this fetch fails.
  const stravaConnected = await checkStravaConnected(supabase);

  return (
    <div className="evr-warm min-h-screen px-4 py-10 sm:px-6 sm:py-16">
      <div className="mx-auto max-w-2xl">
        <OnboardingWizard
          fullName={profile?.full_name ?? user.email ?? "atlet"}
          stravaConnected={stravaConnected}
        />
      </div>
    </div>
  );
}

async function checkStravaConnected(
  supabase: Awaited<ReturnType<typeof createClient>>,
): Promise<boolean> {
  try {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session?.access_token) return false;

    const res = await fetch(`${BACKEND_URL}/providers/strava/status`, {
      method: "GET",
      headers: { Authorization: `Bearer ${session.access_token}` },
      cache: "no-store",
    });
    if (!res.ok) return false;
    const data = (await res.json()) as { connected?: boolean };
    return Boolean(data.connected);
  } catch {
    return false;
  }
}

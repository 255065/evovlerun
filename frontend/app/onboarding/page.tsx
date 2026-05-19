import { redirect } from "next/navigation";

// V1: the 5-question onboarding wizard was rolled back because its answers
// didn't feed into anything actionable in the V1 product surface. The
// underlying profile columns (migration 0006) still exist so a V2 version
// of this flow can re-use them without a schema change. Any stale link
// to /onboarding falls through to the dashboard instead of 404-ing.
export default function OnboardingRedirect() {
  redirect("/dashboard");
}

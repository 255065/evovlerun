import { redirect } from "next/navigation";

// V1: Garmin direct integration is hidden — Strava is the only enabled
// provider in the UI. Any old bookmark to this route bounces back to
// /dashboard/connections so the user lands in the supported flow. The
// backend credential-login endpoint and python-garminconnect code path
// still live in the repo; we'll re-enable this page in V2 when we
// switch to the official Garmin partner API.
export default function GarminConnectRedirect() {
  redirect("/dashboard/connections");
}

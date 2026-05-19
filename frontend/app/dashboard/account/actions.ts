"use server";

import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

async function getToken(): Promise<string> {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) redirect("/login");
  return session.access_token;
}

export type BillingStatus = {
  status: string | null;
  price_id: string | null;
  current_period_end: string | null;
  customer_id: string | null;
  has_subscription: boolean;
};

export async function loadBillingStatus(): Promise<BillingStatus | null> {
  try {
    const token = await getToken();
    const res = await fetch(`${BACKEND_URL}/billing/status`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!res.ok) return null;
    return (await res.json()) as BillingStatus;
  } catch {
    return null;
  }
}

/**
 * Kick off a Stripe Checkout session and redirect the browser to it. The
 * backend creates a single-tier subscription session and returns the URL —
 * we don't expose Stripe keys to the client at all.
 */
export async function startCheckoutAction() {
  const token = await getToken();
  const res = await fetch(`${BACKEND_URL}/billing/create-checkout-session`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Checkout failed (${res.status}): ${text}`);
  }
  const { url } = (await res.json()) as { url: string };
  redirect(url);
}

/**
 * Hand the user off to the Stripe billing portal so they can update card,
 * cancel, view invoices, etc. — without us reimplementing any of it.
 */
export async function openBillingPortalAction() {
  const token = await getToken();
  const res = await fetch(`${BACKEND_URL}/billing/create-portal-session`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Portal failed (${res.status}): ${text}`);
  }
  const { url } = (await res.json()) as { url: string };
  redirect(url);
}

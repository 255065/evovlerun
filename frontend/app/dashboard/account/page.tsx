import { createClient } from "@/lib/supabase/server";
import { loadBillingStatus, openBillingPortalAction, startCheckoutAction } from "./actions";
import { logoutAction } from "@/app/(auth)/actions";

export const dynamic = "force-dynamic";

type SearchParams = { checkout?: string; paywall?: string };

/**
 * Single billing page: shows subscription state, lets the user start a new
 * Checkout if they aren't subscribed, or open the Stripe billing portal if
 * they are. Account deletion is left as a manual support flow for V1.
 */
export default async function AccountPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const billing = await loadBillingStatus();

  const isActive = billing?.has_subscription ?? false;
  const periodEnd = billing?.current_period_end
    ? new Date(billing.current_period_end).toLocaleDateString("da-DK", {
        day: "numeric",
        month: "long",
        year: "numeric",
      })
    : null;

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-[28px] font-semibold tracking-[-0.025em]">Account &amp; billing</h1>
        <p className="mt-1 text-[14px] text-neutral-600">
          {user?.email && <>Signed in as <span className="font-mono">{user.email}</span></>}
        </p>
      </div>

      {params.paywall === "1" && (
        <Banner tone="warn">
          EvolveRun kræver et aktivt abonnement. Start ét nedenfor for at få adgang til
          dashboard, MCP-connectoren og chatten.
        </Banner>
      )}
      {params.checkout === "success" && (
        <Banner tone="ok">
          🎉 Subscription active. Du har fuld adgang nu — godt at have dig om bord.
        </Banner>
      )}
      {params.checkout === "cancelled" && (
        <Banner tone="warn">
          Checkout afbrudt. Ingen penge trukket. Du kan starte igen nedenfor.
        </Banner>
      )}

      <div className="rounded-[10px] border border-neutral-200 bg-white p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="text-[12.5px] font-mono uppercase tracking-widest text-neutral-500">
              Subscription
            </div>
            <div className="mt-2 flex items-baseline gap-3">
              <StatusPill status={billing?.status ?? null} />
            </div>
            {periodEnd && (
              <p className="mt-2 text-[13px] text-neutral-600">
                {isActive ? "Fornyes" : "Udløb"} {periodEnd}
              </p>
            )}
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-3">
          {isActive ? (
            <form action={openBillingPortalAction}>
              <button
                type="submit"
                className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 bg-white px-5 py-2.5 text-[13.5px] font-medium hover:bg-neutral-50"
              >
                Manage billing →
              </button>
            </form>
          ) : (
            <form action={startCheckoutAction}>
              <button
                type="submit"
                className="inline-flex items-center gap-2 rounded-lg bg-neutral-950 px-5 py-2.5 text-[13.5px] font-medium text-white"
              >
                Start subscription →
              </button>
            </form>
          )}
          {billing === null && (
            <p className="text-[12.5px] text-amber-700">
              Kunne ikke hente billing-status — Stripe er muligvis ikke konfigureret endnu.
            </p>
          )}
        </div>
      </div>

      <div className="rounded-[10px] border border-neutral-200 bg-white p-6">
        <div className="text-[12.5px] font-mono uppercase tracking-widest text-neutral-500">
          Account
        </div>
        <p className="mt-2 text-[14px] text-neutral-700">
          Vil du slette din konto? Skriv til support — vi sletter alt inden for 7 dage. (V2: self-service knap her.)
        </p>
        <form action={logoutAction} className="mt-4">
          <button
            type="submit"
            className="text-[13px] text-neutral-600 underline hover:text-neutral-950"
          >
            Log ud
          </button>
        </form>
      </div>
    </div>
  );
}

function StatusPill({ status }: { status: string | null }) {
  const { label, cls } = pillStyle(status);
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-[13px] font-medium ${cls}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}

function pillStyle(status: string | null): { label: string; cls: string } {
  switch (status) {
    case "active":
      return { label: "Active", cls: "bg-emerald-100 text-emerald-800" };
    case "trialing":
      return { label: "Trialing", cls: "bg-blue-100 text-blue-800" };
    case "past_due":
      return { label: "Past due", cls: "bg-amber-100 text-amber-800" };
    case "canceled":
      return { label: "Canceled", cls: "bg-neutral-200 text-neutral-700" };
    case "incomplete":
    case "incomplete_expired":
      return { label: "Incomplete", cls: "bg-amber-100 text-amber-800" };
    case "unpaid":
      return { label: "Unpaid", cls: "bg-red-100 text-red-800" };
    case "paused":
      return { label: "Paused", cls: "bg-neutral-200 text-neutral-700" };
    default:
      return { label: "No subscription", cls: "bg-neutral-200 text-neutral-700" };
  }
}

function Banner({ tone, children }: { tone: "ok" | "warn"; children: React.ReactNode }) {
  const cls =
    tone === "ok"
      ? "border-emerald-200 bg-emerald-50 text-emerald-900"
      : "border-amber-200 bg-amber-50 text-amber-900";
  return <div className={`rounded-md border px-4 py-3 text-[13.5px] ${cls}`}>{children}</div>;
}

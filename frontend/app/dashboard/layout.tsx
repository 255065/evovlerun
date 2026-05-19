import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { Nav } from "@/components/nav";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  // Subscription gating lives in lib/supabase/middleware.ts — it has reliable
  // pathname access and runs before page rendering, so we don't double-check
  // here. This layout is only responsible for auth and chrome.

  return (
    <div className="min-h-screen bg-white text-neutral-950">
      <Nav email={user.email} />
      <main className="mx-auto max-w-[1280px] px-6 py-8 sm:px-8">{children}</main>
    </div>
  );
}

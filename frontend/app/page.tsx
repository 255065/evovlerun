import "./_landing/landing.css";
import { Nav } from "./_landing/nav";
import { Hero, HowItWorks, Features, Pricing, CTA, Footer } from "./_landing/sections";
import { ChatDemo } from "./_landing/chat-demo";
import { RevealController } from "./_landing/reveal-controller";

type SearchParams = { deleted?: string };

export default async function LandingPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  return (
    <div className="evr-landing">
      {params.deleted === "1" && (
        <div className="border-b border-emerald-200 bg-emerald-50 px-6 py-3 text-center text-[13.5px] text-emerald-900">
          Your account and all data have been deleted. Thanks for trying EvolveRun.
        </div>
      )}
      <RevealController />
      <Nav />
      <main>
        <Hero />
        <ChatDemo />
        <HowItWorks />
        <Features />
        <Pricing />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}

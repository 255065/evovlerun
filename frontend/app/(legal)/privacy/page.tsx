import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy — EvolveRun",
  description:
    "How EvolveRun collects, uses, stores, and deletes your training and account data.",
};

// NOTE FOR THE FOUNDER:
// This is a structurally-complete starting point, NOT legal advice. Have it
// reviewed before launch. The Strava-data and deletion sections are required
// for Strava API production approval; the billing section is required for
// Stripe.
export default function PrivacyPage() {
  return (
    <article className="prose-legal">
      <h1 className="evr-headline text-[34px] tracking-[-0.02em]">Privacy Policy</h1>
      <p className="mt-2 text-[13px] text-neutral-500">Last updated: June 12, 2026</p>

      <Section title="Who we are">
        EvolveRun (&quot;EvolveRun&quot;, &quot;we&quot;, &quot;us&quot;) is operated by
        Valdemar Størum (sole trader), Denmark. For any privacy
        question or request, contact us at <strong>vstoerum@gmail.com</strong>.
      </Section>

      <Section title="What data we collect">
        <ul>
          <li>
            <strong>Account data:</strong> email address and authentication
            details (handled by our auth provider, Supabase).
          </li>
          <li>
            <strong>Training data from Strava:</strong> when you connect Strava,
            we import your activities, splits, heart-rate, pace, power, and
            related metrics so the AI connector can answer questions about them.
          </li>
          <li>
            <strong>Plans you create:</strong> training plans and sessions saved
            through the connector.
          </li>
          <li>
            <strong>Billing data:</strong> subscription status and customer ID
            from our payment processor, Stripe. We do not store card numbers.
          </li>
        </ul>
      </Section>

      <Section title="How we use your data">
        We use your data solely to provide the service: syncing your Strava
        activities, computing training metrics, and exposing them to the AI
        assistant (Claude or ChatGPT) that you connect via the
        EvolveRun connector. We do not sell your data or use it for advertising.
      </Section>

      <Section title="Strava data">
        EvolveRun uses the Strava API. Your Strava data is imported only after
        you explicitly authorize the connection and is used only to provide the
        features described above. You can disconnect Strava at any time from
        your dashboard, which stops further syncing. This product is not
        endorsed or certified by Strava.
      </Section>

      <Section title="Third parties we share data with">
        We share data only with the infrastructure providers that run the
        service: <strong>Supabase</strong> (database, authentication),{" "}
        <strong>Stripe</strong> (payments), <strong>Railway</strong> and{" "}
        <strong>Vercel</strong> (hosting). When you use the AI connector, your
        selected assistant provider (Anthropic or OpenAI) receives the
        training data the assistant requests, under their respective terms.
      </Section>

      <Section title="Data retention &amp; deletion">
        We keep your data while your account is active. You can delete your
        account at any time from <strong>Account settings</strong>; this
        permanently removes your profile, connected-provider tokens, imported
        activities, and saved plans. You may also email{" "}
        <strong>vstoerum@gmail.com</strong> to request deletion.
      </Section>

      <Section title="Your rights">
        Depending on your location (e.g. under the GDPR), you have the right to
        access, correct, export, or delete your personal data, and to withdraw
        consent. Contact <strong>vstoerum@gmail.com</strong> to exercise these
        rights.
      </Section>

      <Section title="Changes to this policy">
        We may update this policy; material changes will be reflected by the
        &quot;Last updated&quot; date above.
      </Section>
    </article>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="text-[18px] font-semibold tracking-[-0.01em]">{title}</h2>
      <div className="mt-2 space-y-2 text-[14.5px] leading-relaxed text-neutral-700 [&_li]:ml-5 [&_li]:list-disc [&_ul]:space-y-1">
        {children}
      </div>
    </section>
  );
}

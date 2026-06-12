import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service — EvolveRun",
  description: "The terms governing your use of EvolveRun.",
};

// NOTE FOR THE FOUNDER:
// Structurally-complete starting point, NOT legal advice. Have it reviewed
// before charging customers (Stripe requires published terms).
export default function TermsPage() {
  return (
    <article className="prose-legal">
      <h1 className="evr-headline text-[34px] tracking-[-0.02em]">Terms of Service</h1>
      <p className="mt-2 text-[13px] text-neutral-500">Last updated: June 12, 2026</p>

      <Section title="1. The service">
        EvolveRun provides a hosted connector that lets an AI assistant you
        control (Claude or ChatGPT) answer questions about your own
        endurance-training data, plus a web app for account management and
        viewing your plan. By creating an account you agree to these terms.
      </Section>

      <Section title="2. Eligibility &amp; accounts">
        You must be at least 16 years old and provide accurate account
        information. You are responsible for activity under your account and for
        keeping your credentials secure.
      </Section>

      <Section title="3. Subscriptions &amp; billing">
        EvolveRun is a paid subscription billed through Stripe at the price shown
        at checkout (€7.99 per month). Subscriptions renew automatically
        until cancelled. You can cancel anytime from your account; access
        continues until the end of the current billing period. If you are a
        consumer in the EU, you have a 14-day right of withdrawal from the day
        you subscribe; by using the service during that period you consent to
        immediate performance, and if you withdraw we may deduct a
        proportionate amount for the time already used. Beyond that, partial
        billing periods are not refunded.
      </Section>

      <Section title="4. Acceptable use">
        You agree not to misuse the service, attempt to access other users&apos;
        data, reverse-engineer or overload the API, or use it for unlawful
        purposes. We may suspend accounts that violate these terms.
      </Section>

      <Section title="5. Your data &amp; third-party services">
        Your use of connected services (Strava, and your chosen AI assistant
        provider) is also governed by their terms. Our handling of your data is
        described in our <a href="/privacy">Privacy Policy</a>. EvolveRun is not
        endorsed or certified by Strava, Anthropic, or OpenAI.
      </Section>

      <Section title="6. Not medical or coaching advice">
        EvolveRun and the connected AI assistant provide informational training
        insights only. They are not medical advice and not a substitute for a
        qualified coach or physician. Train at your own risk and consult a
        professional before making significant changes to your training.
      </Section>

      <Section title="7. Disclaimers &amp; liability">
        The service is provided &quot;as is&quot; without warranties of any
        kind. To the maximum extent permitted by law, EvolveRun&apos;s liability
        is limited to the amount you paid in the 12 months preceding the
        claim.
      </Section>

      <Section title="8. Termination">
        You may stop using the service and delete your account at any time. We
        may suspend or terminate access for breach of these terms or to comply
        with the law.
      </Section>

      <Section title="9. Governing law">
        These terms are governed by the laws of Denmark,
        without regard to conflict-of-laws rules.
      </Section>

      <Section title="10. Contact">
        Questions about these terms: <strong>vstoerum@gmail.com</strong>.
      </Section>
    </article>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-8">
      <h2 className="text-[18px] font-semibold tracking-[-0.01em]">{title}</h2>
      <div className="mt-2 space-y-2 text-[14.5px] leading-relaxed text-neutral-700 [&_a]:underline">
        {children}
      </div>
    </section>
  );
}

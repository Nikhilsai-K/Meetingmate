export const metadata = { title: 'Terms — MeetingMate' };

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16 text-zinc-200">
      <h1 className="text-3xl font-bold">Terms of service</h1>
      <p className="mt-2 text-sm text-zinc-500">Effective 2026-04-01.</p>
      <p className="mt-6 text-sm">
        By using MeetingMate you agree to the following. MeetingMate is provided as a Chromium
        browser extension and related backend services that transcribe, translate, and summarize
        Google Meet audio that you capture from your own computer.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Your responsibilities</h2>
      <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
        <li>
          You are responsible for complying with any meeting-recording or transcription laws that
          apply to you and for informing your colleagues that you are using an AI assistant.
        </li>
        <li>You own your transcripts and notes.</li>
        <li>You will not attempt to reverse-engineer the extension or abuse the backend.</li>
      </ul>

      <h2 className="mt-8 text-xl font-semibold">Service availability</h2>
      <p className="mt-2 text-sm">
        We aim for 99.9% uptime but the service is provided as-is. Planned maintenance is announced
        on our status page.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Billing</h2>
      <p className="mt-2 text-sm">
        Free tier: 5 meeting-hours per day. Paid tiers: billed monthly via Stripe. You can cancel
        any time from the customer portal.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Changes</h2>
      <p className="mt-2 text-sm">
        We may update these terms. We will email all account holders if material changes are made.
      </p>
      <p className="mt-6 text-sm">Contact: support@meetingmate.app</p>
    </main>
  );
}

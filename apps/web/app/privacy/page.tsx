export const metadata = { title: 'Privacy policy — MeetingMate' };

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16 text-zinc-200">
      <h1 className="text-3xl font-bold">Privacy policy</h1>
      <p className="mt-2 text-sm text-zinc-500">Effective 2026-04-01.</p>

      <h2 className="mt-8 text-xl font-semibold">What we collect</h2>
      <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
        <li>Your Clerk account (email + user id).</li>
        <li>Meeting metadata (title, start/end time, languages).</li>
        <li>Transcripts and AI-generated notes.</li>
        <li>Pinned vocabulary and preferences.</li>
        <li>Usage metrics (minutes transcribed) for billing.</li>
      </ul>

      <h2 className="mt-8 text-xl font-semibold">What we do NOT store</h2>
      <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
        <li>
          <strong>Audio.</strong> Your tab audio is streamed to our servers only to be transcribed.
          It is held in memory for Deepgram relay and discarded within 60 seconds of transcription.
          It is never written to disk.
        </li>
        <li>
          <strong>Prompt contents in observability.</strong> Langfuse and Sentry receive only
          metadata (model, tokens, latency, meeting id). Transcript text is never logged.
        </li>
      </ul>

      <h2 className="mt-8 text-xl font-semibold">Who we share with</h2>
      <p className="mt-2 text-sm">Sub-processors used strictly to provide the service:</p>
      <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
        <li>Deepgram — speech-to-text (audio passes through, not stored by us).</li>
        <li>Anthropic — translation and notes generation.</li>
        <li>Voyage AI — multilingual embeddings.</li>
        <li>Cohere — reranking.</li>
        <li>Clerk — authentication.</li>
        <li>Stripe — billing.</li>
        <li>Fly.io, AWS, Cloudflare — hosting + edge security.</li>
      </ul>

      <h2 className="mt-8 text-xl font-semibold">Your rights</h2>
      <ul className="mt-2 list-disc space-y-1 pl-6 text-sm">
        <li>Delete any meeting — transcripts + embeddings are purged immediately.</li>
        <li>Delete your account — all data is deleted within 7 days.</li>
        <li>Export all your data as JSON at any time.</li>
        <li>Contact privacy@meetingmate.app for GDPR / APPI data requests.</li>
      </ul>

      <h2 className="mt-8 text-xl font-semibold">Consent & transparency</h2>
      <p className="mt-2 text-sm">
        You acknowledge on first use that you are responsible for informing meeting participants
        that you are using an AI assistant. MeetingMate displays a visible "AI Assistant Active"
        indicator in the sidebar whenever it is capturing audio.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Security</h2>
      <p className="mt-2 text-sm">
        All transport is TLS 1.3. Data at rest uses AES-256. Per-user isolation is enforced by
        Postgres row-level security and per-payload filters in Qdrant. We are working toward SOC 2
        Type II.
      </p>

      <h2 className="mt-8 text-xl font-semibold">Contact</h2>
      <p className="mt-2 text-sm">privacy@meetingmate.app</p>
    </main>
  );
}

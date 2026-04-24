import Link from 'next/link';
import { SignedIn, SignedOut, SignInButton, UserButton } from '@clerk/nextjs';

export default function HomePage() {
  return (
    <div>
      <header className="border-b border-zinc-900 bg-zinc-950/50 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Link href="/" className="text-lg font-bold">
            MeetingMate
          </Link>
          <nav className="flex items-center gap-4 text-sm text-zinc-300">
            <Link href="/pricing" className="hover:text-white">Pricing</Link>
            <Link href="/privacy" className="hover:text-white">Privacy</Link>
            <SignedOut>
              <SignInButton mode="modal">
                <button className="btn-primary">Sign in</button>
              </SignInButton>
            </SignedOut>
            <SignedIn>
              <Link href="/dashboard" className="btn-ghost">Dashboard</Link>
              <UserButton afterSignOutUrl="/" />
            </SignedIn>
          </nav>
        </div>
      </header>

      <main>
        <section className="mx-auto max-w-5xl px-6 py-20 text-center">
          <p className="mb-3 inline-block rounded-full border border-brand-700/40 bg-brand-600/10 px-3 py-1 text-xs text-brand-500">
            Built for foreign workers in Japan
          </p>
          <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight md:text-6xl">
            Follow every Google Meet — even when it's not in your language.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-zinc-300">
            Live Japanese ↔ English translation in a sidebar. AI-generated notes, decisions, and
            action items when the meeting ends. Privacy-first: your audio is never stored.
          </p>
          <div className="mt-8 flex items-center justify-center gap-3">
            <a
              href="https://chromewebstore.google.com/"
              target="_blank"
              rel="noreferrer"
              className="btn-primary"
            >
              Install for Chrome
            </a>
            <Link href="/pricing" className="btn-ghost">
              See pricing
            </Link>
          </div>
        </section>

        <section className="mx-auto max-w-5xl px-6 py-16">
          <div className="grid gap-6 md:grid-cols-3">
            <Feature
              title="Live translation"
              body="Two-column sidebar — original language on the left, your language on the right. ~1 second latency."
            />
            <Feature
              title="AI meeting notes"
              body="Summary, decisions, action items, glossary. Generated automatically when the meeting ends."
            />
            <Feature
              title="Private by default"
              body="Audio is transcribed in memory and discarded within 60 seconds. Only transcripts and notes are saved — and you control them."
            />
          </div>
        </section>
      </main>

      <footer className="border-t border-zinc-900 py-8 text-center text-xs text-zinc-500">
        © {new Date().getFullYear()} MeetingMate ·{' '}
        <Link href="/privacy" className="hover:text-white">Privacy</Link> ·{' '}
        <Link href="/terms" className="hover:text-white">Terms</Link>
      </footer>
    </div>
  );
}

function Feature({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
      <h3 className="font-semibold">{title}</h3>
      <p className="mt-2 text-sm text-zinc-400">{body}</p>
    </div>
  );
}

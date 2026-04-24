import { auth, currentUser } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import Link from 'next/link';

export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  const { userId } = await auth();
  if (!userId) redirect('/');
  const user = await currentUser();

  return (
    <main className="mx-auto max-w-5xl px-6 py-12">
      <header className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            Welcome back{user?.firstName ? `, ${user.firstName}` : ''}.
          </h1>
          <p className="text-sm text-zinc-400">Open Google Meet — the sidebar opens automatically.</p>
        </div>
        <Link
          href="https://meet.google.com/"
          target="_blank"
          rel="noreferrer"
          className="btn-primary"
        >
          Open Google Meet ↗
        </Link>
      </header>

      <section className="grid gap-4 md:grid-cols-2">
        <Card title="Install the extension">
          <p className="text-sm text-zinc-300">
            MeetingMate lives as a Chromium extension. Install it from the Chrome Web Store and pin
            it to your toolbar.
          </p>
          <a
            href="https://chromewebstore.google.com/"
            target="_blank"
            rel="noreferrer"
            className="btn-primary mt-4"
          >
            Install
          </a>
        </Card>
        <Card title="Your meetings">
          <p className="text-sm text-zinc-300">
            All your past meetings are available in the extension sidebar under "History".
          </p>
        </Card>
        <Card title="Billing">
          <p className="mb-4 text-sm text-zinc-300">Manage plan and payment method.</p>
          <form action="/api/billing/portal" method="POST">
            <button className="btn-ghost">Manage billing</button>
          </form>
        </Card>
        <Card title="Privacy controls">
          <p className="text-sm text-zinc-300">Delete account or export data.</p>
          <div className="mt-3 flex gap-2">
            <form action="/api/account/export" method="POST">
              <button className="btn-ghost">Export data</button>
            </form>
          </div>
        </Card>
      </section>
    </main>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
      <h3 className="mb-2 font-semibold">{title}</h3>
      {children}
    </div>
  );
}

import Link from 'next/link';

export const metadata = { title: 'Pricing — MeetingMate' };

const plans = [
  {
    name: 'Free',
    price: '$0',
    blurb: 'For trying it out.',
    bullets: [
      '5 meeting-hours per day',
      '7-day meeting history',
      '2 integrations',
      'AI notes after every meeting',
    ],
    cta: 'Start free',
    href: '/sign-up',
    highlight: false,
  },
  {
    name: 'Pro',
    price: '$12',
    per: '/ month',
    blurb: 'For daily users.',
    bullets: [
      'Unlimited meeting-hours',
      'Unlimited history + search',
      'All integrations',
      'Priority processing',
      'PDF / Notion / Markdown export',
      'Pre-meeting briefs (Calendar)',
    ],
    cta: 'Upgrade',
    href: '/dashboard?upgrade=pro',
    highlight: true,
  },
  {
    name: 'Team',
    price: '$25',
    per: '/ user / month',
    blurb: 'For small teams.',
    bullets: [
      'Everything in Pro',
      'Shared meeting library',
      'Admin console',
      'SSO (Google Workspace)',
    ],
    cta: 'Contact sales',
    href: 'mailto:sales@meetingmate.app',
    highlight: false,
  },
];

export default function PricingPage() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-16">
      <h1 className="text-center text-4xl font-bold">Simple pricing</h1>
      <p className="mt-2 text-center text-zinc-400">
        Free for light use. Pro when you need it daily.
      </p>
      <div className="mt-12 grid gap-4 md:grid-cols-3">
        {plans.map((p) => (
          <div
            key={p.name}
            className={[
              'rounded-2xl border bg-zinc-900/60 p-6',
              p.highlight ? 'border-brand-600 ring-1 ring-brand-600/40' : 'border-zinc-800',
            ].join(' ')}
          >
            <div className="text-sm text-zinc-400">{p.name}</div>
            <div className="mt-1">
              <span className="text-3xl font-bold">{p.price}</span>
              {p.per && <span className="ml-1 text-sm text-zinc-400">{p.per}</span>}
            </div>
            <p className="mt-1 text-sm text-zinc-400">{p.blurb}</p>
            <ul className="mt-4 space-y-1 text-sm">
              {p.bullets.map((b) => (
                <li key={b} className="text-zinc-300">• {b}</li>
              ))}
            </ul>
            <Link
              href={p.href}
              className={p.highlight ? 'btn-primary mt-6 w-full' : 'btn-ghost mt-6 w-full'}
            >
              {p.cta}
            </Link>
          </div>
        ))}
      </div>
    </main>
  );
}

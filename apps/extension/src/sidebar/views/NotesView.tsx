import { useAuth } from '@clerk/chrome-extension';
import { useQuery } from '@tanstack/react-query';
import { useStore } from '../store';
import { api } from '../api';
import { Loader2, CheckCircle2, Circle, Download } from 'lucide-react';

export function NotesView() {
  const { getToken } = useAuth();
  const meetingId = useStore((s) => s.meetingId);

  const q = useQuery({
    queryKey: ['meeting', meetingId],
    enabled: !!meetingId,
    refetchInterval: (query) =>
      query.state.data?.status === 'complete' ? false : 3000,
    queryFn: async () => {
      const tok = await getToken();
      if (!tok || !meetingId) throw new Error('no_token');
      return api.getMeeting(tok, meetingId);
    },
  });

  if (!meetingId) {
    return <Empty text="End a meeting to see notes here." />;
  }

  if (q.isLoading || !q.data) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-zinc-400">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        Loading…
      </div>
    );
  }

  const m = q.data;
  const processing = m.status !== 'complete';

  return (
    <div className="flex h-full flex-col overflow-y-auto px-4 py-4">
      <header className="mb-4">
        <div className="text-xs uppercase tracking-wide text-zinc-500">
          {processing ? 'Processing — this takes ~20s' : 'Meeting complete'}
        </div>
        <h2 className="text-lg font-semibold">{m.title ?? 'Untitled meeting'}</h2>
        <div className="mt-1 flex items-center gap-2 text-xs text-zinc-400">
          <span>{Math.round(m.duration_s / 60)} min</span>
          <span>·</span>
          <span>
            {m.source_language} → {m.target_language}
          </span>
        </div>
      </header>

      {processing ? (
        <ProcessingSkeleton />
      ) : (
        <>
          <Section title="Summary">
            <p className="text-sm leading-relaxed text-zinc-200">{m.summary ?? '—'}</p>
          </Section>

          <Section title="Key decisions">
            {m.decisions.length === 0 ? (
              <p className="text-sm text-zinc-500">No decisions recorded.</p>
            ) : (
              <ul className="space-y-1 text-sm">
                {m.decisions.map((d, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-400" />
                    <span>{typeof d === 'string' ? d : JSON.stringify(d)}</span>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Action items">
            {m.action_items.length === 0 ? (
              <p className="text-sm text-zinc-500">No action items.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {m.action_items.map((a, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <Circle className="mt-1 h-3.5 w-3.5 flex-shrink-0 text-brand-500" />
                    <div>
                      <div className="font-medium">{a.task}</div>
                      <div className="text-xs text-zinc-400">
                        {a.owner ? `Owner: ${a.owner}` : ''}
                        {a.owner && a.deadline ? ' · ' : ''}
                        {a.deadline ? `Due: ${a.deadline}` : ''}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          {m.open_questions.length > 0 && (
            <Section title="Open questions">
              <ul className="space-y-1 text-sm">
                {m.open_questions.map((q, i) => (
                  <li key={i} className="text-zinc-300">
                    ? {q}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          {m.glossary.length > 0 && (
            <Section title="Glossary">
              <ul className="space-y-2 text-sm">
                {m.glossary.map((g, i) => (
                  <li key={i} className="rounded-lg border border-surface-border bg-surface-muted p-3">
                    <div className="font-semibold">
                      {g.term}
                      {g.pronunciation && (
                        <span className="ml-2 text-xs text-zinc-400">({g.pronunciation})</span>
                      )}
                    </div>
                    {g.meaning && <div className="mt-1 text-zinc-300">{g.meaning}</div>}
                    {g.example && (
                      <div className="mt-1 italic text-zinc-500">e.g. {g.example}</div>
                    )}
                  </li>
                ))}
              </ul>
            </Section>
          )}

          <div className="mt-6 flex gap-2">
            <ExportButton meetingId={m.id} />
          </div>
        </>
      )}
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mb-5">
      <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-400">
        {title}
      </h3>
      {children}
    </section>
  );
}

function ProcessingSkeleton() {
  return (
    <div className="space-y-4">
      {[0, 1, 2].map((i) => (
        <div key={i} className="space-y-2">
          <div className="h-3 w-24 rounded bg-surface-soft" />
          <div className="h-4 w-full rounded bg-surface-soft" />
          <div className="h-4 w-5/6 rounded bg-surface-soft" />
        </div>
      ))}
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="flex h-full items-center justify-center p-6 text-sm text-zinc-500">
      {text}
    </div>
  );
}

function ExportButton({ meetingId }: { meetingId: string }) {
  const { getToken } = useAuth();
  async function exportMd() {
    const tok = await getToken();
    if (!tok) return;
    const m = await api.getMeeting(tok, meetingId);
    const md = renderMarkdown(m);
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `meetingmate-${meetingId}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <button onClick={exportMd} className="btn-ghost">
      <Download className="mr-1 h-4 w-4" /> Export Markdown
    </button>
  );
}

function renderMarkdown(m: Awaited<ReturnType<typeof api.getMeeting>>): string {
  const lines: string[] = [];
  lines.push(`# ${m.title ?? 'Meeting'}`);
  lines.push('');
  if (m.summary) {
    lines.push('## Summary');
    lines.push(m.summary);
    lines.push('');
  }
  if (m.decisions.length) {
    lines.push('## Decisions');
    for (const d of m.decisions) lines.push(`- ${typeof d === 'string' ? d : JSON.stringify(d)}`);
    lines.push('');
  }
  if (m.action_items.length) {
    lines.push('## Action items');
    for (const a of m.action_items) {
      lines.push(`- **${a.task}** — ${a.owner ?? 'Unassigned'}${a.deadline ? ` (${a.deadline})` : ''}`);
    }
    lines.push('');
  }
  if (m.glossary.length) {
    lines.push('## Glossary');
    for (const g of m.glossary) lines.push(`- **${g.term}** — ${g.meaning ?? ''}`);
  }
  return lines.join('\n');
}

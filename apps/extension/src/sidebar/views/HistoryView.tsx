import { useAuth } from '@clerk/chrome-extension';
import { useQuery } from '@tanstack/react-query';
import { useStore } from '../store';
import { api } from '../api';
import { cn } from '../lib/cn';
import { CheckCircle2, Loader2, AlertCircle, ChevronRight } from 'lucide-react';

export function HistoryView() {
  const { getToken } = useAuth();
  const setView = useStore((s) => s.setView);

  const q = useQuery({
    queryKey: ['history'],
    queryFn: async () => {
      const tok = await getToken();
      if (!tok) throw new Error('no_token');
      return api.listMeetings(tok);
    },
  });

  if (q.isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-zinc-400">
        Loading…
      </div>
    );
  }

  const items = q.data?.items ?? [];
  if (items.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-sm text-zinc-500">
        No past meetings yet. Your meetings will appear here after they finish.
      </div>
    );
  }

  return (
    <ul className="h-full space-y-2 overflow-y-auto px-4 py-4">
      {items.map((m) => (
        <li key={m.id}>
          <button
            onClick={() => {
              useStore.setState({ meetingId: m.id });
              setView(m.status === 'complete' ? 'notes' : 'notes');
            }}
            className="card flex w-full items-start justify-between gap-3 text-left hover:border-brand-600/40"
          >
            <div className="flex-1">
              <div className="flex items-center gap-2 text-sm font-medium">
                <StatusIcon status={m.status} />
                <span>{m.title ?? 'Untitled meeting'}</span>
              </div>
              <div className="mt-1 text-xs text-zinc-500">
                {m.source_language} → {m.target_language} · {Math.round(m.duration_s / 60)} min ·{' '}
                {m.status}
              </div>
              {m.summary && (
                <p className="mt-1 line-clamp-2 text-xs text-zinc-400">{m.summary}</p>
              )}
            </div>
            <ChevronRight className="mt-1 h-4 w-4 text-zinc-500" />
          </button>
        </li>
      ))}
    </ul>
  );
}

function StatusIcon({ status }: { status: string }) {
  const cls = cn(
    'h-3.5 w-3.5',
    status === 'complete' && 'text-emerald-400',
    status === 'processing' && 'text-amber-400 animate-pulse',
    status === 'failed' && 'text-red-400',
  );
  if (status === 'complete') return <CheckCircle2 className={cls} />;
  if (status === 'failed') return <AlertCircle className={cls} />;
  return <Loader2 className={cls} />;
}

import { useAuth } from '@clerk/chrome-extension';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../api';
import { config } from '../../shared/config';
import { Trash2, Plus } from 'lucide-react';

export function SettingsView() {
  const { getToken } = useAuth();
  const qc = useQueryClient();

  const vocab = useQuery({
    queryKey: ['vocab'],
    queryFn: async () => {
      const tok = await getToken();
      if (!tok) throw new Error('no_token');
      return api.listVocab(tok);
    },
  });

  const usage = useQuery({
    queryKey: ['usage'],
    queryFn: async () => {
      const tok = await getToken();
      if (!tok) throw new Error('no_token');
      return api.usage(tok);
    },
  });

  const addVocab = useMutation({
    mutationFn: async (item: { term: string; translation?: string }) => {
      const tok = await getToken();
      if (!tok) throw new Error('no_token');
      return api.addVocab(tok, item);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['vocab'] }),
  });

  const removeVocab = useMutation({
    mutationFn: async (term: string) => {
      const tok = await getToken();
      if (!tok) throw new Error('no_token');
      return api.deleteVocab(tok, term);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['vocab'] }),
  });

  const [term, setTerm] = useState('');
  const [translation, setTranslation] = useState('');

  return (
    <div className="h-full overflow-y-auto px-4 py-4 space-y-5">
      <section className="card">
        <h3 className="mb-2 text-sm font-semibold">Usage today</h3>
        {usage.data ? (
          <div className="text-sm text-zinc-300">
            <div>
              {usage.data.minutes_today} / {usage.data.minutes_limit} minutes
            </div>
            <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-surface-soft">
              <div
                className="h-full bg-brand-600"
                style={{
                  width: `${Math.min(100, (usage.data.minutes_today / Math.max(1, usage.data.minutes_limit)) * 100)}%`,
                }}
              />
            </div>
            <div className="mt-2 text-xs text-zinc-500">Plan: {usage.data.plan}</div>
          </div>
        ) : (
          <div className="text-sm text-zinc-500">—</div>
        )}
      </section>

      <section className="card">
        <h3 className="mb-2 text-sm font-semibold">Pinned vocabulary</h3>
        <p className="mb-3 text-xs text-zinc-400">
          Terms here are boosted in speech recognition and respected by the translator.
        </p>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (!term.trim()) return;
            addVocab.mutate({ term: term.trim(), translation: translation.trim() || undefined });
            setTerm('');
            setTranslation('');
          }}
          className="flex items-center gap-2"
        >
          <input
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="Term (e.g. マイグレーション)"
            className="flex-1 rounded-md border border-surface-border bg-surface-soft px-2 py-1.5 text-sm"
          />
          <input
            value={translation}
            onChange={(e) => setTranslation(e.target.value)}
            placeholder="Translation (optional)"
            className="flex-1 rounded-md border border-surface-border bg-surface-soft px-2 py-1.5 text-sm"
          />
          <button className="btn-primary" disabled={addVocab.isPending || !term.trim()}>
            <Plus className="h-4 w-4" />
          </button>
        </form>

        <ul className="mt-3 space-y-1 text-sm">
          {(vocab.data?.items ?? []).map((v) => (
            <li
              key={v.term}
              className="flex items-center justify-between rounded-md border border-surface-border bg-surface-soft px-3 py-1.5"
            >
              <div>
                <span className="font-medium">{v.term}</span>
                {v.translation && (
                  <span className="ml-2 text-xs text-zinc-400">→ {v.translation}</span>
                )}
              </div>
              <button
                onClick={() => removeVocab.mutate(v.term)}
                className="text-zinc-500 hover:text-red-400"
                title="Remove"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </li>
          ))}
          {(vocab.data?.items ?? []).length === 0 && (
            <li className="text-xs text-zinc-500">No terms yet.</li>
          )}
        </ul>
      </section>

      <section className="card">
        <h3 className="mb-2 text-sm font-semibold">Account</h3>
        <a
          href={config.webBaseUrl + '/dashboard'}
          target="_blank"
          rel="noreferrer"
          className="text-sm text-brand-500 hover:underline"
        >
          Open dashboard ↗
        </a>
      </section>

      <section className="card">
        <h3 className="mb-2 text-sm font-semibold">Privacy</h3>
        <p className="text-xs text-zinc-400">
          Audio is processed in real time and never stored — only transcripts + notes are saved.
          You can delete any meeting any time from history.
        </p>
        <div className="mt-2 text-xs">
          <a
            href={config.webBaseUrl + '/privacy'}
            target="_blank"
            rel="noreferrer"
            className="text-brand-500 hover:underline"
          >
            Privacy policy ↗
          </a>
          <span className="mx-2 text-zinc-600">·</span>
          <a
            href={config.webBaseUrl + '/terms'}
            target="_blank"
            rel="noreferrer"
            className="text-brand-500 hover:underline"
          >
            Terms ↗
          </a>
        </div>
      </section>
    </div>
  );
}

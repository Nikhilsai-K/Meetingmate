import { useState, useRef, useEffect } from 'react';
import { useAuth } from '@clerk/chrome-extension';
import { useStore } from '../store';
import { api } from '../api';
import { Send, Loader2 } from 'lucide-react';

type ChatTurn = { role: 'user' | 'assistant'; content: string };

export function ChatView() {
  const { getToken } = useAuth();
  const meetingId = useStore((s) => s.meetingId);
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState('');
  const [pending, setPending] = useState(false);
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!meetingId || !input.trim() || pending) return;
    const question = input.trim();
    setInput('');
    setTurns((t) => [...t, { role: 'user', content: question }, { role: 'assistant', content: '' }]);
    setPending(true);
    try {
      const tok = await getToken();
      if (!tok) throw new Error('no_token');
      await api.chatStream(tok, meetingId, question, (chunk) => {
        setTurns((t) => {
          const copy = [...t];
          copy[copy.length - 1] = {
            role: 'assistant',
            content: copy[copy.length - 1].content + chunk,
          };
          return copy;
        });
      });
    } catch (e) {
      setTurns((t) => [
        ...t.slice(0, -1),
        { role: 'assistant', content: 'Sorry, I had trouble answering that. Try again.' },
      ]);
    } finally {
      setPending(false);
    }
  }

  if (!meetingId) {
    return (
      <div className="flex h-full items-center justify-center p-6 text-center text-sm text-zinc-500">
        Finish a meeting first, then ask questions about what was said.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {turns.length === 0 && (
          <div className="card text-sm text-zinc-400">
            Ask anything about this meeting — e.g. <span className="text-zinc-200">"What did we decide about the Q3 budget?"</span>.
          </div>
        )}
        {turns.map((t, i) => (
          <div
            key={i}
            className={
              t.role === 'user'
                ? 'ml-auto max-w-[85%] rounded-lg bg-brand-600 px-3 py-2 text-sm text-white'
                : 'max-w-[95%] rounded-lg border border-surface-border bg-surface-muted px-3 py-2 text-sm'
            }
          >
            {renderWithCitations(t.content)}
          </div>
        ))}
        {pending && (
          <div className="text-xs text-zinc-500">
            <Loader2 className="mr-1 inline h-3 w-3 animate-spin" /> thinking…
          </div>
        )}
        <div ref={endRef} />
      </div>
      <form onSubmit={submit} className="border-t border-surface-border bg-surface-muted/40 p-3">
        <div className="flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about this meeting…"
            className="flex-1 rounded-md border border-surface-border bg-surface-soft px-3 py-2 text-sm focus:border-brand-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={pending || !input.trim()}
            className="btn-primary disabled:opacity-60"
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </form>
    </div>
  );
}

function renderWithCitations(content: string) {
  // Replace [utt:<uuid>] with a small chip.
  const parts = content.split(/(\[utt:[0-9a-fA-F-]{36}\])/g);
  return parts.map((p, i) => {
    const m = p.match(/^\[utt:([0-9a-fA-F-]{36})\]$/);
    if (m) {
      return (
        <span key={i} className="chip ml-1">
          source
        </span>
      );
    }
    return <span key={i}>{p}</span>;
  });
}

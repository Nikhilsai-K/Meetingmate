import { useAuth } from '@clerk/chrome-extension';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api';
import { ShieldCheck } from 'lucide-react';

export function ConsentGate({ children }: { children: React.ReactNode }) {
  const { getToken } = useAuth();
  const qc = useQueryClient();

  const me = useQuery({
    queryKey: ['me'],
    queryFn: async () => {
      const tok = await getToken();
      if (!tok) throw new Error('no_token');
      return api.me(tok);
    },
  });

  const ack = useMutation({
    mutationFn: async () => {
      const tok = await getToken();
      if (!tok) throw new Error('no_token');
      return api.ackConsent(tok);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['me'] }),
  });

  if (me.isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-zinc-400">
        Loading…
      </div>
    );
  }

  if (me.data && !me.data.consent_recording_ack_at) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <div className="w-full max-w-sm rounded-xl border border-surface-border bg-surface-muted p-6">
          <div className="mb-4 grid h-10 w-10 place-items-center rounded-lg bg-brand-600/20 text-brand-500">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <h2 className="text-base font-semibold">Recording & transparency</h2>
          <p className="mt-2 text-sm text-zinc-300">
            MeetingMate captures the audio of your Google Meet tab to transcribe + translate it in
            real time. Audio is never stored. Only transcripts and notes are saved to your account.
          </p>
          <p className="mt-3 text-sm text-zinc-300">
            You are responsible for informing meeting participants that you are using an AI
            assistant. A visible "AI Assistant Active" indicator will be shown in the sidebar during
            every meeting.
          </p>
          <button
            onClick={() => ack.mutate()}
            disabled={ack.isPending}
            className="btn-primary mt-5 w-full"
          >
            {ack.isPending ? 'Saving…' : 'I understand — continue'}
          </button>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

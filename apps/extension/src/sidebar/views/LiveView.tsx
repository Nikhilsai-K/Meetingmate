import { useEffect, useRef } from 'react';
import { useAuth } from '@clerk/chrome-extension';
import { useMutation } from '@tanstack/react-query';
import { useStore } from '../store';
import { api } from '../api';
import { send } from '../bridge';
import { cn, speakerColor } from '../lib/cn';
import { Play, Square, Pause, AlertTriangle, Star, PauseCircle, PlayCircle } from 'lucide-react';
import { useKeyboardShortcut } from '../hooks/useKeyboardShortcut';

const LANGS = [
  { code: 'ja', label: '日本語' },
  { code: 'en', label: 'English' },
  { code: 'ko', label: '한국어' },
  { code: 'zh', label: '中文' },
  { code: 'es', label: 'Español' },
  { code: 'fr', label: 'Français' },
  { code: 'de', label: 'Deutsch' },
];

export function LiveView() {
  const { getToken } = useAuth();
  const {
    isCapturing,
    isPaused,
    utterances,
    interim,
    sourceLang,
    targetLang,
    meetCode,
    error,
    setLanguages,
    start,
    stop,
    pause,
    resume,
    markImportant,
  } = useStore();

  const scrollerRef = useRef<HTMLDivElement | null>(null);
  const autoScrollRef = useRef(true);

  useEffect(() => {
    const el = scrollerRef.current;
    if (!el || !autoScrollRef.current) return;
    el.scrollTop = el.scrollHeight;
  }, [utterances.length, interim?.text]);

  const startMut = useMutation({
    mutationFn: async () => {
      const tok = await getToken();
      if (!tok) throw new Error('no_token');
      const res = await api.createMeeting(tok, {
        source_language: sourceLang,
        target_language: targetLang,
        google_meet_code: meetCode ?? null,
        template: 'default',
      });
      start(res.meeting_id);
      send({
        kind: 'start-capture',
        meetingId: res.meeting_id,
        wsUrl: res.ws_url,
        jwt: tok,
        sourceLang,
        targetLang,
      });
    },
  });

  useKeyboardShortcut('mod+shift+i', () => {
    const last = utterances[utterances.length - 1];
    if (!last) return;
    markImportant(last.id, !last.isImportant);
    void getToken().then((tok) => {
      if (!tok || !useStore.getState().meetingId) return;
      api.markImportant(tok, useStore.getState().meetingId!, last.id).catch(() => {});
    });
  });

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-surface-border bg-surface-muted/40 px-4 py-3">
        <div className="flex items-center gap-2">
          <LangPicker
            label="From"
            value={sourceLang}
            onChange={(v) => setLanguages(v, targetLang)}
            disabled={isCapturing}
          />
          <span className="text-zinc-500">→</span>
          <LangPicker
            label="To"
            value={targetLang}
            onChange={(v) => setLanguages(sourceLang, v)}
            disabled={isCapturing}
          />
          <div className="flex-1" />
          {!isCapturing ? (
            <button
              className="btn-primary"
              disabled={startMut.isPending}
              onClick={() => startMut.mutate()}
            >
              <Play className="mr-1 h-4 w-4" />
              Start
            </button>
          ) : (
            <div className="flex items-center gap-2">
              {isPaused ? (
                <button
                  className="btn-ghost"
                  onClick={() => {
                    resume();
                    send({ kind: 'resume-capture' });
                  }}
                  title="Resume"
                >
                  <PlayCircle className="h-4 w-4" />
                </button>
              ) : (
                <button
                  className="btn-ghost"
                  onClick={() => {
                    pause();
                    send({ kind: 'pause-capture' });
                  }}
                  title="Pause"
                >
                  <PauseCircle className="h-4 w-4" />
                </button>
              )}
              <button
                className="btn-danger"
                onClick={() => {
                  stop();
                  send({ kind: 'stop-capture' });
                }}
              >
                <Square className="mr-1 h-4 w-4" />
                End meeting
              </button>
            </div>
          )}
        </div>
        {error && (
          <div className="mt-2 flex items-start gap-2 rounded-md bg-amber-500/10 px-3 py-2 text-xs text-amber-300">
            <AlertTriangle className="mt-0.5 h-3.5 w-3.5" />
            <span>We had trouble connecting. Retrying…</span>
          </div>
        )}
      </div>

      <div
        ref={scrollerRef}
        onScroll={(e) => {
          const el = e.currentTarget;
          autoScrollRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
        }}
        className="flex-1 overflow-y-auto px-4 py-4 space-y-3"
      >
        {utterances.length === 0 && !interim && (
          <EmptyPlaceholder isCapturing={isCapturing} />
        )}
        {utterances.map((u) => (
          <article
            key={u.id}
            className={cn(
              'card grid grid-cols-2 gap-3',
              u.isImportant && 'ring-2 ring-amber-400/60',
            )}
          >
            <div>
              <div className={cn('mb-1 text-xs font-semibold', speakerColor(u.speakerId))}>
                {u.speakerName ?? `Speaker ${u.speakerId}`}
                <span className="ml-2 text-[10px] text-zinc-500">
                  {Math.floor(u.startMs / 60000)}:{String(Math.floor((u.startMs % 60000) / 1000)).padStart(2, '0')}
                </span>
                <button
                  onClick={() => markImportant(u.id, !u.isImportant)}
                  className="float-right text-zinc-500 hover:text-amber-400"
                  title="Mark important (⌘⇧I)"
                >
                  <Star className={cn('h-3.5 w-3.5', u.isImportant && 'fill-amber-400 text-amber-400')} />
                </button>
              </div>
              <p className="text-sm leading-relaxed text-zinc-100">{u.original}</p>
            </div>
            <div className="border-l border-surface-border pl-3">
              <div className="mb-1 text-[10px] uppercase tracking-wide text-zinc-500">
                {targetLang}
              </div>
              <p className="text-sm leading-relaxed text-zinc-300">
                {u.translation}
                {u.translationInProgress && <span className="ml-0.5 animate-pulse">▍</span>}
              </p>
            </div>
          </article>
        ))}
        {interim && (
          <article className="card opacity-70">
            <div className={cn('mb-1 text-xs font-semibold', speakerColor(interim.speakerId))}>
              Speaker {interim.speakerId} (interim)
            </div>
            <p className="text-sm italic text-zinc-400">{interim.text}</p>
          </article>
        )}
      </div>
    </div>
  );
}

function EmptyPlaceholder({ isCapturing }: { isCapturing: boolean }) {
  return (
    <div className="mx-auto max-w-xs py-16 text-center text-sm text-zinc-500">
      {isCapturing ? (
        <>
          <Pause className="mx-auto mb-3 h-6 w-6 text-zinc-600" />
          Waiting for speech…
        </>
      ) : (
        <>
          <Play className="mx-auto mb-3 h-6 w-6 text-zinc-600" />
          Choose your languages and click <span className="font-medium text-zinc-300">Start</span>{' '}
          when the meeting is live. Chrome will ask to share tab audio.
        </>
      )}
    </div>
  );
}

function LangPicker({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex flex-col text-[10px] uppercase tracking-wide text-zinc-500">
      {label}
      <select
        value={value}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="mt-0.5 rounded-md border border-surface-border bg-surface-soft px-2 py-1 text-xs text-zinc-100 disabled:opacity-60"
      >
        {LANGS.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>
    </label>
  );
}

import { SignedIn, SignedOut, useAuth, SignIn } from '@clerk/chrome-extension';
import { useEffect } from 'react';
import { TopBar } from './views/TopBar';
import { LiveView } from './views/LiveView';
import { NotesView } from './views/NotesView';
import { ChatView } from './views/ChatView';
import { SettingsView } from './views/SettingsView';
import { HistoryView } from './views/HistoryView';
import { ConsentGate } from './views/ConsentGate';
import { useStore } from './store';
import { onMessage } from './bridge';
import { api } from './api';

export function App() {
  return (
    <>
      <SignedOut>
        <div className="flex h-full items-center justify-center p-6">
          <div className="w-full">
            <header className="mb-6 text-center">
              <h1 className="text-xl font-bold">MeetingMate</h1>
              <p className="mt-1 text-sm text-zinc-400">
                Sign in to start live translation and AI notes for Google Meet.
              </p>
            </header>
            <SignIn routing="virtual" />
          </div>
        </div>
      </SignedOut>
      <SignedIn>
        <AuthenticatedApp />
      </SignedIn>
    </>
  );
}

function AuthenticatedApp() {
  const view = useStore((s) => s.view);
  const tickElapsed = useStore((s) => s.tickElapsed);
  const isCapturing = useStore((s) => s.isCapturing);

  // Register bridge listeners once
  useEventBridge();

  // Tick elapsed clock
  useEffect(() => {
    if (!isCapturing) return;
    const id = window.setInterval(() => tickElapsed(), 1000);
    return () => window.clearInterval(id);
  }, [isCapturing, tickElapsed]);

  return (
    <ConsentGate>
      <div className="flex h-full flex-col">
        <TopBar />
        <main className="flex-1 overflow-hidden">
          {view === 'live' && <LiveView />}
          {view === 'notes' && <NotesView />}
          {view === 'chat' && <ChatView />}
          {view === 'settings' && <SettingsView />}
          {view === 'history' && <HistoryView />}
        </main>
      </div>
    </ConsentGate>
  );
}

function useEventBridge() {
  const addFinal = useStore((s) => s.addFinal);
  const setInterim = useStore((s) => s.setInterim);
  const appendDelta = useStore((s) => s.appendTranslationDelta);
  const finishTranslation = useStore((s) => s.finishTranslation);
  const setError = useStore((s) => s.setError);
  const setMeetContext = useStore((s) => s.setMeetContext);
  const stop = useStore((s) => s.stop);
  const setView = useStore((s) => s.setView);

  useEffect(() => {
    const off = onMessage((msg) => {
      switch (msg.kind) {
        case 'transcript-event': {
          const e = msg.event;
          if (e.type === 'interim') {
            setInterim({ speakerId: e.speaker_id, text: e.text });
          } else if (e.type === 'final') {
            addFinal({
              id: e.utterance_id,
              speakerId: e.speaker_id,
              startMs: e.start_ms,
              endMs: e.end_ms,
              original: e.text,
            });
          } else if (e.type === 'translation-delta') {
            appendDelta(e.utterance_id, e.delta);
          } else if (e.type === 'translation-done') {
            finishTranslation(e.utterance_id, e.text);
          } else if (e.type === 'error') {
            setError(e.code);
          } else if (e.type === 'ended') {
            stop();
            setView('notes');
          }
          break;
        }
        case 'meet-context':
          setMeetContext(msg.meetCode, msg.participants);
          break;
        case 'capture-ended':
          stop();
          setView('notes');
          break;
        case 'capture-error':
          setError(msg.error);
          stop();
          break;
      }
    });
    return () => {
      off();
    };
  }, [addFinal, setInterim, appendDelta, finishTranslation, setError, setMeetContext, stop, setView]);
}

// Re-export for tests that need an auth hook mock
export function useAuthReExport() {
  return useAuth();
}

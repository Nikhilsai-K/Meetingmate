import { create } from 'zustand';

export type UtteranceRow = {
  id: string;
  speakerId: string;
  speakerName?: string | null;
  startMs: number;
  endMs: number;
  original: string;
  translation: string;
  translationInProgress: boolean;
  isImportant?: boolean;
};

type SidebarView = 'live' | 'notes' | 'chat' | 'settings' | 'history';

type State = {
  view: SidebarView;
  meetingId: string | null;
  isCapturing: boolean;
  isPaused: boolean;
  elapsedSec: number;
  sourceLang: string;
  targetLang: string;
  participants: string[];
  meetCode: string | null;
  utterances: UtteranceRow[];
  interim: { speakerId: string; text: string } | null;
  error: string | null;

  setView: (view: SidebarView) => void;
  setLanguages: (s: string, t: string) => void;
  start: (meetingId: string) => void;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  tickElapsed: () => void;
  setError: (e: string | null) => void;
  setMeetContext: (meetCode: string | null, participants: string[]) => void;
  setInterim: (r: { speakerId: string; text: string } | null) => void;
  addFinal: (u: {
    id: string;
    speakerId: string;
    startMs: number;
    endMs: number;
    original: string;
  }) => void;
  appendTranslationDelta: (utteranceId: string, delta: string) => void;
  finishTranslation: (utteranceId: string, text: string) => void;
  markImportant: (utteranceId: string, v: boolean) => void;
  reset: () => void;
};

export const useStore = create<State>((set) => ({
  view: 'live',
  meetingId: null,
  isCapturing: false,
  isPaused: false,
  elapsedSec: 0,
  sourceLang: 'ja',
  targetLang: 'en',
  participants: [],
  meetCode: null,
  utterances: [],
  interim: null,
  error: null,

  setView: (view) => set({ view }),
  setLanguages: (s, t) => set({ sourceLang: s, targetLang: t }),
  start: (meetingId) =>
    set({
      meetingId,
      isCapturing: true,
      isPaused: false,
      elapsedSec: 0,
      utterances: [],
      interim: null,
      view: 'live',
      error: null,
    }),
  stop: () => set({ isCapturing: false, isPaused: false, interim: null }),
  pause: () => set({ isPaused: true }),
  resume: () => set({ isPaused: false }),
  tickElapsed: () =>
    set((s) => (s.isCapturing && !s.isPaused ? { elapsedSec: s.elapsedSec + 1 } : {})),
  setError: (error) => set({ error }),
  setMeetContext: (meetCode, participants) => set({ meetCode, participants }),
  setInterim: (interim) => set({ interim }),
  addFinal: (u) =>
    set((s) => ({
      interim: null,
      utterances: [
        ...s.utterances,
        {
          id: u.id,
          speakerId: u.speakerId,
          startMs: u.startMs,
          endMs: u.endMs,
          original: u.original,
          translation: '',
          translationInProgress: true,
        },
      ],
    })),
  appendTranslationDelta: (utteranceId, delta) =>
    set((s) => ({
      utterances: s.utterances.map((u) =>
        u.id === utteranceId
          ? { ...u, translation: u.translation + delta, translationInProgress: true }
          : u,
      ),
    })),
  finishTranslation: (utteranceId, text) =>
    set((s) => ({
      utterances: s.utterances.map((u) =>
        u.id === utteranceId ? { ...u, translation: text, translationInProgress: false } : u,
      ),
    })),
  markImportant: (utteranceId, v) =>
    set((s) => ({
      utterances: s.utterances.map((u) =>
        u.id === utteranceId ? { ...u, isImportant: v } : u,
      ),
    })),
  reset: () =>
    set({
      meetingId: null,
      isCapturing: false,
      isPaused: false,
      elapsedSec: 0,
      utterances: [],
      interim: null,
      error: null,
      view: 'live',
    }),
}));

/**
 * Message contracts between content script, background, and sidebar.
 */

export type ExtMsg =
  | {
      kind: 'start-capture';
      meetingId: string;
      wsUrl: string;
      jwt: string;
      sourceLang: string;
      targetLang: string;
    }
  | { kind: 'stop-capture' }
  | { kind: 'pause-capture' }
  | { kind: 'resume-capture' }
  | { kind: 'capture-started'; tabId: number }
  | { kind: 'capture-error'; error: string }
  | { kind: 'capture-ended'; durationSec: number }
  | {
      kind: 'transcript-event';
      event:
        | {
            type: 'interim';
            speaker_id: string;
            text: string;
            start_ms: number;
            end_ms: number;
          }
        | {
            type: 'final';
            utterance_id: string;
            speaker_id: string;
            text: string;
            start_ms: number;
            end_ms: number;
            detected_language?: string | null;
          }
        | { type: 'translation-delta'; utterance_id: string; delta: string }
        | {
            type: 'translation-done';
            utterance_id: string;
            text: string;
            start_ms: number;
            end_ms: number;
          }
        | { type: 'ready'; meeting_id: string }
        | { type: 'ended'; duration_s: number }
        | { type: 'error'; code: string }
        | { type: 'translation-failed'; utterance_id: string; reason: string };
    }
  | { kind: 'meet-context'; meetCode: string | null; participants: string[] };

export const EXT_MSG_CHANNEL = 'meetingmate::ext';

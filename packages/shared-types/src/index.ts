/**
 * Types shared between the extension, the web dashboard, and anywhere else in
 * TS-land that talks to the MeetingMate API.
 */

export type Language = 'ja' | 'en' | 'ko' | 'zh' | 'es' | 'fr' | 'de';

export type MeetingStatus = 'recording' | 'processing' | 'complete' | 'failed';

export interface ActionItem {
  owner?: string;
  task?: string;
  deadline?: string | null;
}

export interface GlossaryEntry {
  term: string;
  pronunciation?: string;
  meaning?: string;
  example?: string;
}

export interface MeetingDTO {
  id: string;
  title: string | null;
  started_at: string | null;
  ended_at: string | null;
  duration_s: number;
  source_language: Language;
  target_language: Language;
  status: MeetingStatus;
  template: string;
  summary: string | null;
  decisions: string[];
  action_items: ActionItem[];
  open_questions: string[];
  glossary: GlossaryEntry[];
}

export interface UtteranceDTO {
  id: string;
  speaker_id: string;
  speaker_name: string | null;
  start_ms: number;
  end_ms: number;
  original_text: string;
  translated_text: string | null;
  confidence: number | null;
  is_important: boolean;
}

export interface WsServerEvent {
  type:
    | 'ready'
    | 'interim'
    | 'final'
    | 'translation-delta'
    | 'translation-done'
    | 'translation-failed'
    | 'ended'
    | 'error';
  [k: string]: unknown;
}

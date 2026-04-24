/**
 * API client used from the sidebar. Tokens come from Clerk's `useAuth().getToken`.
 */

import { config } from '../shared/config';

export type Meeting = {
  id: string;
  title: string | null;
  started_at: string | null;
  ended_at: string | null;
  duration_s: number;
  source_language: string;
  target_language: string;
  status: 'recording' | 'processing' | 'complete' | 'failed';
  template: string;
  summary: string | null;
  decisions: string[];
  action_items: { owner?: string; task?: string; deadline?: string | null }[];
  open_questions: string[];
  glossary: { term: string; pronunciation?: string; meaning?: string; example?: string }[];
};

async function req<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${config.apiBaseUrl}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status}: ${txt || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  async createMeeting(
    token: string,
    body: {
      source_language: string;
      target_language: string;
      google_meet_code?: string | null;
      title?: string;
      template?: string;
    },
  ): Promise<{ meeting_id: string; ws_url: string }> {
    return req('/v1/meetings', token, { method: 'POST', body: JSON.stringify(body) });
  },

  async me(token: string) {
    return req<{
      id: string;
      email: string;
      plan: string;
      preferred_source_lang: string;
      preferred_target_lang: string;
      consent_recording_ack_at: string | null;
    }>('/v1/me', token);
  },

  async ackConsent(token: string) {
    return req<{ ok: true; at: string }>('/v1/me/consent/recording', token, { method: 'POST' });
  },

  async updatePreferences(
    token: string,
    body: { preferred_source_lang?: string; preferred_target_lang?: string },
  ) {
    return req<{ ok: true }>('/v1/me/preferences', token, {
      method: 'PATCH',
      body: JSON.stringify(body),
    });
  },

  async getMeeting(token: string, id: string): Promise<Meeting> {
    return req(`/v1/meetings/${id}`, token);
  },

  async listMeetings(token: string): Promise<{ items: Meeting[] }> {
    return req('/v1/meetings?limit=20', token);
  },

  async markImportant(token: string, meetingId: string, utteranceId: string) {
    return req<{ id: string; is_important: boolean }>(
      `/v1/meetings/${meetingId}/utterances/${utteranceId}/mark-important`,
      token,
      { method: 'POST' },
    );
  },

  async listVocab(token: string) {
    return req<{ items: { term: string; translation?: string; pronunciation?: string }[] }>(
      '/v1/vocabulary',
      token,
    );
  },

  async addVocab(token: string, item: { term: string; translation?: string }) {
    return req<{ items: { term: string; translation?: string }[] }>(
      '/v1/vocabulary',
      token,
      { method: 'POST', body: JSON.stringify(item) },
    );
  },

  async deleteVocab(token: string, term: string) {
    return req<{ items: { term: string }[] }>(
      `/v1/vocabulary/${encodeURIComponent(term)}`,
      token,
      { method: 'DELETE' },
    );
  },

  async search(token: string, q: string) {
    return req<{ items: Array<Record<string, unknown>> }>(
      `/v1/search?q=${encodeURIComponent(q)}`,
      token,
    );
  },

  async usage(token: string) {
    return req<{ minutes_today: number; minutes_limit: number; plan: string }>(
      '/v1/usage/current',
      token,
    );
  },

  async chatStream(
    token: string,
    meetingId: string,
    message: string,
    onDelta: (chunk: string) => void,
  ): Promise<void> {
    const res = await fetch(`${config.apiBaseUrl}/v1/meetings/${meetingId}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ message }),
    });
    if (!res.ok || !res.body) throw new Error(`chat ${res.status}`);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const parts = buf.split('\n\n');
      buf = parts.pop() ?? '';
      for (const part of parts) {
        if (part.startsWith('data: ')) onDelta(part.slice(6));
      }
    }
  },
};

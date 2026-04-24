/**
 * Build-time config derived from Vite env. In dev these point to localhost; prod
 * points at api.meetingmate.app.
 */

const API_BASE =
  (import.meta as { env?: Record<string, string> }).env?.VITE_API_BASE_URL ??
  'http://localhost:8000';
const WS_BASE = API_BASE.replace(/^http/, 'ws');

export const config = {
  apiBaseUrl: API_BASE,
  wsBaseUrl: WS_BASE,
  webBaseUrl:
    (import.meta as { env?: Record<string, string> }).env?.VITE_WEB_BASE_URL ??
    'http://localhost:3000',
  clerkPublishableKey:
    (import.meta as { env?: Record<string, string> }).env?.VITE_CLERK_PUBLISHABLE_KEY ?? '',
};

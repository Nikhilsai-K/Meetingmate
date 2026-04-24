import { defineManifest } from '@crxjs/vite-plugin';
import pkg from './package.json' assert { type: 'json' };

// Manifest V3 — narrow host permissions (Google Meet only), explicit per-permission
// justifications in docs/PERMISSIONS.md.

export default defineManifest({
  manifest_version: 3,
  name: 'MeetingMate — Live Translation for Google Meet',
  short_name: 'MeetingMate',
  description:
    'Live Japanese ↔ English translation and AI-generated notes for Google Meet. Built for foreign workers in Japan.',
  version: pkg.version,
  minimum_chrome_version: '120',
  action: {
    default_title: 'MeetingMate',
    default_icon: {
      16: 'icons/icon-16.png',
      32: 'icons/icon-32.png',
      48: 'icons/icon-48.png',
      128: 'icons/icon-128.png',
    },
  },
  icons: {
    16: 'icons/icon-16.png',
    32: 'icons/icon-32.png',
    48: 'icons/icon-48.png',
    128: 'icons/icon-128.png',
  },
  background: {
    service_worker: 'src/background/service-worker.ts',
    type: 'module',
  },
  content_scripts: [
    {
      matches: ['https://meet.google.com/*'],
      js: ['src/content/content-script.ts'],
      run_at: 'document_idle',
    },
  ],
  permissions: ['activeTab', 'storage', 'scripting', 'tabCapture'],
  host_permissions: ['https://meet.google.com/*'],
  content_security_policy: {
    extension_pages:
      "script-src 'self' 'wasm-unsafe-eval'; object-src 'self'; connect-src 'self' https://api.meetingmate.app wss://api.meetingmate.app https://clerk.meetingmate.app http://localhost:8000 ws://localhost:8000;",
  },
  web_accessible_resources: [
    {
      resources: ['src/sidebar/index.html', 'src/audio/worklet.js', 'assets/*', 'icons/*'],
      matches: ['https://meet.google.com/*'],
    },
  ],
});

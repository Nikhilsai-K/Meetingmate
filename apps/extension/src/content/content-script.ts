/**
 * Content script — runs in the page context of meet.google.com.
 *
 *  - injects a floating "Open MeetingMate" button.
 *  - opens/closes the sidebar iframe.
 *  - bridges messages between the sidebar iframe (postMessage) and the service
 *    worker (chrome.runtime.sendMessage).
 *  - scrapes participant names for Phase 2 speaker-name mapping.
 */

import { EXT_MSG_CHANNEL, type ExtMsg } from '../shared/messages';

const HOST_ID = 'meetingmate-root';
const SIDEBAR_IFRAME_ID = 'meetingmate-sidebar-iframe';
const LAUNCHER_ID = 'meetingmate-launcher';

function getMeetCode(): string | null {
  const match = location.pathname.match(/^\/([a-z]{3}-[a-z]{4}-[a-z]{3})(?:$|\?)/i);
  return match ? match[1] : null;
}

function scrapeParticipants(): string[] {
  const names = new Set<string>();
  // Google Meet DOM changes constantly; we target multiple heuristics.
  document
    .querySelectorAll<HTMLElement>('[data-self-name], [data-participant-id] [jsname]')
    .forEach((el) => {
      const t = el.getAttribute('data-self-name') || el.innerText;
      if (t && t.trim().length > 0 && t.trim().length < 80) names.add(t.trim());
    });
  document
    .querySelectorAll<HTMLElement>('[role="listitem"] [class*="participant"]')
    .forEach((el) => {
      const t = el.innerText?.trim();
      if (t && t.length > 0 && t.length < 80) names.add(t);
    });
  return Array.from(names).slice(0, 50);
}

function ensureHost(): HTMLElement {
  let host = document.getElementById(HOST_ID);
  if (!host) {
    host = document.createElement('div');
    host.id = HOST_ID;
    host.style.cssText = 'all: initial; position: fixed; z-index: 2147483647;';
    document.documentElement.appendChild(host);
  }
  return host;
}

function openSidebar(): HTMLIFrameElement {
  const host = ensureHost();
  let iframe = document.getElementById(SIDEBAR_IFRAME_ID) as HTMLIFrameElement | null;
  if (iframe) return iframe;
  iframe = document.createElement('iframe');
  iframe.id = SIDEBAR_IFRAME_ID;
  iframe.src = chrome.runtime.getURL('src/sidebar/index.html');
  iframe.allow = 'clipboard-read; clipboard-write';
  iframe.style.cssText = [
    'position: fixed',
    'top: 0',
    'right: 0',
    'width: 420px',
    'height: 100vh',
    'border: none',
    'background: transparent',
    'box-shadow: -8px 0 32px rgba(0,0,0,0.35)',
    'z-index: 2147483647',
    'color-scheme: dark',
  ].join('; ');
  host.appendChild(iframe);
  return iframe;
}

function closeSidebar() {
  document.getElementById(SIDEBAR_IFRAME_ID)?.remove();
}

function addLauncher() {
  if (document.getElementById(LAUNCHER_ID)) return;
  const btn = document.createElement('button');
  btn.id = LAUNCHER_ID;
  btn.textContent = 'MeetingMate';
  btn.setAttribute('aria-label', 'Open MeetingMate sidebar');
  btn.style.cssText = [
    'all: initial',
    'position: fixed',
    'bottom: 96px',
    'right: 20px',
    'z-index: 2147483646',
    'background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
    'color: white',
    'font-family: Inter, system-ui, sans-serif',
    'font-weight: 600',
    'font-size: 14px',
    'padding: 12px 16px',
    'border-radius: 999px',
    'cursor: pointer',
    'box-shadow: 0 12px 28px rgba(37, 99, 235, 0.35)',
  ].join('; ');
  btn.addEventListener('click', () => {
    openSidebar();
  });
  document.body.appendChild(btn);
}

function forwardToSidebar(msg: ExtMsg) {
  const iframe = document.getElementById(SIDEBAR_IFRAME_ID) as HTMLIFrameElement | null;
  iframe?.contentWindow?.postMessage({ channel: EXT_MSG_CHANNEL, msg }, '*');
}

// Handle messages coming from background
chrome.runtime.onMessage.addListener((msg: ExtMsg, _sender, sendResponse) => {
  forwardToSidebar(msg);
  sendResponse({ ok: true });
  return true;
});

// Handle messages coming from sidebar iframe via postMessage
window.addEventListener('message', (ev: MessageEvent) => {
  const data = ev.data as { channel?: string; msg?: ExtMsg } | undefined;
  if (!data || data.channel !== EXT_MSG_CHANNEL || !data.msg) return;

  const msg = data.msg;
  if (msg.kind === 'start-capture') {
    // Sidebar had a user click; relay to background right away so the user-gesture
    // context is preserved for chrome.tabCapture.capture.
    chrome.runtime.sendMessage(msg, (res) => {
      if (!res?.ok) forwardToSidebar({ kind: 'capture-error', error: res?.error ?? 'start_failed' });
    });
  } else if (msg.kind === 'stop-capture' || msg.kind === 'pause-capture' || msg.kind === 'resume-capture') {
    chrome.runtime.sendMessage(msg);
  }
});

// Periodically publish meet context to sidebar
setInterval(() => {
  forwardToSidebar({
    kind: 'meet-context',
    meetCode: getMeetCode(),
    participants: scrapeParticipants(),
  });
}, 5_000);

addLauncher();

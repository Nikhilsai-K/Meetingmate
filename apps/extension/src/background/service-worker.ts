/**
 * MV3 service worker.
 *
 * Responsibilities:
 *  - handle `start-capture` from content script → call `chrome.tabCapture.capture`
 *    (must remain synchronous inside the user-gesture window).
 *  - run the captured MediaStream through the AudioWorklet downsampler.
 *  - pipe 100ms PCM frames to backend WebSocket.
 *  - forward server events to the sidebar iframe (via content script).
 *  - on stop → close WS + flush + notify sidebar.
 */

import type { ExtMsg } from '../shared/messages';

type CaptureState = {
  tabId: number;
  stream: MediaStream | null;
  audioCtx: AudioContext | null;
  workletNode: AudioWorkletNode | null;
  ws: WebSocket | null;
  startedAt: number;
  paused: boolean;
};

let state: CaptureState | null = null;

async function postToTab(tabId: number, msg: ExtMsg): Promise<void> {
  try {
    await chrome.tabs.sendMessage(tabId, msg);
  } catch (e) {
    // tab may have closed
    console.warn('[mm-bg] postToTab failed', e);
  }
}

function teardown(notifyTabId?: number) {
  if (!state) return;
  try {
    state.workletNode?.disconnect();
    state.audioCtx?.close();
    state.stream?.getTracks().forEach((t) => t.stop());
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      try {
        state.ws.send(JSON.stringify({ type: 'end' }));
      } catch {
        /* noop */
      }
      state.ws.close(1000, 'client_stop');
    }
  } catch (e) {
    console.warn('[mm-bg] teardown error', e);
  }
  const duration = Math.floor((Date.now() - state.startedAt) / 1000);
  const tab = notifyTabId ?? state.tabId;
  state = null;
  if (tab) void postToTab(tab, { kind: 'capture-ended', durationSec: duration });
}

async function startCapture(
  tabId: number,
  wsUrl: string,
  jwt: string,
): Promise<void> {
  // NOTE: `tabCapture.capture` MUST be called immediately after the user-gesture
  // message arrives. Do not await anything before it.
  const stream: MediaStream = await new Promise((resolve, reject) => {
    chrome.tabCapture.capture(
      { audio: true, video: false },
      (s) => {
        if (chrome.runtime.lastError || !s) {
          reject(new Error(chrome.runtime.lastError?.message ?? 'capture_failed'));
        } else {
          resolve(s);
        }
      },
    );
  });

  const audioCtx = new AudioContext({ sampleRate: 48000 });
  const workletUrl = chrome.runtime.getURL('src/audio/worklet.js');
  await audioCtx.audioWorklet.addModule(workletUrl);
  const source = audioCtx.createMediaStreamSource(stream);
  const workletNode = new AudioWorkletNode(audioCtx, 'meetingmate-downsampler');
  source.connect(workletNode);
  // Important: do NOT connect worklet to destination — it would route audio to
  // the user's speakers twice. The captured stream is already playing in the tab.

  const ws = new WebSocket(wsUrl, ['meetingmate.v1', `bearer.${jwt}`]);
  ws.binaryType = 'arraybuffer';

  state = {
    tabId,
    stream,
    audioCtx,
    workletNode,
    ws,
    startedAt: Date.now(),
    paused: false,
  };

  ws.addEventListener('open', () => {
    workletNode.port.onmessage = (ev: MessageEvent<ArrayBuffer>) => {
      if (!state || state.paused) return;
      if (ws.readyState === WebSocket.OPEN) ws.send(ev.data);
    };
  });

  ws.addEventListener('message', (ev) => {
    if (!state) return;
    let parsed: unknown;
    try {
      parsed =
        typeof ev.data === 'string' ? JSON.parse(ev.data) : JSON.parse(new TextDecoder().decode(ev.data as ArrayBuffer));
    } catch {
      return;
    }
    void postToTab(state.tabId, {
      kind: 'transcript-event',
      event: parsed as ExtMsg extends { kind: 'transcript-event' }
        ? ExtMsg['event']
        : never,
    });
  });

  ws.addEventListener('close', () => {
    if (state) teardown();
  });

  ws.addEventListener('error', (e) => {
    console.error('[mm-bg] ws error', e);
    if (state) void postToTab(state.tabId, { kind: 'capture-error', error: 'ws_error' });
  });

  // Detect the captured tab being closed and stop
  stream.getAudioTracks()[0]?.addEventListener('ended', () => {
    if (state) teardown();
  });

  void postToTab(tabId, { kind: 'capture-started', tabId });
}

chrome.runtime.onMessage.addListener((msg: ExtMsg, sender, sendResponse) => {
  (async () => {
    try {
      if (msg.kind === 'start-capture') {
        const tabId = sender.tab?.id;
        if (!tabId) throw new Error('no_tab');
        await startCapture(tabId, msg.wsUrl, msg.jwt);
        sendResponse({ ok: true });
      } else if (msg.kind === 'stop-capture') {
        teardown();
        sendResponse({ ok: true });
      } else if (msg.kind === 'pause-capture') {
        if (state) state.paused = true;
        sendResponse({ ok: true });
      } else if (msg.kind === 'resume-capture') {
        if (state) state.paused = false;
        sendResponse({ ok: true });
      } else {
        sendResponse({ ok: false, error: 'unknown_msg' });
      }
    } catch (e) {
      const err = e instanceof Error ? e.message : String(e);
      console.error('[mm-bg] handler error', err);
      if (sender.tab?.id)
        void postToTab(sender.tab.id, { kind: 'capture-error', error: err });
      sendResponse({ ok: false, error: err });
    }
  })();
  return true; // keep channel open for async sendResponse
});

// Cleanup on extension update / reload
chrome.runtime.onSuspend.addListener(() => teardown());

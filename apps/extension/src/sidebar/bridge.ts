/**
 * Bridge between the sidebar iframe and the content script / background.
 *
 * Sidebar -> outgoing: window.parent.postMessage({channel, msg})
 * Sidebar <- incoming: listen for `message` events from parent.
 */

import { EXT_MSG_CHANNEL, type ExtMsg } from '../shared/messages';

type Listener = (msg: ExtMsg) => void;

const listeners = new Set<Listener>();

window.addEventListener('message', (ev: MessageEvent) => {
  const data = ev.data as { channel?: string; msg?: ExtMsg } | undefined;
  if (!data || data.channel !== EXT_MSG_CHANNEL || !data.msg) return;
  for (const l of listeners) l(data.msg);
});

export function onMessage(l: Listener): () => void {
  listeners.add(l);
  return () => listeners.delete(l);
}

export function send(msg: ExtMsg): void {
  window.parent.postMessage({ channel: EXT_MSG_CHANNEL, msg }, '*');
}

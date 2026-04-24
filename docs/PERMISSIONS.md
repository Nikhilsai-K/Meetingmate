# Chrome Web Store permission justifications

Every permission MeetingMate requests is narrow and directly tied to a user-visible feature. The extension does **not** request `<all_urls>` or any broad host permission — it runs only on `https://meet.google.com/*`.

| Permission | Why we request it |
| --- | --- |
| `tabCapture` | **Core feature.** Required to capture the audio of the active Google Meet tab so we can transcribe and translate it in real time. Capture only starts after the user clicks "Start" in our sidebar (a direct user gesture), and is explicitly confirmed by Chrome's native permission prompt. We do not capture video. |
| `activeTab` | To read the current Meet meeting code and participant names after the user clicks our launcher. |
| `storage` | To persist the user's language preferences, pinned vocabulary, Clerk session, and UI state. |
| `scripting` | To inject our sidebar iframe into the Meet page when the user clicks the launcher. |
| `host_permissions: https://meet.google.com/*` | The extension only runs on Google Meet. We do not request access to any other site. |

## Data handling

- **Audio is never persisted.** Captured audio is streamed over a secure WebSocket to the backend and forwarded to Deepgram for transcription. Audio bytes are held in memory only for the duration of the active relay and discarded within 60 seconds of the final utterance. Nothing is written to disk.
- **Transcripts + notes** are stored in Postgres under the user's account, encrypted at rest, and can be deleted any time from the sidebar's History tab.
- **No analytics on transcript content.** Observability systems (Langfuse, Sentry) receive metadata only (meeting id, model, tokens, latency, language).

## Remote code

None. The extension ships all code in its bundle and uses CSP `script-src 'self' 'wasm-unsafe-eval'`. No `eval`, no inline scripts, no remote script loads. Updates are delivered only via the Chrome Web Store.

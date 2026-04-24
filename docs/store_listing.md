# Chrome Web Store listing

## Name
MeetingMate — Live Translation for Google Meet

## Short description (132 char max)
Live Japanese ↔ English translation + AI-generated notes for every Google Meet. Follow every meeting, even when it's not in your language.

## Detailed description
MeetingMate is a privacy-first AI assistant for Google Meet, built for foreign workers attending meetings in a language they don't fully understand.

**What it does**
- **Live transcription** of the meeting in its original language (with speaker labels).
- **Live translation** into your preferred language, shown side-by-side.
- **AI-generated notes** when the meeting ends: summary, key decisions, action items (with owners + deadlines), glossary of technical terms.
- **Ask the meeting** afterwards in plain English — every answer includes timestamped citations.

**How it works**
1. Open a Google Meet tab.
2. Click the MeetingMate launcher (bottom-right corner).
3. Click **Start** in the sidebar. Chrome will ask to share this tab's audio — click Allow.
4. A visible **"AI Assistant Active"** indicator stays in the sidebar for the duration of the meeting so you can mention it to colleagues.
5. When you click **End meeting**, structured notes are ready in ~20 seconds.

**Privacy**
- Audio is processed in real time and never stored. Only transcripts and notes are saved to your account — and you can delete them any time.
- Per-user row-level security on every database row.
- No transcript contents are ever sent to analytics or error-tracking systems.
- Full privacy policy: https://meetingmate.app/privacy

**Languages (launch)**
Source (audio): Japanese, English. Target (translation + notes): Japanese, English. Korean, Chinese, Spanish, French, German coming in Phase 4.

**Pricing**
- Free: 5 meeting-hours/day, 7-day history.
- Pro $12/mo: unlimited hours and history, integrations, export.
- Team $25/user/mo: shared library, admin console, SSO.

## Category
Productivity

## Permission justifications
See `docs/PERMISSIONS.md`. Summary:
- `tabCapture` — capture Google Meet tab audio for transcription.
- `activeTab` — read meeting code and participants after user click.
- `storage` — persist preferences and pinned vocabulary.
- `scripting` — inject the sidebar UI.
- Host permission is limited strictly to `https://meet.google.com/*`.

## Screenshots (1280 × 800, 5 required)
1. `screenshots/01-live-sidebar.png` — Live transcription + translation during a Japanese meeting. Shows "🔴 AI Assistant Active" + timer.
2. `screenshots/02-final-notes.png` — Post-meeting notes: summary, decisions, action items.
3. `screenshots/03-glossary.png` — Glossary with Japanese technical terms and English explanations.
4. `screenshots/04-chat.png` — Ask-the-meeting chat with timestamped citations.
5. `screenshots/05-settings.png` — Pinned vocabulary + usage meter + privacy links.

## Promo video (30s)
`promo/meetingmate-demo.mp4` — joins a Meet, clicks Start, shows ~10s of real-time translation, ends the meeting, zoom on generated notes.

## Support
- Email: support@meetingmate.app
- Privacy: https://meetingmate.app/privacy
- Terms: https://meetingmate.app/terms
- Homepage: https://meetingmate.app

## Single-purpose statement
MeetingMate exists for one purpose: to provide live transcription, translation, and AI-generated notes for Google Meet calls. It does not collect or transmit any data unrelated to this purpose.

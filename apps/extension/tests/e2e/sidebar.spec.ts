import { test, expect, chromium, type BrowserContext } from '@playwright/test';
import path from 'node:path';

const extensionPath = path.resolve(__dirname, '..', '..', 'dist');

// E2E: load the built extension into a real Chromium instance and verify the
// sidebar launcher button is injected when the URL pattern matches.
//
// This test exercises manifest-matching and content-script injection — it does
// not attempt real audio capture (that requires a user-gesture prompt).

test('content script injects launcher on meet.google.com', async () => {
  const context: BrowserContext = await chromium.launchPersistentContext('', {
    headless: false,
    args: [
      '--disable-extensions-except=' + extensionPath,
      '--load-extension=' + extensionPath,
    ],
  });
  try {
    const page = await context.newPage();
    // Go to a fake Meet URL (Google may redirect; we just need the host match).
    await page.goto('https://meet.google.com/abc-defg-hij', { waitUntil: 'domcontentloaded' });
    const launcher = page.locator('#meetingmate-launcher');
    await expect(launcher).toBeVisible({ timeout: 15_000 });
  } finally {
    await context.close();
  }
});

import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';

const extensionPath = path.resolve(__dirname, '..', '..', 'dist');

export default defineConfig({
  testDir: '.',
  timeout: 60_000,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'https://meet.google.com',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium-extension',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: [
            `--disable-extensions-except=${extensionPath}`,
            `--load-extension=${extensionPath}`,
          ],
        },
      },
    },
  ],
});

import '@testing-library/jest-dom/vitest';

// Minimal chrome global for unit tests that touch it.
(globalThis as unknown as { chrome: unknown }).chrome = {
  runtime: {
    sendMessage: () => {},
    onMessage: { addListener: () => {}, removeListener: () => {} },
    getURL: (p: string) => `chrome-extension://test/${p}`,
    lastError: null,
  },
  tabs: { sendMessage: () => {} },
  tabCapture: { capture: () => {} },
};

import React from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ClerkProvider } from '@clerk/chrome-extension';
import { App } from './App';
import { config } from '../shared/config';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

const root = createRoot(document.getElementById('root')!);
root.render(
  <React.StrictMode>
    <ClerkProvider
      publishableKey={config.clerkPublishableKey || 'pk_test_placeholder'}
      syncHost={config.webBaseUrl}
    >
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </ClerkProvider>
  </React.StrictMode>,
);

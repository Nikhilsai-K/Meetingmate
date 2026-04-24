import './globals.css';
import { ClerkProvider } from '@clerk/nextjs';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'MeetingMate — Live translation + AI notes for Google Meet',
  description:
    'Live Japanese ↔ English translation and AI-generated notes for every Google Meet. Built for foreign workers in Japan.',
  metadataBase: new URL('https://meetingmate.app'),
  openGraph: {
    title: 'MeetingMate',
    description: 'Live translation + AI notes for Google Meet.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" className="dark">
        <body className="min-h-screen antialiased">{children}</body>
      </html>
    </ClerkProvider>
  );
}

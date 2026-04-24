import clsx, { type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatElapsed(sec: number): string {
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const s = sec % 60;
  const mm = String(m).padStart(2, '0');
  const ss = String(s).padStart(2, '0');
  if (h > 0) return `${String(h).padStart(2, '0')}:${mm}:${ss}`;
  return `${mm}:${ss}`;
}

export function speakerColor(id: string): string {
  const palette = [
    'text-sky-300',
    'text-emerald-300',
    'text-amber-300',
    'text-fuchsia-300',
    'text-rose-300',
    'text-violet-300',
    'text-teal-300',
  ];
  const n = id.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);
  return palette[n % palette.length];
}

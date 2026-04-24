import { useEffect } from 'react';

export function useKeyboardShortcut(combo: string, handler: () => void) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const parts = combo.toLowerCase().split('+');
      const key = parts[parts.length - 1];
      const wantMeta = parts.includes('mod') || parts.includes('cmd') || parts.includes('ctrl');
      const wantShift = parts.includes('shift');
      const wantAlt = parts.includes('alt');
      if (e.key.toLowerCase() !== key) return;
      if (wantMeta && !(e.metaKey || e.ctrlKey)) return;
      if (wantShift && !e.shiftKey) return;
      if (wantAlt && !e.altKey) return;
      e.preventDefault();
      handler();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [combo, handler]);
}

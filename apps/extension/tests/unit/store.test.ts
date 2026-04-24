import { describe, it, expect, beforeEach } from 'vitest';
import { useStore } from '../../src/sidebar/store';

describe('sidebar store', () => {
  beforeEach(() => useStore.getState().reset());

  it('starts capturing with a meeting id', () => {
    useStore.getState().start('m-1');
    expect(useStore.getState().isCapturing).toBe(true);
    expect(useStore.getState().meetingId).toBe('m-1');
  });

  it('appends finals and streams translation', () => {
    useStore.getState().start('m-1');
    useStore.getState().addFinal({
      id: 'u-1',
      speakerId: '0',
      startMs: 0,
      endMs: 1000,
      original: 'こんにちは',
    });
    useStore.getState().appendTranslationDelta('u-1', 'Hel');
    useStore.getState().appendTranslationDelta('u-1', 'lo');
    useStore.getState().finishTranslation('u-1', 'Hello');
    const u = useStore.getState().utterances[0];
    expect(u.translation).toBe('Hello');
    expect(u.translationInProgress).toBe(false);
  });

  it('drops interim when a final arrives', () => {
    useStore.getState().start('m-1');
    useStore.getState().setInterim({ speakerId: '0', text: 'partial' });
    expect(useStore.getState().interim).not.toBeNull();
    useStore.getState().addFinal({ id: 'u-2', speakerId: '0', startMs: 0, endMs: 500, original: 'a' });
    expect(useStore.getState().interim).toBeNull();
  });

  it('ticks elapsed when capturing and not paused', () => {
    useStore.getState().start('m-1');
    useStore.getState().tickElapsed();
    useStore.getState().tickElapsed();
    expect(useStore.getState().elapsedSec).toBe(2);
    useStore.getState().pause();
    useStore.getState().tickElapsed();
    expect(useStore.getState().elapsedSec).toBe(2);
  });
});

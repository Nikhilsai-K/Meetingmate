// AudioWorkletProcessor: downsamples tab audio to 16kHz mono and emits 100ms
// Int16 PCM frames. Runs on the audio render thread — no blocking work.

class DownsampleProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._inputSampleRate = sampleRate; // worklet-global (typically 48000 on Chrome)
    this._targetSampleRate = 16000;
    this._ratio = this._inputSampleRate / this._targetSampleRate;
    this._samplesPerFrame = Math.round(0.1 * this._targetSampleRate); // 1600 samples = 100ms
    this._buf = new Int16Array(this._samplesPerFrame);
    this._bufIdx = 0;
    this._carry = 0;
  }

  static get parameterDescriptors() {
    return [];
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;
    // Mix down channels to mono
    const channels = input.length;
    const frames = input[0].length;
    if (frames === 0) return true;

    for (let i = 0; i < frames; i++) {
      this._carry += 1;
      if (this._carry < this._ratio) continue;
      this._carry -= this._ratio;

      let sample = 0;
      for (let c = 0; c < channels; c++) sample += input[c][i];
      sample /= channels;
      // clamp + convert to Int16
      const s16 = Math.max(-1, Math.min(1, sample)) * 0x7fff;
      this._buf[this._bufIdx++] = s16 | 0;

      if (this._bufIdx >= this._samplesPerFrame) {
        // Copy buffer so we can keep using the same underlying memory.
        const out = new Int16Array(this._buf);
        this.port.postMessage(out.buffer, [out.buffer]);
        this._buf = new Int16Array(this._samplesPerFrame);
        this._bufIdx = 0;
      }
    }
    return true;
  }
}

registerProcessor('meetingmate-downsampler', DownsampleProcessor);

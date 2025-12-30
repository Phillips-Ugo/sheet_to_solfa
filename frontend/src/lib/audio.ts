/**
 * Web Audio API utilities for playing solfa notes
 */

// Note frequencies (A4 = 440Hz standard)
const NOTE_FREQUENCIES: Record<string, number> = {
  'C3': 130.81, 'D3': 146.83, 'E3': 164.81, 'F3': 174.61, 'G3': 196.00, 'A3': 220.00, 'B3': 246.94,
  'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'F4': 349.23, 'G4': 392.00, 'A4': 440.00, 'B4': 493.88,
  'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46, 'G5': 783.99, 'A5': 880.00, 'B5': 987.77,
  'C6': 1046.50,
};

// Solfa to note mapping (C major default)
const SOLFA_TO_NOTE: Record<string, string> = {
  'd': 'C', 'r': 'D', 'm': 'E', 'f': 'F', 's': 'G', 'l': 'A', 't': 'B',
};

let audioContext: AudioContext | null = null;

/**
 * Initialize or get the audio context
 */
function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  return audioContext;
}

/**
 * Convert solfa syllable to frequency
 */
export function solfaToFrequency(
  syllable: string,
  octave: number = 4,
  keyRoot: string = 'C'
): number {
  const baseSyllable = syllable.toLowerCase().replace(/[',]/g, '');
  const noteName = SOLFA_TO_NOTE[baseSyllable];
  
  if (!noteName) return 0; // Rest or invalid
  
  // Adjust octave based on modifiers
  let adjustedOctave = octave;
  const highCount = (syllable.match(/'/g) || []).length;
  const lowCount = (syllable.match(/,/g) || []).length;
  adjustedOctave += highCount - lowCount;
  
  const noteKey = `${noteName}${adjustedOctave}`;
  return NOTE_FREQUENCIES[noteKey] || NOTE_FREQUENCIES['C4'];
}

/**
 * Play a single note
 */
export function playNote(
  frequency: number,
  duration: number = 0.5,
  volume: number = 0.3,
  waveform: OscillatorType = 'sine'
): void {
  if (frequency === 0) {
    console.log("Skipping rest (frequency=0)");
    return; // Don't play rests
  }
  
  console.log(`Playing note: freq=${frequency.toFixed(2)}Hz, duration=${duration.toFixed(2)}s`);
  
  const ctx = getAudioContext();
  const oscillator = ctx.createOscillator();
  const gainNode = ctx.createGain();
  
  oscillator.connect(gainNode);
  gainNode.connect(ctx.destination);
  
  oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);
  oscillator.type = waveform;
  
  // ADSR envelope for nicer sound
  gainNode.gain.setValueAtTime(0, ctx.currentTime);
  gainNode.gain.linearRampToValueAtTime(volume, ctx.currentTime + 0.05); // Attack
  gainNode.gain.linearRampToValueAtTime(volume * 0.7, ctx.currentTime + 0.1); // Decay to sustain
  gainNode.gain.linearRampToValueAtTime(0, ctx.currentTime + duration); // Release
  
  oscillator.start(ctx.currentTime);
  oscillator.stop(ctx.currentTime + duration + 0.1);
}

/**
 * Play a solfa note
 */
export function playSolfaNote(
  syllable: string,
  octave: number = 4,
  durationBeats: number = 1,
  tempo: number = 120
): void {
  console.log(`playSolfaNote: syllable="${syllable}", octave=${octave}, duration=${durationBeats}, tempo=${tempo}`);
  const frequency = solfaToFrequency(syllable, octave);
  const durationSeconds = (durationBeats * 60) / tempo;
  console.log(`  -> frequency=${frequency}, durationSeconds=${durationSeconds.toFixed(2)}`);
  playNote(frequency, durationSeconds);
}

/**
 * Play a sequence of notes
 */
export async function playSequence(
  notes: Array<{ syllable: string; octave?: number; duration?: number; isRest?: boolean }>,
  tempo: number = 120
): Promise<void> {
  for (const note of notes) {
    // Skip rests
    if (note.isRest || !note.syllable || note.syllable.trim() === '' || note.syllable === '0') {
      console.log("Skipping rest or invalid note:", note);
      const durationBeats = note.duration || 1;
      const durationMs = (durationBeats * 60 * 1000) / tempo;
      await new Promise(resolve => setTimeout(resolve, durationMs));
      continue;
    }
    
    const octave = note.octave || 4;
    const durationBeats = note.duration || 1;
    const durationMs = (durationBeats * 60 * 1000) / tempo;
    
    console.log(`Playing note in sequence: ${note.syllable}`);
    playSolfaNote(note.syllable, octave, durationBeats, tempo);
    
    await new Promise(resolve => setTimeout(resolve, durationMs));
  }
}

/**
 * Play a measure
 */
export async function playMeasure(
  notes: Array<{ syllable: string; octave?: number; duration?: number }>,
  tempo: number = 120
): Promise<void> {
  return playSequence(notes, tempo);
}

/**
 * Check if Web Audio API is available
 */
export function isAudioAvailable(): boolean {
  return typeof window !== 'undefined' && 
    !!(window.AudioContext || (window as any).webkitAudioContext);
}

/**
 * Resume audio context (required after user interaction)
 */
export async function resumeAudio(): Promise<void> {
  const ctx = getAudioContext();
  if (ctx.state === 'suspended') {
    await ctx.resume();
  }
}


/**
 * Solfa Color System
 * 
 * Each solfa syllable has a semantically meaningful color based on
 * its musical function and position in the scale.
 */

export type SolfaSyllable = 'd' | 'r' | 'm' | 'f' | 's' | 'l' | 't' | '0';

export interface SolfaColorInfo {
  syllable: SolfaSyllable;
  name: string;
  fullName: string;
  color: string;
  bgColor: string;
  meaning: string;
  scaleDegree: number;
}

// Color palette inspired by chromesthesia and music theory
export const SOLFA_COLORS: Record<SolfaSyllable, SolfaColorInfo> = {
  'd': {
    syllable: 'd',
    name: 'Do',
    fullName: 'Do (Tonic)',
    color: '#dc2626', // Red - home, stability
    bgColor: '#fef2f2',
    meaning: 'Tonic - home base',
    scaleDegree: 1,
  },
  'r': {
    syllable: 'r',
    name: 'Re',
    fullName: 'Re (Supertonic)',
    color: '#ea580c', // Orange - moving forward
    bgColor: '#fff7ed',
    meaning: 'Supertonic - second degree',
    scaleDegree: 2,
  },
  'm': {
    syllable: 'm',
    name: 'Mi',
    fullName: 'Mi (Mediant)',
    color: '#ca8a04', // Yellow/Gold - brightness
    bgColor: '#fefce8',
    meaning: 'Mediant - major/minor character',
    scaleDegree: 3,
  },
  'f': {
    syllable: 'f',
    name: 'Fa',
    fullName: 'Fa (Subdominant)',
    color: '#16a34a', // Green - nature, balance
    bgColor: '#f0fdf4',
    meaning: 'Subdominant - fourth degree',
    scaleDegree: 4,
  },
  's': {
    syllable: 's',
    name: 'Sol',
    fullName: 'Sol (Dominant)',
    color: '#2563eb', // Blue - dominant, strong
    bgColor: '#eff6ff',
    meaning: 'Dominant - fifth degree',
    scaleDegree: 5,
  },
  'l': {
    syllable: 'l',
    name: 'La',
    fullName: 'La (Submediant)',
    color: '#7c3aed', // Indigo/Violet - relative minor
    bgColor: '#f5f3ff',
    meaning: 'Submediant - sixth degree',
    scaleDegree: 6,
  },
  't': {
    syllable: 't',
    name: 'Ti',
    fullName: 'Ti (Leading Tone)',
    color: '#c026d3', // Magenta - tension, leading
    bgColor: '#fdf4ff',
    meaning: 'Leading tone - wants to resolve',
    scaleDegree: 7,
  },
  '0': {
    syllable: '0',
    name: 'Rest',
    fullName: 'Rest (Silence)',
    color: '#6b7280', // Gray - silence
    bgColor: '#f9fafb',
    meaning: 'Silence',
    scaleDegree: 0,
  },
};

/**
 * Get color info for a solfa syllable
 */
export function getSolfaColor(syllable: string): SolfaColorInfo {
  const normalized = syllable.toLowerCase().replace(/[',.]/g, '');
  const key = normalized as SolfaSyllable;
  return SOLFA_COLORS[key] || SOLFA_COLORS['0'];
}

/**
 * Parse a syllable string to extract base syllable and octave modifier
 */
export function parseSolfaSyllable(text: string): {
  syllable: SolfaSyllable;
  octaveModifier: string;
  isEighth: boolean;
} {
  const isEighth = text.startsWith('(') && text.endsWith(')');
  const cleaned = text.replace(/[()]/g, '');
  
  // Extract octave modifiers (apostrophes for high, commas for low)
  const octaveMatch = cleaned.match(/([']+|[,]+)$/);
  const octaveModifier = octaveMatch ? octaveMatch[0] : '';
  
  // Get base syllable
  const baseSyllable = cleaned.replace(/[',.]/g, '').toLowerCase();
  const syllable = (baseSyllable === '-' ? '0' : baseSyllable) as SolfaSyllable;
  
  return {
    syllable: SOLFA_COLORS[syllable] ? syllable : '0',
    octaveModifier,
    isEighth,
  };
}

/**
 * Duration type for rhythm visualization
 */
export type DurationType = 'whole' | 'half' | 'quarter' | 'eighth' | 'sixteenth';

/**
 * Get width multiplier based on note duration
 */
export function getDurationWidth(durationBeats: number): number {
  if (durationBeats >= 4) return 4; // whole note
  if (durationBeats >= 2) return 2; // half note
  if (durationBeats >= 1) return 1; // quarter note
  if (durationBeats >= 0.5) return 0.5; // eighth note
  return 0.25; // sixteenth note
}

/**
 * Get duration type from beats
 */
export function getDurationType(durationBeats: number): DurationType {
  if (durationBeats >= 4) return 'whole';
  if (durationBeats >= 2) return 'half';
  if (durationBeats >= 1) return 'quarter';
  if (durationBeats >= 0.5) return 'eighth';
  return 'sixteenth';
}

/**
 * CSS class names for duration types
 */
export const DURATION_CLASSES: Record<DurationType, string> = {
  whole: 'w-24',
  half: 'w-16',
  quarter: 'w-10',
  eighth: 'w-6',
  sixteenth: 'w-4',
};


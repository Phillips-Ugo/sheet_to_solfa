"use client";

import React, { useState, useEffect, useMemo } from "react";
import { Copy, Check, Play, Pause, ZoomIn, ZoomOut, Printer } from "lucide-react";
import MeasureBar, { type MeasureData } from "./solfa/MeasureBar";
import SolfaLegend from "./solfa/SolfaLegend";
import { type SolfaNoteData } from "./solfa/SolfaNote";
import { playSolfaNote, playMeasure, resumeAudio, isAudioAvailable } from "@/lib/audio";

// Types for structured solfa data
export interface StructuredMeasure {
  number: number;
  text?: string;
  notes: Array<{
    syllable: string;
    octave_modifier?: string;
    duration?: number;
    is_rest?: boolean;
    display?: string;
  }>;
}

export interface StructuredSolfaData {
  measures: StructuredMeasure[];
}

interface SolfaDisplayProps {
  text: string;
  keySignature: string;
  timeSignature: string;
  measureCount: number;
  structuredData?: StructuredSolfaData;
}

type ZoomLevel = 'sm' | 'md' | 'lg' | 'xl';

export default function SolfaDisplay({
  text,
  keySignature,
  timeSignature,
  measureCount,
  structuredData,
}: SolfaDisplayProps) {
  const [copied, setCopied] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentMeasure, setCurrentMeasure] = useState<number | null>(null);
  const [zoom, setZoom] = useState<ZoomLevel>('md');
  const [showLegend, setShowLegend] = useState(true);
  const [animate, setAnimate] = useState(true);
  
  // Parse time signature for beats per measure
  const beatsPerMeasure = useMemo(() => {
    const parts = timeSignature.split('/');
    return parseInt(parts[0]) || 4;
  }, [timeSignature]);
  
  // Convert structured data or parse from text
  const measures: MeasureData[] = useMemo(() => {
    if (structuredData?.measures) {
      return structuredData.measures.map((m) => ({
        number: m.number,
        beatsPerMeasure,
        notes: m.notes.map((n) => ({
          syllable: n.display || n.syllable + (n.octave_modifier || ''),
          duration: n.duration || 1,
          isRest: n.is_rest || false,
        })),
      }));
    }
    
    // Fallback: parse from plain text
    return parseTextToMeasures(text, beatsPerMeasure);
  }, [structuredData, text, beatsPerMeasure]);
  
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  const handlePrint = () => {
    window.print();
  };
  
  const handleNoteClick = async (note: SolfaNoteData) => {
    await resumeAudio();
    playSolfaNote(note.syllable, 4, note.duration || 1, 120);
  };
  
  const handlePlayAll = async () => {
    if (!isAudioAvailable()) return;
    
    setIsPlaying(true);
    await resumeAudio();
    
    for (let i = 0; i < measures.length; i++) {
      if (!isPlaying) break;
      
      setCurrentMeasure(measures[i].number);
      await playMeasure(measures[i].notes, 120);
    }
    
    setCurrentMeasure(null);
    setIsPlaying(false);
  };
  
  const handleStop = () => {
    setIsPlaying(false);
    setCurrentMeasure(null);
  };
  
  const cycleZoom = (direction: 'in' | 'out') => {
    const levels: ZoomLevel[] = ['sm', 'md', 'lg', 'xl'];
    const currentIndex = levels.indexOf(zoom);
    if (direction === 'in' && currentIndex < levels.length - 1) {
      setZoom(levels[currentIndex + 1]);
    } else if (direction === 'out' && currentIndex > 0) {
      setZoom(levels[currentIndex - 1]);
    }
  };
  
  // Disable animation after initial render
  useEffect(() => {
    const timer = setTimeout(() => setAnimate(false), 2000);
    return () => clearTimeout(timer);
  }, []);
  
  return (
    <div className="w-full space-y-6">
      {/* Header info cards */}
      <div className="flex flex-wrap gap-3">
        <div className="bg-gradient-to-r from-staff-100 to-staff-50 px-5 py-3 rounded-xl shadow-sm border border-staff-200">
          <span className="text-ink-400 text-sm">Key</span>
          <div className="font-semibold text-ink-800 text-lg">{keySignature}</div>
        </div>
        <div className="bg-gradient-to-r from-staff-100 to-staff-50 px-5 py-3 rounded-xl shadow-sm border border-staff-200">
          <span className="text-ink-400 text-sm">Time</span>
          <div className="font-semibold text-ink-800 text-lg">{timeSignature}</div>
        </div>
        <div className="bg-gradient-to-r from-staff-100 to-staff-50 px-5 py-3 rounded-xl shadow-sm border border-staff-200">
          <span className="text-ink-400 text-sm">Measures</span>
          <div className="font-semibold text-ink-800 text-lg">{measureCount}</div>
        </div>
      </div>

      {/* Main notation display */}
      <div className="bg-white rounded-2xl border border-ink-200 shadow-lg overflow-hidden">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-ink-100 bg-ink-50 no-print">
          <div className="flex items-center gap-2">
            {isAudioAvailable() && (
              <button
                onClick={isPlaying ? handleStop : handlePlayAll}
                className="flex items-center gap-2 px-4 py-2 bg-staff-500 text-white rounded-lg hover:bg-staff-600 transition-colors"
              >
                {isPlaying ? (
                  <>
                    <Pause className="w-4 h-4" /> Stop
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" /> Play All
                  </>
                )}
              </button>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {/* Zoom controls */}
            <button
              onClick={() => cycleZoom('out')}
              className="p-2 text-ink-400 hover:text-ink-600 hover:bg-ink-100 rounded-lg transition-colors"
              title="Zoom out"
              disabled={zoom === 'sm'}
            >
              <ZoomOut className="w-5 h-5" />
            </button>
            <span className="text-sm text-ink-500 w-8 text-center">{zoom.toUpperCase()}</span>
            <button
              onClick={() => cycleZoom('in')}
              className="p-2 text-ink-400 hover:text-ink-600 hover:bg-ink-100 rounded-lg transition-colors"
              title="Zoom in"
              disabled={zoom === 'xl'}
            >
              <ZoomIn className="w-5 h-5" />
            </button>
            
            <div className="w-px h-6 bg-ink-200 mx-2" />
            
            {/* Print */}
            <button
              onClick={handlePrint}
              className="p-2 text-ink-400 hover:text-ink-600 hover:bg-ink-100 rounded-lg transition-colors"
              title="Print"
            >
              <Printer className="w-5 h-5" />
            </button>
            
            {/* Copy */}
            <button
              onClick={handleCopy}
              className="p-2 text-ink-400 hover:text-ink-600 hover:bg-ink-100 rounded-lg transition-colors"
              title="Copy to clipboard"
            >
              {copied ? (
                <Check className="w-5 h-5 text-green-500" />
              ) : (
                <Copy className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>

        {/* Notation content */}
        <div className={`p-6 overflow-x-auto zoom-container zoom-${zoom}`}>
          {/* Measures grid */}
          <div className="flex flex-wrap gap-y-8">
            {measures.map((measure, index) => (
              <div 
                key={measure.number}
                className={`
                  transition-all duration-200
                  ${currentMeasure === measure.number ? 'ring-2 ring-staff-400 ring-offset-2 rounded-lg' : ''}
                `}
                style={{ 
                  width: `${100 / Math.min(measures.length, 4)}%`,
                  minWidth: '200px',
                }}
              >
                <MeasureBar
                  measure={measure}
                  showMeasureNumber={true}
                  animate={animate}
                  baseDelay={index * 100}
                  onNoteClick={(note) => handleNoteClick(note)}
                />
              </div>
            ))}
          </div>
          
          {/* Empty state */}
          {measures.length === 0 && (
            <div className="text-center py-12 text-ink-400">
              <p>No measures to display</p>
            </div>
          )}
        </div>
        
        {/* Plain text fallback (for accessibility and copying) */}
        <details className="border-t border-ink-100 no-print">
          <summary className="px-4 py-2 text-sm text-ink-500 cursor-pointer hover:bg-ink-50">
            View as plain text
          </summary>
          <pre className="p-4 bg-ink-50 text-ink-700 text-sm font-mono whitespace-pre-wrap overflow-x-auto">
            {text}
          </pre>
        </details>
      </div>

      {/* Legend */}
      {showLegend && (
        <SolfaLegend
          compact={false}
          interactive={true}
          onSyllableClick={(syllable) => {
            resumeAudio();
            playSolfaNote(syllable, 4, 1, 120);
          }}
        />
      )}
    </div>
  );
}

/**
 * Parse plain text solfa notation into measure data
 */
function parseTextToMeasures(text: string, beatsPerMeasure: number): MeasureData[] {
  const measures: MeasureData[] = [];
  const lines = text.split('\n');
  
  let measureNumber = 1;
  
  for (const line of lines) {
    // Skip header lines
    if (line.startsWith('#') || line.startsWith('Key:') || line.startsWith('Time') || 
        line.startsWith('Measures:') || line.startsWith('-') || line.startsWith('Generated:') ||
        !line.trim()) {
      continue;
    }
    
    // Parse measure lines (format: | d r m f | s l t d' |)
    if (line.includes('|')) {
      const measureTexts = line.split('|').filter(m => m.trim());
      
      for (const measureText of measureTexts) {
        const noteTokens = measureText.trim().split(/\s+/).filter(t => t);
        const notes: SolfaNoteData[] = [];
        
        for (const token of noteTokens) {
          // Handle held notes (dashes)
          if (token === '-') {
            // Extend previous note's duration
            if (notes.length > 0) {
              notes[notes.length - 1].duration = (notes[notes.length - 1].duration || 1) + 1;
            }
            continue;
          }
          
          // Handle eighth notes in parentheses
          const isEighth = token.startsWith('(') && token.endsWith(')');
          const cleanToken = token.replace(/[()]/g, '');
          
          notes.push({
            syllable: cleanToken,
            duration: isEighth ? 0.5 : 1,
            isRest: cleanToken === '0',
          });
        }
        
        measures.push({
          number: measureNumber++,
          beatsPerMeasure,
          notes,
        });
      }
    }
  }
  
  return measures;
}

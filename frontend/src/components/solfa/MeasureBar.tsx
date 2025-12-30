"use client";

import React from "react";
import SolfaNote, { type SolfaNoteData } from "./SolfaNote";

export interface MeasureData {
  number: number;
  notes: SolfaNoteData[];
  beatsPerMeasure?: number;
}

interface MeasureBarProps {
  measure: MeasureData;
  showMeasureNumber?: boolean;
  animate?: boolean;
  baseDelay?: number;
  onNoteClick?: (note: SolfaNoteData, measureNumber: number) => void;
}

export default function MeasureBar({
  measure,
  showMeasureNumber = true,
  animate = false,
  baseDelay = 0,
  onNoteClick,
}: MeasureBarProps) {
  const beatsPerMeasure = measure.beatsPerMeasure || 4;
  
  return (
    <div className="measure-container staff-lines-bg relative">
      {/* Measure number */}
      {showMeasureNumber && (
        <span className="measure-number">{measure.number}</span>
      )}
      
      {/* Beat grid with notes */}
      <div className="beat-grid flex-1 flex items-stretch p-1">
        {measure.notes.map((note, noteIndex) => (
          <SolfaNote
            key={`${measure.number}-${noteIndex}`}
            note={note}
            animate={animate}
            animationDelay={baseDelay + noteIndex * 50}
            onClick={() => onNoteClick?.(note, measure.number)}
          />
        ))}
        
        {/* Fill remaining space if measure is incomplete */}
        {measure.notes.length === 0 && (
          <div className="flex-1 flex items-center justify-center text-gray-300">
            <span className="text-sm italic">empty</span>
          </div>
        )}
      </div>
    </div>
  );
}


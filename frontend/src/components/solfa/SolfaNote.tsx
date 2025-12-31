"use client";

import React, { useState } from "react";
import { getSolfaColor, getDurationType, parseSolfaSyllable, type SolfaSyllable } from "@/lib/solfa-colors";

export interface SolfaNoteData {
  syllable: string;
  octave?: number;
  duration?: number;
  isRest?: boolean;
  originalPitch?: string;
}

interface SolfaNoteProps {
  note: SolfaNoteData;
  showTooltip?: boolean;
  animate?: boolean;
  animationDelay?: number;
  onClick?: () => void;
}

export default function SolfaNote({
  note,
  showTooltip = true,
  animate = false,
  animationDelay = 0,
  onClick,
}: SolfaNoteProps) {
  const [isHovered, setIsHovered] = useState(false);
  
  const { syllable, octaveModifier, isEighth } = parseSolfaSyllable(note.syllable);
  const colorInfo = getSolfaColor(syllable);
  const durationType = getDurationType(note.duration || 1);
  const isRest = note.isRest || syllable === '0';
  
  // Duration class for width
  const durationClass = `note-${durationType}`;
  
  // Color class
  const colorClass = `solfa-note-${syllable}`;
  
  // Build octave display
  const renderOctaveModifier = () => {
    if (!octaveModifier) return null;
    
    const isHigh = octaveModifier.includes("'");
    const count = octaveModifier.length;
    
    return (
      <span className={isHigh ? "octave-high" : "octave-low"}>
        {octaveModifier}
      </span>
    );
  };
  
  // Format duration for tooltip
  const formatDuration = (beats: number) => {
    if (beats >= 4) return "whole note";
    if (beats >= 2) return "half note";
    if (beats >= 1) return "quarter note";
    if (beats >= 0.5) return "eighth note";
    return "sixteenth note";
  };
  
  return (
    <div
      className={`
        solfa-note-box ${colorClass} ${durationClass}
        ${isRest ? 'solfa-rest' : ''}
        ${animate ? 'note-animate' : ''}
      `}
      style={{
        animationDelay: animate ? `${animationDelay}ms` : undefined,
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      role="button"
      tabIndex={0}
      aria-label={`${colorInfo.name}${octaveModifier ? ` octave ${octaveModifier}` : ''}, ${formatDuration(note.duration || 1)}`}
    >
      {/* Main syllable display */}
      <span className="flex items-baseline">
        <span className="text-lg font-bold">
          {isRest ? '∅' : syllable}
        </span>
        {renderOctaveModifier()}
      </span>
      
      {/* Eighth note beam indicator */}
      {isEighth && !isRest && <div className="eighth-beam" />}
      
      {/* Tooltip */}
      {showTooltip && (
        <div className="solfa-tooltip">
          <div className="font-semibold">{colorInfo.fullName}</div>
          <div className="text-gray-300 text-xs">
            {formatDuration(note.duration || 1)}
            {note.originalPitch && ` • ${note.originalPitch}`}
          </div>
        </div>
      )}
    </div>
  );
}



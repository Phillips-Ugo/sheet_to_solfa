"use client";

import React, { useState } from "react";
import { SOLFA_COLORS, type SolfaSyllable } from "@/lib/solfa-colors";
import { ChevronDown, ChevronUp } from "lucide-react";

interface SolfaLegendProps {
  compact?: boolean;
  interactive?: boolean;
  onSyllableClick?: (syllable: SolfaSyllable) => void;
}

export default function SolfaLegend({
  compact = false,
  interactive = true,
  onSyllableClick,
}: SolfaLegendProps) {
  const [expanded, setExpanded] = useState(!compact);
  
  const syllables: SolfaSyllable[] = ['d', 'r', 'm', 'f', 's', 'l', 't', '0'];
  
  if (compact && !expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="flex items-center gap-2 text-sm text-ink-500 hover:text-ink-700 transition-colors"
      >
        <span>Show Legend</span>
        <ChevronDown className="w-4 h-4" />
      </button>
    );
  }
  
  return (
    <div className="bg-gradient-to-br from-ink-50 to-staff-50 rounded-xl p-5 border border-ink-100">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-ink-700">Solfa Legend</h4>
        {compact && (
          <button
            onClick={() => setExpanded(false)}
            className="text-ink-400 hover:text-ink-600 transition-colors"
          >
            <ChevronUp className="w-4 h-4" />
          </button>
        )}
      </div>
      
      {/* Color legend grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {syllables.map((syllable) => {
          const info = SOLFA_COLORS[syllable];
          return (
            <button
              key={syllable}
              onClick={() => interactive && onSyllableClick?.(syllable)}
              className={`
                flex items-center gap-3 p-3 rounded-lg
                transition-all duration-200
                ${interactive ? 'hover:scale-105 hover:shadow-md cursor-pointer' : 'cursor-default'}
              `}
              style={{
                backgroundColor: info.bgColor,
                borderLeft: `4px solid ${info.color}`,
              }}
              disabled={!interactive}
            >
              <span
                className="w-8 h-8 rounded-full flex items-center justify-center font-bold text-lg"
                style={{ 
                  backgroundColor: info.color,
                  color: 'white',
                }}
              >
                {syllable === '0' ? '∅' : syllable}
              </span>
              <div className="text-left">
                <div className="font-medium text-sm" style={{ color: info.color }}>
                  {info.name}
                </div>
                <div className="text-xs text-ink-400">
                  {syllable === '0' ? 'Rest' : `${info.scaleDegree}${getOrdinalSuffix(info.scaleDegree)}`}
                </div>
              </div>
            </button>
          );
        })}
      </div>
      
      {/* Duration legend */}
      <div className="mt-5 pt-4 border-t border-ink-100">
        <h5 className="text-sm font-medium text-ink-600 mb-3">Duration</h5>
        <div className="flex flex-wrap gap-4 text-sm text-ink-500">
          <div className="flex items-center gap-2">
            <div className="w-16 h-6 bg-staff-100 rounded border border-staff-200" />
            <span>Whole</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-10 h-6 bg-staff-100 rounded border border-staff-200" />
            <span>Half</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-staff-100 rounded border border-staff-200" />
            <span>Quarter</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-6 bg-staff-100 rounded border border-staff-200" />
            <span>Eighth</span>
          </div>
        </div>
      </div>
      
      {/* Octave notation */}
      <div className="mt-4 pt-4 border-t border-ink-100">
        <h5 className="text-sm font-medium text-ink-600 mb-2">Octave Markers</h5>
        <div className="flex flex-wrap gap-6 text-sm text-ink-500">
          <div>
            <code className="font-mono text-staff-600">'</code> = Higher octave
          </div>
          <div>
            <code className="font-mono text-staff-600">''</code> = Two octaves higher
          </div>
          <div>
            <code className="font-mono text-staff-600">,</code> = Lower octave
          </div>
        </div>
      </div>
    </div>
  );
}

function getOrdinalSuffix(n: number): string {
  const s = ["th", "st", "nd", "rd"];
  const v = n % 100;
  return s[(v - 20) % 10] || s[v] || s[0];
}


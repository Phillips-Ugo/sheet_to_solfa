"use client";

import { useState } from "react";
import { Copy, Check } from "lucide-react";

interface SolfaDisplayProps {
  text: string;
  keySignature: string;
  timeSignature: string;
  measureCount: number;
}

export default function SolfaDisplay({
  text,
  keySignature,
  timeSignature,
  measureCount,
}: SolfaDisplayProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Parse the text to highlight measures
  const lines = text.split("\n");

  return (
    <div className="w-full">
      {/* Header info */}
      <div className="flex flex-wrap gap-4 mb-6 text-sm">
        <div className="bg-staff-100 px-4 py-2 rounded-lg">
          <span className="text-ink-500">Key:</span>{" "}
          <span className="font-medium text-ink-800">{keySignature}</span>
        </div>
        <div className="bg-staff-100 px-4 py-2 rounded-lg">
          <span className="text-ink-500">Time:</span>{" "}
          <span className="font-medium text-ink-800">{timeSignature}</span>
        </div>
        <div className="bg-staff-100 px-4 py-2 rounded-lg">
          <span className="text-ink-500">Measures:</span>{" "}
          <span className="font-medium text-ink-800">{measureCount}</span>
        </div>
      </div>

      {/* Solfa notation display */}
      <div className="relative bg-white rounded-xl border border-ink-200 overflow-hidden">
        {/* Copy button */}
        <button
          onClick={handleCopy}
          className="absolute top-4 right-4 p-2 text-ink-400 hover:text-staff-600 transition-colors"
          title="Copy to clipboard"
        >
          {copied ? (
            <Check className="w-5 h-5 text-green-500" />
          ) : (
            <Copy className="w-5 h-5" />
          )}
        </button>

        {/* Notation content */}
        <div className="p-6 pt-12 overflow-x-auto">
          <div className="solfa-notation text-lg leading-relaxed">
            {lines.map((line, index) => {
              // Empty line
              if (!line.trim()) {
                return <div key={index} className="h-4" />;
              }

              // Check if this is a warning/demo line
              if (line.includes("DEMO MODE") || line.includes("===") || line.includes("PLACEHOLDER")) {
                return (
                  <div key={index} className="text-amber-600 font-bold text-sm mb-1">
                    {line}
                  </div>
                );
              }

              // Check if this is a header line
              if (line.startsWith("#") || line.startsWith("Key:") || line.startsWith("Time:") || line.startsWith("Measures:") || line.startsWith("-") || line.startsWith("Generated:")) {
                return (
                  <div key={index} className="text-ink-500 text-sm mb-2">
                    {line}
                  </div>
                );
              }

              // Check if this is a measure line with bar lines
              if (line.includes("|")) {
                return (
                  <div
                    key={index}
                    className="font-mono text-ink-800 py-2 whitespace-pre"
                  >
                    {line}
                  </div>
                );
              }

              return (
                <div key={index} className="text-ink-600 whitespace-pre-wrap">
                  {line}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 p-4 bg-ink-50 rounded-lg">
        <h4 className="font-medium text-ink-700 mb-2">Solfa Legend</h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-sm text-ink-600">
          <div>
            <code className="font-mono text-staff-600">d</code> = Do
          </div>
          <div>
            <code className="font-mono text-staff-600">r</code> = Re
          </div>
          <div>
            <code className="font-mono text-staff-600">m</code> = Mi
          </div>
          <div>
            <code className="font-mono text-staff-600">f</code> = Fa
          </div>
          <div>
            <code className="font-mono text-staff-600">s</code> = Sol
          </div>
          <div>
            <code className="font-mono text-staff-600">l</code> = La
          </div>
          <div>
            <code className="font-mono text-staff-600">t</code> = Ti
          </div>
          <div>
            <code className="font-mono text-staff-600">'</code> = High octave
          </div>
        </div>
      </div>
    </div>
  );
}


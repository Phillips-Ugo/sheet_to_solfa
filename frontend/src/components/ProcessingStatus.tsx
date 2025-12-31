"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Loader, Music } from "lucide-react";

interface ProcessingStatusProps {
  jobId: string;
  state: string;
  progress: number;
  message: string;
  error?: string;
}

const STAGE_INFO: Record<string, { label: string; icon: string }> = {
  pending: { label: "Queued", icon: "⏳" },
  preprocessing: { label: "Preparing Images", icon: "🖼️" },
  omr_processing: { label: "Reading Music", icon: "🎵" },
  analyzing: { label: "Analyzing", icon: "🔍" },
  converting: { label: "Converting to Solfa", icon: "🎼" },
  rendering: { label: "Generating Output", icon: "📄" },
  completed: { label: "Complete!", icon: "✅" },
  failed: { label: "Failed", icon: "❌" },
};

export default function ProcessingStatus({
  jobId,
  state,
  progress,
  message,
  error,
}: ProcessingStatusProps) {
  const stageInfo = STAGE_INFO[state] || { label: state, icon: "⚙️" };
  const isComplete = state === "completed";
  const isFailed = state === "failed";
  const isProcessing = !isComplete && !isFailed;

  return (
    <div className="w-full max-w-xl mx-auto">
      {/* Status card */}
      <div className="bg-white rounded-2xl shadow-lg p-8 border border-ink-100">
        {/* Icon and status */}
        <div className="flex flex-col items-center text-center mb-8">
          <div
            className={`w-20 h-20 rounded-full flex items-center justify-center text-4xl mb-4 ${
              isComplete
                ? "bg-green-100"
                : isFailed
                ? "bg-red-100"
                : "bg-staff-100"
            }`}
          >
            {isProcessing ? (
              <div className="relative">
                <Music className="w-10 h-10 text-staff-600 animate-pulse" />
              </div>
            ) : (
              stageInfo.icon
            )}
          </div>
          <h2 className="font-display text-2xl font-semibold text-ink-800">
            {stageInfo.label}
          </h2>
          <p className="text-ink-500 mt-2">{message}</p>
        </div>

        {/* Progress bar */}
        {isProcessing && (
          <div className="mb-6">
            <div className="flex justify-between text-sm text-ink-500 mb-2">
              <span>Progress</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="h-3 bg-ink-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-staff-400 to-staff-600 progress-bar rounded-full"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Processing stages indicator */}
        {isProcessing && (
          <div className="flex justify-between items-center text-xs text-ink-400 mt-8">
            {Object.entries(STAGE_INFO)
              .filter(([key]) => !["completed", "failed"].includes(key))
              .map(([key, info], index) => {
                const stages = [
                  "pending",
                  "preprocessing",
                  "omr_processing",
                  "analyzing",
                  "converting",
                  "rendering",
                ];
                const currentIndex = stages.indexOf(state);
                const stageIndex = stages.indexOf(key);
                const isPast = stageIndex < currentIndex;
                const isCurrent = key === state;

                return (
                  <div
                    key={key}
                    className={`flex flex-col items-center ${
                      isPast
                        ? "text-staff-600"
                        : isCurrent
                        ? "text-staff-500"
                        : "text-ink-300"
                    }`}
                  >
                    <div
                      className={`w-3 h-3 rounded-full mb-1 ${
                        isPast
                          ? "bg-staff-500"
                          : isCurrent
                          ? "bg-staff-400 animate-pulse"
                          : "bg-ink-200"
                      }`}
                    />
                    <span className="hidden sm:block">{info.icon}</span>
                  </div>
                );
              })}
          </div>
        )}

        {/* Error display */}
        {isFailed && error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        {/* Job ID */}
        <div className="mt-8 pt-6 border-t border-ink-100 text-center">
          <p className="text-xs text-ink-400">
            Job ID: <code className="font-mono">{jobId}</code>
          </p>
        </div>
      </div>
    </div>
  );
}



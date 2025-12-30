"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import SolfaDisplay from "@/components/SolfaDisplay";
import DownloadPanel from "@/components/DownloadPanel";
import { getJobStatus, JobStatus, JobResult } from "@/lib/api";
import { CheckCircle, ArrowLeft } from "lucide-react";

export default function ResultPage() {
  const params = useParams();
  const jobId = params.id as string;

  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchResult() {
      try {
        const data = await getJobStatus(jobId);
        setStatus(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to get result");
      }
    }

    fetchResult();
  }, [jobId]);

  if (error) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center p-4">
        <div className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">❌</span>
          </div>
          <h1 className="font-display text-2xl font-semibold text-ink-800 mb-2">
            Error
          </h1>
          <p className="text-ink-600">{error}</p>
          <a href="/" className="inline-block mt-6 btn-primary">
            Try Again
          </a>
        </div>
      </div>
    );
  }

  if (!status || !status.result) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="spinner w-12 h-12" />
      </div>
    );
  }

  const result = status.result as JobResult;

  return (
    <div className="page-transition py-12 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <a
              href="/"
              className="inline-flex items-center gap-2 text-ink-500 hover:text-staff-600 transition-colors mb-4"
            >
              <ArrowLeft className="w-4 h-4" />
              Convert Another
            </a>
            <h1 className="font-display text-3xl font-bold text-ink-900 flex items-center gap-3">
              <CheckCircle className="w-8 h-8 text-green-500" />
              Conversion Complete!
            </h1>
            <p className="text-ink-600 mt-2">
              Your sheet music has been converted to tonic solfa notation.
            </p>
          </div>
        </div>

        {/* Results grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Solfa display - main content */}
          <div className="lg:col-span-2">
            <SolfaDisplay
              text={result.solfa_text}
              keySignature={result.key_detected}
              timeSignature={result.time_signature}
              measureCount={result.measure_count}
            />
          </div>

          {/* Sidebar - downloads and info */}
          <div className="space-y-8">
            {/* Download panel */}
            <DownloadPanel
              jobId={jobId}
              availableFormats={result.available_formats}
            />

            {/* Stats */}
            <div className="bg-white rounded-xl border border-ink-200 p-6">
              <h3 className="font-display text-lg font-semibold text-ink-800 mb-4">
                Conversion Stats
              </h3>
              <dl className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <dt className="text-ink-500">Notes Converted</dt>
                  <dd className="font-medium text-ink-800">
                    {result.note_count}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-500">Measures</dt>
                  <dd className="font-medium text-ink-800">
                    {result.measure_count}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-500">Detected Key</dt>
                  <dd className="font-medium text-ink-800">
                    {result.key_detected}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-ink-500">Time Signature</dt>
                  <dd className="font-medium text-ink-800">
                    {result.time_signature}
                  </dd>
                </div>
              </dl>
            </div>

            {/* Help */}
            <div className="bg-ink-50 rounded-xl p-6">
              <h3 className="font-display text-lg font-semibold text-ink-800 mb-3">
                Need Help?
              </h3>
              <p className="text-sm text-ink-600">
                The output uses standard tonic solfa notation with movable Do.
                Octave markers (', ,) indicate higher or lower octaves.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}


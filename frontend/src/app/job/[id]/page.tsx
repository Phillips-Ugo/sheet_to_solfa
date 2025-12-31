"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, useParams } from "next/navigation";
import ProcessingStatus from "@/components/ProcessingStatus";
import { getJobStatus, JobStatus } from "@/lib/api";

export default function JobPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.id as string;

  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const data = await getJobStatus(jobId);
      setStatus(data);

      // Redirect to result page when complete
      if (data.state === "completed") {
        router.push(`/result/${jobId}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get status");
    }
  }, [jobId, router]);

  useEffect(() => {
    fetchStatus();

    // Poll for status updates
    const interval = setInterval(() => {
      if (status?.state !== "completed" && status?.state !== "failed") {
        fetchStatus();
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [fetchStatus, status?.state]);

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
          <a
            href="/"
            className="inline-block mt-6 btn-primary"
          >
            Try Again
          </a>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="spinner w-12 h-12" />
      </div>
    );
  }

  return (
    <div className="page-transition py-16 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="font-display text-3xl font-bold text-ink-900">
            Processing Your Sheet Music
          </h1>
          <p className="text-ink-600 mt-2">
            This may take a minute depending on the complexity of your score.
          </p>
        </div>

        <ProcessingStatus
          jobId={status.job_id}
          state={status.state}
          progress={status.progress}
          message={status.message}
          error={status.error}
        />

        {status.state === "failed" && (
          <div className="mt-8 text-center">
            <a href="/" className="btn-primary">
              Try Another File
            </a>
          </div>
        )}
      </div>
    </div>
  );
}



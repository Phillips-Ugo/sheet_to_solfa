/**
 * Backend API client for Sheet to Solfa.
 */

// Remove trailing slash from URL if present, then add /api
const baseUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
const API_BASE = `${baseUrl}/api`;

export interface UploadResponse {
  job_id: string;
  message: string;
  filename: string;
}

export interface JobStatus {
  job_id: string;
  state: string;
  progress: number;
  message: string;
  error?: string;
  result?: JobResult;
  updated_at?: string;
}

export interface JobResult {
  solfa_text: string;
  key_detected: string;
  time_signature: string;
  measure_count: number;
  note_count: number;
  available_formats: string[];
  is_demo?: boolean;
}

export interface TextResult {
  job_id: string;
  text: string;
  key: string;
  time_signature: string;
  measure_count: number;
}

/**
 * Upload a PDF file for processing.
 */
export async function uploadPDF(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(error.detail || "Upload failed");
  }

  return response.json();
}

/**
 * Create a test job (for development).
 */
export async function createTestJob(): Promise<UploadResponse> {
  const response = await fetch(`${API_BASE}/upload/test`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Test failed" }));
    throw new Error(error.detail || "Test failed");
  }

  return response.json();
}

/**
 * Get the status of a processing job.
 */
export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`);

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Job not found");
    }
    const error = await response.json().catch(() => ({ detail: "Status check failed" }));
    throw new Error(error.detail || "Status check failed");
  }

  return response.json();
}

/**
 * Get the result of a completed job.
 */
export async function getJobResult(jobId: string): Promise<JobResult> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/result`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to get result" }));
    throw new Error(error.detail || "Failed to get result");
  }

  return response.json();
}

/**
 * Get the text result for display.
 */
export async function getTextResult(jobId: string): Promise<TextResult> {
  const response = await fetch(`${API_BASE}/export/${jobId}/text`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Failed to get text" }));
    throw new Error(error.detail || "Failed to get text");
  }

  return response.json();
}

/**
 * Get the download URL for a specific format.
 */
export function getDownloadUrl(jobId: string, format: string): string {
  return `${API_BASE}/export/${jobId}/${format}`;
}

/**
 * Download the result in a specific format.
 */
export async function downloadResult(jobId: string, format: string): Promise<void> {
  const url = getDownloadUrl(jobId, format);
  
  // Create a temporary link and click it
  const link = document.createElement("a");
  link.href = url;
  link.download = `solfa_${jobId.slice(0, 8)}.${format}`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}


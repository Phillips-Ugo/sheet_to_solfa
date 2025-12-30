"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, FileText, X, AlertCircle } from "lucide-react";

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  isUploading: boolean;
  error?: string;
}

export default function FileUploader({
  onFileSelect,
  isUploading,
  error,
}: FileUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type === "application/pdf" || file.name.endsWith(".pdf")) {
        setSelectedFile(file);
      }
    }
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        setSelectedFile(files[0]);
      }
    },
    []
  );

  const handleUpload = useCallback(() => {
    if (selectedFile) {
      onFileSelect(selectedFile);
    }
  }, [selectedFile, onFileSelect]);

  const clearFile = useCallback(() => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* Dropzone */}
      <div
        className={`dropzone relative border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${
          isDragging
            ? "border-staff-500 bg-staff-50"
            : selectedFile
            ? "border-staff-400 bg-staff-50/50"
            : "border-ink-300 hover:border-staff-400"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleFileInput}
          className="hidden"
        />

        {selectedFile ? (
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 bg-staff-100 rounded-xl flex items-center justify-center">
              <FileText className="w-8 h-8 text-staff-600" />
            </div>
            <div>
              <p className="font-medium text-ink-800">{selectedFile.name}</p>
              <p className="text-sm text-ink-500">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                clearFile();
              }}
              className="text-sm text-ink-500 hover:text-staff-600 flex items-center gap-1"
            >
              <X className="w-4 h-4" />
              Remove
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4">
            <div className="w-16 h-16 bg-ink-100 rounded-xl flex items-center justify-center">
              <Upload className="w-8 h-8 text-ink-400" />
            </div>
            <div>
              <p className="font-medium text-ink-700">
                Drop your PDF here, or{" "}
                <span className="text-staff-600">browse</span>
              </p>
              <p className="text-sm text-ink-500 mt-1">
                Scanned or digital sheet music (max 50MB)
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <p className="text-red-700 text-sm">{error}</p>
        </div>
      )}

      {/* Upload button */}
      <div className="mt-6 flex justify-center">
        <button
          onClick={handleUpload}
          disabled={!selectedFile || isUploading}
          className="btn-primary flex items-center gap-2 min-w-[200px] justify-center"
        >
          {isUploading ? (
            <>
              <div className="spinner w-5 h-5" />
              Uploading...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5" />
              Convert to Solfa
            </>
          )}
        </button>
      </div>
    </div>
  );
}


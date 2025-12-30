"use client";

import { FileText, FileJson, FileDown } from "lucide-react";
import { getDownloadUrl } from "@/lib/api";

interface DownloadPanelProps {
  jobId: string;
  availableFormats: string[];
}

const FORMAT_INFO: Record<
  string,
  { label: string; description: string; icon: React.ReactNode }
> = {
  txt: {
    label: "Plain Text",
    description: "Simple text format, easy to print",
    icon: <FileText className="w-6 h-6" />,
  },
  json: {
    label: "JSON",
    description: "Structured data for developers",
    icon: <FileJson className="w-6 h-6" />,
  },
  pdf: {
    label: "PDF",
    description: "Formatted document, ready to share",
    icon: <FileDown className="w-6 h-6" />,
  },
};

export default function DownloadPanel({
  jobId,
  availableFormats,
}: DownloadPanelProps) {
  return (
    <div className="w-full">
      <h3 className="font-display text-xl font-semibold text-ink-800 mb-4">
        Download Your Solfa
      </h3>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {availableFormats.map((format) => {
          const info = FORMAT_INFO[format] || {
            label: format.toUpperCase(),
            description: `Download as ${format}`,
            icon: <FileDown className="w-6 h-6" />,
          };

          return (
            <a
              key={format}
              href={getDownloadUrl(jobId, format)}
              download
              className="group bg-white border-2 border-ink-200 hover:border-staff-400 rounded-xl p-6 transition-all hover:shadow-lg"
            >
              <div className="flex flex-col items-center text-center gap-3">
                <div className="w-12 h-12 bg-ink-100 group-hover:bg-staff-100 rounded-xl flex items-center justify-center text-ink-500 group-hover:text-staff-600 transition-colors">
                  {info.icon}
                </div>
                <div>
                  <h4 className="font-medium text-ink-800">{info.label}</h4>
                  <p className="text-sm text-ink-500 mt-1">{info.description}</p>
                </div>
              </div>
            </a>
          );
        })}
      </div>
    </div>
  );
}


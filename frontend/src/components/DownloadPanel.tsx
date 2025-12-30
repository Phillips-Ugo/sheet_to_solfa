"use client";

import { FileText, FileJson, FileDown, Download, Sparkles } from "lucide-react";
import { getDownloadUrl } from "@/lib/api";

interface DownloadPanelProps {
  jobId: string;
  availableFormats: string[];
}

const FORMAT_INFO: Record<
  string,
  { label: string; description: string; icon: React.ReactNode; gradient: string }
> = {
  txt: {
    label: "Plain Text",
    description: "Simple text format, easy to print",
    icon: <FileText className="w-5 h-5" />,
    gradient: "from-emerald-500 to-teal-600",
  },
  json: {
    label: "JSON",
    description: "Structured data for developers",
    icon: <FileJson className="w-5 h-5" />,
    gradient: "from-violet-500 to-purple-600",
  },
  pdf: {
    label: "PDF",
    description: "Formatted document, ready to share",
    icon: <FileDown className="w-5 h-5" />,
    gradient: "from-rose-500 to-pink-600",
  },
};

export default function DownloadPanel({
  jobId,
  availableFormats,
}: DownloadPanelProps) {
  return (
    <div className="bg-white rounded-xl border border-ink-200 p-6 shadow-sm">
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 bg-gradient-to-br from-staff-400 to-staff-600 rounded-xl flex items-center justify-center">
          <Download className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-display text-lg font-semibold text-ink-800">
            Download Your Solfa
          </h3>
          <p className="text-sm text-ink-500">Choose your preferred format</p>
        </div>
      </div>

      <div className="space-y-3">
        {availableFormats.map((format, index) => {
          const info = FORMAT_INFO[format] || {
            label: format.toUpperCase(),
            description: `Download as ${format}`,
            icon: <FileDown className="w-5 h-5" />,
            gradient: "from-gray-500 to-gray-600",
          };

          return (
            <a
              key={format}
              href={getDownloadUrl(jobId, format)}
              download
              className="group flex items-center gap-4 p-4 rounded-xl border-2 border-ink-100 hover:border-transparent hover:shadow-lg transition-all duration-200 relative overflow-hidden"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              {/* Gradient background on hover */}
              <div className={`absolute inset-0 bg-gradient-to-r ${info.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-200`} />
              
              {/* Content */}
              <div className="relative flex items-center gap-4 w-full">
                <div className={`w-10 h-10 bg-gradient-to-br ${info.gradient} rounded-lg flex items-center justify-center text-white shadow-sm group-hover:shadow-lg group-hover:scale-110 transition-all duration-200`}>
                  {info.icon}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-ink-800 group-hover:text-white transition-colors">
                    {info.label}
                  </h4>
                  <p className="text-sm text-ink-500 group-hover:text-white/80 transition-colors">
                    {info.description}
                  </p>
                </div>
                <Download className="w-5 h-5 text-ink-300 group-hover:text-white group-hover:translate-y-0.5 transition-all" />
              </div>
            </a>
          );
        })}
      </div>
      
      {/* Quick tip */}
      <div className="mt-5 pt-4 border-t border-ink-100">
        <div className="flex items-start gap-2 text-sm text-ink-500">
          <Sparkles className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
          <span>
            <strong className="text-ink-700">Tip:</strong> PDF format is great for printing and sharing. Use JSON for integration with other apps.
          </span>
        </div>
      </div>
    </div>
  );
}


"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import FileUploader from "@/components/FileUploader";
import { uploadPDF } from "@/lib/api";
import { Music, Sparkles, Zap, Users } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | undefined>();

  const handleFileSelect = useCallback(
    async (file: File) => {
      setIsUploading(true);
      setError(undefined);

      try {
        const response = await uploadPDF(file);
        // Redirect to job status page
        router.push(`/job/${response.job_id}`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Upload failed");
        setIsUploading(false);
      }
    },
    [router]
  );

  return (
    <div className="page-transition">
      {/* Hero section */}
      <section className="py-16 md:py-24 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-ink-900 leading-tight">
            Transform Sheet Music into{" "}
            <span className="text-staff-600">Tonic Solfa</span>
          </h1>
          <p className="mt-6 text-lg text-ink-600 max-w-2xl mx-auto">
            Upload your PDF sheet music and get accurate tonic solfa notation
            in seconds. Perfect for choir directors, music teachers, and
            students learning sight-singing.
          </p>
        </div>
      </section>

      {/* Upload section */}
      <section className="py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <FileUploader
            onFileSelect={handleFileSelect}
            isUploading={isUploading}
            error={error}
          />
        </div>
      </section>

      {/* Features section */}
      <section className="py-16 px-4 mt-8">
        <div className="max-w-5xl mx-auto">
          <h2 className="font-display text-2xl font-semibold text-center text-ink-800 mb-12">
            Why Sheet to Solfa?
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-white rounded-2xl p-6 shadow-sm border border-ink-100">
              <div className="w-12 h-12 bg-staff-100 rounded-xl flex items-center justify-center mb-4">
                <Zap className="w-6 h-6 text-staff-600" />
              </div>
              <h3 className="font-display text-lg font-semibold text-ink-800">
                Fast & Accurate
              </h3>
              <p className="mt-2 text-ink-600 text-sm">
                Advanced music recognition converts your sheet music to solfa
                notation in seconds with high accuracy.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-ink-100">
              <div className="w-12 h-12 bg-staff-100 rounded-xl flex items-center justify-center mb-4">
                <Music className="w-6 h-6 text-staff-600" />
              </div>
              <h3 className="font-display text-lg font-semibold text-ink-800">
                Movable Do System
              </h3>
              <p className="mt-2 text-ink-600 text-sm">
                Uses the movable Do system with la-based minor, supporting
                chromatic alterations and key changes.
              </p>
            </div>

            <div className="bg-white rounded-2xl p-6 shadow-sm border border-ink-100">
              <div className="w-12 h-12 bg-staff-100 rounded-xl flex items-center justify-center mb-4">
                <Users className="w-6 h-6 text-staff-600" />
              </div>
              <h3 className="font-display text-lg font-semibold text-ink-800">
                Built for Educators
              </h3>
              <p className="mt-2 text-ink-600 text-sm">
                Designed for choir directors, music teachers, and students
                learning sight-singing with tonic solfa.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-16 px-4 bg-ink-900 text-white mt-16">
        <div className="max-w-4xl mx-auto">
          <h2 className="font-display text-2xl font-semibold text-center mb-12">
            How It Works
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            {[
              { step: "1", title: "Upload", desc: "Drop your PDF sheet music" },
              {
                step: "2",
                title: "Process",
                desc: "Our engine reads the notation",
              },
              {
                step: "3",
                title: "Convert",
                desc: "Notes become solfa syllables",
              },
              {
                step: "4",
                title: "Download",
                desc: "Get your solfa in multiple formats",
              },
            ].map((item) => (
              <div key={item.step} className="text-center">
                <div className="w-12 h-12 bg-staff-500 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="font-display font-bold text-lg">
                    {item.step}
                  </span>
                </div>
                <h3 className="font-medium mb-1">{item.title}</h3>
                <p className="text-sm text-ink-400">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* About section */}
      <section id="about" className="py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="font-display text-2xl font-semibold text-ink-800 mb-6">
            About Tonic Solfa
          </h2>
          <p className="text-ink-600 leading-relaxed">
            Tonic solfa (movable Do) is a system of musical notation where each
            note of a scale is given a distinct syllable: Do, Re, Mi, Fa, Sol,
            La, Ti. This method is widely used in Africa and the UK for teaching
            sight-singing and is particularly popular in choral music education.
          </p>
          <p className="text-ink-600 leading-relaxed mt-4">
            Our system automatically detects the key signature and converts each
            note to its corresponding solfa syllable, handling chromatic
            alterations (di, ra, fi, te, etc.) and octave changes with
            apostrophes and commas.
          </p>
        </div>
      </section>
    </div>
  );
}


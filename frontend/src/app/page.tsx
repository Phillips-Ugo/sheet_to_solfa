"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import FileUploader from "@/components/FileUploader";
import { uploadPDF } from "@/lib/api";
import { Music, Sparkles, Zap, Users, Volume2, Palette, ArrowRight } from "lucide-react";

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
      {/* Hero section with animated background */}
      <section className="relative py-16 md:py-24 px-4 overflow-hidden">
        {/* Animated gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-staff-50 via-transparent to-amber-50 opacity-70" />
        
        {/* Floating musical notes decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-[10%] text-staff-200 text-6xl animate-bounce" style={{ animationDelay: '0s', animationDuration: '3s' }}>♪</div>
          <div className="absolute top-40 right-[15%] text-staff-200 text-4xl animate-bounce" style={{ animationDelay: '0.5s', animationDuration: '2.5s' }}>♫</div>
          <div className="absolute bottom-20 left-[20%] text-staff-200 text-5xl animate-bounce" style={{ animationDelay: '1s', animationDuration: '3.5s' }}>♬</div>
          <div className="absolute bottom-32 right-[25%] text-amber-200 text-3xl animate-bounce" style={{ animationDelay: '1.5s', animationDuration: '2s' }}>♩</div>
        </div>
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-white/80 backdrop-blur rounded-full border border-staff-200 shadow-sm mb-8">
            <Sparkles className="w-4 h-4 text-amber-500" />
            <span className="text-sm font-medium text-ink-700">Powered by AI</span>
          </div>
          
          <h1 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-ink-900 leading-tight">
            Transform Sheet Music into{" "}
            <span className="bg-gradient-to-r from-staff-500 to-staff-700 bg-clip-text text-transparent">
              Tonic Solfa
            </span>
          </h1>
          <p className="mt-6 text-lg md:text-xl text-ink-600 max-w-2xl mx-auto">
            Upload your PDF sheet music and get accurate tonic solfa notation
            in seconds. Perfect for choir directors, music teachers, and
            students learning sight-singing.
          </p>
          
          {/* Feature pills */}
          <div className="flex flex-wrap justify-center gap-3 mt-8">
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-sm text-sm text-ink-600">
              <Palette className="w-4 h-4 text-staff-500" />
              Color-coded notation
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-sm text-sm text-ink-600">
              <Volume2 className="w-4 h-4 text-staff-500" />
              Play notes aloud
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white rounded-full shadow-sm text-sm text-ink-600">
              <Zap className="w-4 h-4 text-staff-500" />
              Instant conversion
            </div>
          </div>
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
          <h2 className="font-display text-2xl font-semibold text-center text-ink-800 mb-4">
            Why Sheet to Solfa?
          </h2>
          <p className="text-center text-ink-500 max-w-2xl mx-auto mb-12">
            The most intuitive way to convert Western notation to tonic solfa for your choir or classroom.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="group bg-white rounded-2xl p-6 shadow-sm border border-ink-100 hover:shadow-xl hover:border-staff-200 transition-all duration-300 hover:-translate-y-1">
              <div className="w-14 h-14 bg-gradient-to-br from-amber-400 to-orange-500 rounded-2xl flex items-center justify-center mb-5 shadow-lg shadow-amber-200 group-hover:scale-110 transition-transform">
                <Zap className="w-7 h-7 text-white" />
              </div>
              <h3 className="font-display text-lg font-semibold text-ink-800">
                Fast & Accurate
              </h3>
              <p className="mt-2 text-ink-600 text-sm leading-relaxed">
                AI-powered music recognition converts your sheet music to solfa
                notation in seconds with high accuracy.
              </p>
            </div>

            <div className="group bg-white rounded-2xl p-6 shadow-sm border border-ink-100 hover:shadow-xl hover:border-staff-200 transition-all duration-300 hover:-translate-y-1">
              <div className="w-14 h-14 bg-gradient-to-br from-staff-400 to-staff-600 rounded-2xl flex items-center justify-center mb-5 shadow-lg shadow-staff-200 group-hover:scale-110 transition-transform">
                <Music className="w-7 h-7 text-white" />
              </div>
              <h3 className="font-display text-lg font-semibold text-ink-800">
                Movable Do System
              </h3>
              <p className="mt-2 text-ink-600 text-sm leading-relaxed">
                Uses the movable Do system with la-based minor, supporting
                chromatic alterations and key changes.
              </p>
            </div>

            <div className="group bg-white rounded-2xl p-6 shadow-sm border border-ink-100 hover:shadow-xl hover:border-staff-200 transition-all duration-300 hover:-translate-y-1">
              <div className="w-14 h-14 bg-gradient-to-br from-violet-400 to-purple-600 rounded-2xl flex items-center justify-center mb-5 shadow-lg shadow-violet-200 group-hover:scale-110 transition-transform">
                <Users className="w-7 h-7 text-white" />
              </div>
              <h3 className="font-display text-lg font-semibold text-ink-800">
                Built for Educators
              </h3>
              <p className="mt-2 text-ink-600 text-sm leading-relaxed">
                Designed for choir directors, music teachers, and students
                learning sight-singing with tonic solfa.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-4 bg-gradient-to-br from-ink-900 via-ink-800 to-ink-900 text-white mt-16 relative overflow-hidden">
        {/* Background decoration */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-staff-500 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-amber-500 rounded-full blur-3xl translate-x-1/2 translate-y-1/2" />
        </div>
        
        <div className="max-w-5xl mx-auto relative z-10">
          <h2 className="font-display text-3xl font-semibold text-center mb-4">
            How It Works
          </h2>
          <p className="text-center text-ink-300 max-w-xl mx-auto mb-14">
            Four simple steps from sheet music to singable solfa notation
          </p>
          
          <div className="grid md:grid-cols-4 gap-8 relative">
            {/* Connecting line */}
            <div className="hidden md:block absolute top-6 left-[12%] right-[12%] h-0.5 bg-gradient-to-r from-staff-500 via-amber-500 to-violet-500" />
            
            {[
              { step: "1", title: "Upload", desc: "Drop your PDF sheet music", color: "from-staff-400 to-staff-600" },
              { step: "2", title: "Process", desc: "AI reads the notation", color: "from-emerald-400 to-teal-600" },
              { step: "3", title: "Convert", desc: "Notes become solfa syllables", color: "from-amber-400 to-orange-500" },
              { step: "4", title: "Download", desc: "Get it in multiple formats", color: "from-violet-400 to-purple-600" },
            ].map((item, index) => (
              <div key={item.step} className="text-center relative">
                <div className={`w-12 h-12 bg-gradient-to-br ${item.color} rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg relative z-10`}>
                  <span className="font-display font-bold text-lg">
                    {item.step}
                  </span>
                </div>
                <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
                <p className="text-sm text-ink-400">{item.desc}</p>
              </div>
            ))}
          </div>
          
          {/* CTA */}
          <div className="text-center mt-14">
            <a 
              href="#top" 
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-staff-500 to-staff-600 hover:from-staff-600 hover:to-staff-700 rounded-xl font-medium shadow-lg shadow-staff-500/25 hover:shadow-xl transition-all"
            >
              Try It Now
              <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>
      </section>

      {/* About section */}
      <section id="about" className="py-20 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="bg-gradient-to-br from-staff-50 to-amber-50 rounded-3xl p-8 md:p-12 border border-staff-100">
            <div className="text-center mb-10">
              <h2 className="font-display text-3xl font-semibold text-ink-800 mb-4">
                About Tonic Solfa
              </h2>
              <div className="w-16 h-1 bg-gradient-to-r from-staff-400 to-amber-400 mx-auto rounded-full" />
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="font-display text-lg font-semibold text-ink-800 mb-3 flex items-center gap-2">
                  <span className="w-8 h-8 bg-staff-500 text-white rounded-lg flex items-center justify-center text-sm">♪</span>
                  What is Tonic Solfa?
                </h3>
                <p className="text-ink-600 leading-relaxed">
                  Tonic solfa (movable Do) is a system of musical notation where each
                  note of a scale is given a distinct syllable: <strong>Do, Re, Mi, Fa, Sol,
                  La, Ti</strong>. This method is widely used in Africa and the UK for teaching
                  sight-singing and is particularly popular in choral music education.
                </p>
              </div>
              
              <div>
                <h3 className="font-display text-lg font-semibold text-ink-800 mb-3 flex items-center gap-2">
                  <span className="w-8 h-8 bg-amber-500 text-white rounded-lg flex items-center justify-center text-sm">⚡</span>
                  How We Convert
                </h3>
                <p className="text-ink-600 leading-relaxed">
                  Our AI-powered system automatically detects the key signature and converts each
                  note to its corresponding solfa syllable, handling chromatic
                  alterations (di, ra, fi, te, etc.) and octave changes with
                  apostrophes and commas.
                </p>
              </div>
            </div>
            
            {/* Solfa scale preview */}
            <div className="mt-10 pt-8 border-t border-staff-200">
              <p className="text-center text-sm text-ink-500 mb-4">The Solfa Scale</p>
              <div className="flex justify-center flex-wrap gap-3">
                {[
                  { s: 'd', c: 'bg-red-500' },
                  { s: 'r', c: 'bg-orange-500' },
                  { s: 'm', c: 'bg-yellow-500' },
                  { s: 'f', c: 'bg-green-500' },
                  { s: 's', c: 'bg-blue-500' },
                  { s: 'l', c: 'bg-indigo-500' },
                  { s: 't', c: 'bg-purple-500' },
                ].map((note) => (
                  <div 
                    key={note.s} 
                    className={`w-10 h-10 ${note.c} text-white rounded-xl flex items-center justify-center font-bold shadow-lg`}
                  >
                    {note.s}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>
      
      {/* Footer */}
      <footer className="py-8 px-4 border-t border-ink-100">
        <div className="max-w-4xl mx-auto text-center text-sm text-ink-500">
          <p>Sheet to Solfa — Transforming music notation for everyone</p>
        </div>
      </footer>
    </div>
  );
}


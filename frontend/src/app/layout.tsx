import React from "react";
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sheet to Solfa - Convert Sheet Music to Tonic Solfa",
  description:
    "Transform PDF sheet music into tonic solfa notation for choir directors, music teachers, and students.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-staff-50">
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <header className="bg-ink-900 text-white">
            <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
              <a href="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
                <div className="w-10 h-10 bg-staff-500 rounded-lg flex items-center justify-center">
                  <span className="text-xl font-display font-bold">♫</span>
                </div>
                <div>
                  <h1 className="font-display text-xl font-semibold">
                    Sheet to Solfa
                  </h1>
                  <p className="text-xs text-ink-400">PDF → Tonic Solfa</p>
                </div>
              </a>
              <nav className="flex items-center gap-6">
                <a
                  href="/"
                  className="text-sm text-ink-300 hover:text-white transition-colors"
                >
                  Convert
                </a>
                <a
                  href="#about"
                  className="text-sm text-ink-300 hover:text-white transition-colors"
                >
                  About
                </a>
              </nav>
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1">{children}</main>

          {/* Footer */}
          <footer className="bg-ink-900 text-ink-400 py-8">
            <div className="max-w-6xl mx-auto px-4 text-center">
              <p className="text-sm">
                Sheet to Solfa — Convert sheet music to tonic solfa notation
              </p>
              <p className="text-xs mt-2">
                Built for choir directors, music teachers, and students
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}


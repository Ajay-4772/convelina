"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  Sparkles,
  ShieldCheck,
  Scale,
  FileCheck,
  Play,
  Layers,
} from "lucide-react";
import WaveAnimation3D from "../ui/WaveAnimation3D";

export default function Hero() {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <section className="relative overflow-hidden pt-16 pb-20 md:pt-24 md:pb-32 border-b border-[#e5e2dc]/70 bg-[#faf9f6] text-[#18181b]">
      {/* 1. Deep Volumetric 3D Wave Animation */}
      <WaveAnimation3D opacity={1.0} />

      {/* 2. Hero Content Container */}
      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8">
        {/* Brand Tagline Badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/90 border border-stone-200 shadow-xs text-xs font-semibold tracking-wide text-zinc-800">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-bold tracking-tight">CONVELINA</span>
          <span className="text-zinc-400">|</span>
          <span className="text-zinc-600 font-medium">Document Reconciliation &amp; Verification</span>
        </div>

        {/* Large Editorial Headline with Clean Serif Typography */}
        <div className="space-y-4 max-w-4xl mx-auto pt-2 sm:pt-4">
          <h1 className="text-4xl sm:text-6xl md:text-7xl lg:text-[5.25rem] font-serif font-normal tracking-tight text-[#111111] leading-[1.08] is-balance">
            Your documents, <br className="hidden sm:inline" />
            <span className="italic font-normal text-zinc-800">
              made easier.
            </span>
          </h1>
        </div>

        {/* Supporting Narrative */}
        <p className="max-w-2xl mx-auto text-base sm:text-lg md:text-xl text-zinc-600 font-normal leading-relaxed is-pretty">
          Understand document differences, find the right forms, and get clear, source-grounded guidance across your Aadhaar, PAN, Passport, Educational certificates, and EPF records.
        </p>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4 w-full sm:w-auto">
          <Link
            href="/signup"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className="relative group w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-9 py-4 rounded-full bg-[#111111] text-white text-sm sm:text-base font-semibold shadow-elevated hover:bg-zinc-800 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0"
          >
            <span>Get started with CONVELINA</span>
            <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
          </Link>

          <a
            href="#video-preview"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-white/90 text-zinc-800 text-sm sm:text-base font-medium backdrop-blur-md border border-stone-300 shadow-glass hover:bg-white hover:border-zinc-400 transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0"
          >
            <Play className="w-4 h-4 fill-zinc-800 text-zinc-800" />
            <span>Platform Overview</span>
          </a>
        </div>

        {/* Light Glass Trust Highlights Strip */}
        <div className="pt-12 border-t border-stone-300/60 max-w-4xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-left">
          <div className="p-4 rounded-2xl bg-white/80 backdrop-blur-md border border-stone-200/80 shadow-xs hover:border-stone-300 hover:bg-white transition-all duration-200">
            <div className="flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold text-zinc-900">Privacy Safeguards</div>
                <div className="text-xs text-zinc-500 leading-snug">Zero long-term storage of raw credential files</div>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white/80 backdrop-blur-md border border-stone-200/80 shadow-xs hover:border-stone-300 hover:bg-white transition-all duration-200">
            <div className="flex items-start gap-3">
              <Scale className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold text-zinc-900">Conflict Detection</div>
                <div className="text-xs text-zinc-500 leading-snug">Automated cross-document format &amp; mismatch analysis</div>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white/80 backdrop-blur-md border border-stone-200/80 shadow-xs hover:border-stone-300 hover:bg-white transition-all duration-200">
            <div className="flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-sky-600 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold text-zinc-900">AI Intelligence</div>
                <div className="text-xs text-zinc-500 leading-snug">Guidance grounded strictly in verified sources</div>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-white/80 backdrop-blur-md border border-stone-200/80 shadow-xs hover:border-stone-300 hover:bg-white transition-all duration-200">
            <div className="flex items-start gap-3">
              <FileCheck className="w-5 h-5 text-purple-600 shrink-0 mt-0.5" />
              <div>
                <div className="text-sm font-semibold text-zinc-900">Cryptographic PKI</div>
                <div className="text-xs text-zinc-500 leading-snug">Ed25519 digital signatures and audit chaining</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

"use client";

import React from "react";
import Link from "next/link";
import { 
  GitCompare, 
  Sparkles, 
  FileText, 
  LayoutDashboard,
  ArrowRight,
  CheckCircle2
} from "lucide-react";
import LiquidGlass from "../ui/glass/LiquidGlass";
import GlassCard from "../ui/glass/GlassCard";

export default function ProductCapabilities() {
  return (
    <section id="capabilities" className="py-20 md:py-32 bg-[#faf9f6] border-b border-[#e5e2dc]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Section Heading */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-6 border-b border-[#e5e2dc]">
          <div className="space-y-3 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#e5e2dc] text-xs font-semibold uppercase tracking-wider text-zinc-700 shadow-xs">
              <span>Capabilities</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#18181b] tracking-tight">
              Purpose-built tools for identity resolution.
            </h2>
          </div>
          <p className="max-w-md text-sm sm:text-base text-zinc-600 leading-relaxed">
            CONVELINA provides structured, statutory assistance across primary Indian identity credentials without overstepping legal boundaries.
          </p>
        </div>

        {/* Asymmetric 4-Capability Grid */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          {/* Capability 1: Inconsistency Detection (Large 7-col Card) */}
          <div className="md:col-span-7">
            <GlassCard className="h-full flex flex-col justify-between space-y-8 p-8 md:p-10 bg-white/75">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-[#18181b] flex items-center justify-center text-white shadow-elevated">
                  <GitCompare className="w-6 h-6" />
                </div>
                <h3 className="text-2xl sm:text-3xl font-serif text-zinc-900 tracking-tight">
                  Document Inconsistency Detection
                </h3>
                <p className="text-sm sm:text-base text-zinc-600 leading-relaxed font-normal">
                  Cross-compares demographic fields across your Aadhaar, PAN, Passport, Educational certificates, and EPF records. Automatically identifies spelling variations, expanded initials, and date of birth differences with clear side-by-side highlighting.
                </p>
              </div>

              {/* Visual Mini Mockup */}
              <div className="p-4 rounded-xl bg-[#faf9f6] border border-[#e5e2dc] space-y-2.5 text-xs">
                <div className="flex items-center justify-between pb-2 border-b border-zinc-200">
                  <span className="font-semibold text-zinc-800">Detected Variance Example:</span>
                  <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-medium">Initial Expansion</span>
                </div>
                <div className="grid grid-cols-2 gap-3 text-zinc-700">
                  <div className="bg-white p-2.5 rounded-lg border border-zinc-200">
                    <span className="text-[10px] text-zinc-400 block font-mono">AADHAAR</span>
                    <span className="font-medium text-zinc-900">Ramanathan Kumar</span>
                  </div>
                  <div className="bg-white p-2.5 rounded-lg border border-amber-300 bg-amber-50/50">
                    <span className="text-[10px] text-amber-700 block font-mono">PAN CARD</span>
                    <span className="font-bold text-amber-950">K. Ramanathan</span>
                  </div>
                </div>
              </div>

              <div>
                <Link
                  href="/signup"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-[#18181b] hover:text-zinc-600 transition"
                >
                  Explore detection <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </GlassCard>
          </div>

          {/* Capability 2: AI Procedure Guidance (5-col Card) */}
          <div className="md:col-span-5">
            <GlassCard className="h-full flex flex-col justify-between space-y-8 p-8 md:p-10 bg-white/75">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-blue-600 flex items-center justify-center text-white shadow-elevated">
                  <Sparkles className="w-6 h-6" />
                </div>
                <h3 className="text-2xl sm:text-3xl font-serif text-zinc-900 tracking-tight">
                  Official Procedure Guidance
                </h3>
                <p className="text-sm sm:text-base text-zinc-600 leading-relaxed font-normal">
                  Ask questions about official correction procedures and receive clear, step-by-step guidance grounded strictly in verified statutory circulars from UIDAI, Income Tax, MEA, and EPFO.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-blue-50/50 border border-blue-200 text-xs text-blue-950 space-y-2">
                <span className="font-semibold block">Grounded Sourcing Policy:</span>
                <p className="text-blue-900/90 leading-relaxed">
                  Answers cite official statutory regulations. If verified procedure information is not available, the assistant declines to answer rather than guessing.
                </p>
              </div>

              <div>
                <Link
                  href="/signup"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-blue-700 hover:text-blue-900 transition"
                >
                  Ask guidance <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </GlassCard>
          </div>

          {/* Capability 3: Official Forms Repository (5-col Card) */}
          <div className="md:col-span-5">
            <GlassCard className="h-full flex flex-col justify-between space-y-8 p-8 md:p-10 bg-white/75">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-emerald-600 flex items-center justify-center text-white shadow-elevated">
                  <FileText className="w-6 h-6" />
                </div>
                <h3 className="text-2xl sm:text-3xl font-serif text-zinc-900 tracking-tight">
                  Official Forms Repository
                </h3>
                <p className="text-sm sm:text-base text-zinc-600 leading-relaxed font-normal">
                  Direct access to authentic government applications including NSDL Form 49A, EPFO Joint Declaration forms, MEA Annexure-E, and UIDAI demographic update instructions.
                </p>
              </div>

              <ul className="space-y-2 text-xs sm:text-sm text-zinc-700">
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Verified direct links to statutory portals</span>
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>Clear prerequisite checklists for submissions</span>
                </li>
              </ul>

              <div>
                <Link
                  href="/signup"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-emerald-800 hover:text-emerald-950 transition"
                >
                  Browse forms <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </GlassCard>
          </div>

          {/* Capability 4: Private Citizen Workspace (7-col Card) */}
          <div className="md:col-span-7">
            <GlassCard className="h-full flex flex-col justify-between space-y-8 p-8 md:p-10 bg-white/75">
              <div className="space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-[#18181b] flex items-center justify-center text-white shadow-elevated">
                  <LayoutDashboard className="w-6 h-6" />
                </div>
                <h3 className="text-2xl sm:text-3xl font-serif text-zinc-900 tracking-tight">
                  Private Citizen Workspace
                </h3>
                <p className="text-sm sm:text-base text-zinc-600 leading-relaxed font-normal">
                  A focused, distraction-free environment to upload records, review reconciliation progress, track your change history, and manage your account with complete data isolation.
                </p>
              </div>

              <div className="p-4 rounded-xl bg-[#faf9f6] border border-[#e5e2dc] text-xs sm:text-sm text-zinc-600 space-y-1.5">
                <span className="font-semibold text-zinc-900 block">Privacy Protection Architecture:</span>
                <p>
                  Document scans are processed in temporary memory and unlinked immediately after extraction. Numbers like Aadhaar are permanently masked.
                </p>
              </div>

              <div>
                <Link
                  href="/signup"
                  className="inline-flex items-center gap-2 text-sm font-semibold text-[#18181b] hover:text-zinc-600 transition"
                >
                  Open workspace <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </section>
  );
}

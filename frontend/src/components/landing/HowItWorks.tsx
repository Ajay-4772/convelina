"use client";

import React from "react";
import { UploadCloud, ScanText, GitCompare, AlertTriangle, Sparkles, FileCheck2 } from "lucide-react";

export default function HowItWorks() {
  const steps = [
    {
      num: "01",
      icon: <UploadCloud className="w-5 h-5 text-zinc-900" />,
      title: "Upload Documents",
      description: "Securely upload your digital scans or photographs in PDF, JPG, or PNG format. Files are processed in temporary memory.",
    },
    {
      num: "02",
      icon: <ScanText className="w-5 h-5 text-zinc-900" />,
      title: "Extract Information",
      description: "Text extraction reads demographic fields while automatically masking sensitive numbers like Aadhaar.",
    },
    {
      num: "03",
      icon: <GitCompare className="w-5 h-5 text-zinc-900" />,
      title: "Compare Document Details",
      description: "Smart comparison matches names, dates of birth, and parent names, recognizing initials and formatting differences.",
    },
    {
      num: "04",
      icon: <AlertTriangle className="w-5 h-5 text-zinc-900" />,
      title: "Review Detected Differences",
      description: "Inspect highlighted variances with clear side-by-side comparisons and straightforward explanations.",
    },
    {
      num: "05",
      icon: <Sparkles className="w-5 h-5 text-zinc-900" />,
      title: "Explore Official Guidance",
      description: "Consult the AI assistant grounded strictly in verified UIDAI, Income Tax, MEA, and EPFO guidelines.",
    },
    {
      num: "06",
      icon: <FileCheck2 className="w-5 h-5 text-zinc-900" />,
      title: "Prepare Next Steps",
      description: "Download official application forms (Form 49A, Joint Declarations) and generate pre-filled draft correction letters.",
    },
  ];

  return (
    <section id="how-it-works" className="py-20 md:py-28 bg-white border-b border-[#e5e2dc]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-14">
        {/* Section Header */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-600">
            <span>The Workflow</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#18181b]">
            How CONVELINA guides your reconciliation.
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 leading-relaxed">
            A structured, privacy-first six-step progression from initial upload to official correction readiness.
          </p>
        </div>

        {/* 6 Steps Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {steps.map((s, idx) => (
            <div
              key={idx}
              className="p-7 rounded-2xl bg-[#faf9f6] border border-[#e5e2dc] shadow-card hover:shadow-elevated hover:translate-y-[-2px] transition duration-200 flex flex-col justify-between space-y-4 group"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-11 h-11 rounded-xl bg-white border border-[#e5e2dc] flex items-center justify-center group-hover:scale-105 transition">
                    {s.icon}
                  </div>
                  <span className="font-mono text-sm font-bold text-zinc-400">{s.num}</span>
                </div>
                <h3 className="text-base sm:text-lg font-semibold text-zinc-900">{s.title}</h3>
                <p className="text-xs sm:text-sm text-zinc-600 leading-relaxed">{s.description}</p>
              </div>

              <div className="pt-3 border-t border-zinc-200/50 flex items-center text-xs font-medium text-zinc-500">
                <span>Step {idx + 1} of 6</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

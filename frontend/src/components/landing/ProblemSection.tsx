"use client";

import React from "react";
import { AlertCircle, HelpCircle, FileX2, Compass } from "lucide-react";

export default function ProblemSection() {
  const problems = [
    {
      icon: <FileX2 className="w-5 h-5 text-zinc-900" />,
      title: "Inconsistent Name Formatting",
      description:
        "Initials expanded in one document (such as 'K. Ramanathan') but abbreviated or omitted in another ('Ramanathan Kumar') frequently cause automated verification failures during passport issuance, job onboarding, or bank KYC.",
    },
    {
      icon: <AlertCircle className="w-5 h-5 text-zinc-900" />,
      title: "Date of Birth & Typographical Variations",
      description:
        "Minor clerical variations in birth dates or parent names between school records, PAN cards, and Aadhaar prevent digital linking (such as PAN-Aadhaar linking) without explaining why the mismatch occurred.",
    },
    {
      icon: <HelpCircle className="w-5 h-5 text-zinc-900" />,
      title: "Multiple Government Portals",
      description:
        "Knowing which agency has authority—UIDAI for Aadhaar, Income Tax/NSDL for PAN, MEA for Passports, or EPFO for Provident Fund—and which document legally serves as primary proof of identity can be confusing.",
    },
    {
      icon: <Compass className="w-5 h-5 text-zinc-900" />,
      title: "Uncertain Correction Procedures",
      description:
        "Citizens often spend weeks visiting administrative offices without knowing the exact affidavits, declarations, or prerequisite documents required before submitting their applications.",
    },
  ];

  return (
    <section className="py-20 md:py-28 bg-[#faf9f6] border-b border-[#e5e2dc]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Section Header */}
        <div className="space-y-4 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-600">
            <span>The Challenge</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#18181b] leading-tight">
            Clerical variance should not delay your life.
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 leading-relaxed">
            Indian citizens routinely face administrative delays due to minor clerical variations across documents issued years apart by different institutions.
          </p>
        </div>

        {/* 4 Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {problems.map((p, idx) => (
            <div
              key={idx}
              className="p-7 rounded-2xl bg-white border border-[#e5e2dc] shadow-card hover:shadow-elevated hover:translate-y-[-2px] transition duration-200 space-y-3.5"
            >
              <div className="w-11 h-11 rounded-xl bg-[#f5f3ef] border border-[#e5e2dc] flex items-center justify-center">
                {p.icon}
              </div>
              <h3 className="text-base sm:text-lg font-semibold text-zinc-900">{p.title}</h3>
              <p className="text-xs sm:text-sm text-zinc-600 leading-relaxed">{p.description}</p>
            </div>
          ))}
        </div>

        {/* Important Principle Note */}
        <div className="p-5 rounded-2xl border border-zinc-200 bg-[#f5f3ef]/70 text-xs sm:text-sm text-zinc-600 leading-relaxed flex items-start gap-3.5">
          <div className="w-2.5 h-2.5 rounded-full bg-zinc-800 shrink-0 mt-1.5" />
          <p>
            <strong className="text-zinc-900 font-semibold">A Vital Principle:</strong> A detected document discrepancy is never proof of fraud or proof that either record is invalid. Clerical variations represent normal administrative friction that can be systematically reconciled through legitimate statutory processes.
          </p>
        </div>
      </div>
    </section>
  );
}

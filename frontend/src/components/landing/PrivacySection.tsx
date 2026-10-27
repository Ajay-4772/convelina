"use client";

import React from "react";
import { Shield, Lock, EyeOff, FileKey, UserCheck } from "lucide-react";
import GlassCard from "../ui/glass/GlassCard";

export default function PrivacySection() {
  const principles = [
    {
      icon: <EyeOff className="w-5 h-5 text-zinc-900" />,
      title: "Automatic Identity Masking",
      desc: "Sensitive numbers like Aadhaar are automatically masked across all screens and logs so your full number is never displayed or exposed.",
    },
    {
      icon: <Lock className="w-5 h-5 text-zinc-900" />,
      title: "Ephemeral Document Handling",
      desc: "Uploaded document scans are processed in temporary memory and unlinked immediately after information extraction. We maintain zero long-term storage of raw identity images.",
    },
    {
      icon: <UserCheck className="w-5 h-5 text-zinc-900" />,
      title: "Private Account Isolation",
      desc: "Your records are strictly compartmentalized. Only you can view or access your uploaded document details, discrepancy reports, and personal notes.",
    },
    {
      icon: <FileKey className="w-5 h-5 text-zinc-900" />,
      title: "Encrypted Data Storage",
      desc: "All stored profile details and extracted information are strongly encrypted at rest to safeguard against unauthorized access.",
    },
  ];

  return (
    <section id="privacy" className="py-20 md:py-32 bg-[#faf9f6] border-b border-[#e5e2dc]/70">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Section Heading */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full liquid-glass text-xs font-semibold uppercase tracking-wider text-zinc-700 shadow-xs">
            <Shield className="w-3.5 h-3.5 text-zinc-900" />
            <span>Privacy &amp; Security</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#111111]">
            Designed for privacy, bound by trust.
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 leading-relaxed">
            CONVELINA implements rigorous safeguards to protect residents&apos; personal data while assisting with document rectifications.
          </p>
        </div>

        {/* 4 Clean Glass Safeguard Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {principles.map((p, idx) => (
            <GlassCard
              key={idx}
              className="p-8 space-y-3.5 rounded-3xl hover:border-white"
            >
              <div className="w-11 h-11 rounded-2xl bg-white border border-stone-200/80 flex items-center justify-center shadow-xs">
                {p.icon}
              </div>
              <h3 className="text-lg sm:text-xl font-serif font-semibold text-zinc-900">
                {p.title}
              </h3>
              <p className="text-xs sm:text-sm text-zinc-600 leading-relaxed font-normal">
                {p.desc}
              </p>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  );
}

"use client";

import React from "react";
import { Shield, Lock, EyeOff, Database, FileKey, History } from "lucide-react";

export default function SecurityPrivacy() {
  const safeguards = [
    {
      icon: <EyeOff className="w-5 h-5 text-zinc-900" />,
      title: "Automatic Identity Masking",
      desc: "Sensitive numbers like Aadhaar and PAN are automatically masked (showing only the last 4 digits) across all user interfaces, logs, and database records to minimize identity exposure.",
    },
    {
      icon: <Lock className="w-5 h-5 text-zinc-900" />,
      title: "Ephemeral Document Handling",
      desc: "Uploaded identity document images are processed strictly in temporary memory and promptly unlinked after information extraction. We do not maintain long-term cloud storage of raw document scans.",
    },
    {
      icon: <Database className="w-5 h-5 text-zinc-900" />,
      title: "Isolated Account Privacy",
      desc: "Your data is strictly partitioned and isolated. Only you can view or access your uploaded document details, discrepancy reports, and personal drafts through verified authentication.",
    },
    {
      icon: <FileKey className="w-5 h-5 text-zinc-900" />,
      title: "Encrypted Data Storage",
      desc: "All stored profile details and extracted information are strongly encrypted at rest, ensuring that unauthorized parties cannot access or read your records.",
    },
    {
      icon: <History className="w-5 h-5 text-zinc-900" />,
      title: "Protected Activity History",
      desc: "Every reconciliation action and profile update is recorded in a protected, append-only history log that prevents unauthorized tampering or deletion.",
    },
    {
      icon: <Shield className="w-5 h-5 text-zinc-900" />,
      title: "Strict Role Separation",
      desc: "Only two roles exist across the system: Citizen and Admin. Public registration strictly provisions standard citizen accounts, with administrative access secured independently on a dedicated portal.",
    },
  ];

  return (
    <section id="security" className="py-20 md:py-28 bg-white border-b border-[#e5e2dc]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        {/* Section Header */}
        <div className="space-y-4 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-600">
            <span>Security & Privacy</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#18181b]">
            Engineered around privacy, bound by trust.
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 leading-relaxed">
            CONVELINA implements defense-in-depth safeguards designed specifically to protect residents&apos; personal data while assisting with document rectifications.
          </p>
        </div>

        {/* 6 Safeguards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {safeguards.map((s, idx) => (
            <div
              key={idx}
              className="p-7 rounded-2xl bg-[#faf9f6] border border-[#e5e2dc] shadow-card hover:shadow-elevated transition space-y-3.5"
            >
              <div className="w-11 h-11 rounded-xl bg-white border border-[#e5e2dc] flex items-center justify-center">
                {s.icon}
              </div>
              <h3 className="text-base sm:text-lg font-semibold text-zinc-900">{s.title}</h3>
              <p className="text-xs sm:text-sm text-zinc-600 leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>

        {/* Honest Security Disclaimer */}
        <div className="p-6 rounded-2xl border border-zinc-200 bg-[#f5f3ef]/80 text-xs sm:text-sm text-zinc-600 leading-relaxed space-y-2">
          <p className="font-semibold text-zinc-900">Transparency Notice:</p>
          <p>
            No digital system can truthfully claim to be completely impenetrable. CONVELINA minimizes risk by operating under the principle of least privilege, deleting raw document scans immediately after text extraction, and strictly compartmentalizing database access.
          </p>
        </div>
      </div>
    </section>
  );
}

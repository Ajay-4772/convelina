"use client";

import React from "react";
import Link from "next/link";
import { 
  GitCompare, 
  Sparkles, 
  FileText, 
  FileEdit, 
  ShieldCheck, 
  LayoutDashboard,
  ArrowRight
} from "lucide-react";

export default function FeaturesGrid() {
  const features = [
    {
      icon: <GitCompare className="w-5 h-5 text-zinc-900" />,
      title: "Document Inconsistency Detection",
      badge: "Automated Matching",
      description:
        "Cross-compares demographic details across your Aadhaar, PAN, Passport, Educational certificates, and EPF records, identifying spelling variations, initial expansions, and date of birth differences.",
      cta: "Explore Detection",
      href: "/signup",
    },
    {
      icon: <Sparkles className="w-5 h-5 text-zinc-900" />,
      title: "Official Procedure Assistant",
      badge: "Grounded Guidance",
      description:
        "Ask questions about official correction procedures and receive clear, step-by-step guidance grounded strictly in verified government circulars and regulations.",
      cta: "Ask Guidance",
      href: "/signup",
    },
    {
      icon: <FileText className="w-5 h-5 text-zinc-900" />,
      title: "Official Forms Repository",
      badge: "Verified Forms",
      description:
        "Direct access to authentic government applications including NSDL Form 49A, EPFO Joint Declarations, MEA Annexure-E, and UIDAI update guidelines with prerequisites.",
      cta: "Browse Forms",
      href: "/signup",
    },
    {
      icon: <FileEdit className="w-5 h-5 text-zinc-900" />,
      title: "Correction Affidavit Drafts",
      badge: "Correction Letters",
      description:
        "Generate standardized, pre-filled legal affidavit drafts in PDF and DOCX format specifying the exact clerical discrepancy and required justification for your submission.",
      cta: "Generate Drafts",
      href: "/signup",
    },
    {
      icon: <ShieldCheck className="w-5 h-5 text-zinc-900" />,
      title: "Strict Identity Safeguards",
      badge: "Privacy First",
      description:
        "Your privacy is protected at every step. Uploaded scans are unlinked immediately after text extraction, sensitive numbers are masked, and data is encrypted at rest.",
      cta: "View Security",
      href: "#security",
    },
    {
      icon: <LayoutDashboard className="w-5 h-5 text-zinc-900" />,
      title: "Private Citizen Workspace",
      badge: "Citizen Workspace",
      description:
        "A focused, private environment to manage your identity records, review reconciliation progress, track your change history, and access official guidance.",
      cta: "Open Workspace",
      href: "/signup",
    },
  ];

  return (
    <section id="features" className="py-20 md:py-28 bg-[#faf9f6] border-b border-[#e5e2dc]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-14">
        {/* Section Header */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-600">
            <span>Core Capabilities</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#18181b]">
            Comprehensive tooling for document clarity.
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 leading-relaxed">
            Every feature is purposefully designed to provide actionable, verified assistance without overstepping statutory legal boundaries.
          </p>
        </div>

        {/* 6 Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, idx) => (
            <div
              key={idx}
              className="p-7 rounded-2xl bg-white border border-[#e5e2dc] shadow-card hover:shadow-elevated hover:translate-y-[-2px] transition duration-200 flex flex-col justify-between space-y-5"
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="w-11 h-11 rounded-xl bg-[#f5f3ef] border border-[#e5e2dc] flex items-center justify-center">
                    {f.icon}
                  </div>
                  <span className="text-xs font-medium px-2.5 py-1 rounded-md bg-zinc-100 text-zinc-700 border border-zinc-200">
                    {f.badge}
                  </span>
                </div>
                <h3 className="text-base sm:text-lg font-semibold text-zinc-900">{f.title}</h3>
                <p className="text-xs sm:text-sm text-zinc-600 leading-relaxed">{f.description}</p>
              </div>

              <div className="pt-3 border-t border-zinc-100">
                <Link
                  href={f.href}
                  className="inline-flex items-center gap-2 text-xs sm:text-sm font-semibold text-[#18181b] hover:text-zinc-600 transition"
                >
                  <span>{f.cta}</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

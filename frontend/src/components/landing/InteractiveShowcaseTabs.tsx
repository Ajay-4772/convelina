"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  FileText,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  ShieldCheck,
  FileSpreadsheet,
  ExternalLink,
} from "lucide-react";
import LiquidGlass from "../ui/glass/LiquidGlass";

interface TabItem {
  id: string;
  title: string;
  subtitle: string;
  badge: string;
  docA: { name: string; type: string; value: string; field: string };
  docB: { name: string; type: string; value: string; field: string };
  discrepancyType: string;
  severity: "low" | "medium" | "high";
  explanation: string;
  statutoryAction: string;
  officialForm: string;
}

const SHOWCASE_TABS: TabItem[] = [
  {
    id: "aadhaar-pan",
    title: "Aadhaar vs PAN Discrepancy",
    subtitle: "Name Transliteration & Initial Expansion",
    badge: "Identity Core",
    docA: {
      name: "Aadhaar e-KYC (UIDAI)",
      type: "Primary ID",
      field: "Full Name",
      value: "KUMAR, RAJESH V.",
    },
    docB: {
      name: "PAN Card (Income Tax NSDL)",
      type: "Tax ID",
      field: "Applicant Name",
      value: "RAJESH VENKATRAMAN KUMAR",
    },
    discrepancyType: "Father's Middle Initial Expanded",
    severity: "low",
    explanation:
      "Clerical expansion of initial 'V.' to 'VENKATRAMAN' detected. Both refer to identical identity records without fraud indicators.",
    statutoryAction:
      "Submit Online NSDL PAN Change Request (Form 49A Reprint) with Aadhaar e-Sign authentication.",
    officialForm: "Income Tax Form 49A",
  },
  {
    id: "epfo-dob",
    title: "EPFO Service Records",
    subtitle: "Date of Birth & Joint Declaration",
    badge: "Provident Fund",
    docA: {
      name: "EPFO Unified Member Portal",
      type: "UAN Record",
      field: "Date of Birth",
      value: "14/05/1992",
    },
    docB: {
      name: "Class 10 CBSE Certificate",
      type: "Statutory Proof",
      field: "Date of Birth",
      value: "15/05/1992",
    },
    discrepancyType: "1-Day Transposition in DOB Record",
    severity: "medium",
    explanation:
      "Discrepancy is within the standard 3-year correction window under EPFO Circular No. WSU/2022/1/JointDeclaration.",
    statutoryAction:
      "Generate EPFO Joint Declaration Form signed by current or previous employer with School Leaving Certificate.",
    officialForm: "EPFO Joint Declaration V2",
  },
  {
    id: "passport-degree",
    title: "Passport vs Degree",
    subtitle: "Surname Splitting & MEA Standards",
    badge: "Immigration & MEA",
    docA: {
      name: "Passport Seva Kendra Record",
      type: "Travel Doc",
      field: "Given Name / Surname",
      value: "Given: AJAY / Surname: SHARMA",
    },
    docB: {
      name: "University Degree Certificate",
      type: "Academic Record",
      field: "Candidate Name",
      value: "AJAY KUMAR SHARMA",
    },
    discrepancyType: "Omission of Middle Name 'KUMAR'",
    severity: "low",
    explanation:
      "MEA Passport Manual allows Annexure-E Deed Poll affidavit or matching Aadhaar verification for minor name variations.",
    statutoryAction:
      "Apply for Passport Re-issue under 'Change in Name / Correction' with self-declaration Annexure E.",
    officialForm: "MEA Annexure E Affidavit",
  },
  {
    id: "voter-ration",
    title: "Voter ID vs Domicile",
    subtitle: "Address & Family Head Mapping",
    badge: "State Portal",
    docA: {
      name: "Election Commission EPIC",
      type: "Voter Record",
      field: "House / Ward",
      value: "Flat 402, Green Meadows, Pune - 411038",
    },
    docB: {
      name: "State Domicile Certificate",
      type: "Revenue Dept",
      field: "Permanent Residence",
      value: "Plot 12, Shivtirth Nagar, Pune - 411038",
    },
    discrepancyType: "Local Residence Address Drift",
    severity: "low",
    explanation:
      "NVSP Form 8 handles online shifting of residence within the same assembly constituency instantly with electricity bill proof.",
    statutoryAction:
      "Submit ECI Form 8 on electors.eci.gov.in with geo-tagged residential utility invoice.",
    officialForm: "ECI Form 8 (Correction of Entries)",
  },
];

export default function InteractiveShowcaseTabs() {
  const [activeIdx, setActiveIdx] = useState(0);
  const [progress, setProgress] = useState(0);

  // 5-second automatic progression matching Notch.so
  useEffect(() => {
    setProgress(0);
    const intervalTime = 50; // update progress every 50ms
    const totalDuration = 5000;
    const increment = (intervalTime / totalDuration) * 100;

    const timer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          setActiveIdx((current) => (current + 1) % SHOWCASE_TABS.length);
          return 0;
        }
        return prev + increment;
      });
    }, intervalTime);

    return () => clearInterval(timer);
  }, [activeIdx]);

  const activeTab = SHOWCASE_TABS[activeIdx];

  return (
    <section className="py-20 md:py-28 bg-[#f5f3ef]/80 border-b border-[#e5e2dc] relative overflow-hidden">
      {/* Background Ambience */}
      <div className="absolute top-1/2 -left-40 -translate-y-1/2 w-[500px] h-[500px] bg-amber-100/40 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-10 right-0 w-[450px] h-[450px] bg-stone-200/50 rounded-full blur-[90px] pointer-events-none" />

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12 relative z-10">
        {/* Section Title */}
        <div className="text-center space-y-3 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/90 border border-[#e5e2dc] text-xs font-semibold uppercase tracking-wider text-zinc-700 shadow-xs">
            <Sparkles className="w-3.5 h-3.5 text-zinc-900" />
            <span>Interactive Discrepancy Engine</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#18181b] tracking-tight">
            See how CONVELINA analyzes records.
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 leading-relaxed max-w-2xl mx-auto">
            CONVELINA breaks down cross-departmental mismatches into clear, actionable, non-judgmental guidance with official forms.
          </p>
        </div>

        {/* 2-Column Notch Showcase Layout: Pinned Tabs Left / Dynamic Live Card Right */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Notch Auto-cycling Tabs Menu */}
          <div className="lg:col-span-5 space-y-3">
            {SHOWCASE_TABS.map((tab, idx) => {
              const isActive = activeIdx === idx;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    setActiveIdx(idx);
                    setProgress(0);
                  }}
                  className={`w-full text-left p-5 rounded-2xl transition-all duration-300 relative overflow-hidden border ${
                    isActive
                      ? "bg-white text-zinc-900 border-[#18181b]/20 shadow-floating"
                      : "bg-white/40 hover:bg-white/70 text-zinc-600 border-[#e5e2dc]/60"
                  }`}
                >
                  {/* Notch 5-second Active Progress Bar */}
                  {isActive && (
                    <div
                      className="absolute bottom-0 left-0 h-[3px] bg-[#18181b] transition-all duration-75"
                      style={{ width: `${progress}%` }}
                    />
                  )}

                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                      {tab.badge}
                    </span>
                    {isActive && (
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                    )}
                  </div>

                  <h3
                    className={`text-base sm:text-lg font-medium mt-1 ${
                      isActive ? "text-zinc-950 font-semibold" : "text-zinc-700"
                    }`}
                  >
                    {tab.title}
                  </h3>
                  <p className="text-xs sm:text-sm text-zinc-500 mt-0.5 line-clamp-1">
                    {tab.subtitle}
                  </p>
                </button>
              );
            })}
          </div>

          {/* Right Column: Live Discrepancy Diffing Canvas */}
          <div className="lg:col-span-7">
            <LiquidGlass
              variant="prominent"
              className="p-5 sm:p-8 rounded-3xl min-h-0 sm:min-h-[480px] flex flex-col justify-between"
            >
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab.id}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -15 }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                  className="space-y-6"
                >
                  {/* Top Status Banner */}
                  <div className="flex items-center justify-between pb-4 border-b border-[#e5e2dc]">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-700 flex items-center justify-center font-semibold text-xs border border-amber-500/20">
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                      <div>
                        <div className="text-xs uppercase tracking-wider text-zinc-500 font-semibold">
                          Detected Difference
                        </div>
                        <div className="text-sm font-semibold text-zinc-900">
                          {activeTab.discrepancyType}
                        </div>
                      </div>
                    </div>
                    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-zinc-100 text-zinc-700 border border-zinc-200">
                      Non-Judgmental Flag
                    </span>
                  </div>

                  {/* Side-by-Side Document Comparison Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Document A */}
                    <div className="p-4 rounded-2xl bg-[#faf9f6] border border-[#e5e2dc] space-y-2">
                      <div className="flex items-center justify-between text-xs text-zinc-500">
                        <span className="font-semibold">{activeTab.docA.type}</span>
                        <FileText className="w-3.5 h-3.5 text-zinc-400" />
                      </div>
                      <div className="text-xs font-medium text-zinc-700">
                        {activeTab.docA.name}
                      </div>
                      <div className="pt-2 border-t border-[#e5e2dc]/60">
                        <div className="text-[11px] text-zinc-400 uppercase">
                          {activeTab.docA.field}
                        </div>
                        <div className="text-sm font-mono font-semibold text-zinc-900 mt-0.5">
                          {activeTab.docA.value}
                        </div>
                      </div>
                    </div>

                    {/* Document B */}
                    <div className="p-4 rounded-2xl bg-[#faf9f6] border border-[#e5e2dc] space-y-2">
                      <div className="flex items-center justify-between text-xs text-zinc-500">
                        <span className="font-semibold">{activeTab.docB.type}</span>
                        <FileSpreadsheet className="w-3.5 h-3.5 text-zinc-400" />
                      </div>
                      <div className="text-xs font-medium text-zinc-700">
                        {activeTab.docB.name}
                      </div>
                      <div className="pt-2 border-t border-[#e5e2dc]/60">
                        <div className="text-[11px] text-zinc-400 uppercase">
                          {activeTab.docB.field}
                        </div>
                        <div className="text-sm font-mono font-semibold text-zinc-900 mt-0.5">
                          {activeTab.docB.value}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Grounded Explanation */}
                  <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-200/50 space-y-1">
                    <div className="text-xs font-semibold text-amber-900 flex items-center gap-1.5">
                      <ShieldCheck className="w-4 h-4 text-amber-700" />
                      Context &amp; Legal Interpretation
                    </div>
                    <p className="text-xs sm:text-sm text-amber-950 leading-relaxed">
                      {activeTab.explanation}
                    </p>
                  </div>

                  {/* Resolution Pathway & Official Form */}
                  <div className="pt-2 space-y-2">
                    <div className="text-xs font-semibold uppercase tracking-wider text-zinc-500">
                      Recommended Official Pathway
                    </div>
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 p-3.5 rounded-2xl bg-zinc-900 text-white">
                      <div className="space-y-0.5">
                        <div className="text-xs text-zinc-400 font-mono">
                          {activeTab.officialForm}
                        </div>
                        <div className="text-xs sm:text-sm font-medium text-zinc-200">
                          {activeTab.statutoryAction}
                        </div>
                      </div>
                      <span className="shrink-0 inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-xl bg-white text-zinc-950 hover:bg-zinc-100 transition-colors">
                        View Steps
                        <ExternalLink className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                </motion.div>
              </AnimatePresence>
            </LiquidGlass>
          </div>
        </div>
      </div>
    </section>
  );
}

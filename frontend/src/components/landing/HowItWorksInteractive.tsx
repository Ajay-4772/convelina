"use client";

import React, { useState } from "react";
import { 
  UploadCloud, 
  ScanText, 
  GitCompare, 
  AlertTriangle, 
  Sparkles, 
  FileCheck2,
  ChevronRight,
} from "lucide-react";
import LiquidGlass from "../ui/glass/LiquidGlass";

export default function HowItWorksInteractive() {
  const [activeStep, setActiveStep] = useState<number>(0);

  const steps = [
    {
      num: "01",
      icon: <UploadCloud className="w-5 h-5 text-zinc-900" />,
      title: "Upload Documents",
      shortDesc: "Securely upload digital scans or photos in PDF, JPG, or PNG format.",
      fullDesc:
        "Upload your identity documents into temporary processing memory. Supported categories include Aadhaar Cards, PAN Cards, Passports, Educational Marksheets, and EPF records.",
      highlight: "Temporary Memory Processing",
    },
    {
      num: "02",
      icon: <ScanText className="w-5 h-5 text-zinc-900" />,
      title: "Extract Information",
      shortDesc: "Text extraction reads demographic attributes with automated privacy masking.",
      fullDesc:
        "Our extraction engine reads relevant demographic attributes (full name, date of birth, gender, parent names) while automatically masking sensitive numbers like Aadhaar so full numbers are never exposed.",
      highlight: "Automatic Identity Masking",
    },
    {
      num: "03",
      icon: <GitCompare className="w-5 h-5 text-zinc-900" />,
      title: "Compare Record Details",
      shortDesc: "Smart matching evaluates name permutations, initials, and date formats.",
      fullDesc:
        "Multi-dimensional comparison matches records across your documents, recognizing expanded initials, spelling variations, and date format differences.",
      highlight: "Initial Expansion Recognition",
    },
    {
      num: "04",
      icon: <AlertTriangle className="w-5 h-5 text-zinc-900" />,
      title: "Review Detected Differences",
      shortDesc: "Inspect highlighted variances with clear side-by-side explanations.",
      fullDesc:
        "Review clear side-by-side comparison cards highlighting the exact nature of the clerical discrepancy, without false fraud claims or invalid assumptions.",
      highlight: "Non-Judgmental Flagging",
    },
    {
      num: "05",
      icon: <Sparkles className="w-5 h-5 text-zinc-900" />,
      title: "Explore Official Guidance",
      shortDesc: "Consult the AI assistant grounded in verified government circulars.",
      fullDesc:
        "Ask the AI assistant about official rectification procedures. Guidance is grounded strictly in verified statutory regulations from UIDAI, Income Tax, MEA, and EPFO.",
      highlight: "Verified Statutory Sourcing",
    },
    {
      num: "06",
      icon: <FileCheck2 className="w-5 h-5 text-zinc-900" />,
      title: "Access Official Forms",
      shortDesc: "Download authentic government applications and prerequisites checklists.",
      fullDesc:
        "Access direct links to authentic government portals (such as NSDL Form 49A or EPFO Joint Declarations) along with clear submission prerequisites.",
      highlight: "Direct Portal Downloads",
    },
  ];

  return (
    <section id="how-it-works" className="py-20 md:py-32 bg-[#faf9f6] border-b border-[#e5e2dc]/70">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        {/* Section Heading */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full liquid-glass text-xs font-semibold uppercase tracking-wider text-zinc-700 shadow-xs">
            <span>The Workflow</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#111111]">
            How CONVELINA guides your reconciliation.
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 leading-relaxed">
            A structured, privacy-first six-stage progression from initial upload to official correction readiness.
          </p>
        </div>

        {/* Interactive Step Navigator */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Column: Step List Navigator */}
          <div className="lg:col-span-6 space-y-3">
            {steps.map((step, idx) => {
              const isActive = activeStep === idx;
              return (
                <button
                  key={idx}
                  onClick={() => setActiveStep(idx)}
                  className={`
                    w-full text-left p-4 sm:p-5 rounded-2xl transition-all duration-300 flex items-center justify-between border
                    ${
                      isActive
                        ? "bg-[#111111] text-white border-zinc-900 shadow-elevated scale-[1.01]"
                        : "liquid-glass-subtle text-zinc-700 hover:bg-white/80 hover:border-white"
                    }
                  `}
                >
                  <div className="flex items-center gap-3.5">
                    <span
                      className={`font-mono text-xs font-bold px-2.5 py-1 rounded-full ${
                        isActive
                          ? "bg-zinc-800 text-zinc-200"
                          : "bg-stone-200/80 text-zinc-700"
                      }`}
                    >
                      {step.num}
                    </span>
                    <div>
                      <h4
                        className={`text-sm sm:text-base font-semibold ${
                          isActive ? "text-white" : "text-zinc-900"
                        }`}
                      >
                        {step.title}
                      </h4>
                      <p
                        className={`text-xs mt-0.5 hidden sm:block ${
                          isActive ? "text-zinc-300" : "text-zinc-500"
                        }`}
                      >
                        {step.shortDesc}
                      </p>
                    </div>
                  </div>

                  <ChevronRight
                    className={`w-4 h-4 transition-transform duration-200 ${
                      isActive ? "rotate-90 text-white" : "text-zinc-400"
                    }`}
                  />
                </button>
              );
            })}
          </div>

          {/* Right Column: Active Stage Display Card */}
          <div className="lg:col-span-6">
            <LiquidGlass variant="prominent" className="p-8 sm:p-10 space-y-6 rounded-3xl shadow-floating">
              <div className="flex items-center justify-between">
                <div className="w-12 h-12 rounded-2xl bg-white border border-stone-200/80 flex items-center justify-center shadow-xs">
                  {steps[activeStep].icon}
                </div>
                <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-emerald-100/90 text-emerald-900 border border-emerald-300/80">
                  {steps[activeStep].highlight}
                </span>
              </div>

              <div className="space-y-2">
                <span className="text-xs font-mono text-zinc-400 font-bold tracking-wider uppercase">
                  Stage {steps[activeStep].num} of 06
                </span>
                <h3 className="text-2xl sm:text-3xl font-serif text-zinc-900 tracking-tight">
                  {steps[activeStep].title}
                </h3>
              </div>

              <p className="text-sm sm:text-base text-zinc-600 leading-relaxed font-normal">
                {steps[activeStep].fullDesc}
              </p>

              <div className="pt-4 border-t border-stone-200/60 flex items-center justify-between">
                <span className="text-xs text-zinc-500">Structured Statutory Flow</span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setActiveStep((prev) => (prev > 0 ? prev - 1 : steps.length - 1))}
                    className="px-3.5 py-1.5 rounded-full border border-stone-300 text-xs font-semibold text-zinc-700 bg-white/70 hover:bg-white transition"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setActiveStep((prev) => (prev < steps.length - 1 ? prev + 1 : 0))}
                    className="px-4 py-1.5 rounded-full bg-[#111111] text-white text-xs font-semibold hover:bg-zinc-800 transition"
                  >
                    Next Stage
                  </button>
                </div>
              </div>
            </LiquidGlass>
          </div>
        </div>
      </div>
    </section>
  );
}

"use client";

import React from "react";

export default function AboutSection() {
  return (
    <section className="py-20 md:py-28 bg-[#faf9f6] border-b border-[#e5e2dc]">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-zinc-600">
            <span>Mission & Purpose</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#18181b]">
            Demystifying government correction procedures.
          </h2>
        </div>

        <div className="text-sm sm:text-base text-zinc-600 leading-relaxed space-y-4 font-normal">
          <p>
            CONVELINA was created to address an everyday reality experienced by millions of residents: the complexity of reconciling clerical inconsistencies across primary identity records. A single misspelled character or altered surname between school certificates, PAN cards, and Aadhaar often results in delayed government schemes, deferred employment onboarding, or rejected passport applications.
          </p>
          <p>
            Rather than leaving citizens to navigate confusing, fragmented administrative portals on their own, CONVELINA provides a clear, structured analytical tool. We compare your records, highlight the exact nature of the variance, identify the relevant statutory authority, and point you directly to the verified forms and procedural steps required.
          </p>
          <p>
            Our core mission is straightforward: to bring transparency, clarity, and peace of mind to personal document management through thoughtful software design and rigorous data privacy.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 pt-6 border-t border-zinc-200">
          <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-xs">
            <h4 className="text-sm font-semibold text-zinc-900 mb-1.5">Clarity First</h4>
            <p className="text-xs sm:text-sm text-zinc-500">Transform confusing circulars into step-by-step guidance.</p>
          </div>
          <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-xs">
            <h4 className="text-sm font-semibold text-zinc-900 mb-1.5">Privacy by Design</h4>
            <p className="text-xs sm:text-sm text-zinc-500">Document scans are processed in memory and promptly unlinked.</p>
          </div>
          <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-xs">
            <h4 className="text-sm font-semibold text-zinc-900 mb-1.5">Authentic Sourcing</h4>
            <p className="text-xs sm:text-sm text-zinc-500">Strictly grounded in verified UIDAI, Income Tax, MEA, and EPFO circulars.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

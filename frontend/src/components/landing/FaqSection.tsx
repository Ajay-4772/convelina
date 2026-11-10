"use client";

import React, { useState } from "react";
import { ChevronDown, MessageSquare, ArrowRight } from "lucide-react";
import Link from "next/link";

interface FaqItem {
  q: string;
  a: string;
}

export default function FaqSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const faqs: FaqItem[] = [
    {
      q: "What is CONVELINA?",
      a: "CONVELINA is an intelligent statutory document reconciliation platform designed to detect and resolve clerical discrepancies across primary Indian identity credentials. It allows you to cross-compare identity documents (Aadhaar, PAN, Passport, Educational certificates, and EPF records), understand clerical variations, find official forms, and receive step-by-step guidance on official correction procedures.",
    },
    {
      q: "Which document categories are supported?",
      a: "CONVELINA currently supports Indian Aadhaar Cards, Permanent Account Number (PAN) Cards, Indian Passports, Secondary & Higher Secondary Educational Marksheets (CBSE and State Boards), and Employees' Provident Fund (EPFO / UAN) records.",
    },
    {
      q: "Does CONVELINA automatically modify or correct my documents?",
      a: "No. Statutory identity documents can only be amended by their respective government authorities (such as UIDAI for Aadhaar or the Income Tax Department / NSDL for PAN). CONVELINA assists you by detecting the exact clerical variance, preparing pre-filled legal affidavit drafts, and providing the precise official instructions and forms needed for submission.",
    },
    {
      q: "Does CONVELINA submit applications directly to government portals on my behalf?",
      a: "No. CONVELINA does not submit data or applications to external government servers. You retain complete control over your identity. We provide direct links to authentic portals, verified form downloads, and formatted draft documentation so you can complete your submissions with confidence.",
    },
    {
      q: "How does document discrepancy detection work?",
      a: "When you upload document scans or photos, our extraction engine reads key demographic fields (full name, date of birth, gender, father's name). Intelligent comparison techniques evaluate the records to identify spelling variations, expanded initials, and date format differences.",
    },
    {
      q: "What does the AI Assistant do, and are its answers grounded in official sources?",
      a: "The AI Assistant provides guidance grounded strictly in verified government circulars and regulations from UIDAI, Income Tax, MEA, and EPFO. If verified information isn't available for a specific situation, it clearly lets you know instead of guessing.",
    },
    {
      q: "How are my uploaded identity documents handled and stored?",
      a: "Uploaded files are processed in temporary memory and unlinked immediately after text extraction. Raw document images are never stored in long-term cloud storage. Extracted Aadhaar numbers are masked to their final 4 digits ('XXXX-XXXX-1234'), and demographic details are encrypted at rest.",
    },
    {
      q: "Do I need an account to use CONVELINA?",
      a: "Yes. To ensure strict data isolation and privacy, a verified account (via email and OTP verification) is required. This ensures that your uploaded document records, conflict analysis reports, and affidavit drafts remain private and are accessible only by you.",
    },
  ];

  return (
    <section id="faq" className="py-20 md:py-28 bg-white border-b border-[#e5e2dc]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          {/* Notch-style Sticky Left Column */}
          <div className="lg:col-span-4 lg:sticky lg:top-28 space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-100 text-xs font-semibold uppercase tracking-wider text-zinc-700">
              <MessageSquare className="w-3.5 h-3.5 text-zinc-900" />
              <span>Questions &amp; Answers</span>
            </div>

            <div className="space-y-3">
              <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#18181b] leading-[1.1] is-pretty">
                Questions? <br />
                <span className="text-zinc-400 font-normal italic">
                  We&apos;re glad you asked.
                </span>
              </h2>
              <p className="text-sm sm:text-base text-zinc-600 leading-relaxed is-pretty">
                Transparent answers regarding platform capabilities, data isolation, and statutory boundaries.
              </p>
            </div>

            <div className="pt-2">
              <Link
                href="/signup"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-[#18181b] text-white text-xs sm:text-sm font-medium hover:bg-zinc-800 transition-colors shadow-elevated"
              >
                <span>Get started now</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* Right Column: Accordion Items */}
          <div className="lg:col-span-8 space-y-3.5">
            {faqs.map((faq, idx) => {
              const isOpen = openIndex === idx;
              return (
                <div
                  key={idx}
                  className="border border-[#e5e2dc] rounded-2xl overflow-hidden transition-all duration-200 bg-[#faf9f6]"
                >
                  <button
                    type="button"
                    onClick={() => setOpenIndex(isOpen ? null : idx)}
                    className="w-full px-6 py-5 text-left flex items-center justify-between gap-4 hover:bg-[#f5f3ef] transition-colors"
                    aria-expanded={isOpen}
                  >
                    <span className="text-sm sm:text-base font-semibold text-zinc-900">
                      {faq.q}
                    </span>
                    <div className="w-8 h-8 rounded-full bg-white border border-[#e5e2dc] flex items-center justify-center shrink-0 shadow-xs">
                      <ChevronDown
                        className={`w-4 h-4 text-zinc-600 transition-transform duration-300 ${
                          isOpen ? "rotate-180 text-zinc-950" : ""
                        }`}
                      />
                    </div>
                  </button>
                  {isOpen && (
                    <div className="px-6 pb-6 pt-1 bg-[#faf9f6] text-xs sm:text-sm text-zinc-600 leading-relaxed animate-in fade-in duration-200 border-t border-[#e5e2dc]/40">
                      {faq.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

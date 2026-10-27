"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import LiquidGlass from "../ui/glass/LiquidGlass";
import Logo from "../ui/Logo";

export default function FinalCTA() {
  return (
    <section className="py-20 md:py-32 bg-[#faf9f6] border-b border-[#e5e2dc]/70 relative overflow-hidden">
      {/* Ambient background glow */}
      <div className="pointer-events-none absolute -bottom-24 left-1/2 -translate-x-1/2 w-[700px] h-[350px] bg-gradient-to-t from-stone-200/40 via-amber-100/20 to-transparent blur-[80px] rounded-full" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-8 relative z-10">
        <LiquidGlass
          variant="prominent"
          className="p-10 sm:p-14 md:p-16 rounded-[2.5rem] shadow-floating space-y-8"
        >
          <div className="flex items-center justify-center mx-auto">
            <Logo size={48} showText={false} />
          </div>

          <div className="space-y-3 max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#111111] tracking-tight">
              Your documents, reconciled with clarity.
            </h2>
            <p className="text-base sm:text-lg text-zinc-600 font-normal leading-relaxed">
              Experience the ease and precision of CONVELINA. Compare your records, eliminate clerical discrepancies, and get guided resolution steps with verified official forms.
            </p>
          </div>

          <div className="pt-2 flex justify-center">
            <Link
              href="/signup"
              className="inline-flex items-center gap-2.5 px-9 py-4 rounded-full bg-[#111111] text-white text-sm sm:text-base font-semibold hover:bg-zinc-800 transition-all duration-200 shadow-elevated hover:shadow-floating hover:-translate-y-0.5 active:translate-y-0"
            >
              <span>Get started with CONVELINA</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </LiquidGlass>
      </div>
    </section>
  );
}

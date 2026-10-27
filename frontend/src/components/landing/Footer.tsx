"use client";

import React from "react";
import Link from "next/link";
import { Mail, ArrowUpRight } from "lucide-react";
import Logo from "../ui/Logo";

export default function Footer() {
  return (
    <footer className="bg-[#faf9f6] text-zinc-600 border-t border-[#e5e2dc]/70">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
          {/* Brand Info */}
          <div className="space-y-3.5 md:col-span-1">
            <Logo size={28} showTagline={true} textClassName="text-lg font-bold text-[#111111]" />
            <p className="text-xs sm:text-sm text-zinc-500 leading-relaxed font-normal">
              Privacy-first statutory document conflict detection and clerical correction guidance for Indian identity credentials.
            </p>
            <div className="flex items-center gap-2 text-xs sm:text-sm text-zinc-600 pt-1">
              <Mail className="w-4 h-4 text-zinc-400 shrink-0" />
              <a href="mailto:contact@convelina.com" className="hover:text-black transition">
                contact@convelina.com
              </a>
            </div>
          </div>

          {/* Column 1: Navigation */}
          <div className="space-y-3 text-xs sm:text-sm">
            <h4 className="font-semibold text-zinc-900 uppercase tracking-wider text-xs">Platform</h4>
            <ul className="space-y-2 text-zinc-600">
              <li>
                <a href="#capabilities" className="hover:text-black transition">Capabilities</a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-black transition">How It Works</a>
              </li>
              <li>
                <a href="#video-preview" className="hover:text-black transition">Overview</a>
              </li>
              <li>
                <Link href="/login" className="hover:text-black transition">Sign In</Link>
              </li>
            </ul>
          </div>

          {/* Column 2: Supported Authorities */}
          <div className="space-y-3 text-xs sm:text-sm">
            <h4 className="font-semibold text-zinc-900 uppercase tracking-wider text-xs">Statutory Standards</h4>
            <ul className="space-y-2 text-zinc-600">
              <li>UIDAI Aadhaar Regulations</li>
              <li>Income Tax / NSDL PAN Portal</li>
              <li>Passport Seva (MEA India)</li>
              <li>EPFO Joint Declarations</li>
              <li>CBSE Student Rectifications</li>
            </ul>
          </div>

          {/* Column 3: Trust & Privacy */}
          <div className="space-y-3 text-xs sm:text-sm">
            <h4 className="font-semibold text-zinc-900 uppercase tracking-wider text-xs">Security &amp; Legal</h4>
            <ul className="space-y-2 text-zinc-600">
              <li>
                <a href="#privacy" className="hover:text-black transition">Privacy Safeguards</a>
              </li>
              <li>
                <a href="#privacy" className="hover:text-black transition">Ed25519 PKI Verification</a>
              </li>
              <li>
                <span className="text-zinc-500">Append-Only Audit Trail</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Disclaimer & Copyright */}
        <div className="pt-8 border-t border-[#e5e2dc] flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-zinc-500">
          <p>© {new Date().getFullYear()} CONVELINA. All rights reserved.</p>
          <p className="text-center sm:text-right text-zinc-400 max-w-xl">
            Disclaimer: CONVELINA is an independent identity document reconciliation and verification platform. It is not affiliated with UIDAI, the Income Tax Department, EPFO, or any statutory authority.
          </p>
        </div>
      </div>
    </footer>
  );
}

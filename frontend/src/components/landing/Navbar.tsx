"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import Logo from "../ui/Logo";

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { firebaseUser, profile } = useAuth();

  return (
    <header className="sticky top-0 z-50 w-full px-4 sm:px-6 lg:px-8 pt-4 pb-2 transition-all duration-300">
      {/* Floating Notch-Style Liquid Glass Pill Bar */}
      <div className="max-w-5xl mx-auto rounded-full liquid-glass px-5 sm:px-7 py-2.5 flex items-center justify-between transition-all duration-300">
        {/* Brand Emblem */}
        <Logo size={28} textClassName="text-lg font-bold text-[#111111]" />

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-zinc-600">
          <a
            href="#capabilities"
            className="transition-colors hover:text-black"
          >
            Capabilities
          </a>
          <a
            href="#how-it-works"
            className="transition-colors hover:text-black"
          >
            How it works
          </a>
          <a
            href="#video-preview"
            className="transition-colors hover:text-black"
          >
            Overview
          </a>
          <a
            href="#privacy"
            className="transition-colors hover:text-black"
          >
            Privacy
          </a>
        </nav>

        {/* Desktop Actions */}
        <div className="hidden md:flex items-center gap-3">
          {firebaseUser ? (
            <Link
              href={profile?.role === "admin" ? "/admin" : "/app"}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#111111] text-white text-sm font-semibold hover:bg-zinc-800 transition shadow-xs active:scale-[0.98]"
            >
              Go to {profile?.role === "admin" ? "Admin" : "Workspace"}
              <ArrowRight className="w-4 h-4" />
            </Link>
          ) : (
            <>
              <Link
                href="/login"
                className="px-4 py-2 text-sm font-medium text-zinc-700 hover:text-black transition"
              >
                Sign in
              </Link>
              <Link
                href="/signup"
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-full bg-[#111111] text-white text-sm font-semibold hover:bg-zinc-800 transition shadow-xs active:scale-[0.98]"
              >
                Get started
              </Link>
            </>
          )}
        </div>

        {/* Mobile Menu Trigger */}
        <div className="flex md:hidden">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-1.5 rounded-full text-zinc-700 hover:text-black hover:bg-white/60 transition"
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Glass Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden max-w-5xl mx-auto mt-2">
          <div className="liquid-glass-prominent rounded-3xl p-5 space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
            <nav className="flex flex-col space-y-3 text-sm font-medium text-zinc-800">
              <a
                href="#capabilities"
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-xl hover:bg-white/60 transition"
              >
                Capabilities
              </a>
              <a
                href="#how-it-works"
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-xl hover:bg-white/60 transition"
              >
                How it works
              </a>
              <a
                href="#video-preview"
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-xl hover:bg-white/60 transition"
              >
                Overview
              </a>
              <a
                href="#privacy"
                onClick={() => setMobileMenuOpen(false)}
                className="px-3 py-2 rounded-xl hover:bg-white/60 transition"
              >
                Privacy
              </a>
            </nav>

            <div className="pt-3 border-t border-zinc-200/60 flex flex-col gap-2.5">
              {firebaseUser ? (
                <Link
                  href={profile?.role === "admin" ? "/admin" : "/app"}
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 rounded-full bg-[#111111] text-white text-sm font-semibold hover:bg-zinc-800 transition shadow-xs"
                >
                  Go to Workspace
                </Link>
              ) : (
                <>
                  <Link
                    href="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2 text-sm font-medium text-zinc-800 bg-white/70 border border-white/80 rounded-full hover:bg-white transition"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/signup"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2.5 rounded-full bg-[#111111] text-white text-sm font-semibold hover:bg-zinc-800 transition shadow-xs"
                  >
                    Get started
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

"use client";

import React from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import Logo from "../ui/Logo";

interface AuthLayoutProps {
  children: React.ReactNode;
  title: string;
  subtitle: string;
}

export default function AuthLayout({ children, title, subtitle }: AuthLayoutProps) {
  return (
    <div className="min-h-screen bg-[#faf9f6] flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans selection:bg-[#111111] selection:text-white">
      {/* Top Brand & Back to Home */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="flex items-center justify-between mb-8">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-zinc-500 hover:text-zinc-900 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to CONVELINA</span>
          </Link>

          <Logo size={24} textClassName="text-sm font-bold text-[#111111]" />
        </div>

        <div className="text-center space-y-1.5">
          <h1 className="text-2xl sm:text-3xl font-serif text-[#18181b]">{title}</h1>
          <p className="text-xs sm:text-sm text-zinc-600">{subtitle}</p>
        </div>
      </div>

      {/* Main Form Container Card */}
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white py-8 px-6 sm:px-8 border border-[#e5e2dc] rounded-3xl shadow-card space-y-6">
          {children}
        </div>
      </div>
    </div>
  );
}

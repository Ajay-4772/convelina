"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";

interface LogoProps {
  size?: number;
  showText?: boolean;
  showTagline?: boolean;
  textClassName?: string;
  className?: string;
  href?: string;
  theme?: "light" | "dark" | "auto";
}

export default function Logo({
  size = 32,
  showText = true,
  showTagline = false,
  textClassName = "",
  className = "",
  href = "/",
  theme = "auto",
}: LogoProps) {
  const isDark = theme === "dark";

  const mark = (
    <div
      className="relative shrink-0 flex items-center justify-center transition-transform duration-200 group-hover:scale-105"
      style={{ width: size, height: size }}
    >
      <Image
        src="/logo.png"
        alt="CONVELINA Logo"
        width={size * 2}
        height={size * 2}
        className="w-full h-full object-contain"
        priority
      />
    </div>
  );

  const content = (
    <div className={`inline-flex items-center gap-2.5 group select-none ${className}`}>
      {mark}
      {showText && (
        <div className="flex flex-col leading-none">
          <span
            className={`font-bold tracking-tight ${
              textClassName || (isDark ? "text-white text-lg" : "text-[#111111] text-lg")
            }`}
          >
            CONVELINA
          </span>
          {showTagline && (
            <span className="text-[10px] tracking-wider uppercase font-medium text-zinc-400 mt-0.5">
              Document Reconciliation & Verification
            </span>
          )}
        </div>
      )}
    </div>
  );

  if (href) {
    return (
      <Link href={href} className="inline-flex items-center">
        {content}
      </Link>
    );
  }

  return content;
}

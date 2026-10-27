"use client";

import React from "react";
import LiquidGlass from "./LiquidGlass";

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  hoverScale?: boolean;
}

export default function GlassCard({
  children,
  className = "",
  hoverScale = true,
  ...props
}: GlassCardProps) {
  return (
    <LiquidGlass
      variant="medium"
      hoverEffect={hoverScale}
      className={`p-6 sm:p-8 rounded-3xl ${className}`}
      {...props}
    >
      {children}
    </LiquidGlass>
  );
}

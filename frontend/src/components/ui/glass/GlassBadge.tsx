"use client";

import React from "react";

interface GlassBadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  dotColor?: "emerald" | "blue" | "amber" | "zinc";
}

export default function GlassBadge({
  children,
  className = "",
  dotColor = "emerald",
  ...props
}: GlassBadgeProps) {
  const dotColors = {
    emerald: "bg-emerald-500",
    blue: "bg-blue-500",
    amber: "bg-amber-500",
    zinc: "bg-zinc-700",
  };

  return (
    <div
      className={`
        inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full
        bg-white/75 backdrop-blur-md border border-[#e5e2dc]/80
        text-xs font-medium text-zinc-800 shadow-glass
        transition-all duration-300 hover:bg-white/90 hover:border-zinc-300
        ${className}
      `}
      {...props}
    >
      <span className={`w-2 h-2 rounded-full ${dotColors[dotColor]} animate-pulse`} />
      <span>{children}</span>
    </div>
  );
}

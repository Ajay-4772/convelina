"use client";

import React from "react";

interface GlassButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
  variant?: "primary" | "glass" | "subtle";
  className?: string;
  size?: "sm" | "md" | "lg";
}

export default function GlassButton({
  children,
  variant = "glass",
  className = "",
  size = "md",
  ...props
}: GlassButtonProps) {
  const sizeClasses = {
    sm: "px-3.5 py-1.5 text-xs rounded-xl gap-1.5",
    md: "px-5 py-2.5 text-sm rounded-xl gap-2",
    lg: "px-7 py-3.5 text-base rounded-2xl gap-2.5",
  };

  const variantClasses = {
    primary:
      "bg-[#18181b] text-white hover:bg-zinc-800 shadow-elevated border border-zinc-700/50 hover:shadow-floating active:scale-[0.98]",
    glass:
      "bg-white/80 text-zinc-900 backdrop-blur-md border border-white/90 shadow-glass hover:bg-white hover:shadow-glass-hover hover:border-zinc-300 active:scale-[0.98]",
    subtle:
      "bg-transparent text-zinc-700 hover:text-black hover:bg-white/50 backdrop-blur-xs border border-transparent hover:border-white/50 active:scale-[0.98]",
  };

  return (
    <button
      className={`
        inline-flex items-center justify-center font-medium transition-all duration-200
        disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-zinc-900
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
      {...props}
    >
      {children}
    </button>
  );
}

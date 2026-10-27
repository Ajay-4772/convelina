"use client";

import React from "react";

interface LiquidGlassProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: "subtle" | "medium" | "prominent" | "panel";
  className?: string;
  hoverEffect?: boolean;
}

export default function LiquidGlass({
  children,
  variant = "medium",
  className = "",
  hoverEffect = false,
  ...props
}: LiquidGlassProps) {
  const variantClasses = {
    subtle: "liquid-glass-subtle",
    medium: "liquid-glass",
    prominent: "liquid-glass-prominent",
    panel: "liquid-glass bg-white/50 border-white/80",
  };

  return (
    <div
      className={`
        relative overflow-hidden transition-all duration-300
        ${variantClasses[variant]}
        ${hoverEffect ? "hover:bg-white/55 hover:border-white hover:shadow-floating hover:-translate-y-0.5" : ""}
        ${className}
      `}
      {...props}
    >
      {/* Top Specular Rim Reflection */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-white/90 to-transparent" />
      {children}
    </div>
  );
}

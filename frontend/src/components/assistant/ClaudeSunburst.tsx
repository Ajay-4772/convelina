"use client";

import React from "react";

interface ClaudeSunburstProps {
  className?: string;
  size?: number;
  color?: string;
}

/**
 * Exact replica of the terracotta radiating sunburst / asterisk brand mark
 * featured in the Claude conversational interface screenshots.
 */
export default function ClaudeSunburst({
  className = "w-8 h-8",
  size = 32,
  color = "#CC6B49",
}: ClaudeSunburstProps) {
  // 14 radiating rounded spokes
  const spokes = [
    0, 25.7, 51.4, 77.1, 102.8, 128.5, 154.2,
    180, 205.7, 231.4, 257.1, 282.8, 308.5, 334.2
  ];

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 36 36"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      {spokes.map((deg, index) => {
        const rad = (deg * Math.PI) / 180;
        const x1 = 18 + Math.cos(rad) * 4.6;
        const y1 = 18 + Math.sin(rad) * 4.6;
        const x2 = 18 + Math.cos(rad) * 14.8;
        const y2 = 18 + Math.sin(rad) * 14.8;
        return (
          <line
            key={index}
            x1={x1.toFixed(2)}
            y1={y1.toFixed(2)}
            x2={x2.toFixed(2)}
            y2={y2.toFixed(2)}
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
          />
        );
      })}
    </svg>
  );
}


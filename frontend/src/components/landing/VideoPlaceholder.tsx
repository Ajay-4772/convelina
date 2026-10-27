"use client";

import React, { useState, useEffect } from "react";
import { Video } from "lucide-react";
import LiquidGlass from "../ui/glass/LiquidGlass";

interface VideoPlaceholderProps {
  videoSrc?: string;
}

export default function VideoPlaceholder({
  videoSrc = "/videos/convelina-demo.mp4",
}: VideoPlaceholderProps) {
  const [hasVideo, setHasVideo] = useState<boolean>(false);

  useEffect(() => {
    if (videoSrc) {
      fetch(videoSrc, { method: "HEAD" })
        .then((res) => {
          if (res.ok && res.headers.get("content-type")?.includes("video")) {
            setHasVideo(true);
          }
        })
        .catch(() => {
          setHasVideo(false);
        });
    }
  }, [videoSrc]);

  return (
    <section id="video-preview" className="py-20 md:py-28 bg-[#faf9f6] border-b border-[#e5e2dc]/70">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        {/* Section Header */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full liquid-glass text-xs font-semibold uppercase tracking-wider text-zinc-700">
            <Video className="w-3.5 h-3.5 text-zinc-900" />
            <span>Platform Overview</span>
          </div>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-serif text-[#111111]">
            Experience document clarity.
          </h2>
          <p className="text-sm sm:text-base text-zinc-600 leading-relaxed">
            A walkthrough of CONVELINA&apos;s discrepancy detection, procedure guidance, and official forms repository.
          </p>
        </div>

        {/* Video Frame with Liquid Glass Bezel */}
        <LiquidGlass
          variant="prominent"
          className="p-3 sm:p-5 rounded-[2.5rem] shadow-floating"
        >
          <div className="relative w-full aspect-video rounded-3xl overflow-hidden bg-[#18181b] border border-zinc-800 shadow-inner flex items-center justify-center">
            {hasVideo ? (
              <video
                src={videoSrc}
                controls
                playsInline
                preload="metadata"
                className="w-full h-full object-cover"
              >
                Your browser does not support the video tag.
              </video>
            ) : (
              /* Clean minimalist placeholder */
              <div className="relative w-full h-full flex flex-col items-center justify-center text-center p-8 bg-gradient-to-b from-zinc-900 via-zinc-950 to-black text-zinc-400 select-none">
                <div 
                  className="absolute inset-0 opacity-20 pointer-events-none"
                  style={{
                    backgroundImage: "radial-gradient(rgba(255, 255, 255, 0.25) 1px, transparent 1px)",
                    backgroundSize: "24px 24px"
                  }}
                />

                <div className="relative z-10 space-y-4 max-w-md">
                  <div className="w-14 h-14 rounded-2xl bg-zinc-800/80 border border-zinc-700/60 flex items-center justify-center text-zinc-300 mx-auto shadow-elevated">
                    <Video className="w-6 h-6 text-zinc-400" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-base sm:text-lg font-medium text-white tracking-tight">
                      Product Demonstration
                    </h3>
                    <p className="text-xs sm:text-sm text-zinc-400 leading-relaxed">
                      Official product video walkthrough will appear here. Place video file at <code className="text-[11px] font-mono bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-300">/public/videos/convelina-demo.mp4</code>.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </LiquidGlass>
      </div>
    </section>
  );
}

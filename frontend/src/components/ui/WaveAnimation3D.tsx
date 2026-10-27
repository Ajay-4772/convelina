"use client";

import React, { useRef, useEffect } from "react";

interface WaveAnimation3DProps {
  opacity?: number;
  className?: string;
}

export default function WaveAnimation3D({
  opacity = 1.0,
  className = "",
}: WaveAnimation3DProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;
    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) return;

    let animationId: number;
    let isVisible = true;
    let dpr = Math.min(window.devicePixelRatio || 1, 2);

    let width = 0;
    let height = 0;

    const handleResize = () => {
      if (!canvas || !container) return;
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = container.offsetWidth;
      height = container.offsetHeight;
      canvas.width = width * dpr;
      canvas.height = height * dpr;
      ctx.scale(dpr, dpr);
    };

    handleResize();
    window.addEventListener("resize", handleResize);

    // Performance Optimization: Pause rendering when scrolled out of viewport
    const observer = new IntersectionObserver(
      ([entry]) => {
        isVisible = entry.isIntersecting;
        if (isVisible && !animationId) {
          render();
        }
      },
      { threshold: 0.05 }
    );
    observer.observe(container);

    let step = 0;
    const ribbons = 36;

    const render = () => {
      if (!isVisible) {
        animationId = 0;
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Light satin base gradient
      const bgGrad = ctx.createLinearGradient(0, 0, width, height);
      bgGrad.addColorStop(0, "#ffffff");
      bgGrad.addColorStop(0.4, "#f7f6f4");
      bgGrad.addColorStop(1, "#eeebe6");
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      step += 0.009;

      // Layered 3D undulating waves with volumetric fills & contrast contours
      for (let i = 0; i < ribbons; i++) {
        const progress = i / ribbons;
        const yBase = height * 0.22 + progress * height * 0.62;
        
        const points: { x: number; y: number }[] = [];
        for (let x = 0; x <= width + 24; x += 14) {
          const nx = x / width;
          const w1 = Math.sin(nx * 2.8 + step * 1.2 + progress * 2.4) * 55;
          const w2 = Math.cos(nx * 1.8 - step * 0.8 + progress * 3.1) * 40;
          const w3 = Math.sin(nx * 4.2 + step * 1.5) * 18;
          const y = yBase + w1 + w2 + w3;
          points.push({ x, y });
        }

        // 1. Soft volumetric gradient fill under ribbon
        if (i % 2 === 0 && points.length > 0) {
          ctx.beginPath();
          ctx.moveTo(points[0].x, points[0].y);
          for (let p = 1; p < points.length; p++) {
            ctx.lineTo(points[p].x, points[p].y);
          }
          ctx.lineTo(width, height);
          ctx.lineTo(0, height);
          ctx.closePath();

          const fillAlpha = Math.sin(progress * Math.PI) * 0.05 + 0.015;
          const fillGrad = ctx.createLinearGradient(0, yBase - 40, 0, height);
          fillGrad.addColorStop(0, `rgba(180, 180, 195, ${fillAlpha * 1.5})`);
          fillGrad.addColorStop(0.5, `rgba(215, 215, 222, ${fillAlpha})`);
          fillGrad.addColorStop(1, `rgba(245, 245, 247, 0)`);
          ctx.fillStyle = fillGrad;
          ctx.fill();
        }

        // 2. High-contrast ash/slate ribbon contours
        ctx.beginPath();
        if (points.length > 0) {
          ctx.moveTo(points[0].x, points[0].y);
          for (let p = 1; p < points.length; p++) {
            ctx.lineTo(points[p].x, points[p].y);
          }
        }

        const strokeAlpha = Math.sin(progress * Math.PI) * 0.55 + 0.12;
        const strokeGrad = ctx.createLinearGradient(0, 0, width, 0);
        strokeGrad.addColorStop(0, "rgba(200, 200, 210, 0)");
        strokeGrad.addColorStop(0.2, `rgba(160, 160, 175, ${strokeAlpha * 0.7})`);
        strokeGrad.addColorStop(0.5, `rgba(110, 110, 128, ${strokeAlpha * 1.1})`);
        strokeGrad.addColorStop(0.8, `rgba(170, 170, 185, ${strokeAlpha * 0.8})`);
        strokeGrad.addColorStop(1, "rgba(220, 220, 230, 0)");

        ctx.strokeStyle = strokeGrad;
        ctx.lineWidth = 1.6 + Math.sin(progress * Math.PI) * 1.0;
        ctx.stroke();
      }

      // Smooth ambient blend gradient at bottom
      const bottomGrad = ctx.createLinearGradient(0, height * 0.65, 0, height);
      bottomGrad.addColorStop(0, "rgba(250, 249, 246, 0)");
      bottomGrad.addColorStop(1, "rgba(250, 249, 246, 0.95)");
      ctx.fillStyle = bottomGrad;
      ctx.fillRect(0, height * 0.65, width, height * 0.35);

      animationId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      observer.disconnect();
      if (animationId) cancelAnimationFrame(animationId);
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className={`absolute inset-0 overflow-hidden pointer-events-none select-none ${className}`}
      style={{ opacity }}
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
      />
      <div className="absolute inset-0 bg-gradient-to-b from-white/30 via-transparent to-[#faf9f6]/80 pointer-events-none" />
    </div>
  );
}

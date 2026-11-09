"use client";

import React, { useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "../../context/AuthContext";
import WorkspaceSidebar from "./WorkspaceSidebar";
import WorkspaceHeader from "./WorkspaceHeader";

interface WorkspaceShellProps {
  children: React.ReactNode;
}

export default function WorkspaceShell({ children }: WorkspaceShellProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { firebaseUser, loading } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Auth protection guard
  useEffect(() => {
    if (!loading && isClient) {
      if (!firebaseUser) {
        router.push("/login");
      }
    }
  }, [firebaseUser, loading, isClient, router]);

  if (!isClient || loading) {
    return (
      <div className="min-h-screen bg-[#FAF9F6] flex flex-col items-center justify-center">
        <div className="w-6 h-6 border-2 border-[#111111] border-t-transparent rounded-full animate-spin mb-3" />
        <span className="font-sans text-xs text-[#777777] tracking-wider uppercase">
          Loading workspace...
        </span>
      </div>
    );
  }

  // Full-bleed Claude-inspired conversational workspace on /app/assistant routes
  const isAssistant = pathname?.startsWith("/app/assistant");
  if (isAssistant) {
    return (
      <div className="h-screen w-screen overflow-hidden bg-[#FAF9F5] text-[#1F1E1D]">
        {children}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FAF9F6] text-[#111111]">
      {/* Fixed Left Navigation */}
      <WorkspaceSidebar
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      {/* Top Header */}
      <WorkspaceHeader onOpenMobile={() => setMobileOpen(true)} />

      {/* Main Content Area */}
      <div className="lg:pl-64 flex flex-col min-h-screen">
        <main className="flex-1 pt-14 w-full bg-[#FAF9F6]">
          {children}
        </main>
      </div>
    </div>
  );
}


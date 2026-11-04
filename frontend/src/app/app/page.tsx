"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Scale,
  Sparkles,
  FolderOpen,
  ArrowRight,
  Clock,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { fetchUserActivity, ActivityItem } from "../../lib/api";

export default function OverviewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { profile, firebaseUser, idToken } = useAuth();

  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loadingActivity, setLoadingActivity] = useState(true);

  // Preserve backwards compatibility with old bookmark URLs like /app?tab=conflicts
  useEffect(() => {
    const tab = searchParams.get("tab");
    if (tab === "conflicts") {
      router.replace("/app/inconsistencies");
    } else if (tab === "assistant") {
      router.replace("/app/assistant");
    } else if (tab === "forms") {
      router.replace("/app/forms");
    } else if (tab === "profile") {
      router.replace("/app/profile");
    }
  }, [searchParams, router]);

  // Load real user activity
  useEffect(() => {
    let isMounted = true;
    async function loadActivity() {
      if (!idToken) {
        setLoadingActivity(false);
        return;
      }
      try {
        const data = await fetchUserActivity(idToken);
        if (isMounted) {
          setActivities(data);
        }
      } catch (err) {
        console.warn("Could not load activity:", err);
        if (isMounted) {
          setActivities([]);
        }
      } finally {
        if (isMounted) {
          setLoadingActivity(false);
        }
      }
    }
    loadActivity();
    return () => {
      isMounted = false;
    };
  }, [idToken]);

  // Personalized greeting calculation
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 17) return "Good afternoon";
    return "Good evening";
  };

  const displayName = profile?.full_name || firebaseUser?.displayName || "Citizen";

  return (
    <div className="max-w-5xl mx-auto w-full py-10 px-4 sm:px-6 lg:px-8 pb-24">
      {/* Editorial Header & Welcome */}
      <header className="mb-10 space-y-2 border-b border-[#E7E5E0] pb-8">
        <div className="flex items-center gap-2">
          <span className="font-sans text-[11px] uppercase tracking-wider text-[#777777] font-medium">
            Overview
          </span>
          <span className="text-[#CCCCCC]">•</span>
          <span className="font-sans text-[11px] text-[#777777]">
            Active Citizen Session
          </span>
        </div>
        <h1 className="font-serif text-3xl sm:text-4xl text-[#111111] font-light tracking-tight">
          {getGreeting()}, {displayName}
        </h1>
        <p className="font-sans text-sm sm:text-base text-[#5E5E5E] max-w-2xl leading-relaxed">
          CONVELINA helps you reconcile clerical differences across primary Indian identity
          records, examine statutory regulations, and access authentic correction forms.
        </p>
      </header>

      {/* Primary Actions Grid (3 Core Actions) */}
      <section className="mb-14">
        <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777] mb-4">
          Primary Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Action 1: Check Inconsistencies */}
          <Link
            href="/app/inconsistencies"
            className="group p-5 bg-white border border-[#E7E5E0] rounded-[4px] hover:border-[#111111] transition-all flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-8 h-8 rounded-[4px] bg-[#FAF9F6] border border-[#E7E5E0] flex items-center justify-center text-[#111111] group-hover:bg-[#111111] group-hover:text-white transition-colors">
                <Scale className="w-4 h-4" />
              </div>
              <h3 className="font-sans text-base font-medium text-[#111111] leading-snug">
                Check Document Inconsistencies
              </h3>
              <p className="font-sans text-xs text-[#5E5E5E] leading-relaxed">
                Upload your Aadhaar, PAN, Passport, or Class 10/12 certificate to identify spelling, date, or parent name mismatches.
              </p>
            </div>
            <div className="pt-6 flex items-center gap-1.5 text-xs font-medium text-[#111111] group-hover:translate-x-0.5 transition-transform">
              <span>Inspect documents</span>
              <ArrowRight className="w-3.5 h-3.5 text-[#777777] group-hover:text-[#111111]" />
            </div>
          </Link>

          {/* Action 2: Ask the AI Assistant */}
          <Link
            href="/app/assistant"
            className="group p-5 bg-white border border-[#E7E5E0] rounded-[4px] hover:border-[#111111] transition-all flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-8 h-8 rounded-[4px] bg-[#FAF9F6] border border-[#E7E5E0] flex items-center justify-center text-[#111111] group-hover:bg-[#111111] group-hover:text-white transition-colors">
                <Sparkles className="w-4 h-4" />
              </div>
              <h3 className="font-sans text-base font-medium text-[#111111] leading-snug">
                Ask the AI Assistant
              </h3>
              <p className="font-sans text-xs text-[#5E5E5E] leading-relaxed">
                Receive grounded guidance on legal document hierarchy, gazette notifications, and verified correction steps.
              </p>
            </div>
            <div className="pt-6 flex items-center gap-1.5 text-xs font-medium text-[#111111] group-hover:translate-x-0.5 transition-transform">
              <span>Start consultation</span>
              <ArrowRight className="w-3.5 h-3.5 text-[#777777] group-hover:text-[#111111]" />
            </div>
          </Link>

          {/* Action 3: Browse Official Forms */}
          <Link
            href="/app/forms"
            className="group p-5 bg-white border border-[#E7E5E0] rounded-[4px] hover:border-[#111111] transition-all flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-8 h-8 rounded-[4px] bg-[#FAF9F6] border border-[#E7E5E0] flex items-center justify-center text-[#111111] group-hover:bg-[#111111] group-hover:text-white transition-colors">
                <FolderOpen className="w-4 h-4" />
              </div>
              <h3 className="font-sans text-base font-medium text-[#111111] leading-snug">
                Browse Official Forms
              </h3>
              <p className="font-sans text-xs text-[#5E5E5E] leading-relaxed">
                Access verified statutory correction petitions (Form 49A, EPFO Joint Declaration, Annexures) and download authentic PDFs.
              </p>
            </div>
            <div className="pt-6 flex items-center gap-1.5 text-xs font-medium text-[#111111] group-hover:translate-x-0.5 transition-transform">
              <span>Explore repository</span>
              <ArrowRight className="w-3.5 h-3.5 text-[#777777] group-hover:text-[#111111]" />
            </div>
          </Link>
        </div>
      </section>

      {/* Real Activity Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b border-[#E7E5E0] pb-2">
          <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777]">
            Recent Activity
          </h2>
          <span className="font-sans text-[11px] text-[#777777]">
            Audit-backed events
          </span>
        </div>

        {loadingActivity ? (
          <div className="py-8 text-center text-xs text-[#777777] font-sans">
            Loading activity log...
          </div>
        ) : activities.length > 0 ? (
          <div className="divide-y divide-[#E7E5E0] border-b border-[#E7E5E0]">
            {activities.map((item) => (
              <div
                key={item.id}
                className="py-3 flex items-center justify-between gap-4 text-xs font-sans"
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <Clock className="w-3.5 h-3.5 text-[#777777] shrink-0" />
                  <span className="font-medium text-[#111111] capitalize">
                    {item.action.replace(/_/g, " ")}
                  </span>
                  <span className="text-[#777777] truncate">
                    {item.entity_type} {item.entity_id ? `(${item.entity_id.slice(0, 8)}...)` : ""}
                  </span>
                </div>
                <span className="text-[#999999] whitespace-nowrap text-[11px]">
                  {new Date(item.created_at).toLocaleDateString("en-IN", {
                    month: "short",
                    day: "numeric",
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              </div>
            ))}
          </div>
        ) : (
          /* Honest Empty State */
          <div className="p-8 bg-white border border-[#E7E5E0] rounded-[4px] text-center space-y-2">
            <div className="w-8 h-8 rounded-full bg-[#FAF9F6] border border-[#E7E5E0] flex items-center justify-center text-[#777777] mx-auto mb-2">
              <Clock className="w-4 h-4" />
            </div>
            <h4 className="font-sans text-sm font-medium text-[#111111]">
              No recent activity recorded
            </h4>
            <p className="font-sans text-xs text-[#777777] max-w-sm mx-auto leading-relaxed">
              When you upload identity credentials, run discrepancy analyses, or interact with the statutory assistant, audit-backed records will appear here.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}

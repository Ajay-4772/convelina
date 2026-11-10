"use client";

import React, { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Scale,
  Sparkles,
  FolderOpen,
  ArrowRight,
  Clock,
  FileText,
  AlertTriangle,
  CheckCircle2,
  FileCheck,
  Shield,
  Layers,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import {
  fetchUserActivity,
  fetchDocuments,
  fetchConflicts,
  fetchCorrectionDrafts,
  fetchPersonalizedGuidance,
  ActivityItem,
  DocumentItem,
  ConflictItem,
  CorrectionDraftItem,
  PersonalizedGuidanceItem,
} from "../../lib/api";

export default function OverviewPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { profile, firebaseUser, idToken } = useAuth();

  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loadingActivity, setLoadingActivity] = useState(true);

  // Workspace Status Data
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [drafts, setDrafts] = useState<CorrectionDraftItem[]>([]);
  const [guidanceItems, setGuidanceItems] = useState<PersonalizedGuidanceItem[]>([]);
  const [loadingWorkspace, setLoadingWorkspace] = useState(true);

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

  // Load real workspace status data
  useEffect(() => {
    let isMounted = true;
    async function loadWorkspaceData() {
      if (!idToken) {
        setLoadingWorkspace(false);
        setLoadingActivity(false);
        return;
      }
      try {
        setLoadingWorkspace(true);
        const [docs, confs, dfts, guidance, acts] = await Promise.all([
          fetchDocuments(idToken).catch(() => []),
          fetchConflicts(idToken).catch(() => []),
          fetchCorrectionDrafts(idToken).catch(() => []),
          fetchPersonalizedGuidance(idToken).then((r) => r.items || []).catch(() => []),
          fetchUserActivity(idToken).catch(() => []),
        ]);
        if (isMounted) {
          setDocuments(docs);
          setConflicts(confs);
          setDrafts(dfts);
          setGuidanceItems(guidance);
          setActivities(acts);
        }
      } catch (err) {
        console.warn("Could not load workspace status:", err);
      } finally {
        if (isMounted) {
          setLoadingWorkspace(false);
          setLoadingActivity(false);
        }
      }
    }
    loadWorkspaceData();
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

  // Workspace Metrics
  const pendingReviewDocs = useMemo(() => {
    return documents.filter((d) => d.ocr_status === "needs_review" || !d.is_user_confirmed);
  }, [documents]);

  const confirmedDocs = useMemo(() => {
    return documents.filter((d) => d.is_user_confirmed);
  }, [documents]);

  const highSeverityConflicts = useMemo(() => {
    return conflicts.filter((c) => c.severity === "high" || c.severity === "critical");
  }, [conflicts]);

  const confirmedDrafts = useMemo(() => {
    return drafts.filter((d) => d.status === "citizen_confirmed" || d.is_citizen_confirmed);
  }, [drafts]);

  // Context-Aware Recommended Next Step
  const recommendedNextStep = useMemo(() => {
    if (documents.length === 0) {
      return {
        stepNumber: "Step 1 of 5",
        title: "Upload Primary Identity Credentials",
        description: "Add your Aadhaar, PAN, Passport, or Class 10/12 certificate to initiate automated discrepancy checking and statutory reconciliation.",
        actionText: "Upload First Document",
        actionHref: "/app/inconsistencies",
        badge: "Initial Setup",
      };
    }
    if (pendingReviewDocs.length > 0) {
      return {
        stepNumber: "Step 2 of 5",
        title: "Review & Confirm Machine Extractions",
        description: `You have ${pendingReviewDocs.length} credential(s) awaiting citizen verification. Confirm extracted values to ensure deterministic comparison accuracy.`,
        actionText: "Review OCR Fields",
        actionHref: "/app/inconsistencies",
        badge: "Verification Pending",
      };
    }
    if (documents.length >= 2 && conflicts.length === 0) {
      return {
        stepNumber: "Step 3 of 5",
        title: "Run Deterministic Cross-Verification",
        description: "All uploaded credentials are confirmed. Run comparison to cross-check personal names, dates of birth, and family credentials.",
        actionText: "Compare Documents",
        actionHref: "/app/inconsistencies",
        badge: "Ready to Compare",
      };
    }
    if (conflicts.length > 0 && drafts.length === 0) {
      return {
        stepNumber: "Step 4 of 5",
        title: "Formulate Administrative Correction Draft",
        description: `CONVELINA detected ${conflicts.length} discrepancy(ies) across your credentials. Consult the AI Assistant or generate a customized statutory representation draft.`,
        actionText: "Generate Correction Draft",
        actionHref: "/app/inconsistencies",
        badge: "Action Required",
      };
    }
    if (drafts.length > 0) {
      return {
        stepNumber: "Step 5 of 5",
        title: "Review & Download Official Representation",
        description: `You have ${drafts.length} correction draft(s) saved in your workspace. Review the legal clauses, confirm truthfulness, and download an official PDF representation.`,
        actionText: "Manage Saved Drafts",
        actionHref: "/app/inconsistencies",
        badge: "Draft Available",
      };
    }
    return {
      stepNumber: "Workspace Active",
      title: "Explore Statutory Guidance & Prescribed Forms",
      description: "Search official application forms, proof matrices, and authoritative procedural circulars across the 6 supported identity categories.",
      actionText: "Explore Forms Repository",
      actionHref: "/app/forms",
      badge: "Guidance Available",
    };
  }, [documents, pendingReviewDocs, conflicts, drafts]);

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

      {/* Workspace Status Snapshot (5 Core Citizen Metrics) */}
      <section className="mb-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777]">
            Workspace Status Snapshot
          </h2>
          <span className="font-sans text-[11px] text-[#777777]">
            Real-time citizen records
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {/* Metric 1: Uploaded Credentials */}
          <Link
            href="/app/inconsistencies"
            className="p-4 bg-white border border-[#E7E5E0] rounded-[4px] hover:border-[#111111] transition-colors flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-[#777777] mb-2">
                <FileText className="w-4 h-4 text-[#111111]" />
                <span className="text-[10px] font-mono uppercase">Credentials</span>
              </div>
              <div className="font-serif text-2xl font-light text-[#111111]">
                {loadingWorkspace ? "—" : documents.length}
              </div>
            </div>
            <div className="text-[11px] text-[#777777] font-sans mt-2 pt-2 border-t border-[#F0EFEA]">
              {documents.length > 0 ? `${confirmedDocs.length} confirmed` : "None uploaded"}
            </div>
          </Link>

          {/* Metric 2: Pending OCR Reviews */}
          <Link
            href="/app/inconsistencies"
            className="p-4 bg-white border border-[#E7E5E0] rounded-[4px] hover:border-[#111111] transition-colors flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-[#777777] mb-2">
                <Clock className="w-4 h-4 text-[#B06000]" />
                <span className="text-[10px] font-mono uppercase">OCR Reviews</span>
              </div>
              <div className="font-serif text-2xl font-light text-[#111111]">
                {loadingWorkspace ? "—" : pendingReviewDocs.length}
              </div>
            </div>
            <div className="text-[11px] font-sans mt-2 pt-2 border-t border-[#F0EFEA]">
              {pendingReviewDocs.length > 0 ? (
                <span className="text-[#B06000] font-medium">Review required</span>
              ) : (
                <span className="text-[#0D652D]">All confirmed</span>
              )}
            </div>
          </Link>

          {/* Metric 3: Detected Discrepancies */}
          <Link
            href="/app/inconsistencies"
            className="p-4 bg-white border border-[#E7E5E0] rounded-[4px] hover:border-[#111111] transition-colors flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-[#777777] mb-2">
                <AlertTriangle className="w-4 h-4 text-[#BA1A1A]" />
                <span className="text-[10px] font-mono uppercase">Discrepancies</span>
              </div>
              <div className="font-serif text-2xl font-light text-[#111111]">
                {loadingWorkspace ? "—" : conflicts.length}
              </div>
            </div>
            <div className="text-[11px] font-sans mt-2 pt-2 border-t border-[#F0EFEA]">
              {conflicts.length > 0 ? (
                <span className="text-[#BA1A1A] font-medium">{highSeverityConflicts.length} high priority</span>
              ) : (
                <span className="text-[#0D652D]">No conflicts</span>
              )}
            </div>
          </Link>

          {/* Metric 4: Saved Correction Drafts */}
          <Link
            href="/app/inconsistencies"
            className="p-4 bg-white border border-[#E7E5E0] rounded-[4px] hover:border-[#111111] transition-colors flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between text-[#777777] mb-2">
                <FileCheck className="w-4 h-4 text-[#111111]" />
                <span className="text-[10px] font-mono uppercase">Petitions</span>
              </div>
              <div className="font-serif text-2xl font-light text-[#111111]">
                {loadingWorkspace ? "—" : drafts.length}
              </div>
            </div>
            <div className="text-[11px] text-[#777777] font-sans mt-2 pt-2 border-t border-[#F0EFEA]">
              {drafts.length > 0 ? `${confirmedDrafts.length} confirmed` : "No active drafts"}
            </div>
          </Link>

          {/* Metric 5: Active Guidance & Checklists */}
          <Link
            href="/app/forms"
            className="p-4 bg-white border border-[#E7E5E0] rounded-[4px] hover:border-[#111111] transition-colors flex flex-col justify-between col-span-2 sm:col-span-1"
          >
            <div>
              <div className="flex items-center justify-between text-[#777777] mb-2">
                <Layers className="w-4 h-4 text-[#111111]" />
                <span className="text-[10px] font-mono uppercase">Procedures</span>
              </div>
              <div className="font-serif text-2xl font-light text-[#111111]">
                {loadingWorkspace ? "—" : (guidanceItems.length || "6")}
              </div>
            </div>
            <div className="text-[11px] text-[#777777] font-sans mt-2 pt-2 border-t border-[#F0EFEA]">
              {guidanceItems.length > 0 ? "Targeted guidance" : "Standard catalogs"}
            </div>
          </Link>
        </div>
      </section>

      {/* Contextual Recommended Next Step Card */}
      <section className="mb-14 p-5 bg-[#FAF9F6] border border-[#111111] rounded-[6px] space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-[#111111] text-white">
              {recommendedNextStep.stepNumber}
            </span>
            <span className="font-sans text-xs text-[#777777] font-medium">
              {recommendedNextStep.badge}
            </span>
          </div>
          <span className="text-[11px] font-sans text-[#777777]">
            Recommended Next Step
          </span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
          <div className="space-y-1">
            <h3 className="font-serif text-xl text-[#111111] font-normal">
              {recommendedNextStep.title}
            </h3>
            <p className="font-sans text-xs text-[#5E5E5E] max-w-2xl leading-relaxed">
              {recommendedNextStep.description}
            </p>
          </div>

          <Link
            href={recommendedNextStep.actionHref}
            className="h-10 px-4 bg-[#111111] text-white rounded-[4px] font-sans text-xs font-medium hover:bg-black/90 active:bg-black transition-colors flex items-center justify-center gap-1.5 shrink-0"
          >
            <span>{recommendedNextStep.actionText}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </section>

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

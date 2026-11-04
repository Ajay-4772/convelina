"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Download,
  ExternalLink,
  Building2,
  FileCheck2,
  CheckCircle2,
  Sparkles,
  Shield,
  HelpCircle,
} from "lucide-react";
import { useAuth } from "../../../../context/AuthContext";
import { fetchOfficialFormById, OfficialFormItem } from "../../../../lib/api";

export default function FormDetailPage() {
  const params = useParams();
  const router = useRouter();
  const formId = params?.formId as string;
  const { idToken } = useAuth();

  const [form, setForm] = useState<OfficialFormItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadForm = useCallback(async () => {
    if (!formId) return;
    try {
      setLoading(true);
      setError(null);
      const data = await fetchOfficialFormById(idToken, formId);
      setForm(data);
    } catch (err: any) {
      console.warn("Could not load form details:", err);
      setError(err.message || "Failed to load form details.");
    } finally {
      setLoading(false);
    }
  }, [idToken, formId]);

  useEffect(() => {
    loadForm();
  }, [loadForm]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto w-full py-16 px-4 text-center text-xs text-[#777777] font-sans">
        Loading statutory form specification...
      </div>
    );
  }

  if (error || !form) {
    return (
      <div className="max-w-4xl mx-auto w-full py-16 px-4">
        <Link
          href="/app/forms"
          className="inline-flex items-center gap-1.5 text-xs text-[#777777] hover:text-[#111111] mb-6 font-sans transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Forms Repository</span>
        </Link>
        <div className="p-8 bg-white border border-[#E7E5E0] rounded-[4px] text-center space-y-2">
          <h2 className="font-sans text-sm font-medium text-[#111111]">
            Form Not Found
          </h2>
          <p className="font-sans text-xs text-[#777777] max-w-sm mx-auto">
            {error || "The requested official statutory form could not be retrieved from the catalog."}
          </p>
        </div>
      </div>
    );
  }

  const formCode = form.form_code || form.form_id.toUpperCase();

  return (
    <div className="max-w-4xl mx-auto w-full py-10 px-4 sm:px-6 lg:px-8 pb-32">
      {/* Back Navigation */}
      <Link
        href="/app/forms"
        className="inline-flex items-center gap-1.5 text-xs text-[#777777] hover:text-[#111111] mb-8 font-sans transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Forms Repository</span>
      </Link>

      {/* Header Banner */}
      <header className="space-y-4 border-b border-[#E7E5E0] pb-8 mb-8">
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="px-2.5 py-0.5 bg-[#111111] text-white font-mono text-xs font-bold tracking-wide rounded-[4px]">
            {formCode}
          </span>
          <span className="px-2 py-0.5 bg-[#F4F3EF] border border-[#E7E5E0] text-[#5E5E5E] font-sans text-xs rounded-[2px] uppercase tracking-wider">
            {form.document_category}
          </span>
          <span className="text-[#CCCCCC]">•</span>
          <span className="text-xs text-[#777777] font-sans flex items-center gap-1">
            <Shield className="w-3.5 h-3.5 text-[#777777]" />
            <span>Verified Official Specimen</span>
          </span>
        </div>

        <h1 className="font-serif text-3xl sm:text-4xl text-[#111111] font-light tracking-tight leading-snug">
          {form.form_name}
        </h1>

        <div className="flex items-center gap-2 text-sm text-[#5E5E5E] font-sans">
          <Building2 className="w-4 h-4 text-[#777777]" />
          <span className="font-medium text-[#111111]">{form.issuing_authority}</span>
          {form.statutory_authority && (
            <>
              <span className="text-[#CCCCCC]">•</span>
              <span className="text-xs text-[#777777]">{form.statutory_authority}</span>
            </>
          )}
        </div>
      </header>

      {/* Main Specification Body */}
      <div className="space-y-8">
        {/* Purpose Description */}
        <section className="space-y-2">
          <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777]">
            Statutory Purpose
          </h2>
          <p className="font-sans text-sm sm:text-base text-[#1A1C1A] leading-relaxed">
            {form.purpose || form.purpose_description}
          </p>
        </section>

        {/* Applicable Issue Types */}
        {form.applicable_issue_types && form.applicable_issue_types.length > 0 && (
          <section className="space-y-2.5">
            <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777]">
              Applicable Discrepancy Types
            </h2>
            <div className="flex flex-wrap gap-2">
              {form.applicable_issue_types.map((type, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 bg-white border border-[#E7E5E0] text-xs font-sans text-[#111111] rounded-[4px] capitalize"
                >
                  {type.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          </section>
        )}

        {/* Prerequisites Checklist */}
        {((form.applicable_conditions && form.applicable_conditions.length > 0) ||
          (form.prerequisites && form.prerequisites.length > 0)) && (
          <section className="space-y-3">
            <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777]">
              Required Supporting Documentation
            </h2>
            <div className="p-4 bg-white border border-[#E7E5E0] rounded-[4px] space-y-2.5">
              {(form.applicable_conditions || form.prerequisites || []).map((req, idx) => (
                <div key={idx} className="flex items-start gap-2.5 text-xs font-sans text-[#1A1C1A]">
                  <CheckCircle2 className="w-4 h-4 text-[#111111] shrink-0 mt-0.5" />
                  <span className="leading-relaxed">{req}</span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Submission Instructions */}
        {form.submission_instructions && (
          <section className="space-y-2">
            <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777]">
              Official Filing Instructions
            </h2>
            <div className="p-4 bg-white border border-[#E7E5E0] rounded-[4px] text-xs font-sans text-[#1A1C1A] leading-relaxed whitespace-pre-line">
              {form.submission_instructions}
            </div>
          </section>
        )}

        {/* Action Buttons */}
        <section className="pt-4 border-t border-[#E7E5E0] flex flex-wrap items-center gap-3">
          {(form.official_download_url || form.download_url) && (
            <a
              href={form.official_download_url || form.download_url}
              target="_blank"
              rel="noopener noreferrer"
              className="h-10 px-5 bg-[#111111] text-white rounded-[4px] text-sm font-sans font-medium hover:bg-black/90 transition-colors flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              <span>Download Official PDF Format</span>
            </a>
          )}

          {form.official_portal_url && (
            <a
              href={form.official_portal_url}
              target="_blank"
              rel="noopener noreferrer"
              className="h-10 px-5 bg-white border border-[#E7E5E0] text-[#111111] rounded-[4px] text-sm font-sans font-medium hover:bg-[#F4F3EF] transition-colors flex items-center gap-2"
            >
              <ExternalLink className="w-4 h-4 text-[#777777]" />
              <span>Visit Official Government Portal</span>
            </a>
          )}

          <Link
            href={`/app/assistant`}
            className="h-10 px-4 bg-white border border-[#E7E5E0] text-[#111111] rounded-[4px] text-sm font-sans font-medium hover:bg-[#F4F3EF] transition-colors flex items-center gap-2 ml-auto"
          >
            <Sparkles className="w-4 h-4 text-[#777777]" />
            <span>Consult Assistant on Filling</span>
          </Link>
        </section>
      </div>
    </div>
  );
}


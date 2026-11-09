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
  AlertTriangle,
  Clock,
  Sparkles,
  Shield,
  HelpCircle,
  FileText,
  BookOpen,
  Calendar,
  Hash,
  Layers,
  ChevronRight,
  Info,
} from "lucide-react";
import { useAuth } from "../../../../context/AuthContext";
import {
  fetchRepositoryResourceDetail,
  fetchOfficialFormById,
  RepositoryResourceDetail,
  ChecklistItem,
} from "../../../../lib/api";

export default function DocumentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const formId = params?.formId as string;
  const { idToken } = useAuth();

  const [resource, setResource] = useState<RepositoryResourceDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Interactive Checklist State (local citizen preparation checklist)
  const [completedItems, setCompletedItems] = useState<Record<string, boolean>>({});

  const toggleChecklistItem = (reqId: string) => {
    setCompletedItems((prev) => ({
      ...prev,
      [reqId]: !prev[reqId],
    }));
  };

  const loadResource = useCallback(async () => {
    if (!formId) return;
    try {
      setLoading(true);
      setError(null);
      // Attempt repository detail endpoint first
      try {
        const data = await fetchRepositoryResourceDetail(idToken, formId);
        setResource(data);
        return;
      } catch (repoErr) {
        // Fallback to legacy official forms endpoint
        const oldForm = await fetchOfficialFormById(idToken, formId);
        if (oldForm) {
          const adapted: RepositoryResourceDetail = {
            id: oldForm.id,
            resource_id: oldForm.form_id,
            title: oldForm.form_name,
            issuing_authority: oldForm.issuing_authority,
            document_category: oldForm.document_category,
            document_type: "application_form",
            description: oldForm.description || oldForm.purpose || "",
            purpose: oldForm.purpose || "",
            intended_cohort: "GENERAL_CITIZEN",
            applicable_categories: [oldForm.document_category],
            publication_date: oldForm.created_at ? oldForm.created_at.slice(0, 10) : null,
            effective_date: null,
            verification_status: oldForm.verification_status || "unverified",
            provenance: oldForm.provenance || "SYNTHETIC_DEVELOPMENT_SAMPLE",
            provenance_notes: oldForm.provenance_notes,
            is_official_government_form: oldForm.is_official_government_form || false,
            is_synthetic_sample: true,
            is_historical: false,
            has_source_conflict: false,
            human_review_required: false,
            file_format: oldForm.file_format || "pdf",
            file_size_bytes: oldForm.file_size_bytes || 0,
            sha256_hash: oldForm.sha256_hash,
            download_available: true,
            download_url: `/api/v1/repository/resources/${oldForm.form_id}/download`,
            preview_url: `/api/v1/repository/resources/${oldForm.form_id}/preview`,
            original_source_url: oldForm.official_download_url,
            key_information_required: oldForm.applicable_conditions || [],
            referenced_laws: [],
            related_procedures: [],
            limitations_and_warnings: [],
            statutory_citations: [],
            supporting_document_checklist: [],
            disclaimer: "SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM",
          };
          setResource(adapted);
          return;
        }
      }
    } catch (err: any) {
      console.warn("Could not load resource details:", err);
      setError(err.message || "Failed to load document details.");
    } finally {
      setLoading(false);
    }
  }, [idToken, formId]);

  useEffect(() => {
    loadResource();
  }, [loadResource]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto w-full py-20 px-4 text-center space-y-2">
        <div className="w-5 h-5 border-2 border-[#111111] border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-[#777777] font-sans">
          Loading document specification from repository...
        </p>
      </div>
    );
  }

  if (error || !resource) {
    return (
      <div className="max-w-4xl mx-auto w-full py-16 px-4">
        <Link
          href="/app/forms"
          className="inline-flex items-center gap-1.5 text-xs text-[#777777] hover:text-[#111111] mb-6 font-sans transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Document Repository</span>
        </Link>
        <div className="p-8 bg-white border border-[#E7E5E0] rounded-[4px] text-center space-y-2">
          <h2 className="font-sans text-sm font-medium text-[#111111]">
            Document Not Found
          </h2>
          <p className="font-sans text-xs text-[#777777] max-w-sm mx-auto">
            {error || "The requested official statutory document could not be retrieved from the repository."}
          </p>
        </div>
      </div>
    );
  }

  const isSynthetic = Boolean(
    resource.is_synthetic_sample || 
    (resource.provenance && resource.provenance.toUpperCase() === "SYNTHETIC_DEVELOPMENT_SAMPLE")
  );
  const isHistorical = Boolean(
    resource.is_historical || 
    (resource.provenance && resource.provenance.toUpperCase() === "HISTORICAL_REFERENCE")
  );
  const isConflict = Boolean(
    resource.source_conflict_flag || 
    resource.has_source_conflict || 
    resource.statutory_limitation_notice || 
    (resource.verification_status && resource.verification_status.toUpperCase() === "SOURCE_METADATA_CONFLICT")
  );

  return (
    <div className="max-w-4xl mx-auto w-full py-10 px-4 sm:px-6 lg:px-8 pb-32">
      {/* Back Navigation */}
      <Link
        href="/app/forms"
        className="inline-flex items-center gap-1.5 text-xs text-[#777777] hover:text-[#111111] mb-8 font-sans transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        <span>Back to Document Repository</span>
      </Link>

      {/* 1. DOCUMENT OVERVIEW */}
      <header className="space-y-4 border-b border-[#E7E5E0] pb-8 mb-8">
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="px-2.5 py-0.5 bg-[#111111] text-white font-mono text-xs font-bold tracking-wide rounded-[4px]">
            {resource.resource_id}
          </span>

          {/* Provenance Badge */}
          {resource.provenance === "OFFICIAL_ORIGINAL" && (
            <span className="px-2 py-0.5 bg-[#E8F5E9] border border-[#C8E6C9] text-[#2E7D32] text-xs font-sans font-medium rounded-[3px]">
              Official Original
            </span>
          )}
          {resource.provenance === "GOVERNMENT_REFERENCE" && (
            <span className="px-2 py-0.5 bg-[#E3F2FD] border border-[#BBDEFB] text-[#1565C0] text-xs font-sans font-medium rounded-[3px]">
              Government Reference
            </span>
          )}
          {isHistorical && (
            <span className="px-2 py-0.5 bg-[#FFF3E0] border border-[#FFE0B2] text-[#E65100] text-xs font-sans font-medium rounded-[3px]">
              Historical Reference (Superseded)
            </span>
          )}
          {isSynthetic && (
            <span className="px-2 py-0.5 bg-[#FBE9E7] border border-[#FFCCBC] text-[#D84315] text-xs font-sans font-medium rounded-[3px]">
              Synthetic Development Sample
            </span>
          )}

          {/* Verification Badge */}
          {resource.verification_status === "verified" && (
            <span className="inline-flex items-center gap-1 text-xs text-[#2E7D32] font-sans font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Verified Status</span>
            </span>
          )}
          {isConflict && (
            <span className="inline-flex items-center gap-1 text-xs text-[#7B1FA2] font-sans font-medium">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Source Conflict Notice</span>
            </span>
          )}
          {resource.verification_status === "needs_review" && (
            <span className="inline-flex items-center gap-1 text-xs text-[#E65100] font-sans font-medium">
              <Clock className="w-3.5 h-3.5" />
              <span>Pending Review</span>
            </span>
          )}

          {/* Category */}
          <span className="ml-auto px-2 py-0.5 bg-[#F4F3EF] border border-[#E7E5E0] text-[#5E5E5E] font-sans text-xs rounded-[3px] uppercase tracking-wider">
            {resource.document_category}
          </span>
        </div>

        <h1 className="font-serif text-2xl sm:text-3xl text-[#111111] font-light leading-snug">
          {resource.title}
        </h1>

        <div className="flex items-center gap-4 flex-wrap text-xs text-[#777777] font-sans">
          <div className="flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5 text-[#999999]" />
            <span>{resource.issuing_authority}</span>
          </div>
          {resource.publication_date && (
            <div className="flex items-center gap-1.5">
              <Calendar className="w-3.5 h-3.5 text-[#999999]" />
              <span>Published: {resource.publication_date}</span>
            </div>
          )}
          {resource.file_size_bytes && resource.file_size_bytes > 0 ? (
            <div className="flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-[#999999]" />
              <span>Size: {(resource.file_size_bytes / 1024).toFixed(1)} KB ({((resource.file_format || "PDF") as string).toUpperCase()})</span>
            </div>
          ) : null}
        </div>

        {/* Mandatory Prominent Disclaimers */}
        {isSynthetic && (
          <div className="p-3 bg-[#FFF8F6] border border-[#FFECE8] rounded-[4px] space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-[#BA1A1A] font-medium font-sans">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM</span>
            </div>
            <p className="text-[11px] text-[#7F1D1D] font-sans">
              This document is an application-generated template constructed for development and testing. Download authentic original forms directly from the issuing authority portal.
            </p>
          </div>
        )}

        {isConflict && (
          <div className="p-3 bg-[#FAF5FC] border border-[#E9D5F5] rounded-[4px] space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-[#6A1B9A] font-medium font-sans">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>STATUTORY LIMITATION NOTICE</span>
            </div>
            <p className="text-[11px] text-[#4A148C] font-sans leading-relaxed">
              {resource.statutory_limitation_notice ||
                "DOC_043 retains an unverified source metadata conflict. Claims regarding third-time exceptions and Regional Office escalation packets cannot be represented as definitive law."}
            </p>
          </div>
        )}

        {isHistorical && (
          <div className="p-3 bg-[#FFFBF0] border border-[#FFE8A3] rounded-[4px] space-y-1">
            <div className="flex items-center gap-1.5 text-xs text-[#B25E00] font-medium font-sans">
              <Info className="w-4 h-4 shrink-0" />
              <span>HISTORICAL REFERENCE ONLY — SUPERSEDED</span>
            </div>
            <p className="text-[11px] text-[#7A4100] font-sans">
              This circular has been superseded by newer statutory notifications and is preserved for historical audit lineage only. Not valid for current statutory filings.
            </p>
          </div>
        )}
      </header>

      {/* Grid of Structured Sections */}
      <div className="space-y-8">
        {/* 2. WHAT IS THIS DOCUMENT USED FOR? */}
        <section className="space-y-3">
          <h2 className="font-serif text-lg text-[#111111] font-normal flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-[#C96442]" />
            <span>What is this document used for?</span>
          </h2>
          <div className="p-4 bg-white border border-[#E7E5E0] rounded-[6px] text-sm text-[#333333] font-sans leading-relaxed">
            {resource.purpose || resource.description}
          </div>
        </section>

        {/* 3. WHO SHOULD USE IT? */}
        <section className="space-y-3">
          <h2 className="font-serif text-lg text-[#111111] font-normal flex items-center gap-2">
            <Layers className="w-4 h-4 text-[#C96442]" />
            <span>Who should use it?</span>
          </h2>
          <div className="p-4 bg-white border border-[#E7E5E0] rounded-[6px] space-y-2 text-xs font-sans">
            <div className="flex items-center gap-2">
              <span className="font-medium text-[#777777] uppercase tracking-wider text-[11px]">Intended Cohort:</span>
              <span className="px-2 py-0.5 bg-[#F4F3EF] text-[#111111] font-medium rounded-[3px]">
                {(resource.intended_cohort || "GENERAL_CITIZEN").replace(/_/g, " ")}
              </span>
            </div>
            <p className="text-[#5E5E5E] leading-relaxed">
              Applicable to citizens, residents, or applicants falling within the statutory jurisdiction of {resource.issuing_authority}. Requirements must be supported by official evidence.
            </p>
          </div>
        </section>

        {/* 4. RELATED CORRECTION PROCEDURES */}
        {resource.related_procedures && resource.related_procedures.length > 0 && (
          <section className="space-y-3">
            <h2 className="font-serif text-lg text-[#111111] font-normal flex items-center gap-2">
              <ChevronRight className="w-4 h-4 text-[#C96442]" />
              <span>Related Correction Procedures</span>
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {resource.related_procedures.map((proc: any, pIdx: number) => {
                const procId = typeof proc === "string" ? proc : (proc.procedure_id || proc.id || `proc_${pIdx}`);
                const procTitle = typeof proc === "string" ? proc.replace(/_/g, " ").toUpperCase() : (proc.title || procId);
                return (
                  <div
                    key={procId}
                    className="p-3.5 bg-white border border-[#E7E5E0] rounded-[4px] flex items-center justify-between"
                  >
                    <div className="space-y-0.5">
                      <div className="font-mono text-[10px] text-[#777777] uppercase">{procId}</div>
                      <div className="font-sans text-xs font-medium text-[#111111]">
                        {procTitle}
                      </div>
                    </div>
                    <Link
                      href={`/app/assistant?initial_prompt=${encodeURIComponent(`Explain the step-by-step procedure and official supporting documents for ${procTitle}.`)}`}
                      className="p-1.5 text-[#5E5E5E] hover:text-[#111111] hover:bg-[#F4F3EF] rounded-[3px] transition-colors"
                      title="Ask AI Assistant"
                    >
                      <Sparkles className="w-4 h-4 text-[#C96442]" />
                    </Link>
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* 5. REQUIRED SUPPORTING DOCUMENTS (EVIDENCE-BACKED CHECKLIST) */}
        {(() => {
          const checklistItems: any[] = resource.supporting_document_checklist || (resource as any).checklists || [];
          return (
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="font-serif text-lg text-[#111111] font-normal flex items-center gap-2">
                  <FileCheck2 className="w-4 h-4 text-[#C96442]" />
                  <span>Required Supporting Documents Checklist</span>
                </h2>
                <span className="text-[11px] text-[#777777] font-sans">
                  Evidence-backed statutory requirements
                </span>
              </div>

              {checklistItems.length === 0 ? (
                <div className="p-4 bg-white border border-[#E7E5E0] rounded-[6px] text-xs text-[#777777] font-sans">
                  No additional supporting documents required for this primary statutory reference circular.
                </div>
              ) : (
                <div className="space-y-2">
                  {checklistItems.map((item: any, idx: number) => {
                    const reqId = item.requirement_id || `req_${idx}`;
                    const isChecked = !!completedItems[reqId];
                    const itemStatus = item.status || item.requirement_status || "VERIFIED_MANDATORY";
                    return (
                      <div
                        key={reqId}
                        onClick={() => toggleChecklistItem(reqId)}
                        className={`p-4 bg-white border rounded-[6px] cursor-pointer transition-all ${
                          isChecked ? "border-[#A5D6A7] bg-[#F1F8E9]/30" : "border-[#E7E5E0] hover:border-[#CCCCCC]"
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          <div className="pt-0.5">
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={() => {}} // Handled by parent click
                              className="w-4 h-4 text-[#111111] rounded-[2px] border-[#CCCCCC] focus:ring-0 cursor-pointer"
                            />
                          </div>
                          <div className="space-y-1 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-sans text-xs font-medium text-[#111111]">
                                {item.title}
                              </span>

                              {/* Status Badge */}
                              {itemStatus === "VERIFIED_MANDATORY" && (
                                <span className="px-1.5 py-0.5 bg-[#FFEBEE] text-[#C62828] text-[9px] font-sans font-bold uppercase rounded-[2px]">
                                  Mandatory
                                </span>
                              )}
                              {itemStatus === "VERIFIED_CONDITIONAL" && (
                                <span className="px-1.5 py-0.5 bg-[#FFF8E1] text-[#F57F17] text-[9px] font-sans font-bold uppercase rounded-[2px]">
                                  Conditional
                                </span>
                              )}
                              {itemStatus === "RECOMMENDED" && (
                                <span className="px-1.5 py-0.5 bg-[#E8F5E9] text-[#2E7D32] text-[9px] font-sans font-bold uppercase rounded-[2px]">
                                  Recommended
                                </span>
                              )}
                              {itemStatus === "HUMAN_REVIEW_REQUIRED" && (
                                <span className="px-1.5 py-0.5 bg-[#EDE7F6] text-[#512DA8] text-[9px] font-sans font-bold uppercase rounded-[2px]">
                                  Human Review
                                </span>
                              )}
                            </div>

                            <p className="font-sans text-xs text-[#5E5E5E] leading-relaxed">
                              {item.description}
                            </p>

                            <div className="pt-1 flex items-center justify-between text-[10px] text-[#888888] font-sans border-t border-[#F0EFEB] mt-2">
                              <span>{item.explanation || item.supporting_source || "Statutory Evidence Rule"}</span>
                              <span className="font-mono text-[9px] text-[#999999]">{item.source_citation || item.source_verification_status || ""}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              <p className="text-[11px] text-[#777777] font-sans italic pt-1">
                Note: Citizen checklist completion is an informational preparation tool and does not constitute official government approval or successful statutory correction.
              </p>
            </section>
          );
        })()}

        {/* 6. ORIGINAL DOCUMENT DOWNLOAD & PREVIEW */}
        <section className="space-y-3">
          <h2 className="font-serif text-lg text-[#111111] font-normal flex items-center gap-2">
            <Download className="w-4 h-4 text-[#C96442]" />
            <span>Original Document Asset</span>
          </h2>
          <div className="p-5 bg-white border border-[#E7E5E0] rounded-[6px] space-y-4">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div className="space-y-1">
                <div className="font-sans text-xs font-medium text-[#111111]">
                  Official Asset Stream (PDF)
                </div>
                <div className="font-mono text-[10px] text-[#777777] break-all">
                  SHA-256: {resource.sha256_hash || "Calculated on ingestion"}
                </div>
              </div>

              <div className="flex items-center gap-2">
                {resource.download_available && (
                  <>
                    <a
                      href={`http://localhost:8000/api/v1/repository/resources/${resource.resource_id}/preview`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 bg-[#F4F3EF] hover:bg-[#EBE9E4] text-[#111111] text-xs font-sans font-medium rounded-[3px] transition-colors"
                    >
                      Preview PDF
                    </a>
                    {resource.resource_id === "DOC_043" ? (
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 border border-amber-200 text-amber-800 text-xs font-sans font-medium rounded-[3px]" title="DOC_043 is an internal operational guideline subject to unverified metadata conflict, not a citizen application form.">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        <span>Reference Circular Only (Not a Filing Form)</span>
                      </span>
                    ) : (
                      <a
                        href={`http://localhost:8000/api/v1/repository/resources/${resource.resource_id}/download`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#111111] hover:bg-[#2A2A2A] text-white text-xs font-sans font-medium rounded-[3px] transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download PDF</span>
                      </a>
                    )}
                  </>
                )}
                {resource.original_source_url && (
                  <a
                    href={resource.original_source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1.5 text-[#777777] hover:text-[#111111] hover:bg-[#F4F3EF] rounded-[3px] transition-colors"
                    title="External Issuing Authority Portal"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* 7. SOURCE & STATUTORY LIMITATIONS */}
        <section className="space-y-3">
          <h2 className="font-serif text-lg text-[#111111] font-normal flex items-center gap-2">
            <Shield className="w-4 h-4 text-[#C96442]" />
            <span>Source Citations & Statutory Limitations</span>
          </h2>
          <div className="p-4 bg-white border border-[#E7E5E0] rounded-[6px] space-y-3 text-xs font-sans">
            {/* Citations */}
            {(() => {
              const citations: any[] = resource.statutory_citations || (resource as any).citations || [];
              if (citations.length === 0) return null;
              return (
                <div className="space-y-1.5">
                  <span className="font-medium text-[#777777] uppercase tracking-wider text-[10px]">
                    Verified Citations
                  </span>
                  {citations.map((c: any, cIdx: number) => {
                    const cTitle = c.title || c.source_name || "Statutory Reference";
                    const cAuth = c.authority || c.issuing_authority || "Government Authority";
                    const cSec = c.section || c.section_or_page || "Statutory Schedule";
                    return (
                      <div key={c.source_id || c.citation_id || `cit_${cIdx}`} className="p-2.5 bg-[#FAF9F5] border border-[#EAE8E2] rounded-[3px] space-y-0.5">
                        <div className="font-medium text-[#111111]">{cTitle}</div>
                        <div className="text-[11px] text-[#5E5E5E]">{cAuth} • {cSec}</div>
                        {c.quote_or_summary && (
                          <div className="text-[10px] text-[#777777] italic pt-0.5">{c.quote_or_summary}</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })()}

            {/* Limitations & Warnings */}
            {resource.limitations_and_warnings && resource.limitations_and_warnings.length > 0 && (
              <div className="space-y-1.5 pt-2 border-t border-[#E7E5E0]">
                <span className="font-medium text-[#777777] uppercase tracking-wider text-[10px]">
                  Statutory Warnings & Exceptions
                </span>
                <ul className="list-disc list-inside space-y-1 text-[#5E5E5E]">
                  {resource.limitations_and_warnings.map((w, idx) => (
                    <li key={idx}>{w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Interactive AI Assistant Consultation Button */}
            <div className="pt-3 border-t border-[#E7E5E0] flex items-center justify-between">
              <span className="text-[11px] text-[#777777]">
                Need help interpreting this circular or form?
              </span>
              <Link
                href={`/app/assistant?initial_prompt=${encodeURIComponent(`I am reviewing ${resource.resource_id} (${resource.title}). Can you explain the exact statutory evidence and steps required for this document?`)}`}
                className="inline-flex items-center gap-1.5 text-xs text-[#C96442] hover:text-[#B25535] font-medium transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Consult AI Assistant</span>
              </Link>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

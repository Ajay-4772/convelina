"use client";

import React, { useState } from "react";
import {
  FileText,
  Download,
  Eye,
  ExternalLink,
  ShieldCheck,
  CheckCircle2,
  Copy,
  Check,
  AlertCircle,
  AlertTriangle,
  FileCheck,
  FileCode,
  Loader2,
} from "lucide-react";
import { OfficialFormItem } from "../../lib/api";

interface OfficialFormCardProps {
  form: OfficialFormItem | any;
  onPreview?: (form: OfficialFormItem) => void;
  onDownload?: (form: OfficialFormItem) => void;
  previewing?: boolean;
  downloading?: boolean;
  className?: string;
}

export default function OfficialFormCard({
  form,
  onPreview,
  onDownload,
  previewing = false,
  downloading = false,
  className = "",
}: OfficialFormCardProps) {
  const [copiedHash, setCopiedHash] = useState(false);

  // Form identity & metadata normalization
  const formId = form.form_id || form.id;
  const formName = form.form_name || form.name || "Statutory Form";
  const formCode = form.form_code || formId?.toUpperCase();
  const authority = form.issuing_authority || form.statutory_authority || "Competent Statutory Authority";
  const category = form.document_category || "General";
  const purpose = form.purpose || form.purpose_description || form.description;
  const provenance = (form.provenance || (form.is_official_government_form ? "OFFICIAL_ORIGINAL" : "APPLICATION_GENERATED")).toUpperCase();
  const isOfficialOriginal = provenance === "OFFICIAL_ORIGINAL";
  const isOfficialCopy = provenance === "OFFICIAL_COPY";
  const isAppGenerated = provenance === "APPLICATION_GENERATED";
  const isSynthetic = provenance === "SYNTHETIC_TEST_ASSET";
  const isVerified = (form.verification_status === "verified") && (isOfficialOriginal || isOfficialCopy);
  const sha256 = form.sha256_hash;
  const portalUrl = form.official_portal_url;
  const downloadUrl = form.official_download_url || form.download_url;
  const prerequisites = form.prerequisites || form.applicable_conditions || [];

  // File size formatting
  const formattedSize = form.file_size_bytes
    ? form.file_size_bytes > 1024 * 1024
      ? `${(form.file_size_bytes / (1024 * 1024)).toFixed(1)} MB`
      : `${(form.file_size_bytes / 1024).toFixed(1)} KB`
    : "~12 KB";

  const handleCopyHash = () => {
    if (!sha256) return;
    navigator.clipboard.writeText(sha256);
    setCopiedHash(true);
    setTimeout(() => setCopiedHash(false), 2000);
  };

  return (
    <div
      className={`bg-white border border-[#E5E5E0] hover:border-[#1F1E1D]/40 rounded-2xl p-4 shadow-sm transition-all space-y-3.5 ${className}`}
      data-testid={`official-form-card-${formId}`}
    >
      {/* 1. Header: Provenance Classification Badge + Document Category */}
      <div className="flex items-start justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2 flex-wrap">
          {/* Provenance Badge */}
          {isOfficialOriginal ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-[#E6F4EA] border border-[#CEEAD6] text-[#0D652D]">
              <CheckCircle2 className="w-3.5 h-3.5 text-[#0D652D]" />
              <span className="uppercase tracking-wider">OFFICIAL GOVERNMENT ORIGINAL</span>
            </span>
          ) : isOfficialCopy ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-[#E8F0FE] border border-[#D2E3FC] text-[#1A73E8]">
              <FileCheck className="w-3.5 h-3.5 text-[#1A73E8]" />
              <span className="uppercase tracking-wider">VERIFIED OFFICIAL COPY</span>
            </span>
          ) : isAppGenerated ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-[#FEF7E0] border border-[#FEEFC3] text-[#B06000]">
              <AlertTriangle className="w-3.5 h-3.5 text-[#B06000]" />
              <span className="uppercase tracking-wider">APPLICATION-GENERATED TEMPLATE</span>
            </span>
          ) : isSynthetic ? (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-[#F3E8FD] border border-[#E9D2FD] text-[#7C3AED]">
              <FileCode className="w-3.5 h-3.5 text-[#7C3AED]" />
              <span className="uppercase tracking-wider">SYNTHETIC TEST ASSET</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-medium bg-[#F1F3F4] border border-[#DADCE0] text-[#5F6368]">
              <AlertCircle className="w-3.5 h-3.5 text-[#5F6368]" />
              <span className="uppercase tracking-wider">UNVERIFIED DOCUMENT</span>
            </span>
          )}

          {/* Verification Status Pill */}
          {isVerified ? (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-[#E6F4EA] border border-[#CEEAD6] text-[#0D652D] font-medium">
              <Check className="w-3 h-3 text-[#0D652D]" />
              <span>VERIFIED</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono bg-[#FAF9F5] border border-[#E5E5E0] text-[#73726E]">
              <span>UNVERIFIED</span>
            </span>
          )}
        </div>

        <span className="text-[10px] font-mono text-[#73726E] uppercase px-2 py-0.5 bg-[#FAF9F5] rounded border border-[#E5E5E0]">
          {category}
        </span>
      </div>

      {/* 2. Form Name, Code and Issuing Authority */}
      <div>
        <div className="flex items-baseline gap-2 flex-wrap">
          <h4 className="font-serif text-sm sm:text-base font-semibold text-[#1F1E1D] leading-snug">
            {formName}
          </h4>
          {formCode && (
            <span className="text-[11px] font-mono font-medium text-[#73726E] bg-[#FAF9F5] px-1.5 py-0.5 rounded border border-[#E5E5E0]">
              {formCode}
            </span>
          )}
        </div>

        <div className="text-xs text-[#73726E] font-sans mt-0.5 flex items-center gap-1.5">
          <span>Issuing Authority:</span>
          <strong className="text-[#1F1E1D] font-medium">{authority}</strong>
        </div>
      </div>

      {/* 3. Provenance Transparency Notice for Application-Generated or Synthetic Assets */}
      {isSynthetic ? (
        <div className="p-3 rounded-xl bg-[#F3E8FD]/40 border border-[#E9D2FD] text-xs space-y-1.5" data-testid="synthetic-asset-disclaimer">
          <div className="flex items-center gap-1.5 font-medium text-[#7C3AED]">
            <AlertTriangle className="w-4 h-4 shrink-0 text-[#7C3AED]" />
            <span className="font-semibold uppercase tracking-wider text-[11px]">SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM</span>
          </div>
          <p className="text-[11px] text-[#5B21B6] leading-relaxed">
            This document contains fictional sample data created strictly for development, testing, and UI verification. Do not submit this to any statutory or government authority.
          </p>
          {downloadUrl && (
            <a
              href={downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[11px] font-medium text-[#7C3AED] hover:underline pt-0.5"
            >
              <span>Download Official Original from {authority}</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      ) : (isAppGenerated || !isVerified) ? (
        <div className="p-3 rounded-xl bg-[#FEF7E0]/30 border border-[#FEEFC3] text-xs space-y-1.5">
          <div className="flex items-center gap-1.5 font-medium text-[#B06000]">
            <AlertCircle className="w-4 h-4 shrink-0 text-[#B06000]" />
            <span>Application-Generated Template • Not an Official Government Original</span>
          </div>
          <p className="text-[11px] text-[#7A4100] leading-relaxed">
            This file is an application-generated template synthesized by CONVELINA for reference. To ensure legal validity, download the authentic statutory original directly from the issuing authority portal:
          </p>
          {downloadUrl && (
            <a
              href={downloadUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[11px] font-medium text-[#0066CC] hover:underline pt-0.5"
            >
              <span>Download Official Original from {authority}</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      ) : null}

      {/* 4. Purpose / Description */}
      {purpose && (
        <p className="text-xs font-sans text-[#4A4946] leading-relaxed bg-[#FAF9F5] p-2.5 rounded-xl border border-[#E5E5E0]/60">
          {purpose}
        </p>
      )}

      {/* 5. Prerequisites / Required Proofs (if available) */}
      {prerequisites.length > 0 && (
        <div className="space-y-1.5 text-xs font-sans">
          <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-[#73726E] block">
            Prerequisites & Prescribed Proofs:
          </span>
          <ul className="space-y-1">
            {prerequisites.slice(0, 3).map((item: string, idx: number) => (
              <li key={idx} className="flex items-start gap-1.5 text-[11px] text-[#4A4946]">
                <FileCheck className="w-3.5 h-3.5 text-[#0D652D] shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 6. Document Integrity and Format Footer */}
      <div className="pt-2 border-t border-[#E5E5E0]/80 flex items-center justify-between gap-2 flex-wrap text-[11px] font-sans text-[#73726E]">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono font-semibold text-[#1F1E1D] bg-[#FAF9F5] px-1.5 py-0.5 rounded border border-[#E5E5E0]">
            PDF
          </span>
          <span className="text-[10px] font-mono">{formattedSize}</span>

          {sha256 && (
            <div className="flex items-center gap-1 font-mono text-[10px] text-[#73726E] bg-[#FAF9F5] px-2 py-0.5 rounded border border-[#E5E5E0]">
              <span className="text-[#999893]">SHA-256:</span>
              <span className="font-medium text-[#1F1E1D]" title={sha256}>
                {sha256.substring(0, 10)}...{sha256.substring(sha256.length - 6)}
              </span>
              <button
                type="button"
                onClick={handleCopyHash}
                className="p-0.5 text-[#73726E] hover:text-[#1F1E1D] rounded transition-colors ml-0.5"
                title="Copy full SHA-256 checksum"
                aria-label="Copy SHA-256 checksum"
              >
                {copiedHash ? (
                  <Check className="w-3 h-3 text-[#0D652D]" />
                ) : (
                  <Copy className="w-3 h-3" />
                )}
              </button>
            </div>
          )}
        </div>

        <span className="text-[10px] font-mono text-[#73726E] font-medium hidden sm:inline">
          {isOfficialOriginal ? "GENUINE OFFICIAL PUBLICATION" : "SYNTHESIZED APPLICATION TEMPLATE"}
        </span>
      </div>

      {/* 7. Action Buttons: Direct Official Download, Preview, and Template Download */}
      <div className="pt-1 flex items-center gap-2 flex-wrap">
        {/* Primary Action: Direct link to Authentic Official Portal */}
        {downloadUrl && (
          <a
            href={downloadUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 bg-[#0066CC] hover:bg-[#0052A3] text-white rounded-xl text-xs font-sans font-medium transition-colors shadow-sm"
            title={`Download official publication directly from ${authority}`}
          >
            <span>Download Official Original</span>
            <ExternalLink className="w-3.5 h-3.5 text-white" />
          </a>
        )}

        {/* Secondary Action: Preview Local File */}
        {onPreview && (
          <button
            type="button"
            onClick={() => onPreview(form)}
            disabled={previewing}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-[#FAF9F5] hover:bg-[#EBE9E4] text-[#1F1E1D] rounded-xl text-xs font-sans font-medium border border-[#E5E5E0] transition-colors"
            data-testid={`preview-form-${formId}`}
          >
            {previewing ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Eye className="w-3.5 h-3.5 text-[#73726E]" />
            )}
            <span>{isOfficialOriginal ? "Preview Document" : "Preview Template"}</span>
          </button>
        )}

        {/* Secondary Action: Download Local File Asset */}
        {onDownload && (
          <button
            type="button"
            onClick={() => onDownload(form)}
            disabled={downloading}
            className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-1.5 px-3 py-1.5 bg-[#FAF9F5] hover:bg-[#EBE9E4] text-[#1F1E1D] rounded-xl text-xs font-sans font-medium border border-[#E5E5E0] transition-colors"
            data-testid={`download-form-${formId}`}
          >
            {downloading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#1F1E1D]" />
            ) : (
              <Download className="w-3.5 h-3.5 text-[#73726E]" />
            )}
            <span>{isOfficialOriginal ? "Download Original File" : "Download Template PDF"}</span>
          </button>
        )}

        {portalUrl && (
          <a
            href={portalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center justify-center gap-1 px-2.5 py-1.5 text-[#73726E] hover:text-[#1F1E1D] hover:underline text-xs font-sans transition-colors ml-auto"
            title="Open issuing authority official portal"
          >
            <span>Authority Portal</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  );
}

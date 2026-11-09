"use client";

import React, { useState } from "react";
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  Download,
  Edit3,
  Lock,
  ExternalLink,
  Sparkles,
  RefreshCw,
  Languages,
} from "lucide-react";
import { CorrectionDraftItem, downloadCorrectionDraft } from "../../lib/api";

interface CorrectionDraftCardProps {
  draft: CorrectionDraftItem;
  token: string | null;
  onOpenDraft?: (draft: CorrectionDraftItem) => void;
  onConfirmDraft?: (draft: CorrectionDraftItem) => void;
}

export default function CorrectionDraftCard({
  draft,
  token,
  onOpenDraft,
  onConfirmDraft,
}: CorrectionDraftCardProps) {
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isDownloadingDocx, setIsDownloadingDocx] = useState(false);

  const handleDownload = async (format: "pdf" | "docx") => {
    if (!token) return;
    if (format === "pdf") setIsDownloadingPdf(true);
    else setIsDownloadingDocx(true);

    try {
      const blob = await downloadCorrectionDraft(token, draft.id, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeTitle = (draft.title || "administrative_draft")
        .replace(/[^a-zA-Z0-9_-]/g, "_")
        .slice(0, 40);
      a.download = `${safeTitle}_v${draft.version}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error(`Failed to download draft as ${format}:`, err);
    } finally {
      if (format === "pdf") setIsDownloadingPdf(false);
      else setIsDownloadingDocx(false);
    }
  };

  const isConfirmed = draft.status === "citizen_confirmed" && draft.is_citizen_confirmed;
  const isEdited = draft.status === "citizen_edited";

  return (
    <div className="my-3 rounded-2xl border border-[#E5E3DC] bg-[#FAF9F5] p-4 shadow-sm hover:border-[#D5D2C8] transition-all max-w-xl">
      {/* Header Row */}
      <div className="flex items-start justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#C96442]/10 border border-[#C96442]/30 flex items-center justify-center text-[#C96442] shrink-0">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-semibold text-[#1F1E1D] flex items-center gap-2">
              <span>{draft.title || "Administrative Correction Draft"}</span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#EFECE6] text-[#6B6966] font-mono">
                v{draft.version}
              </span>
            </div>
            <div className="text-[11px] text-[#6B6966] capitalize">
              Category: {draft.document_category?.replace(/_/g, " ")}
            </div>
          </div>
        </div>

        {/* Status Badge */}
        <div>
          {isConfirmed ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#E6F4EA] text-[#0D652D] border border-[#CEEAD6]">
              <CheckCircle2 className="w-3 h-3" />
              CONFIRMED
            </span>
          ) : isEdited ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#FEF7E0] text-[#B06000] border border-[#FEEFC3]">
              <Edit3 className="w-3 h-3" />
              EDITED
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#E8F0FE] text-[#1A73E8] border border-[#D2E3FC]">
              <Sparkles className="w-3 h-3" />
              AI DRAFT
            </span>
          )}
        </div>
      </div>

      {/* Recipient and Subject Preview */}
      {(draft.recipient_authority || draft.subject) && (
        <div className="mb-2.5 p-2 rounded-lg bg-white border border-[#EFECE6] text-[11px] space-y-1">
          {draft.recipient_authority && (
            <div>
              <span className="font-semibold text-[#6B6966]">To: </span>
              <span className="text-[#1F1E1D]">{draft.recipient_authority}</span>
            </div>
          )}
          {draft.subject && (
            <div>
              <span className="font-semibold text-[#6B6966]">Subject: </span>
              <span className="text-[#1F1E1D]">{draft.subject}</span>
            </div>
          )}
        </div>
      )}

      {/* Content Snippet */}
      <div className="text-xs text-[#6B6966] bg-white p-2.5 rounded-lg border border-[#EFECE6] font-mono leading-relaxed mb-3 line-clamp-3">
        {draft.content}
      </div>

      {/* Mandatory Disclaimer Pill */}
      <div className="text-[10px] text-[#8E8B85] italic mb-3 flex items-center gap-1">
        <span>* AI-generated administrative representation • Review all details before submission</span>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#EFECE6]">
        {onOpenDraft && (
          <button
            onClick={() => onOpenDraft(draft)}
            className="px-3 py-1.5 text-xs font-medium bg-[#1F1E1D] text-white hover:bg-[#33312E] rounded-lg transition-colors flex items-center gap-1.5"
          >
            <Edit3 className="w-3 h-3" />
            <span>Review & Edit</span>
          </button>
        )}

        {!isConfirmed && onConfirmDraft && (
          <button
            onClick={() => onConfirmDraft(draft)}
            className="px-3 py-1.5 text-xs font-medium bg-[#0D652D] text-white hover:bg-[#0B5324] rounded-lg transition-colors flex items-center gap-1.5 shadow-sm"
          >
            <Lock className="w-3 h-3" />
            <span>Confirm v{draft.version}</span>
          </button>
        )}

        <button
          onClick={() => handleDownload("pdf")}
          disabled={isDownloadingPdf}
          className="px-2.5 py-1.5 text-xs font-medium bg-white border border-[#D5D2C8] text-[#1F1E1D] hover:bg-[#FAF9F5] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
        >
          {isDownloadingPdf ? (
            <RefreshCw className="w-3 h-3 animate-spin" />
          ) : (
            <Download className="w-3 h-3 text-[#C96442]" />
          )}
          <span>PDF</span>
        </button>

        <button
          onClick={() => handleDownload("docx")}
          disabled={isDownloadingDocx}
          className="px-2.5 py-1.5 text-xs font-medium bg-white border border-[#D5D2C8] text-[#1F1E1D] hover:bg-[#FAF9F5] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
        >
          {isDownloadingDocx ? (
            <RefreshCw className="w-3 h-3 animate-spin" />
          ) : (
            <Download className="w-3 h-3 text-[#1A73E8]" />
          )}
          <span>DOCX</span>
        </button>
      </div>
    </div>
  );
}


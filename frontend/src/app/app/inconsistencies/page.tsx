"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  UploadCloud,
  FileText,
  Trash2,
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Scale,
  Sparkles,
  ChevronDown,
  ChevronUp,
  ArrowRight,
  RefreshCw,
  X,
  Eye,
  Edit3,
  Download,
  Save,
  Check,
  FileSpreadsheet,
  Shield,
  ExternalLink,
} from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import AdministrativeDraftingModal from "../../../components/drafting/AdministrativeDraftingModal";
import {
  fetchDocuments,
  uploadDocument,
  deleteDocument,
  updateDocumentFields,
  confirmDocumentFields,
  fetchConflicts,
  detectConflicts,
  fetchCorrectionDrafts,
  createCorrectionDraft,
  updateCorrectionDraft,
  deleteCorrectionDraft,
  downloadCorrectionDraft,
  compareDocuments,
  fetchResolutionContext,
  DocumentItem,
  ConflictItem,
  CorrectionDraftItem,
  DocumentCompareResponse,
  ResolutionContextData,
} from "../../../lib/api";

const CLASSIFICATION_BADGES: Record<string, { label: string; textClass: string; bgClass: string; borderClass: string }> = {
  EXACT_MATCH: {
    label: "EXACT MATCH",
    textClass: "text-[#0D652D]",
    bgClass: "bg-[#E6F4EA]",
    borderClass: "border-[#CEEAD6]",
  },
  FORMAT_ONLY_MATCH: {
    label: "FORMATTING-ONLY DIFFERENCE",
    textClass: "text-[#1A73E8]",
    bgClass: "bg-[#E8F0FE]",
    borderClass: "border-[#D2E3FC]",
  },
  TOKEN_ORDER_VARIATION: {
    label: "FORMATTING-ONLY DIFFERENCE",
    textClass: "text-[#1A73E8]",
    bgClass: "bg-[#E8F0FE]",
    borderClass: "border-[#D2E3FC]",
  },
  TRANSLITERATION_OR_VARIANT: {
    label: "TRANSLITERATION / SPELLING VARIATION",
    textClass: "text-[#007B83]",
    bgClass: "bg-[#E0F2F1]",
    borderClass: "border-[#B2DFDB]",
  },
  LIKELY_SAME_PERSON: {
    label: "TRANSLITERATION / SPELLING VARIATION",
    textClass: "text-[#007B83]",
    bgClass: "bg-[#E0F2F1]",
    borderClass: "border-[#B2DFDB]",
  },
  TRUNCATION_OR_PARTIAL_MATCH: {
    label: "POSSIBLE TRUNCATION",
    textClass: "text-[#B06000]",
    bgClass: "bg-[#FEF7E0]",
    borderClass: "border-[#FEEFC3]",
  },
  AMBIGUOUS_NEEDS_REVIEW: {
    label: "AMBIGUOUS MATCH",
    textClass: "text-[#B06000]",
    bgClass: "bg-[#FEF7E0]",
    borderClass: "border-[#FEEFC3]",
  },
  INITIAL_AMBIGUITY: {
    label: "AMBIGUOUS MATCH",
    textClass: "text-[#B06000]",
    bgClass: "bg-[#FEF7E0]",
    borderClass: "border-[#FEEFC3]",
  },
  GENDER_AWARE_SIMILAR_NAME: {
    label: "AMBIGUOUS MATCH",
    textClass: "text-[#B06000]",
    bgClass: "bg-[#FEF7E0]",
    borderClass: "border-[#FEEFC3]",
  },
  MISMATCH: {
    label: "GENUINE MISMATCH",
    textClass: "text-[#C5221F]",
    bgClass: "bg-[#FCE8E6]",
    borderClass: "border-[#FAD2CF]",
  },
  HIGH_RISK_GENUINE_MISMATCH: {
    label: "GENUINE MISMATCH",
    textClass: "text-[#C5221F]",
    bgClass: "bg-[#FCE8E6]",
    borderClass: "border-[#FAD2CF]",
  },
  LOW_CONFIDENCE_NEEDS_REVIEW: {
    label: "MANUAL REVIEW REQUIRED",
    textClass: "text-[#E37400]",
    bgClass: "bg-[#FEF7E0]",
    borderClass: "border-[#FEEFC3]",
  },
  UNRESOLVABLE_NEEDS_MANUAL_REVIEW: {
    label: "MANUAL REVIEW REQUIRED",
    textClass: "text-[#C5221F]",
    bgClass: "bg-[#FCE8E6]",
    borderClass: "border-[#FAD2CF]",
  },
  INSUFFICIENT_DATA: {
    label: "MANUAL REVIEW REQUIRED",
    textClass: "text-[#777777]",
    bgClass: "bg-[#F4F3EF]",
    borderClass: "border-[#E7E5E0]",
  },
};

const DOC_TYPE_LABELS: Record<string, string> = {
  aadhaar: "Aadhaar Card",
  pan: "PAN Card",
  passport: "Passport",
  education: "Educational Certificate (Class 10/12)",
  education_10th: "Class 10 Certificate / Marksheet",
  education_12th: "Class 12 Certificate / Marksheet",
  epf: "EPF Records",
  epf_record: "EPFO / UAN Records",
  voter_id: "Voter ID Card",
  driving_licence: "Driving Licence",
  other: "Other Identity Document",
};

export default function InconsistenciesPage() {
  const router = useRouter();
  const { idToken } = useAuth();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Core Data States
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [drafts, setDrafts] = useState<CorrectionDraftItem[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  // Operation States
  const [selectedDocType, setSelectedDocType] = useState("aadhaar");
  const [uploading, setUploading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [comparing, setComparing] = useState(false);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] = useState<DocumentCompareResponse | null>(null);
  const [generatingDraftForConflict, setGeneratingDraftForConflict] = useState<string | null>(null);
  const [downloadingDraftId, setDownloadingDraftId] = useState<string | null>(null);

  // Status Feedback
  const [statusMessage, setStatusMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Modal State: Review Extracted Fields (Stage 5)
  const [reviewingDoc, setReviewingDoc] = useState<DocumentItem | null>(null);
  const [editedFields, setEditedFields] = useState<Record<string, any>>({});
  const [savingFields, setSavingFields] = useState(false);

  // Modal State: View / Edit Correction Draft (Module 7)
  const [editingDraft, setEditingDraft] = useState<CorrectionDraftItem | null>(null);
  const [draftContent, setDraftContent] = useState("");
  const [draftTitle, setDraftTitle] = useState("");
  const [savingDraft, setSavingDraft] = useState(false);

  // Administrative Drafting Modal State (Phase P3G)
  const [draftingModalOpen, setDraftingModalOpen] = useState(false);
  const [draftingConflict, setDraftingConflict] = useState<ConflictItem | null>(null);
  const [draftingSelectedDraft, setDraftingSelectedDraft] = useState<CorrectionDraftItem | null>(null);

  const handleOpenDraftingForConflict = (conflict: ConflictItem) => {
    setDraftingConflict(conflict);
    setDraftingSelectedDraft(null);
    setDraftingModalOpen(true);
  };

  const handleOpenDraftingForExistingDraft = (dft: CorrectionDraftItem) => {
    const matchedConflict = conflicts.find((c) => c.id === dft.conflict_id) || null;
    setDraftingConflict(matchedConflict);
    setDraftingSelectedDraft(dft);
    setDraftingModalOpen(true);
  };

  const handleDraftSaved = (savedDraft: CorrectionDraftItem) => {
    setDrafts((prev) => {
      const idx = prev.findIndex((d) => d.id === savedDraft.id);
      if (idx >= 0) {
        const copy = [...prev];
        copy[idx] = savedDraft;
        return copy;
      }
      return [savedDraft, ...prev];
    });
  };

  // Discrepancy In-Place AI Resolution Context Preview (Phase P3C)
  const [expandedPreviewId, setExpandedPreviewId] = useState<string | null>(null);
  const [previewContexts, setPreviewContexts] = useState<Record<string, ResolutionContextData>>({});
  const [loadingPreviewId, setLoadingPreviewId] = useState<string | null>(null);

  const handleTogglePreviewContext = async (conflictId: string) => {
    if (expandedPreviewId === conflictId) {
      setExpandedPreviewId(null);
      return;
    }
    setExpandedPreviewId(conflictId);
    if (!previewContexts[conflictId] && idToken) {
      try {
        setLoadingPreviewId(conflictId);
        const ctx = await fetchResolutionContext(idToken, conflictId);
        setPreviewContexts((prev) => ({ ...prev, [conflictId]: ctx }));
      } catch (err) {
        console.warn("Could not load preview context:", err);
      } finally {
        setLoadingPreviewId(null);
      }
    }
  };

  // Load documents, conflicts, and drafts
  const loadAllData = useCallback(async () => {
    if (!idToken) return;
    try {
      setLoadingData(true);
      const [docs, confs, dfts] = await Promise.all([
        fetchDocuments(idToken).catch(() => []),
        fetchConflicts(idToken).catch(() => []),
        fetchCorrectionDrafts(idToken).catch(() => []),
      ]);
      setDocuments(docs);
      setConflicts(confs);
      setDrafts(dfts);
    } catch (err: any) {
      console.warn("Error loading data:", err);
    } finally {
      setLoadingData(false);
    }
  }, [idToken]);

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Handle file selection and upload
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    if (file.size > 10 * 1024 * 1024) {
      setStatusMessage({
        type: "error",
        text: "File size exceeds 10MB limit. Please upload a smaller document.",
      });
      return;
    }

    setUploading(true);
    setStatusMessage(null);

    try {
      await uploadDocument(idToken, selectedDocType, file);
      setStatusMessage({
        type: "success",
        text: `${DOC_TYPE_LABELS[selectedDocType] || "Document"} uploaded and OCR processed successfully. Temporary file unlinked per Aadhaar privacy retention.`,
      });
      await loadAllData();
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Failed to process document upload.",
      });
    } finally {
      setUploading(false);
    }
  };

  // Handle document deletion
  const handleDeleteDoc = async (docId: string, docLabel: string) => {
    if (!confirm(`Delete ${docLabel}? This will remove the document and its extracted demographic fields.`)) {
      return;
    }
    try {
      await deleteDocument(idToken, docId);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
      setStatusMessage({
        type: "success",
        text: `${docLabel} removed successfully.`,
      });
      if (idToken) {
        const confs = await fetchConflicts(idToken);
        setConflicts(confs);
      }
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Failed to delete document.",
      });
    }
  };

  // Open Extracted Fields Review Modal
  const handleOpenReview = (doc: DocumentItem) => {
    setReviewingDoc(doc);
    const initialFields = doc.is_user_confirmed && doc.confirmed_fields && Object.keys(doc.confirmed_fields).length > 0
      ? { ...doc.confirmed_fields }
      : doc.extracted_fields
      ? { ...doc.extracted_fields }
      : {};
    setEditedFields(initialFields);
  };

  const [confirmingFields, setConfirmingFields] = useState(false);

  // Confirm Extracted & Corrected Demographic Fields (Citizen Confirmation)
  const handleConfirmFields = async () => {
    if (!reviewingDoc || !idToken) return;
    setConfirmingFields(true);
    try {
      const updated = await confirmDocumentFields(idToken, reviewingDoc.id, editedFields);
      setDocuments((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setStatusMessage({
        type: "success",
        text: `Demographic fields for ${DOC_TYPE_LABELS[reviewingDoc.document_type] || "document"} verified and confirmed by citizen. Ready for deterministic comparison.`,
      });
      setReviewingDoc(null);
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Failed to confirm document fields.",
      });
    } finally {
      setConfirmingFields(false);
    }
  };

  // Save Extracted Fields Changes
  const handleSaveFields = async () => {
    if (!reviewingDoc || !idToken) return;
    setSavingFields(true);
    try {
      const updated = await updateDocumentFields(idToken, reviewingDoc.id, editedFields);
      setDocuments((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setStatusMessage({
        type: "success",
        text: `Extracted demographic fields for ${DOC_TYPE_LABELS[reviewingDoc.document_type] || "document"} updated successfully. Run "Detect Conflicts" to update discrepancy analysis.`,
      });
      setReviewingDoc(null);
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Failed to save updated fields.",
      });
    } finally {
      setSavingFields(false);
    }
  };

  // Toggle selection of a document for comparison
  const handleToggleDocSelect = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  // Select all completed documents
  const handleSelectAllReadyDocs = () => {
    const readyIds = documents.filter((d) => d.ocr_status === "completed").map((d) => d.id);
    setSelectedDocIds(readyIds);
  };

  // Clear document selection
  const handleClearDocSelection = () => {
    setSelectedDocIds([]);
  };

  // Run Phase P1 Deterministic Document Comparison
  const handleCompareDocuments = async (targetDocIds?: string[]) => {
    const ids =
      targetDocIds && targetDocIds.length >= 2
        ? targetDocIds
        : selectedDocIds.length >= 2
        ? selectedDocIds
        : documents.filter((d) => d.ocr_status === "completed").map((d) => d.id);

    if (ids.length < 2) {
      setStatusMessage({
        type: "error",
        text: "Please select at least 2 completed credentials to execute deterministic comparison.",
      });
      return;
    }

    setComparing(true);
    setStatusMessage(null);
    try {
      const res = await compareDocuments(idToken, ids);
      setComparisonResult(res);
      const confs = await fetchConflicts(idToken).catch(() => []);
      setConflicts(confs);
      const badge = CLASSIFICATION_BADGES[res.overall_classification]?.label || res.overall_classification;
      setStatusMessage({
        type: "success",
        text: `Deterministic comparison complete: ${badge} (${Math.round(res.confidence_score * 100)}% confidence).`,
      });
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Failed to compare selected documents.",
      });
    } finally {
      setComparing(false);
    }
  };

  // Run legacy full conflict detection
  const handleDetectConflicts = async () => {
    if (documents.length < 2) {
      setStatusMessage({
        type: "error",
        text: "Please upload at least 2 credentials (e.g., Aadhaar and PAN) to compare and detect discrepancies.",
      });
      return;
    }

    setDetecting(true);
    setStatusMessage(null);

    try {
      const res = await detectConflicts(idToken);
      setConflicts(res.conflicts || []);
      setStatusMessage({
        type: "success",
        text: `Analysis complete: ${res.detected_conflicts_count || 0} discrepancy(ies) detected across records.`,
      });
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Conflict detection failed.",
      });
    } finally {
      setDetecting(false);
    }
  };

  // Generate Correction Draft for a Conflict
  const handleGenerateDraft = async (conflict: ConflictItem) => {
    if (!idToken) return;
    setGeneratingDraftForConflict(conflict.id);
    setStatusMessage(null);

    try {
      const newDraft = await createCorrectionDraft(idToken, {
        conflict_id: conflict.id,
        document_type: "formal_representation",
        document_category: "identity_correction",
        confirmed_fields: {
          [conflict.field_name]: conflict.value_a,
        },
      });
      setDrafts((prev) => [newDraft, ...prev]);
      setStatusMessage({
        type: "success",
        text: `Legal correction draft "${newDraft.title}" generated successfully. You can review, edit, or download it below.`,
      });
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Failed to generate correction draft.",
      });
    } finally {
      setGeneratingDraftForConflict(null);
    }
  };

  // Open Draft Edit Modal
  const handleOpenEditDraft = (draft: CorrectionDraftItem) => {
    setEditingDraft(draft);
    setDraftTitle(draft.title);
    setDraftContent(draft.content);
  };

  // Save Draft Changes
  const handleSaveDraft = async () => {
    if (!editingDraft || !idToken) return;
    setSavingDraft(true);
    try {
      const updated = await updateCorrectionDraft(idToken, editingDraft.id, {
        title: draftTitle,
        content: draftContent,
      });
      setDrafts((prev) => prev.map((d) => (d.id === updated.id ? updated : d)));
      setStatusMessage({
        type: "success",
        text: `Correction draft updated (Version ${updated.version}).`,
      });
      setEditingDraft(null);
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Failed to update draft.",
      });
    } finally {
      setSavingDraft(false);
    }
  };

  // Delete Draft
  const handleDeleteDraft = async (draftId: string, title: string) => {
    if (!confirm(`Delete draft "${title}"? This action cannot be undone.`)) return;
    try {
      await deleteCorrectionDraft(idToken, draftId);
      setDrafts((prev) => prev.filter((d) => d.id !== draftId));
      setStatusMessage({
        type: "success",
        text: `Draft "${title}" deleted successfully.`,
      });
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Failed to delete draft.",
      });
    }
  };

  // Download Draft (PDF / DOCX)
  const handleDownload = async (draft: CorrectionDraftItem, format: "pdf" | "docx") => {
    if (!idToken) return;
    setDownloadingDraftId(`${draft.id}-${format}`);
    try {
      const blob = await downloadCorrectionDraft(idToken, draft.id, format);
      const url = window.URL.createObjectURL(blob);
      const safeTitle = draft.title.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 40);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${safeTitle}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || `Failed to download ${format.toUpperCase()} file.`,
      });
    } finally {
      setDownloadingDraftId(null);
    }
  };

  // Helper to format document type name
  const getDocName = (docId: string) => {
    const doc = documents.find((d) => d.id === docId);
    return doc ? DOC_TYPE_LABELS[doc.document_type] || doc.document_type : "Document";
  };

  return (
    <div className="max-w-4xl mx-auto w-full py-10 px-4 sm:px-6 lg:px-8 pb-24">
      {/* Header & Editorial Intro */}
      <header className="mb-10 space-y-2 border-b border-[#E7E5E0] pb-8">
        <div className="flex items-center gap-2">
          <span className="font-sans text-[11px] uppercase tracking-wider text-[#777777] font-medium">
            Verification Engine
          </span>
          <span className="text-[#CCCCCC]">•</span>
          <span className="font-sans text-[11px] text-[#777777]">
            Deterministic Matching & Legal Rectification
          </span>
        </div>
        <h1 className="font-serif text-3xl sm:text-4xl text-[#111111] font-light tracking-tight">
          Document Inconsistencies & Rectification
        </h1>
        <p className="font-sans text-sm sm:text-base text-[#5E5E5E] max-w-2xl leading-relaxed">
          Upload and review identity credentials, detect spelling variations and date of birth
          discrepancies, and generate formal legal correction drafts for administrative rectification.
        </p>
      </header>

      {/* Status Alert Banner */}
      {statusMessage && (
        <div
          className={`mb-6 p-4 rounded-[4px] border text-xs font-sans flex items-start gap-3 ${
            statusMessage.type === "success"
              ? "bg-[#FAF9F6] border-[#111111] text-[#111111]"
              : "bg-[#FFDAD6]/30 border-[#BA1A1A] text-[#BA1A1A]"
          }`}
        >
          {statusMessage.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-[#111111] shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 text-[#BA1A1A] shrink-0 mt-0.5" />
          )}
          <span className="flex-1 leading-relaxed">{statusMessage.text}</span>
          <button
            onClick={() => setStatusMessage(null)}
            className="text-[#777777] hover:text-[#111111]"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Section 1: Upload Credentials */}
      <section className="space-y-4 mb-10">
        <h2 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777]">
          Add Document for Reconciliation
        </h2>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative w-full sm:w-72">
            <select
              value={selectedDocType}
              onChange={(e) => setSelectedDocType(e.target.value)}
              className="w-full h-10 px-3 pr-8 bg-white text-[#111111] font-sans text-sm border border-[#E7E5E0] rounded-[4px] focus:border-[#111111] focus:outline-none appearance-none transition-colors"
            >
              <optgroup label="Tier 1 Primary Identity Categories">
                <option value="aadhaar">Aadhaar Card</option>
                <option value="pan">PAN Card</option>
                <option value="passport">Passport</option>
                <option value="education_10th">Class 10 Certificate / Marksheet</option>
                <option value="education_12th">Class 12 Certificate / Marksheet</option>
                <option value="epf_record">EPFO / UAN Records</option>
              </optgroup>
              <optgroup label="Secondary Supporting Evidence">
                <option value="voter_id">Voter ID Card</option>
                <option value="driving_licence">Driving Licence</option>
                <option value="other">Other Identity Document</option>
              </optgroup>
            </select>
            <ChevronDown className="w-4 h-4 text-[#777777] absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          <label className="h-10 px-4 bg-white border border-[#E7E5E0] rounded-[4px] text-[#111111] hover:bg-[#F4F3EF] font-sans text-sm flex items-center justify-center gap-2 cursor-pointer transition-colors shrink-0">
            <UploadCloud className="w-4 h-4 text-[#5E5E5E]" />
            <span>{uploading ? "Extracting OCR..." : "Upload File"}</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.png,.jpg,.jpeg"
              onChange={handleFileChange}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>

        {uploading && (
          <div className="p-3.5 bg-[#FAF9F6] border border-[#111111] rounded-[4px] text-xs font-sans text-[#111111] flex items-center gap-3 animate-pulse">
            <RefreshCw className="w-4 h-4 animate-spin text-[#111111] shrink-0" />
            <div className="space-y-0.5">
              <div className="font-semibold">Processing Credential OCR & Privacy Masking...</div>
              <div className="text-[11px] text-[#5E5E5E]">
                Executing in-memory text extraction, demographic attribute isolation, and sensitive identifier masking. Ephemeral processing active: temporary upload files are unlinked immediately after extraction; sensitive fields are masked in views.
              </div>
            </div>
          </div>
        )}

        <p className="font-sans text-[11px] text-[#777777]">
          Accepted formats: PDF, PNG, JPEG (up to 10MB). Six Tier 1 primary identity categories are evaluated for statutory discrepancy analysis; secondary documents serve as corroborating evidence. Ephemeral processing active: temporary files are unlinked immediately.
        </p>

        {/* Uploaded Documents List */}
        <div className="pt-4">
          <div className="flex items-center justify-between mb-2.5">
            <h3 className="font-sans text-xs font-medium text-[#777777]">
              Uploaded Credentials ({documents.length})
            </h3>
            {documents.length >= 2 && (
              <div className="flex items-center gap-2 text-xs font-sans">
                <button
                  type="button"
                  onClick={handleSelectAllReadyDocs}
                  className="text-[#111111] hover:underline font-medium"
                >
                  Select All Ready
                </button>
                {selectedDocIds.length > 0 && (
                  <>
                    <span className="text-[#CCCCCC]">•</span>
                    <button
                      type="button"
                      onClick={handleClearDocSelection}
                      className="text-[#777777] hover:underline"
                    >
                      Clear ({selectedDocIds.length})
                    </button>
                  </>
                )}
              </div>
            )}
          </div>

          {loadingData ? (
            <div className="py-4 text-xs text-[#777777] font-sans">
              Loading document library...
            </div>
          ) : documents.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {documents.map((doc) => {
                const label = DOC_TYPE_LABELS[doc.document_type] || doc.document_type;
                const fieldCount = Object.keys(doc.extracted_fields || {}).length;
                const isSelected = selectedDocIds.includes(doc.id);
                const isReady = doc.ocr_status === "completed";

                return (
                  <div
                    key={doc.id}
                    onClick={() => isReady && handleToggleDocSelect(doc.id)}
                    className={`flex flex-col justify-between rounded-[4px] p-3 transition-colors cursor-pointer border ${
                      isSelected
                        ? "border-[#111111] bg-[#FAF9F6] shadow-sm"
                        : "border-[#E7E5E0] bg-white hover:border-[#CCCCCC]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleToggleDocSelect(doc.id);
                          }}
                          disabled={!isReady}
                          className="w-4 h-4 rounded border-[#CCCCCC] text-[#111111] focus:ring-0 cursor-pointer"
                        />
                        <FileText className="w-4 h-4 text-[#777777] shrink-0" />
                        <span className="font-sans text-sm font-medium truncate text-[#111111]">
                          {label}
                        </span>
                      </div>
                      <span
                        className={`font-sans text-[10px] px-1.5 py-0.5 rounded-[2px] shrink-0 font-medium ${
                          doc.is_user_confirmed
                            ? "bg-[#E6F4EA] text-[#0D652D] border border-[#CEEAD6]"
                            : doc.ocr_status === "needs_review"
                            ? "bg-[#FEF7E0] text-[#B06000] border border-[#FEEFC3]"
                            : isReady
                            ? "bg-[#E8F0FE] text-[#1A73E8]"
                            : "bg-[#F4F3EF] text-[#5E5E5E]"
                        }`}
                      >
                        {doc.is_user_confirmed
                          ? "Confirmed"
                          : doc.ocr_status === "needs_review"
                          ? "Needs Review"
                          : isReady
                          ? "Ready"
                          : doc.ocr_status}
                      </span>
                    </div>

                    {doc.masked_id && (
                      <div className="font-mono text-xs text-[#5E5E5E] mt-2 ml-6">
                        ID: {doc.masked_id}
                      </div>
                    )}

                    <div
                      className="mt-3 pt-2.5 border-t border-[#F0EFEA] flex items-center justify-between text-xs font-sans"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <button
                        onClick={() => handleOpenReview(doc)}
                        className="text-[#111111] hover:underline flex items-center gap-1 font-medium"
                      >
                        <Eye className="w-3.5 h-3.5 text-[#777777]" />
                        <span>Review Fields ({fieldCount})</span>
                      </button>

                      <button
                        onClick={() => handleDeleteDoc(doc.id, label)}
                        aria-label={`Remove ${label}`}
                        className="text-[#777777] hover:text-[#BA1A1A] transition-colors p-1"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="p-4 bg-white border border-[#E7E5E0] rounded-[4px] text-xs text-[#777777] font-sans">
              No credentials uploaded yet. Upload at least 2 documents to detect discrepancies.
            </div>
          )}
        </div>

        {/* Primary Action Buttons */}
        <div className="pt-4 flex flex-wrap items-center gap-3">
          <button
            onClick={() => handleCompareDocuments()}
            disabled={comparing || documents.filter((d) => d.ocr_status === "completed").length < 2}
            className="h-10 px-5 bg-[#111111] text-white font-sans text-sm rounded-[4px] font-medium hover:bg-black/90 active:bg-black disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {comparing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Comparing Selected Records...</span>
              </>
            ) : (
              <>
                <Scale className="w-4 h-4" />
                <span>
                  Compare Selected Credentials
                  {selectedDocIds.length >= 2 ? ` (${selectedDocIds.length})` : ""}
                </span>
              </>
            )}
          </button>

          <button
            onClick={handleDetectConflicts}
            disabled={detecting || documents.length < 2}
            className="h-10 px-4 bg-white border border-[#E7E5E0] text-[#111111] font-sans text-sm rounded-[4px] font-medium hover:bg-[#F4F3EF] active:bg-[#E7E5E0] disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {detecting ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Scanning All...</span>
              </>
            ) : (
              <>
                <FileSpreadsheet className="w-4 h-4 text-[#5E5E5E]" />
                <span>Detect All Inconsistencies</span>
              </>
            )}
          </button>
        </div>

        {/* Phase P1 Deterministic Comparison Analysis Result Panel */}
        {comparisonResult && (
          <div className="mt-8 border border-[#111111] rounded-[6px] bg-white overflow-hidden shadow-sm">
            {/* Header & Classification Badge */}
            <div className="p-5 border-b border-[#E7E5E0] bg-[#FAF9F6] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="font-sans text-[11px] uppercase tracking-wider text-[#777777] font-semibold">
                    Automated Comparison Result
                  </span>
                  <span className="text-[#CCCCCC]">•</span>
                  <span className="font-sans text-xs text-[#5E5E5E]">
                    Confidence: {Math.round(comparisonResult.confidence_score * 100)}%
                  </span>
                </div>
                <h3 className="font-serif text-2xl text-[#111111] font-light">
                  {comparisonResult.explanation}
                </h3>
              </div>

              <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
                {(() => {
                  const badge =
                    CLASSIFICATION_BADGES[comparisonResult.overall_classification] || {
                      label: comparisonResult.overall_classification.replace(/_/g, " "),
                      textClass: "text-[#111111]",
                      bgClass: "bg-[#F4F3EF]",
                      borderClass: "border-[#E7E5E0]",
                    };
                  return (
                    <div
                      className={`px-3.5 py-1.5 rounded-[4px] border font-sans text-xs font-semibold tracking-wide ${badge.bgClass} ${badge.textClass} ${badge.borderClass}`}
                    >
                      {badge.label}
                    </div>
                  );
                })()}

                <button
                  type="button"
                  onClick={() => {
                    const matchedConflict = conflicts.find((c) =>
                      selectedDocIds.includes(c.doc_a_id) || selectedDocIds.includes(c.doc_b_id)
                    ) || conflicts[0];
                    if (matchedConflict) {
                      router.push(`/app/assistant?conflictId=${matchedConflict.id}`);
                    } else {
                      router.push("/app/assistant");
                    }
                  }}
                  className="h-8 px-3 bg-[#111111] text-white rounded-[4px] text-xs font-sans font-medium hover:bg-black/90 transition-colors flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Get Resolution Guidance</span>
                </button>
              </div>
            </div>

            {/* Statutory Disclaimer - Separating Automated Result from Official Verification */}
            <div className="px-5 py-3.5 bg-[#FAF9F6] border-b border-[#E7E5E0] text-xs font-sans text-[#5E5E5E] space-y-1">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 font-mono text-[10px] uppercase font-bold text-[#111111]">
                  <AlertCircle className="w-3.5 h-3.5 text-[#777777] shrink-0" />
                  <span>AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION</span>
                </div>
                <button
                  onClick={() => setComparisonResult(null)}
                  className="text-[#777777] hover:text-[#111111] font-medium shrink-0 ml-2"
                >
                  Dismiss
                </button>
              </div>
              <p className="text-[11px] text-[#777777] leading-relaxed">
                CONVELINA provides automated identity discrepancy detection and statutory guidance. It does not constitute official government verification, certification, or legal determination. CONVELINA does not declare which document is legally correct. Review statutory guidelines or consult competent authorities.
              </p>
            </div>

            {/* Low OCR Confidence Warning Notice */}
            {comparisonResult.overall_classification === "LOW_CONFIDENCE_NEEDS_REVIEW" && (
              <div className="px-5 py-3.5 bg-[#FEF7E0] border-b border-[#FEEFC3] text-xs font-sans text-[#B06000] flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 text-[#E37400] shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold">
                    Some document information could not be read with sufficient confidence.
                  </div>
                  <div className="text-[11px] text-[#777777] mt-0.5">
                    Safe next action: Please upload a clearer, high-resolution document scan or use &quot;Review Fields&quot; to verify extracted values.
                  </div>
                </div>
              </div>
            )}

            {/* Body: Multi-Field Evidence & Discrepancies */}
            <div className="p-5 space-y-6">
              {/* Supporting Evidence List */}
              {comparisonResult.evidence.length > 0 && (
                <div>
                  <h4 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777] mb-2">
                    Supporting Verification Evidence
                  </h4>
                  <ul className="space-y-1.5 font-sans text-xs text-[#111111]">
                    {comparisonResult.evidence.map((ev, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <Check className="w-3.5 h-3.5 text-[#0D652D] shrink-0 mt-0.5" />
                        <span>{ev}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Matched Fields Pills */}
              {comparisonResult.matched_fields.length > 0 && (
                <div>
                  <h4 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777] mb-2">
                    Consistent Demographic Attributes
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {comparisonResult.matched_fields.map((field) => (
                      <span
                        key={field}
                        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-[4px] bg-[#E6F4EA] text-[#0D652D] font-sans text-xs font-medium border border-[#CEEAD6]"
                      >
                        <Check className="w-3 h-3" />
                        <span className="capitalize">{field.replace(/_/g, " ")}</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Detailed Field Breakdown */}
              {Object.keys(comparisonResult.field_results).length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-sans text-xs font-semibold uppercase tracking-wider text-[#777777]">
                    Attribute-by-Attribute Breakdown
                  </h4>
                  <div className="grid grid-cols-1 gap-3">
                    {Object.entries(comparisonResult.field_results).map(([fname, fresult]) => {
                      const fBadge =
                        CLASSIFICATION_BADGES[fresult.classification] || {
                          label: fresult.classification.replace(/_/g, " "),
                          textClass: "text-[#111111]",
                          bgClass: "bg-[#F4F3EF]",
                          borderClass: "border-[#E7E5E0]",
                        };

                      return (
                        <div
                          key={fname}
                          className="p-4 rounded-[4px] border border-[#E7E5E0] bg-[#FAF9F6] space-y-2.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-sans text-xs font-semibold uppercase text-[#111111]">
                              {fname.replace(/_/g, " ")}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded-[2px] font-sans text-[10px] font-semibold tracking-wider ${fBadge.bgClass} ${fBadge.textClass} border ${fBadge.borderClass}`}
                            >
                              {fBadge.label}
                            </span>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-sans">
                            <div className="p-2.5 bg-white border border-[#E7E5E0] rounded-[3px]">
                              <span className="text-[10px] text-[#777777] uppercase block">
                                Document A
                              </span>
                              <span className="font-medium text-[#111111]">
                                {fresult.value_a_raw || "—"}
                              </span>
                            </div>
                            <div className="p-2.5 bg-white border border-[#E7E5E0] rounded-[3px]">
                              <span className="text-[10px] text-[#777777] uppercase block">
                                Document B
                              </span>
                              <span className="font-medium text-[#111111]">
                                {fresult.value_b_raw || "—"}
                              </span>
                            </div>
                          </div>

                          <div className="text-xs font-sans text-[#5E5E5E] leading-relaxed">
                            {fresult.explanation}
                          </div>

                          {fresult.recommended_action && (
                            <div className="text-xs font-sans text-[#111111] bg-white p-2.5 border border-[#E7E5E0] rounded-[3px]">
                              <strong className="text-[#777777] uppercase text-[10px] block mb-0.5">
                                Recommended Action
                              </strong>
                              {fresult.recommended_action}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </section>

      {/* Section 2: Discrepancy Stream */}
      <section className="mt-14 border-t border-[#E7E5E0] pt-8">
        <div className="flex items-center justify-between pb-6">
          <div>
            <h2 className="font-serif text-2xl text-[#111111] font-normal tracking-tight">
              Detected Discrepancies ({conflicts.length})
            </h2>
            <p className="font-sans text-xs text-[#777777] mt-0.5">
              Deterministic cross-verification comparing demographic attributes
            </p>
          </div>
          {conflicts.length > 0 && (
            <span className="font-sans text-[11px] bg-[#FAF9F6] border border-[#E7E5E0] px-2.5 py-1 rounded-[2px] text-[#111111] font-medium">
              Action Required
            </span>
          )}
        </div>

        {conflicts.length > 0 ? (
          <div className="divide-y divide-[#E7E5E0]">
            {conflicts.map((conflict) => {
              const docAName = getDocName(conflict.doc_a_id);
              const docBName = getDocName(conflict.doc_b_id);
              const isGenerating = generatingDraftForConflict === conflict.id;

              return (
                <article key={conflict.id} className="py-6 space-y-4">
                  {/* Meta indicator & Classification Badges */}
                  <div className="flex items-center justify-between text-[11px] font-sans flex-wrap gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-[10px] uppercase tracking-wider px-2 py-0.5 rounded bg-zinc-100 border border-zinc-200 text-zinc-800 font-semibold">
                        {conflict.conflict_type.replace(/[-_]/g, " ")}
                      </span>
                      <span
                        className={
                          conflict.severity === "high" || conflict.severity === "critical"
                            ? "font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-[#FCE8E6] border border-[#FAD2CF] text-[#BA1A1A] font-semibold"
                            : "font-mono text-[10px] uppercase px-2 py-0.5 rounded bg-[#FAF9F6] border border-[#E7E5E0] text-[#111111] font-medium"
                        }
                      >
                        Severity: {conflict.severity}
                      </span>
                      {conflict.similarity_score !== undefined && conflict.similarity_score !== null && (
                        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-[#E6F4EA] border border-[#CEEAD6] text-[#0D652D] font-medium">
                          Match Score: {conflict.similarity_score}%
                        </span>
                      )}
                    </div>
                    {conflict.comparison_method && (
                      <span className="text-[#777777] text-[10px] font-mono">
                        Method: {conflict.comparison_method}
                      </span>
                    )}
                  </div>

                  {/* Field Name & Description */}
                  <div>
                    <h3 className="font-serif text-xl text-[#111111] font-normal capitalize">
                      {conflict.field_name.replace(/_/g, " ")} Discrepancy
                    </h3>
                    {conflict.description && (
                      <p className="font-sans text-xs text-[#5E5E5E] mt-1 leading-relaxed">
                        {conflict.description}
                      </p>
                    )}
                  </div>

                  {/* Two-Column Side-by-Side Comparison */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                    <div className="p-3.5 bg-white border border-[#E7E5E0] rounded-[4px] space-y-1">
                      <div className="font-sans text-[11px] text-[#777777] uppercase tracking-wide flex items-center justify-between">
                        <span>{docAName}</span>
                        <span className="font-mono text-[10px] text-[#999999]">Record A</span>
                      </div>
                      <div className="font-sans text-base text-[#111111] font-medium tracking-tight">
                        {conflict.value_a || "—"}
                      </div>
                    </div>
                    <div className="p-3.5 bg-white border border-[#E7E5E0] rounded-[4px] space-y-1">
                      <div className="font-sans text-[11px] text-[#777777] uppercase tracking-wide flex items-center justify-between">
                        <span>{docBName}</span>
                        <span className="font-mono text-[10px] text-[#999999]">Record B</span>
                      </div>
                      <div className="font-sans text-base text-[#111111] font-medium tracking-tight">
                        {conflict.value_b || "—"}
                      </div>
                    </div>
                  </div>

                  {/* OCR Warning if detected */}
                  {conflict.metadata?.ocr_warning && (
                    <div className="text-[11px] text-[#B06000] bg-[#FEF7E0] border border-[#FEEFC3] px-3 py-1.5 rounded-[4px] flex items-center gap-1.5 font-sans">
                      <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                      <span>{conflict.metadata.ocr_warning}</span>
                    </div>
                  )}

                  {/* Mandatory Statutory Disclaimer & Legal Correctness Notice */}
                  <div className="text-xs font-sans text-[#5E5E5E] bg-[#FAF9F6] border border-[#E7E5E0] p-3 rounded-[4px] space-y-1">
                    <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase font-bold text-[#111111]">
                      <AlertCircle className="w-3.5 h-3.5 text-[#777777] shrink-0" />
                      <span>AUTOMATED COMPARISON RESULT — NOT OFFICIAL GOVERNMENT VERIFICATION</span>
                    </div>
                    <p className="text-[11px] text-[#777777] leading-relaxed">
                      CONVELINA provides automated identity discrepancy detection and statutory guidance. CONVELINA does not declare which document is legally correct. Review statutory guidelines or consult official authorities.
                    </p>
                  </div>

                  {/* In-Place Context Preview Accordion (Phase P3C) */}
                  {expandedPreviewId === conflict.id && (
                    <div className="p-4 bg-[#FAF9F6] border border-[#E7E5E0] rounded-[4px] space-y-3 animate-in fade-in duration-150">
                      <div className="flex items-center justify-between border-b border-[#E7E5E0] pb-2">
                        <div className="flex items-center gap-2">
                          <Shield className="w-4 h-4 text-[#111111]" />
                          <span className="font-serif text-sm font-medium text-[#111111]">
                            Verified Statutory Resolution Preview
                          </span>
                        </div>
                        <button
                          type="button"
                          onClick={() => setExpandedPreviewId(null)}
                          className="text-xs text-[#777777] hover:text-[#111111]"
                        >
                          Close Preview
                        </button>
                      </div>

                      {loadingPreviewId === conflict.id ? (
                        <div className="py-4 text-center text-xs text-[#777777] flex items-center justify-center gap-2">
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Retrieving statutory precedents from knowledge base...</span>
                        </div>
                      ) : previewContexts[conflict.id] ? (
                        <div className="space-y-3 text-xs font-sans">
                          {previewContexts[conflict.id].recommended_action && (
                            <div className="p-2.5 bg-white border border-[#E7E5E0] rounded space-y-1">
                              <span className="text-[10px] font-semibold uppercase text-[#777777] block">
                                Recommended Action
                              </span>
                              <p className="text-[#111111] leading-relaxed">
                                {previewContexts[conflict.id].recommended_action}
                              </p>
                            </div>
                          )}

                          {previewContexts[conflict.id].resolution_mapping && (
                            <div className="p-2.5 bg-white border border-[#E7E5E0] rounded space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-[#111111]">
                                  {previewContexts[conflict.id].resolution_mapping?.procedure_name}
                                </span>
                                <span className="font-mono text-[10px] text-[#0D652D] bg-[#E6F4EA] px-2 py-0.5 rounded">
                                  {previewContexts[conflict.id].resolution_mapping?.procedure_type.replace(/_/g, " ")}
                                </span>
                              </div>
                              <div className="text-[11px] text-[#777777]">
                                Authority: <strong className="text-[#111111]">{previewContexts[conflict.id].resolution_mapping?.authority_name}</strong>
                              </div>
                              {previewContexts[conflict.id].resolution_mapping?.prescribed_forms && previewContexts[conflict.id].resolution_mapping!.prescribed_forms.length > 0 && (
                                <div className="pt-1.5 border-t border-[#E7E5E0] space-y-1">
                                  <span className="text-[10px] uppercase font-semibold text-[#777777] block">
                                    Official Prescribed Forms:
                                  </span>
                                  <div className="space-y-1">
                                    {previewContexts[conflict.id].resolution_mapping!.prescribed_forms.map((f) => (
                                      <a
                                        key={f.form_id}
                                        href={f.official_download_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[#0066CC] hover:underline flex items-center justify-between py-0.5"
                                      >
                                        <span>• {f.form_name}</span>
                                        <ExternalLink className="w-3 h-3 text-[#777777]" />
                                      </a>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )}

                          <div className="pt-1 flex items-center justify-between">
                            <span className="text-[11px] text-[#777777]">
                              Ready for comprehensive guidance?
                            </span>
                            <Link
                              href={`/app/assistant?conflictId=${conflict.id}`}
                              className="text-xs font-medium text-[#C96442] hover:underline inline-flex items-center gap-1"
                            >
                              <span>Open In CONVELINA AI Workspace</span>
                              <ArrowRight className="w-3 h-3" />
                            </Link>
                          </div>
                        </div>
                      ) : (
                        <div className="text-xs text-[#777777]">
                          Unable to load statutory preview. You can discuss this directly in the AI workspace.
                        </div>
                      )}
                    </div>
                  )}

                  {/* Actions: AI Assistant, Forms, Preview, and Draft Generation */}
                  <div className="pt-2 flex flex-wrap items-center gap-3">
                    {/* Discuss with CONVELINA AI button */}
                    <Link
                      href={`/app/assistant?conflictId=${conflict.id}`}
                      className="h-9 px-3.5 bg-[#FAF9F5] border border-[#C96442]/40 text-[#C96442] hover:bg-[#C96442]/10 rounded-[4px] text-xs font-sans font-medium transition-colors flex items-center gap-1.5 shadow-sm"
                      title="Launch conversational AI inquiry pre-linked to this discrepancy"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-[#C96442]" />
                      <span>Discuss with CONVELINA AI</span>
                    </Link>

                    {/* In-Place Context Preview toggle */}
                    <button
                      type="button"
                      onClick={() => handleTogglePreviewContext(conflict.id)}
                      className="h-9 px-3 bg-white border border-[#E7E5E0] text-[#111111] hover:bg-[#F4F3EF] rounded-[4px] text-xs font-sans font-medium transition-colors flex items-center gap-1.5"
                    >
                      {expandedPreviewId === conflict.id ? (
                        <>
                          <ChevronUp className="w-3.5 h-3.5 text-[#777777]" />
                          <span>Hide AI Preview</span>
                        </>
                      ) : (
                        <>
                          <ChevronDown className="w-3.5 h-3.5 text-[#777777]" />
                          <span>Quick AI Preview</span>
                        </>
                      )}
                    </button>

                    <button
                      onClick={() => handleOpenDraftingForConflict(conflict)}
                      className="h-9 px-3.5 bg-[#111111] text-white rounded-[4px] text-xs font-sans font-medium hover:bg-black/90 active:bg-black transition-colors flex items-center gap-1.5"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>Generate Correction Draft</span>
                    </button>

                    <Link
                      href="/app/forms"
                      className="h-9 px-3.5 bg-white border border-[#E7E5E0] text-[#111111] rounded-[4px] text-xs font-sans font-medium hover:bg-[#F4F3EF] transition-colors flex items-center gap-1.5"
                    >
                      <span>Applicable Forms</span>
                      <ArrowRight className="w-3.5 h-3.5 text-[#777777]" />
                    </Link>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="p-8 bg-white border border-[#E7E5E0] rounded-[4px] text-center space-y-2">
            <div className="w-8 h-8 rounded-full bg-[#FAF9F6] border border-[#E7E5E0] flex items-center justify-center text-[#777777] mx-auto mb-2">
              <CheckCircle2 className="w-4 h-4 text-[#111111]" />
            </div>
            <h4 className="font-sans text-sm font-medium text-[#111111]">
              {documents.length >= 2
                ? "No discrepancies detected"
                : "No comparisons executed"}
            </h4>
            <p className="font-sans text-xs text-[#777777] max-w-md mx-auto leading-relaxed">
              {documents.length >= 2
                ? "All evaluated attributes (name, date of birth, gender, and family credentials) match across your uploaded records."
                : "Upload at least two official credentials (e.g. Aadhaar and PAN) and click 'Detect Conflicts' to initiate deterministic reconciliation."}
            </p>
          </div>
        )}
      </section>

      {/* Section 3: Generated Correction Drafts (Module 7) */}
      <section className="mt-14 border-t border-[#E7E5E0] pt-8">
        <div className="flex items-center justify-between pb-6">
          <div>
            <h2 className="font-serif text-2xl text-[#111111] font-normal tracking-tight">
              Generated Correction Drafts & Petitions ({drafts.length})
            </h2>
            <p className="font-sans text-xs text-[#777777] mt-0.5">
              Legally structured representations, checklists, and sworn declarations ready for official submission
            </p>
          </div>
        </div>

        {drafts.length > 0 ? (
          <div className="space-y-4">
            {drafts.map((draft) => {
              const isPdfDownloading = downloadingDraftId === `${draft.id}-pdf`;
              const isDocxDownloading = downloadingDraftId === `${draft.id}-docx`;

              return (
                <div
                  key={draft.id}
                  className="p-5 bg-white border border-[#E7E5E0] rounded-[4px] space-y-3 hover:border-[#CCCCCC] transition-colors"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="font-serif text-lg text-[#111111] font-medium">
                          {draft.title}
                        </span>
                        <span className="font-sans text-[10px] bg-[#F4F3EF] text-[#5E5E5E] px-1.5 py-0.5 rounded-[2px]">
                          v{draft.version}
                        </span>
                        <span className="font-sans text-[10px] bg-[#FAF9F6] border border-[#E7E5E0] text-[#111111] px-1.5 py-0.5 rounded-[2px] uppercase">
                          {draft.status}
                        </span>
                      </div>
                      <div className="font-sans text-xs text-[#777777]">
                        Category: {draft.document_category} • Created:{" "}
                        {new Date(draft.created_at).toLocaleDateString()}
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        onClick={() => handleOpenDraftingForExistingDraft(draft)}
                        className="h-8 px-3 bg-white border border-[#E7E5E0] text-[#111111] rounded-[4px] text-xs font-sans font-medium hover:bg-[#F4F3EF] transition-colors flex items-center gap-1.5"
                      >
                        <Edit3 className="w-3.5 h-3.5 text-[#5E5E5E]" />
                        <span>View / Edit</span>
                      </button>

                      <button
                        onClick={() => handleDownload(draft, "pdf")}
                        disabled={isPdfDownloading}
                        className="h-8 px-3 bg-white border border-[#E7E5E0] text-[#111111] rounded-[4px] text-xs font-sans font-medium hover:bg-[#F4F3EF] disabled:opacity-50 transition-colors flex items-center gap-1.5"
                      >
                        {isPdfDownloading ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Download className="w-3.5 h-3.5 text-[#5E5E5E]" />
                        )}
                        <span>PDF</span>
                      </button>

                      <button
                        onClick={() => handleDownload(draft, "docx")}
                        disabled={isDocxDownloading}
                        className="h-8 px-3 bg-white border border-[#E7E5E0] text-[#111111] rounded-[4px] text-xs font-sans font-medium hover:bg-[#F4F3EF] disabled:opacity-50 transition-colors flex items-center gap-1.5"
                      >
                        {isDocxDownloading ? (
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <FileSpreadsheet className="w-3.5 h-3.5 text-[#5E5E5E]" />
                        )}
                        <span>DOCX</span>
                      </button>

                      <button
                        onClick={() => handleDeleteDraft(draft.id, draft.title)}
                        className="h-8 w-8 text-[#777777] hover:text-[#BA1A1A] transition-colors flex items-center justify-center rounded-[4px] border border-transparent hover:border-[#E7E5E0]"
                        aria-label="Delete draft"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Snippet preview */}
                  <div className="p-3 bg-[#FAF9F6] border border-[#E7E5E0] rounded-[2px] font-mono text-[11px] text-[#5E5E5E] max-h-24 overflow-hidden text-ellipsis leading-relaxed whitespace-pre-wrap">
                    {draft.content.slice(0, 300)}...
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-6 bg-white border border-[#E7E5E0] rounded-[4px] text-center space-y-1.5">
            <h4 className="font-sans text-sm font-medium text-[#111111]">
              No correction drafts generated yet
            </h4>
            <p className="font-sans text-xs text-[#777777] max-w-md mx-auto leading-relaxed">
              When a discrepancy is detected between your credentials, click &ldquo;Generate Correction Draft&rdquo; on any discrepancy card to produce a statutory petition.
            </p>
          </div>
        )}
      </section>

      {/* Modal: Review Extracted Demographic Fields (Stage 5) */}
      {reviewingDoc && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[6px] border border-[#E7E5E0] shadow-xl max-w-lg w-full p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-start justify-between border-b border-[#E7E5E0] pb-3">
              <div>
                <h3 className="font-serif text-xl text-[#111111] font-normal">
                  Review Extracted Demographic Fields
                </h3>
                <p className="font-sans text-xs text-[#777777] mt-0.5">
                  {DOC_TYPE_LABELS[reviewingDoc.document_type] || reviewingDoc.document_type} • Stage 5 Citizen Confirmation
                </p>
              </div>
              <button
                onClick={() => setReviewingDoc(null)}
                className="text-[#777777] hover:text-[#111111] p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {reviewingDoc.is_user_confirmed ? (
              <div className="p-3.5 bg-[#E6F4EA] border border-[#CEEAD6] rounded text-xs text-[#0D652D] space-y-1">
                <div className="flex items-center gap-1.5 font-semibold">
                  <CheckCircle2 className="w-4 h-4 shrink-0 text-[#0D652D]" />
                  <span>CITIZEN-CONFIRMED DEMOGRAPHIC DATA</span>
                </div>
                <p className="text-[11px] text-[#1E4620] leading-relaxed">
                  Citizen verified and confirmed these demographic attributes on {reviewingDoc.confirmed_at ? new Date(reviewingDoc.confirmed_at).toLocaleDateString() : "record"}. Confirmed values take legal precedence in deterministic identity comparisons. You may still edit and re-confirm if corrections are necessary.
                </p>
              </div>
            ) : (
              <div className="p-3.5 bg-[#FEF7E0] border border-[#FEEFC3] rounded text-xs text-[#B06000] space-y-1">
                <div className="flex items-center gap-1.5 font-semibold">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-[#B06000]" />
                  <span>TENTATIVE MACHINE EXTRACTION — CITIZEN CONFIRMATION REQUIRED</span>
                </div>
                <p className="text-[11px] text-[#8C5E28] leading-relaxed">
                  The values below were extracted automatically by OCR. They may contain scanning noise, font misinterpretations, or truncation. Review each field carefully, correct any errors, and click &quot;Confirm &amp; Verify Demographic Data&quot; to authorize these values for deterministic cross-comparison.
                </p>
              </div>
            )}

            <div className="space-y-3.5">
              {Object.keys(editedFields).length > 0 ? (
                Object.entries(editedFields).map(([key, val]) => {
                  const extraction = reviewingDoc.field_extractions?.[key];
                  const conf = extraction?.confidence !== undefined ? extraction.confidence : 1.0;
                  const isLowConf = conf < 0.60;
                  const isFormatWarning = extraction?.validation_status === "invalid_format";

                  return (
                    <div key={key} className="space-y-1.5 p-3 rounded border border-[#E7E5E0] bg-[#FAF9F6]">
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <label className="font-sans text-xs font-semibold text-[#111111] capitalize">
                          {key.replace(/_/g, " ")}
                        </label>
                        <div className="flex items-center gap-1.5 flex-wrap">
                          {isLowConf && (
                            <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-[#FEF7E0] border border-[#FEEFC3] text-[#B06000]">
                              <AlertTriangle className="w-3 h-3 text-[#B06000]" />
                              Low OCR Confidence ({Math.round(conf * 100)}%) — Manual Review Required
                            </span>
                          )}
                          {!isLowConf && extraction && (
                            <span className="text-[10px] font-mono text-[#0D652D] bg-[#E6F4EA] px-1.5 py-0.5 rounded border border-[#CEEAD6]">
                              {Math.round(conf * 100)}% OCR
                            </span>
                          )}
                          {isFormatWarning && (
                            <span className="text-[10px] font-medium text-[#C5221F] bg-[#FCE8E6] px-1.5 py-0.5 rounded border border-[#FAD2CF]">
                              Format Discrepancy
                            </span>
                          )}
                        </div>
                      </div>
                      <input
                        type="text"
                        value={typeof val === "string" ? val : JSON.stringify(val)}
                        onChange={(e) =>
                          setEditedFields((prev) => ({ ...prev, [key]: e.target.value }))
                        }
                        className="w-full h-9 px-3 bg-white text-[#111111] font-sans text-sm border border-[#E7E5E0] rounded-[4px] focus:border-[#111111] focus:outline-none"
                      />
                      {extraction?.raw_value && extraction.raw_value !== val && (
                        <div className="text-[10px] text-[#777777] font-mono">
                          Raw OCR: {extraction.raw_value}
                        </div>
                      )}
                    </div>
                  );
                })
              ) : (
                <div className="space-y-3">
                  <div className="space-y-1">
                    <label className="font-sans text-xs font-medium text-[#111111]">
                      Full Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. SAKUNTHALA RANGARAJAN"
                      value={editedFields["full_name"] || ""}
                      onChange={(e) =>
                        setEditedFields((prev) => ({ ...prev, full_name: e.target.value }))
                      }
                      className="w-full h-9 px-3 bg-white text-[#111111] font-sans text-sm border border-[#E7E5E0] rounded-[4px] focus:border-[#111111] focus:outline-none"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-sans text-xs font-medium text-[#111111]">
                      Date of Birth (YYYY-MM-DD)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. 1985-05-15"
                      value={editedFields["date_of_birth"] || ""}
                      onChange={(e) =>
                        setEditedFields((prev) => ({ ...prev, date_of_birth: e.target.value }))
                      }
                      className="w-full h-9 px-3 bg-white text-[#111111] font-sans text-sm border border-[#E7E5E0] rounded-[4px] focus:border-[#111111] focus:outline-none"
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-[#E7E5E0] flex items-center justify-end gap-2.5 flex-wrap">
              <button
                type="button"
                onClick={() => setReviewingDoc(null)}
                className="h-9 px-4 bg-white border border-[#E7E5E0] text-[#111111] rounded-[4px] text-xs font-sans font-medium hover:bg-[#F4F3EF]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveFields}
                disabled={savingFields || confirmingFields}
                className="h-9 px-4 bg-white border border-[#111111] text-[#111111] rounded-[4px] text-xs font-sans font-medium hover:bg-[#FAF9F6] disabled:opacity-50 flex items-center gap-1.5"
              >
                {savingFields ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Save Edits</span>
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={handleConfirmFields}
                disabled={confirmingFields || savingFields}
                className="h-9 px-4 bg-[#0D652D] text-white rounded-[4px] text-xs font-sans font-medium hover:bg-[#0B5324] active:bg-[#083E1B] disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
              >
                {confirmingFields ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Confirming...</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Confirm & Verify Demographic Data</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: View & Edit Correction Draft (Module 7) */}
      {editingDraft && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[6px] border border-[#E7E5E0] shadow-xl max-w-2xl w-full p-6 space-y-4 max-h-[90vh] flex flex-col">
            <div className="flex items-start justify-between border-b border-[#E7E5E0] pb-3 shrink-0">
              <div>
                <h3 className="font-serif text-xl text-[#111111] font-normal">
                  Review & Edit Legal Correction Draft
                </h3>
                <p className="font-sans text-xs text-[#777777] mt-0.5">
                  Version {editingDraft.version} • {editingDraft.document_category}
                </p>
              </div>
              <button
                onClick={() => setEditingDraft(null)}
                className="text-[#777777] hover:text-[#111111] p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3 shrink-0">
              <div className="space-y-1">
                <label className="font-sans text-xs font-medium text-[#111111]">
                  Petition Title
                </label>
                <input
                  type="text"
                  value={draftTitle}
                  onChange={(e) => setDraftTitle(e.target.value)}
                  className="w-full h-9 px-3 bg-white text-[#111111] font-sans text-sm border border-[#E7E5E0] rounded-[4px] focus:border-[#111111] focus:outline-none"
                />
              </div>
            </div>

            <div className="flex-1 min-h-[260px] flex flex-col space-y-1">
              <label className="font-sans text-xs font-medium text-[#111111]">
                Petition Content (Official Format)
              </label>
              <textarea
                value={draftContent}
                onChange={(e) => setDraftContent(e.target.value)}
                className="flex-1 w-full p-3 bg-white text-[#111111] font-mono text-xs border border-[#E7E5E0] rounded-[4px] focus:border-[#111111] focus:outline-none resize-none leading-relaxed"
                placeholder="Draft petition content..."
              />
            </div>

            <p className="font-sans text-[11px] text-[#777777] shrink-0">
              Note: Saving changes will increment the draft version and record a manual modification entry in the audit history.
            </p>

            <div className="pt-3 border-t border-[#E7E5E0] flex items-center justify-end gap-2.5 shrink-0">
              <button
                type="button"
                onClick={() => setEditingDraft(null)}
                className="h-9 px-4 bg-white border border-[#E7E5E0] text-[#111111] rounded-[4px] text-xs font-sans font-medium hover:bg-[#F4F3EF]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveDraft}
                disabled={savingDraft}
                className="h-9 px-4 bg-[#111111] text-white rounded-[4px] text-xs font-sans font-medium hover:bg-black/90 active:bg-black disabled:opacity-50 flex items-center gap-1.5"
              >
                {savingDraft ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Save className="w-3.5 h-3.5" />
                    <span>Save Changes (v{editingDraft.version + 1})</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Comprehensive Administrative Drafting Modal (Phase P3G) */}
      <AdministrativeDraftingModal
        isOpen={draftingModalOpen}
        onClose={() => setDraftingModalOpen(false)}
        token={idToken}
        initialConflict={draftingConflict}
        initialDraft={draftingSelectedDraft}
        documents={documents}
        onDraftSaved={handleDraftSaved}
      />
    </div>
  );
}

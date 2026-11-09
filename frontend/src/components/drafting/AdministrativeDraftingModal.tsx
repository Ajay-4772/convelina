"use client";

import React, { useState, useEffect, useMemo } from "react";
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  Shield,
  ExternalLink,
  Download,
  Edit3,
  Save,
  RefreshCw,
  X,
  ChevronRight,
  ChevronLeft,
  Lock,
  Scale,
  Sparkles,
  Clock,
  Check,
  Languages,
  RotateCcw,
  BookOpen,
} from "lucide-react";
import {
  CorrectionDraftItem,
  ConflictItem,
  DocumentItem,
  DRAFT_COMPATIBILITY_MATRIX,
  DRAFT_TYPE_LABELS,
  createCorrectionDraft,
  updateCorrectionDraft,
  confirmCorrectionDraft,
  regenerateCorrectionDraft,
  translateCorrectionDraft,
  downloadCorrectionDraft,
  confirmDocumentFields,
} from "../../lib/api";

interface AdministrativeDraftingModalProps {
  isOpen: boolean;
  onClose: () => void;
  token: string | null;
  initialConflict?: ConflictItem | null;
  initialDraft?: CorrectionDraftItem | null;
  documents?: DocumentItem[];
  onDraftSaved?: (draft: CorrectionDraftItem) => void;
}

type WizardStep = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;

export default function AdministrativeDraftingModal({
  isOpen,
  onClose,
  token,
  initialConflict,
  initialDraft,
  documents = [],
  onDraftSaved,
}: AdministrativeDraftingModalProps) {
  // Wizard active step
  const [currentStep, setCurrentStep] = useState<WizardStep>(initialDraft ? 6 : 1);

  // Selected conflict
  const [conflict, setConflict] = useState<ConflictItem | null>(initialConflict || null);

  // Step 2: Confirmed identity fields
  const [applicantName, setApplicantName] = useState("");
  const [requestedValue, setRequestedValue] = useState("");
  const [confirmedDateOfBirth, setConfirmedDateOfBirth] = useState("");
  const [confirmedParentName, setConfirmedParentName] = useState("");
  const [confirmedAddress, setConfirmedAddress] = useState("");
  const [isPersistingConfirmation, setIsPersistingConfirmation] = useState(false);
  const [confirmationSavedMessage, setConfirmationSavedMessage] = useState<string | null>(null);

  // Step 3: Selected draft type
  const [selectedDraftType, setSelectedDraftType] = useState<string>("identity_correction_request");

  // Step 4: Citizen explanation & requested action
  const [userExplanation, setUserExplanation] = useState("");
  const [requestedAction, setRequestedAction] = useState("");
  const [language, setLanguage] = useState("en");

  // Step 5: Active Draft State & Generation
  const [draft, setDraft] = useState<CorrectionDraftItem | null>(initialDraft || null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [generationStage, setGenerationStage] = useState("");

  // Step 6: Sectioned editing
  const [isEditingSection, setIsEditingSection] = useState(false);
  const [editRecipient, setEditRecipient] = useState("");
  const [editSubject, setEditSubject] = useState("");
  const [editContent, setEditContent] = useState("");
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  // Step 8: Confirmation
  const [confirmationStatement, setConfirmationStatement] = useState("");
  const [isConfirming, setIsConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  // Step 9: Export
  const [isDownloadingPdf, setIsDownloadingPdf] = useState(false);
  const [isDownloadingDocx, setIsDownloadingDocx] = useState(false);
  const [isTranslating, setIsTranslating] = useState(false);

  // General error/success banner
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Detect document category from conflict
  const documentCategory = useMemo(() => {
    if (draft?.document_category) return draft.document_category;
    if (!conflict) return "pan";
    // Check if conflict matches any known documents
    const docA = documents.find((d) => d.id === conflict.doc_a_id);
    const docB = documents.find((d) => d.id === conflict.doc_b_id);
    if (docA?.document_type && docA.document_type !== "aadhaar") return docA.document_type;
    if (docB?.document_type && docB.document_type !== "aadhaar") return docB.document_type;
    return docA?.document_type || "pan";
  }, [conflict, documents, draft]);

  // Applicable draft types
  const applicableDraftTypes = useMemo(() => {
    const types = DRAFT_COMPATIBILITY_MATRIX[documentCategory] || DRAFT_COMPATIBILITY_MATRIX["pan"];
    return types;
  }, [documentCategory]);

  // Initialize state when initialConflict or initialDraft changes
  useEffect(() => {
    if (initialDraft) {
      setDraft(initialDraft);
      setCurrentStep(6);
      setEditRecipient(initialDraft.recipient_authority || "");
      setEditSubject(initialDraft.subject || "");
      setEditContent(initialDraft.content);
      setSelectedDraftType(initialDraft.document_type);
      setUserExplanation(initialDraft.user_explanation || "");
      setRequestedAction(initialDraft.requested_action || "");
    } else if (initialConflict) {
      setConflict(initialConflict);
      setCurrentStep(1);
      setDraft(null);

      // Pre-fill values from linked documents if available
      const docA = documents.find((d) => d.id === initialConflict.doc_a_id);
      const docB = documents.find((d) => d.id === initialConflict.doc_b_id);

      const confirmedPool = {
        ...(docA?.confirmed_fields || {}),
        ...(docB?.confirmed_fields || {}),
      };

      const nameVal =
        confirmedPool.applicant_name ||
        confirmedPool.name ||
        docA?.extracted_fields?.name ||
        docB?.extracted_fields?.name ||
        initialConflict.value_a;

      setApplicantName(nameVal || "");
      setRequestedValue(initialConflict.value_a || initialConflict.value_b || "");
      setConfirmedDateOfBirth(confirmedPool.date_of_birth || "");
      setConfirmedParentName(confirmedPool.father_name || confirmedPool.parent_name || "");
      setConfirmedAddress(confirmedPool.address || "");
    }
  }, [initialConflict, initialDraft, documents]);

  // Reset selected draft type if category changes and type is not applicable
  useEffect(() => {
    if (!applicableDraftTypes.includes(selectedDraftType)) {
      setSelectedDraftType(applicableDraftTypes[0] || "identity_correction_request");
    }
  }, [applicableDraftTypes, selectedDraftType]);

  if (!isOpen) return null;

  // Mask sensitive identifiers for display
  const maskAadhaar = (val: string) => {
    const clean = val.replace(/\D/g, "");
    if (clean.length >= 4) {
      return `XXXX-XXXX-${clean.slice(-4)}`;
    }
    return val;
  };

  const maskPan = (val: string) => {
    const clean = val.trim().toUpperCase();
    if (clean.length === 10) {
      return `XXXXX${clean.slice(5, 9)}${clean.slice(9)}`;
    }
    return val;
  };

  // Step 2: Handle Explicit Demographic Confirmation Persistence
  const handlePersistDemographicConfirmation = async () => {
    if (!token || !conflict) return;
    setIsPersistingConfirmation(true);
    setErrorMessage(null);

    try {
      const confirmedFieldsToSave: Record<string, any> = {
        applicant_name: applicantName.trim(),
        requested_value: requestedValue.trim(),
      };
      if (confirmedDateOfBirth) confirmedFieldsToSave.date_of_birth = confirmedDateOfBirth.trim();
      if (confirmedParentName) confirmedFieldsToSave.father_name = confirmedParentName.trim();
      if (confirmedAddress) confirmedFieldsToSave.address = confirmedAddress.trim();

      // Persist to document A if exists
      if (conflict.doc_a_id) {
        await confirmDocumentFields(token, conflict.doc_a_id, confirmedFieldsToSave);
      }

      setConfirmationSavedMessage("Citizen identity confirmation successfully authenticated and persisted.");
      setTimeout(() => setConfirmationSavedMessage(null), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to persist identity confirmation.");
    } finally {
      setIsPersistingConfirmation(false);
    }
  };

  // Step 5: Handle Draft Generation
  const handleGenerateDraft = async () => {
    if (!token || !conflict) return;
    setIsGenerating(true);
    setErrorMessage(null);
    setCurrentStep(5);
    setGenerationProgress(15);
    setGenerationStage("Retrieving citizen-confirmed identity particulars under PostgreSQL RLS...");

    try {
      setTimeout(() => {
        setGenerationProgress(45);
        setGenerationStage("Querying verified procedural guidance & statutory forms from official RAG corpus...");
      }, 500);

      setTimeout(() => {
        setGenerationProgress(75);
        setGenerationStage("Synthesizing administrative representation with mandatory disclaimers...");
      }, 1000);

      const confirmedPayload: Record<string, any> = {
        applicant_name: applicantName.trim(),
        requested_value: requestedValue.trim(),
      };
      if (confirmedDateOfBirth) confirmedPayload.date_of_birth = confirmedDateOfBirth.trim();
      if (confirmedParentName) confirmedPayload.father_name = confirmedParentName.trim();
      if (confirmedAddress) confirmedPayload.address = confirmedAddress.trim();

      const newDraft = await createCorrectionDraft(token, {
        conflict_id: conflict.id,
        document_type: selectedDraftType,
        document_category: documentCategory,
        confirmed_fields: confirmedPayload,
        user_explanation: userExplanation.trim() || undefined,
        requested_action: requestedAction.trim() || undefined,
        language,
      });

      setGenerationProgress(100);
      setGenerationStage("Draft generated successfully!");
      setDraft(newDraft);
      setEditRecipient(newDraft.recipient_authority || "");
      setEditSubject(newDraft.subject || "");
      setEditContent(newDraft.content);

      if (onDraftSaved) onDraftSaved(newDraft);

      setTimeout(() => {
        setIsGenerating(false);
        setCurrentStep(6);
      }, 600);
    } catch (err: any) {
      setIsGenerating(false);
      setErrorMessage(err.message || "Draft generation failed.");
      setCurrentStep(4);
    }
  };

  // Step 6: Save Manual Edits
  const handleSaveManualEdit = async () => {
    if (!token || !draft) return;
    setIsSavingEdit(true);
    setErrorMessage(null);

    try {
      const updated = await updateCorrectionDraft(token, draft.id, {
        content: editContent,
        recipient_authority: editRecipient,
        subject: editSubject,
        user_explanation: userExplanation,
        requested_action: requestedAction,
      });

      setDraft(updated);
      setIsEditingSection(false);
      if (onDraftSaved) onDraftSaved(updated);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to save draft edits.");
    } finally {
      setIsSavingEdit(false);
    }
  };

  // Step 6: Re-generate with updated instructions
  const handleRegenerate = async (tone: string = "formal") => {
    if (!token || !draft) return;
    setIsGenerating(true);
    setErrorMessage(null);

    try {
      const regenerated = await regenerateCorrectionDraft(token, draft.id, {
        user_explanation: userExplanation,
        requested_action: requestedAction,
        tone,
      });

      setDraft(regenerated);
      setEditContent(regenerated.content);
      setEditRecipient(regenerated.recipient_authority || "");
      setEditSubject(regenerated.subject || "");
      if (onDraftSaved) onDraftSaved(regenerated);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to regenerate draft.");
    } finally {
      setIsGenerating(false);
    }
  };

  // Step 8: Confirm Draft Version
  const handleConfirmDraft = async () => {
    if (!token || !draft) return;
    if (!confirmationStatement.trim()) {
      setConfirmError("Please enter your acknowledgement statement to confirm.");
      return;
    }

    setIsConfirming(true);
    setConfirmError(null);

    try {
      const confirmed = await confirmCorrectionDraft(token, draft.id, {
        confirmation_statement: confirmationStatement.trim(),
        version_number: draft.version,
        expected_sha256_hash: draft.sha256_hash || undefined,
      });

      setDraft(confirmed);
      if (onDraftSaved) onDraftSaved(confirmed);
      setCurrentStep(9);
    } catch (err: any) {
      setConfirmError(err.message || "Confirmation failed.");
    } finally {
      setIsConfirming(false);
    }
  };

  // Step 9: Translation
  const handleTranslate = async (targetLang: string, bilingual: boolean = false) => {
    if (!token || !draft) return;
    setIsTranslating(true);
    setErrorMessage(null);

    try {
      const translated = await translateCorrectionDraft(token, draft.id, {
        target_language: targetLang,
        bilingual: bilingual,
      });

      setDraft(translated);
      setEditContent(translated.content);
      if (onDraftSaved) onDraftSaved(translated);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to translate draft.");
    } finally {
      setIsTranslating(false);
    }
  };

  // Step 9: Download PDF / DOCX
  const handleDownload = async (format: "pdf" | "docx") => {
    if (!draft) return;
    if (format === "pdf") setIsDownloadingPdf(true);
    else setIsDownloadingDocx(true);

    try {
      const blob = await downloadCorrectionDraft(token, draft.id, format);
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = blobUrl;
      const safeTitle = (draft.title || "administrative_draft").replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 40);
      a.download = `${safeTitle}_v${draft.version}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(blobUrl);
      document.body.removeChild(a);
    } catch (err: any) {
      setErrorMessage(err.message || `Failed to download ${format.toUpperCase()}.`);
    } finally {
      if (format === "pdf") setIsDownloadingPdf(false);
      else setIsDownloadingDocx(false);
    }
  };

  // Status Badge Component
  const renderStatusBadge = () => {
    if (!draft) return null;
    if (draft.status === "citizen_confirmed" && draft.is_citizen_confirmed) {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#E6F4EA] text-[#0D652D] border border-[#CEEAD6]">
          <CheckCircle2 className="w-3.5 h-3.5" />
          CITIZEN-CONFIRMED FINAL DRAFT (v{draft.version})
        </span>
      );
    }
    if (draft.status === "citizen_edited") {
      return (
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#FEF7E0] text-[#B06000] border border-[#FEEFC3]">
          <Edit3 className="w-3.5 h-3.5" />
          CITIZEN-EDITED DRAFT (v{draft.version})
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#E8F0FE] text-[#1A73E8] border border-[#D2E3FC]">
        <Sparkles className="w-3.5 h-3.5" />
        AI-GENERATED DRAFT (v{draft.version})
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div
        data-testid="administrative-drafting-modal"
        className="bg-[#FAF9F5] border border-[#E5E3DC] rounded-2xl w-full max-w-4xl shadow-2xl flex flex-col max-h-[92vh] overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#E5E3DC] bg-[#FAF9F5]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-[#C96442]/10 border border-[#C96442]/30 flex items-center justify-center text-[#C96442]">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-serif font-medium text-[#1F1E1D]">
                Administrative Document Drafting
              </h2>
              <p className="text-xs text-[#6B6966]">
                Personalized petitions, representations, and statutory correction requests
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {renderStatusBadge()}
            <button
              onClick={onClose}
              className="p-1.5 text-[#6B6966] hover:text-[#1F1E1D] hover:bg-[#EFECE6] rounded-lg transition-colors"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Wizard Steps Stepper */}
        <div className="px-6 py-2.5 bg-[#F4F1EA] border-b border-[#E5E3DC] overflow-x-auto flex items-center gap-2 text-xs">
          {[
            { num: 1, label: "Discrepancy" },
            { num: 2, label: "Identity Confirmation" },
            { num: 3, label: "Draft Type" },
            { num: 4, label: "Explanation" },
            { num: 5, label: "Generate" },
            { num: 6, label: "Editable Preview" },
            { num: 7, label: "Official Sources" },
            { num: 8, label: "Confirm Version" },
            { num: 9, label: "Export" },
          ].map((s) => {
            const isActive = currentStep === s.num;
            const isCompleted = currentStep > s.num;
            return (
              <button
                key={s.num}
                onClick={() => {
                  // Only allow jumping back, or jumping to step 6+ if draft exists
                  if (s.num <= currentStep || (draft && s.num >= 6)) {
                    setCurrentStep(s.num as WizardStep);
                  }
                }}
                disabled={s.num > currentStep && !draft}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full whitespace-nowrap transition-colors ${
                  isActive
                    ? "bg-[#C96442] text-white font-medium shadow-sm"
                    : isCompleted
                    ? "bg-[#E6F4EA] text-[#0D652D] hover:bg-[#CEEAD6]"
                    : "text-[#8E8B85] hover:text-[#1F1E1D]"
                }`}
              >
                <span
                  className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                    isActive
                      ? "bg-white text-[#C96442] font-bold"
                      : isCompleted
                      ? "bg-[#0D652D] text-white"
                      : "bg-[#E5E3DC] text-[#8E8B85]"
                  }`}
                >
                  {isCompleted ? "✓" : s.num}
                </span>
                <span>{s.label}</span>
              </button>
            );
          })}
        </div>

        {/* Global Error Banner */}
        {errorMessage && (
          <div className="mx-6 mt-4 p-3 rounded-xl bg-[#FCE8E6] border border-[#FAD2CF] text-[#C5221F] text-xs flex items-start gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <div className="flex-1">{errorMessage}</div>
            <button onClick={() => setErrorMessage(null)} className="text-[#C5221F] hover:opacity-75">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Body content based on step */}
        <div className="flex-1 p-6 overflow-y-auto space-y-6">
          {/* STEP 1: Select Discrepancy */}
          {currentStep === 1 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-[#1F1E1D]">
                  Step 1: Identified Discrepancy Overview
                </h3>
                <p className="text-xs text-[#6B6966]">
                  Review the demographic inconsistency detected between your uploaded credentials.
                </p>
              </div>

              {conflict ? (
                <div className="p-4 rounded-xl border border-[#E5E3DC] bg-white space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#1F1E1D] uppercase">
                      Target Field: {conflict.field_name.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-medium bg-[#FCE8E6] text-[#C5221F] border border-[#FAD2CF]">
                      {conflict.conflict_type.toUpperCase()}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    <div className="p-3 rounded-lg bg-[#FAF9F5] border border-[#E5E3DC]">
                      <div className="text-[11px] text-[#6B6966] mb-1">Primary Document Value:</div>
                      <div className="font-mono font-medium text-[#1F1E1D]">
                        {conflict.field_name.includes("aadhaar")
                          ? maskAadhaar(conflict.value_a)
                          : conflict.field_name.includes("pan")
                          ? maskPan(conflict.value_a)
                          : conflict.value_a}
                      </div>
                    </div>
                    <div className="p-3 rounded-lg bg-[#FAF9F5] border border-[#E5E3DC]">
                      <div className="text-[11px] text-[#6B6966] mb-1">Conflicting Document Value:</div>
                      <div className="font-mono font-medium text-[#1F1E1D]">
                        {conflict.field_name.includes("aadhaar")
                          ? maskAadhaar(conflict.value_b)
                          : conflict.field_name.includes("pan")
                          ? maskPan(conflict.value_b)
                          : conflict.value_b}
                      </div>
                    </div>
                  </div>

                  <div className="text-xs text-[#6B6966] border-t border-[#F0EEE6] pt-2">
                    <span className="font-medium text-[#1F1E1D]">Statutory Category:</span>{" "}
                    <span className="capitalize">{documentCategory.replace(/_/g, " ")}</span> •{" "}
                    <span className="font-medium text-[#1F1E1D]">Description:</span> {conflict.description}
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-[#6B6966] bg-white border border-[#E5E3DC] rounded-xl">
                  No discrepancy selected. Please select a discrepancy from the Inconsistencies dashboard.
                </div>
              )}
            </div>
          )}

          {/* STEP 2: Review Identity Information (Safety Gate) */}
          {currentStep === 2 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-[#1F1E1D]">
                  Step 2: Review & Confirm Identity Information
                </h3>
                <p className="text-xs text-[#6B6966]">
                  <strong>Mandatory Invariant:</strong> NO UNCONFIRMED IDENTITY FIELD MAY BE TREATED AS A VERIFIED FACT IN A PERSONALIZED DRAFT.
                  Review and confirm each required field below.
                </p>
              </div>

              {confirmationSavedMessage && (
                <div className="p-3 rounded-xl bg-[#E6F4EA] border border-[#CEEAD6] text-[#0D652D] text-xs flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  <span>{confirmationSavedMessage}</span>
                </div>
              )}

              <div className="space-y-3 bg-white p-4 rounded-xl border border-[#E5E3DC]">
                <div>
                  <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                    Applicant Full Name <span className="text-[#C5221F]">*</span>
                  </label>
                  <input
                    type="text"
                    value={applicantName}
                    onChange={(e) => setApplicantName(e.target.value)}
                    placeholder="e.g. PRIYA SHARMA"
                    className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                  />
                  <div className="flex items-center gap-2 mt-1 text-[11px] text-[#6B6966]">
                    <span className="font-medium">Status:</span>
                    {applicantName.trim() ? (
                      <span className="text-[#0D652D] flex items-center gap-1">
                        <Check className="w-3 h-3" /> Confirmed
                      </span>
                    ) : (
                      <span className="text-[#C5221F] flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> Missing Information (Required)
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                    Target Correct Value for Discrepancy <span className="text-[#C5221F]">*</span>
                  </label>
                  <input
                    type="text"
                    value={requestedValue}
                    onChange={(e) => setRequestedValue(e.target.value)}
                    placeholder="e.g. Correct name or date of birth"
                    className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                  />
                  <div className="flex items-center gap-2 mt-1 text-[11px] text-[#6B6966]">
                    <span className="font-medium">Status:</span>
                    {requestedValue.trim() ? (
                      <span className="text-[#0D652D] flex items-center gap-1">
                        <Check className="w-3 h-3" /> Confirmed
                      </span>
                    ) : (
                      <span className="text-[#C5221F] flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" /> Needs Correction
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-[#F0EEE6]">
                  <div>
                    <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                      Date of Birth (Optional)
                    </label>
                    <input
                      type="text"
                      value={confirmedDateOfBirth}
                      onChange={(e) => setConfirmedDateOfBirth(e.target.value)}
                      placeholder="DD/MM/YYYY"
                      className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                      Parent / Father&apos;s Name (Optional)
                    </label>
                    <input
                      type="text"
                      value={confirmedParentName}
                      onChange={(e) => setConfirmedParentName(e.target.value)}
                      placeholder="Parent full name"
                      className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                    Current Postal Address (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={confirmedAddress}
                    onChange={(e) => setConfirmedAddress(e.target.value)}
                    placeholder="Current address for communication"
                    className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                  />
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={handlePersistDemographicConfirmation}
                    disabled={isPersistingConfirmation || !applicantName.trim() || !requestedValue.trim()}
                    className="px-4 py-2 text-xs font-medium bg-[#1F1E1D] text-white hover:bg-[#33312E] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {isPersistingConfirmation ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    )}
                    <span>Persist Citizen Confirmation to Database</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: Select Administrative Draft Type */}
          {currentStep === 3 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-[#1F1E1D]">
                  Step 3: Select Administrative Draft Type
                </h3>
                <p className="text-xs text-[#6B6966]">
                  Only draft types verified as compatible with your document category (
                  <span className="font-semibold capitalize">{documentCategory.replace(/_/g, " ")}</span>) are displayed.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {applicableDraftTypes.map((typeKey) => {
                  const isSelected = selectedDraftType === typeKey;
                  const label = DRAFT_TYPE_LABELS[typeKey] || typeKey.replace(/_/g, " ");
                  return (
                    <div
                      key={typeKey}
                      onClick={() => setSelectedDraftType(typeKey)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                        isSelected
                          ? "border-[#C96442] bg-[#FAF5F2] ring-1 ring-[#C96442]"
                          : "border-[#E5E3DC] bg-white hover:border-[#D5D2C8]"
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <span className="text-xs font-medium text-[#1F1E1D]">{label}</span>
                        <div
                          className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                            isSelected
                              ? "border-[#C96442] bg-[#C96442] text-white"
                              : "border-[#D5D2C8] bg-transparent"
                          }`}
                        >
                          {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                        </div>
                      </div>
                      <div className="text-[11px] text-[#6B6966] mt-1 font-mono">
                        category: {documentCategory}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* STEP 4: Provide Explanation */}
          {currentStep === 4 && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-[#1F1E1D]">
                  Step 4: Citizen Explanation & Requested Relief
                </h3>
                <p className="text-xs text-[#6B6966]">
                  Describe the circumstances of the discrepancy in your own words.
                  Instructions will be strictly sanitized to prevent adversarial prompt injection.
                </p>
              </div>

              <div className="space-y-3 bg-white p-4 rounded-xl border border-[#E5E3DC]">
                <div>
                  <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                    Circumstances / Factual Reason for Discrepancy
                  </label>
                  <textarea
                    rows={3}
                    value={userExplanation}
                    onChange={(e) => setUserExplanation(e.target.value)}
                    placeholder="e.g. My surname was mistakenly truncated during digital enrollment, while my educational mark sheets reflect my full expanded name."
                    className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                    Specific Rectification Requested
                  </label>
                  <textarea
                    rows={2}
                    value={requestedAction}
                    onChange={(e) => setRequestedAction(e.target.value)}
                    placeholder="e.g. Issue a rectified certificate matching my official identity particulars."
                    className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                    Draft Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="px-3 py-1.5 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                  >
                    <option value="en">English (Official Standard)</option>
                    <option value="ta">Tamil (தமிழ்)</option>
                    <option value="hi">Hindi (हिंदी)</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* STEP 5: Generation Progress */}
          {currentStep === 5 && (
            <div className="p-8 text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-[#C96442]/10 border border-[#C96442]/30 flex items-center justify-center text-[#C96442] mx-auto animate-pulse">
                <Sparkles className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#1F1E1D]">
                  Generating Administrative Draft
                </h3>
                <p className="text-xs text-[#6B6966] mt-1">{generationStage}</p>
              </div>

              <div className="w-full max-w-md mx-auto bg-[#E5E3DC] rounded-full h-2 overflow-hidden">
                <div
                  className="bg-[#C96442] h-full transition-all duration-300 rounded-full"
                  style={{ width: `${generationProgress}%` }}
                />
              </div>

              <div className="text-[11px] text-[#6B6966] max-w-sm mx-auto">
                Grounding with confirmed identity facts, authentic procedural rules, and statutory disclaimers.
              </div>
            </div>
          )}

          {/* STEP 6: Editable Preview */}
          {currentStep === 6 && draft && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-[#1F1E1D]">
                    Step 6: Editable Administrative Draft Preview
                  </h3>
                  <p className="text-xs text-[#6B6966]">
                    Version {draft.version} • {draft.document_type.replace(/_/g, " ").toUpperCase()}
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setIsEditingSection(!isEditingSection)}
                    className="px-3 py-1.5 text-xs font-medium bg-white border border-[#D5D2C8] text-[#1F1E1D] hover:bg-[#FAF9F5] rounded-lg transition-colors flex items-center gap-1.5"
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>{isEditingSection ? "Cancel Edit" : "Edit Section"}</span>
                  </button>

                  <button
                    onClick={() => handleRegenerate("formal")}
                    disabled={isGenerating}
                    className="px-3 py-1.5 text-xs font-medium bg-white border border-[#D5D2C8] text-[#1F1E1D] hover:bg-[#FAF9F5] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Regenerate</span>
                  </button>
                </div>
              </div>

              {/* Invalidation Alert if Edited */}
              {draft.status === "citizen_edited" && (
                <div className="p-3 rounded-xl bg-[#FEF7E0] border border-[#FEEFC3] text-[#B06000] text-xs flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    This draft has been edited by the citizen. Any prior version confirmation has been invalidated.
                    You must review the final content and explicitly confirm this exact version before export.
                  </div>
                </div>
              )}

              {/* Editing Mode */}
              {isEditingSection ? (
                <div className="space-y-3 bg-white p-4 rounded-xl border border-[#E5E3DC]">
                  <div>
                    <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                      Recipient Authority
                    </label>
                    <input
                      type="text"
                      value={editRecipient}
                      onChange={(e) => setEditRecipient(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-[#1F1E1D] mb-1">Subject</label>
                    <input
                      type="text"
                      value={editSubject}
                      onChange={(e) => setEditSubject(e.target.value)}
                      className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                      Document Body (Preserve Confirmed Facts)
                    </label>
                    <textarea
                      rows={12}
                      value={editContent}
                      onChange={(e) => setEditContent(e.target.value)}
                      className="w-full font-mono text-xs px-3 py-2 rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                    />
                  </div>

                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      onClick={() => setIsEditingSection(false)}
                      className="px-3 py-1.5 text-xs text-[#6B6966] hover:text-[#1F1E1D]"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleSaveManualEdit}
                      disabled={isSavingEdit}
                      className="px-4 py-1.5 text-xs font-medium bg-[#1F1E1D] text-white hover:bg-[#33312E] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50"
                    >
                      {isSavingEdit ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                      <span>Save Changes (v{draft.version + 1})</span>
                    </button>
                  </div>
                </div>
              ) : (
                /* Preview Container */
                <div className="p-5 bg-white rounded-xl border border-[#E5E3DC] shadow-sm font-sans space-y-4">
                  {/* Mandatory Purple/Blue AI Draft Disclaimer */}
                  <div className="p-3 rounded-lg bg-[#FAF5F2] border border-[#E8D8CF] text-[#C96442] text-xs flex items-start gap-2">
                    <Shield className="w-4 h-4 shrink-0 mt-0.5" />
                    <div className="text-[11px] leading-relaxed">
                      <strong>AI-GENERATED ADMINISTRATIVE DRAFT:</strong> This representation has been prepared from citizen-confirmed facts and verified procedural guidance. It is an administrative draft for submission to competent authorities and does not represent official government approval or grant.
                    </div>
                  </div>

                  {/* Clean Formatted Document Content */}
                  <div className="p-4 rounded-lg bg-[#FAF9F5] border border-[#EFECE6] font-mono text-xs leading-relaxed whitespace-pre-wrap text-[#1F1E1D] max-h-[400px] overflow-y-auto">
                    {draft.content}
                  </div>

                  {/* Enclosure Checklist */}
                  {draft.supporting_documents && draft.supporting_documents.length > 0 && (
                    <div className="p-3 rounded-lg bg-[#FAF9F5] border border-[#E5E3DC]">
                      <div className="text-xs font-semibold text-[#1F1E1D] mb-1.5 flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5 text-[#C96442]" />
                        <span>Prescribed Enclosures & Supporting Documents:</span>
                      </div>
                      <ul className="text-xs space-y-1 text-[#6B6966] list-disc list-inside">
                        {draft.supporting_documents.map((doc, idx) => (
                          <li key={idx}>
                            <span className="font-medium text-[#1F1E1D]">{doc.document_name}</span>{" "}
                            {doc.mandatory ? (
                              <span className="text-[10px] text-[#C5221F] font-semibold">(Mandatory)</span>
                            ) : (
                              <span className="text-[10px] text-[#6B6966]">(Optional)</span>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* STEP 7: Official Source Verification */}
          {currentStep === 7 && draft && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-[#1F1E1D]">
                  Step 7: Official Procedural Source Verification
                </h3>
                <p className="text-xs text-[#6B6966]">
                  Inspect the official circulars, standard operating procedures, and government rules grounding this draft.
                </p>
              </div>

              {draft.source_references && draft.source_references.length > 0 ? (
                <div className="space-y-3">
                  {draft.source_references.map((src, idx) => (
                    <div
                      key={idx}
                      className="p-4 rounded-xl bg-white border border-[#E5E3DC] shadow-sm space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-[#1F1E1D]">{src.title}</span>
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-[#E6F4EA] text-[#0D652D] border border-[#CEEAD6]">
                          <CheckCircle2 className="w-3 h-3" /> VERIFIED OFFICIAL SOURCE
                        </span>
                      </div>

                      <div className="text-xs text-[#6B6966]">
                        <span className="font-medium text-[#1F1E1D]">Issuing Authority:</span>{" "}
                        {src.authority || src.issuing_authority || "Government Authority"} •{" "}
                        <span className="font-medium text-[#1F1E1D]">Relevance Score:</span>{" "}
                        {src.relevance_score ? (src.relevance_score * 100).toFixed(1) + "%" : "Verified"}
                      </div>

                      {src.content && (
                        <div className="p-2.5 rounded-lg bg-[#FAF9F5] border border-[#EFECE6] text-[11px] text-[#6B6966] leading-relaxed">
                          {src.content}
                        </div>
                      )}

                      {src.source_url && (
                        <div className="pt-1">
                          <a
                            href={src.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-[#1A73E8] hover:underline"
                          >
                            <span>Inspect Official Portal</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                /* Honest Statutory Abstention Notice */
                <div className="p-5 rounded-xl bg-[#FEF7E0] border border-[#FEEFC3] space-y-3 text-xs text-[#B06000]">
                  <div className="flex items-center gap-2 font-semibold">
                    <Scale className="w-4 h-4" />
                    <span>Statutory Procedural Abstention</span>
                  </div>
                  <p className="leading-relaxed">
                    Official procedural guidance for this specific discrepancy in{" "}
                    <span className="font-semibold capitalize">{documentCategory.replace(/_/g, " ")}</span> records is
                    currently undergoing administrative verification. CONVELINA adheres to zero hallucination and will not
                    fabricate procedural rules, fees, or timelines without verified official authority.
                  </p>
                  <p className="text-[11px] text-[#6B6966]">
                    Please consult your designated facilitation center or the competent authority directly before
                    submitting formal representations.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* STEP 8: Explicit Final Confirmation */}
          {currentStep === 8 && draft && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-[#1F1E1D]">
                  Step 8: Explicit Final Version Confirmation
                </h3>
                <p className="text-xs text-[#6B6966]">
                  Review the complete document particulars. Explicit confirmation binds to this exact version number (
                  <span className="font-mono font-semibold">v{draft.version}</span>) and its SHA-256 content hash.
                </p>
              </div>

              {confirmError && (
                <div className="p-3 rounded-xl bg-[#FCE8E6] border border-[#FAD2CF] text-[#C5221F] text-xs flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{confirmError}</span>
                </div>
              )}

              <div className="p-4 rounded-xl bg-white border border-[#E5E3DC] space-y-3">
                <div className="flex items-center justify-between text-xs border-b border-[#F0EEE6] pb-2">
                  <span className="font-semibold text-[#1F1E1D]">Version to Confirm:</span>
                  <span className="font-mono font-medium">Version {draft.version}</span>
                </div>

                {draft.sha256_hash && (
                  <div className="flex items-center justify-between text-xs border-b border-[#F0EEE6] pb-2">
                    <span className="font-semibold text-[#1F1E1D]">Content SHA-256 Hash:</span>
                    <span className="font-mono text-[11px] text-[#6B6966]">{draft.sha256_hash}</span>
                  </div>
                )}

                <div>
                  <label className="block text-xs font-medium text-[#1F1E1D] mb-1">
                    Citizen Acknowledgement Statement <span className="text-[#C5221F]">*</span>
                  </label>
                  <textarea
                    rows={2}
                    value={confirmationStatement}
                    onChange={(e) => setConfirmationStatement(e.target.value)}
                    placeholder="e.g. I have reviewed all identity details in this administrative draft (Version 1) and confirm they are accurate for submission."
                    className="w-full px-3 py-2 text-xs rounded-lg border border-[#D5D2C8] bg-[#FAF9F5] focus:outline-none focus:border-[#C96442]"
                  />
                  <div className="text-[11px] text-[#6B6966] mt-1">
                    Notice: This confirmation means only that the citizen reviewed the draft. It does not represent legal approval or government acceptance.
                  </div>
                </div>

                <div className="pt-2 flex justify-end">
                  <button
                    onClick={handleConfirmDraft}
                    disabled={isConfirming || !confirmationStatement.trim()}
                    className="px-4 py-2 text-xs font-medium bg-[#0D652D] text-white hover:bg-[#0B5324] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-50 shadow-sm"
                  >
                    {isConfirming ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Lock className="w-3.5 h-3.5" />}
                    <span>Confirm Draft Version {draft.version}</span>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* STEP 9: Export */}
          {currentStep === 9 && draft && (
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-[#1F1E1D]">
                  Step 9: Export Final Administrative Draft
                </h3>
                <p className="text-xs text-[#6B6966]">
                  Download your confirmed representation in print-ready PDF or editable DOCX format.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* PDF Card */}
                <div className="p-5 rounded-xl bg-white border border-[#E5E3DC] shadow-sm flex flex-col justify-between space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-[#1F1E1D]">Print-Ready PDF</span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#E6F4EA] text-[#0D652D]">
                        OFFICIAL FORMAT
                      </span>
                    </div>
                    <p className="text-xs text-[#6B6966] leading-relaxed">
                      Standardized A4 layout with mandatory disclaimer banner, formal letterhead styling, and signature line.
                    </p>
                  </div>

                  <button
                    onClick={() => handleDownload("pdf")}
                    disabled={isDownloadingPdf}
                    className="w-full py-2.5 px-4 text-xs font-medium bg-[#1F1E1D] text-white hover:bg-[#33312E] rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50 shadow-sm"
                  >
                    {isDownloadingPdf ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    <span>Download PDF Document</span>
                  </button>
                </div>

                {/* DOCX Card */}
                <div className="p-5 rounded-xl bg-white border border-[#E5E3DC] shadow-sm flex flex-col justify-between space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-semibold text-[#1F1E1D]">Editable DOCX</span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#E8F0FE] text-[#1A73E8]">
                        WORD PROCESSOR
                      </span>
                    </div>
                    <p className="text-xs text-[#6B6966] leading-relaxed">
                      Fully editable Microsoft Word document for fine-tuning layout or appending local advocate details.
                    </p>
                  </div>

                  <button
                    onClick={() => handleDownload("docx")}
                    disabled={isDownloadingDocx}
                    className="w-full py-2.5 px-4 text-xs font-medium bg-white border border-[#D5D2C8] text-[#1F1E1D] hover:bg-[#FAF9F5] rounded-lg transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {isDownloadingDocx ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    <span>Download DOCX Document</span>
                  </button>
                </div>
              </div>

              {/* Unconfirmed Draft Warning Banner */}
              {!draft.is_citizen_confirmed && (
                <div className="p-3.5 rounded-xl bg-[#FEF7F0] border border-[#FAD2B8] flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <AlertCircle className="w-4 h-4 text-[#C96442] shrink-0" />
                    <div className="text-xs text-[#1F1E1D]">
                      <span className="font-semibold">Unconfirmed Draft Version {draft.version} ({draft.language?.toUpperCase() || "EN"}): </span>
                      <span>This draft was edited or translated and requires your confirmation before final official submission.</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setCurrentStep(8)}
                    className="px-3 py-1 text-xs font-semibold bg-[#C96442] text-white hover:bg-[#A34F33] rounded-lg transition-colors shrink-0 ml-3 shadow-sm"
                  >
                    Confirm Version {draft.version}
                  </button>
                </div>
              )}

              {/* Translation Tool */}
              <div className="p-4 rounded-xl bg-[#FAF9F5] border border-[#E5E3DC] flex flex-col md:flex-row md:items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-semibold text-[#1F1E1D] flex items-center gap-1.5">
                    <Languages className="w-4 h-4 text-[#C96442]" />
                    <span>Multilingual Representation Translation</span>
                  </div>
                  <p className="text-[11px] text-[#6B6966] mt-0.5">
                    Generate an authentic regional language translation while preserving citizen-confirmed facts.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  {draft.language !== "en" && (
                    <button
                      onClick={() => handleTranslate("en")}
                      disabled={isTranslating}
                      className="px-3 py-1.5 text-xs font-medium bg-white border border-[#D5D2C8] text-[#1F1E1D] hover:bg-[#FAF9F5] rounded-lg transition-colors disabled:opacity-50"
                    >
                      English Original
                    </button>
                  )}
                  {draft.language !== "ta" && (
                    <button
                      onClick={() => handleTranslate("ta")}
                      disabled={isTranslating}
                      className="px-3 py-1.5 text-xs font-medium bg-white border border-[#D5D2C8] text-[#1F1E1D] hover:bg-[#FAF9F5] rounded-lg transition-colors disabled:opacity-50"
                    >
                      Translate to Tamil (தமிழ்)
                    </button>
                  )}
                  {draft.language !== "bilingual_en_ta" && (
                    <button
                      onClick={() => handleTranslate("bilingual_en_ta", true)}
                      disabled={isTranslating}
                      className="px-3 py-1.5 text-xs font-medium bg-white border border-[#D5D2C8] text-[#1F1E1D] hover:bg-[#FAF9F5] rounded-lg transition-colors disabled:opacity-50"
                    >
                      Bilingual (English + தமிழ்)
                    </button>
                  )}
                  {draft.language !== "hi" && (
                    <button
                      onClick={() => handleTranslate("hi")}
                      disabled={isTranslating}
                      className="px-3 py-1.5 text-xs font-medium bg-white border border-[#D5D2C8] text-[#1F1E1D] hover:bg-[#FAF9F5] rounded-lg transition-colors disabled:opacity-50"
                    >
                      Translate to Hindi (हिंदी)
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Navigation Buttons */}
        <div className="flex items-center justify-between px-6 py-3.5 border-t border-[#E5E3DC] bg-[#FAF9F5]">
          <button
            onClick={() => {
              if (currentStep > 1) setCurrentStep((currentStep - 1) as WizardStep);
            }}
            disabled={currentStep === 1 || isGenerating}
            className="px-4 py-2 text-xs font-medium text-[#6B6966] hover:text-[#1F1E1D] disabled:opacity-30 flex items-center gap-1"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous</span>
          </button>

          <div className="flex items-center gap-2">
            {currentStep < 4 && (
              <button
                onClick={() => setCurrentStep((currentStep + 1) as WizardStep)}
                disabled={currentStep === 2 && (!applicantName.trim() || !requestedValue.trim())}
                className="px-4 py-2 text-xs font-medium bg-[#1F1E1D] text-white hover:bg-[#33312E] rounded-lg transition-colors flex items-center gap-1 disabled:opacity-40"
              >
                <span>Continue</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            )}

            {currentStep === 4 && (
              <button
                onClick={handleGenerateDraft}
                disabled={isGenerating || !applicantName.trim() || !requestedValue.trim()}
                className="px-5 py-2 text-xs font-medium bg-[#C96442] text-white hover:bg-[#B55737] rounded-lg transition-colors flex items-center gap-1.5 disabled:opacity-40 shadow-sm"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate Administrative Draft</span>
              </button>
            )}

            {currentStep >= 6 && currentStep < 9 && (
              <button
                onClick={() => setCurrentStep((currentStep + 1) as WizardStep)}
                className="px-4 py-2 text-xs font-medium bg-[#1F1E1D] text-white hover:bg-[#33312E] rounded-lg transition-colors flex items-center gap-1"
              >
                <span>Next Step</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            )}

            {currentStep === 9 && (
              <button
                onClick={onClose}
                className="px-5 py-2 text-xs font-medium bg-[#1F1E1D] text-white hover:bg-[#33312E] rounded-lg transition-colors"
              >
                Done
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

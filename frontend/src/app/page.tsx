"use client";

import { useEffect, useState } from "react";
import { 
  ShieldCheck, 
  FileSearch, 
  Server, 
  Database, 
  Layers, 
  RefreshCw,
  CheckCircle2, 
  AlertCircle, 
  Cpu, 
  FileText,
  Lock,
  UserCheck,
  KeyRound,
  ShieldAlert,
  LogOut,
  UploadCloud,
  Trash2,
  Eye,
  FileCheck,
  GitCompare,
  AlertTriangle,
  Info,
  Sliders,
  Check,
  Bot,
  Sparkles,
  BookOpen,
  ExternalLink,
  Send,
  Download,
  FileEdit,
  Printer,
  FileDown,
  ClipboardCheck,
  UserCheck2,
  HelpCircle,
  CheckSquare,
  XCircle,
  ArrowRightLeft,
  MessageSquare,
  History
} from "lucide-react";


interface HealthData {
  status: string;
  timestamp?: number;
  services?: {
    backend?: { status: string; error?: string };
    postgres?: { status: string; error?: string };
    qdrant?: { status: string; error?: string };
    firebase_auth?: { status: string };
  };
}

interface UserProfile {
  id: string;
  firebase_uid: string;
  email: string;
  full_name: string;
  role: string;
}

interface ConflictItem {
  id: string;
  user_id: string;
  doc_a_id: string;
  doc_b_id: string;
  conflict_type: string;
  severity: string;
  field_name: string;
  value_a: string;
  value_b: string;
  description: string;
  status: string;
  comparison_method?: string;
  similarity_score?: number | null;
  created_at: string;
  updated_at: string;
}

interface SigningKeyItem {
  id: string;
  key_id: string;
  public_key: string;
  fingerprint: string;
  algorithm: string;
  purpose: string;
  status: string;
  valid_from: string;
  valid_until?: string | null;
  revoked_at?: string | null;
  revocation_reason?: string | null;
  created_at: string;
}

interface DocumentAttestationItem {
  id: string;
  document_id?: string | null;
  case_id?: string | null;
  correction_draft_id?: string | null;
  citizen_id: string;
  officer_id: string;
  document_type: string;
  document_fingerprint: string;
  signing_key_id: string;
  key_id: string;
  canonical_payload: any;
  signature: string;
  algorithm: string;
  status: string;
  expires_at?: string | null;
  created_at: string;
}

interface VerificationResultItem {
  verification_status: string;
  is_valid: boolean;
  human_readable_summary: string;
  signature_valid: boolean;
  document_integrity_valid: boolean;
  key_trusted: boolean;
  key_status: string;
  attestation_id?: string | null;
  key_id: string;
  fingerprint?: string | null;
  details: Record<string, any>;
  verified_at: string;
}

interface PKIStatsItem {
  total_attestations: number;
  valid_attestations: number;
  revoked_attestations: number;
  total_verifications: number;
  valid_verifications: number;
  tampered_detections: number;
  active_keys: number;
  revoked_keys: number;
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>("");

  // Demo active role identity state for interactive verification
  const [activeIdentity, setActiveIdentity] = useState<"citizen" | "officer" | "admin">("citizen");
  const [activeProfile, setActiveProfile] = useState<UserProfile | null>(null);
  const [authTestOutput, setAuthTestOutput] = useState<Record<string, { status: number; message: string }>>({});
  const [testingAuth, setTestingAuth] = useState<boolean>(false);

  // Module 4: Secure Document Upload & OCR state
  const [selectedDocType, setSelectedDocType] = useState<string>("aadhaar");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(false);

  // Module 5: Conflict Detection Engine state
  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [loadingConflicts, setLoadingConflicts] = useState<boolean>(false);
  const [detectingConflicts, setDetectingConflicts] = useState<boolean>(false);
  const [detectionMessage, setDetectionMessage] = useState<string | null>(null);
  const [activeConflictDetail, setActiveConflictDetail] = useState<ConflictItem | null>(null);

  // Module 6: RAG Resolution Assistant state
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [chatInput, setChatInput] = useState<string>("");
  const [sendingChat, setSendingChat] = useState<boolean>(false);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [activeAssistantConflict, setActiveAssistantConflict] = useState<ConflictItem | null>(null);
  const [officialForms, setOfficialForms] = useState<any[]>([]);
  const [loadingForms, setLoadingForms] = useState<boolean>(false);

  // Module 7: Correction Document Generator state
  const [selectedConflictForDraft, setSelectedConflictForDraft] = useState<ConflictItem | null>(null);
  const [draftDocType, setDraftDocType] = useState<string>("correction_request_letter");
  const [confirmedApplicantName, setConfirmedApplicantName] = useState<string>("");
  const [confirmedRequestedValue, setConfirmedRequestedValue] = useState<string>("");
  const [userDraftExplanation, setUserDraftExplanation] = useState<string>("");
  const [generatingDraft, setGeneratingDraft] = useState<boolean>(false);
  const [draftError, setDraftError] = useState<string | null>(null);
  const [activeDraft, setActiveDraft] = useState<any | null>(null);
  const [draftList, setDraftList] = useState<any[]>([]);
  const [loadingDrafts, setLoadingDrafts] = useState<boolean>(false);
  const [editingContent, setEditingContent] = useState<string>("");
  const [savingEdit, setSavingEdit] = useState<boolean>(false);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Module 8: Officer Verification Workflow state
  const [citizenCases, setCitizenCases] = useState<any[]>([]);
  const [loadingCases, setLoadingCases] = useState<boolean>(false);
  const [officerCases, setOfficerCases] = useState<any[]>([]);
  const [activeDossier, setActiveDossier] = useState<any | null>(null);
  const [loadingDossier, setLoadingDossier] = useState<boolean>(false);
  const [adminOfficers, setAdminOfficers] = useState<any[]>([]);
  const [adminCases, setAdminCases] = useState<any[]>([]);
  const [loadingAdminView, setLoadingAdminView] = useState<boolean>(false);
  const [selectedCaseToAssign, setSelectedCaseToAssign] = useState<string | null>(null);
  const [selectedOfficerForAssign, setSelectedOfficerForAssign] = useState<string>("");
  const [actionSuccessMsg, setActionSuccessMsg] = useState<string | null>(null);
  const [actionErrorMsg, setActionErrorMsg] = useState<string | null>(null);
  const [reviewActionNote, setReviewActionNote] = useState<string>("");
  const [infoRequestReason, setInfoRequestReason] = useState<string>("");
  const [citizenClarificationText, setCitizenClarificationText] = useState<string>("");
  const [submittingClarification, setSubmittingClarification] = useState<boolean>(false);
  const [activeRequestId, setActiveRequestId] = useState<string | null>(null);

  // Module 9: Ed25519 PKI & Document Authenticity State
  const [pkiStats, setPkiStats] = useState<PKIStatsItem | null>(null);
  const [signingKeys, setSigningKeys] = useState<SigningKeyItem[]>([]);
  const [attestations, setAttestations] = useState<DocumentAttestationItem[]>([]);
  const [recentVerifications, setRecentVerifications] = useState<any[]>([]);
  const [loadingPKI, setLoadingPKI] = useState<boolean>(false);
  const [selectedAttestation, setSelectedAttestation] = useState<DocumentAttestationItem | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResultItem | null>(null);
  const [verifyingAttestation, setVerifyingAttestation] = useState<boolean>(false);
  const [pkiSuccessMsg, setPkiSuccessMsg] = useState<string | null>(null);
  const [pkiErrorMsg, setPkiErrorMsg] = useState<string | null>(null);
  const [attestingDoc, setAttestingDoc] = useState<boolean>(false);
  const [newKeyIdInput, setNewKeyIdInput] = useState<string>("");
  const [rotatingKey, setRotatingKey] = useState<boolean>(false);
  const [revokingKeyId, setRevokingKeyId] = useState<string | null>(null);
  const [revokeReasonInput, setRevokeReasonInput] = useState<string>("");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const getSimulatedToken = (role: "citizen" | "officer" | "admin") => {
    return `test_token_:ui_demo_${role}:${role}.demo@synthetic.test:${role.toUpperCase()} User`;
  };


  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/health`, { cache: "no-store" });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        setHealth(errorData);
        setError(`Service degraded (HTTP ${res.status})`);
      } else {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to connect to backend");
      setHealth(null);
    } finally {
      setLoading(false);
      setLastChecked(new Date().toLocaleTimeString());
    }
  };

  const syncIdentityAndTestRoutes = async (role: "citizen" | "officer" | "admin") => {
    setTestingAuth(true);
    setActiveIdentity(role);
    const token = getSimulatedToken(role);

    try {
      // 1. Provision / sync profile
      await fetch(`${apiUrl}/api/v1/auth/provision`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ full_name: `${role.toUpperCase()} Demo User` })
      });

      // 2. Fetch /me
      const meRes = await fetch(`${apiUrl}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (meRes.ok) {
        const profileData = await meRes.json();
        setActiveProfile(profileData);
      }

      // 3. Test RBAC endpoints
      const endpoints = [
        { key: "citizen", url: "/api/v1/auth/citizen-only" },
        { key: "officer", url: "/api/v1/auth/officer-only" },
        { key: "admin", url: "/api/v1/auth/admin-only" }
      ];

      const results: Record<string, { status: number; message: string }> = {};
      for (const ep of endpoints) {
        const r = await fetch(`${apiUrl}${ep.url}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const resJson = await r.json().catch(() => ({}));
        results[ep.key] = {
          status: r.status,
          message: r.ok ? "Access Granted" : (resJson.detail || "Forbidden")
        };
      }
      setAuthTestOutput(results);
      fetchDocuments(role);
      fetchConflicts(role);
      fetchDrafts(role);
      if (role === "citizen") fetchCitizenCases();
      if (role === "officer") fetchOfficerCasesList();
      if (role === "admin") fetchAdminWorkload();
      fetchPKIData(role);

    } catch (e: unknown) {
      console.error("Auth test failed:", e);
    } finally {
      setTestingAuth(false);
    }

  };

  const fetchDocuments = async (role = activeIdentity) => {
    setLoadingDocs(true);
    try {
      const token = getSimulatedToken(role);
      const res = await fetch(`${apiUrl}/api/v1/documents`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (e) {
      console.error("Failed to fetch documents", e);
    } finally {
      setLoadingDocs(false);
    }
  };

  const fetchConflicts = async (role = activeIdentity) => {
    setLoadingConflicts(true);
    try {
      const token = getSimulatedToken(role);
      const res = await fetch(`${apiUrl}/api/v1/conflicts`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setConflicts(data.conflicts || []);
      }
    } catch (e) {
      console.error("Failed to fetch conflicts", e);
    } finally {
      setLoadingConflicts(false);
    }
  };

  const handleRunDetection = async () => {
    setDetectingConflicts(true);
    setDetectionMessage(null);
    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/conflicts/detect`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (res.ok) {
        setDetectionMessage(data.message || `Detection complete. Discrepancies: ${data.total_conflicts_detected}`);
        setConflicts(data.conflicts || []);
      } else {
        setDetectionMessage(data.detail || "Conflict detection execution failed.");
      }
    } catch (e) {
      setDetectionMessage("Network error during conflict detection.");
    } finally {
      setDetectingConflicts(false);
    }
  };

  const fetchOfficialForms = async () => {
    setLoadingForms(true);
    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/knowledge/forms`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setOfficialForms(data.forms || []);
      }
    } catch (e) {
      console.error("Failed to load official forms", e);
    } finally {
      setLoadingForms(false);
    }
  };

  const handleExplainConflict = async (conflict: ConflictItem) => {
    setActiveAssistantConflict(conflict);
    setSendingChat(true);
    const token = getSimulatedToken(activeIdentity);
    try {
      const res = await fetch(`${apiUrl}/api/v1/assistant/explain-conflict/${conflict.id}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentConversationId(data.conversation_id);
        setChatMessages((prev) => [
          ...prev,
          {
            role: "user",
            content: `Explain discrepancy in ${conflict.field_name} (${conflict.value_a} vs ${conflict.value_b})`
          },
          {
            role: "assistant",
            content: data.response.answer,
            response: data.response
          }
        ]);
      }
    } catch (e) {
      console.error("Error explaining conflict", e);
    } finally {
      setSendingChat(false);
    }
  };

  const handleResolveConflict = async (conflict: ConflictItem) => {
    setActiveAssistantConflict(conflict);
    setSendingChat(true);
    const token = getSimulatedToken(activeIdentity);
    try {
      const res = await fetch(`${apiUrl}/api/v1/assistant/resolve-conflict/${conflict.id}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentConversationId(data.conversation_id);
        setChatMessages((prev) => [
          ...prev,
          {
            role: "user",
            content: `How do I resolve the inconsistency in my ${conflict.field_name}?`
          },
          {
            role: "assistant",
            content: data.response.answer,
            response: data.response
          }
        ]);
      }
    } catch (e) {
      console.error("Error resolving conflict", e);
    } finally {
      setSendingChat(false);
    }
  };

  const handleSendChatMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!chatInput.trim() || sendingChat) return;

    const messageText = chatInput.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { role: "user", content: messageText }]);
    setSendingChat(true);

    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/assistant/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          message: messageText,
          conversation_id: currentConversationId,
          conflict_id: activeAssistantConflict?.id || null
        })
      });

      if (res.ok) {
        const data = await res.json();
        setCurrentConversationId(data.conversation_id);
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: data.response.answer,
            response: data.response
          }
        ]);
      } else {
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Unable to process inquiry. Please verify the request or consult jurisdictional authority."
          }
        ]);
      }
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Network error communicating with AI resolution assistant."
        }
      ]);
    } finally {
      setSendingChat(false);
    }
  };

  const handleUpdateReviewStatus = async (conflictId: string, newStatus: string) => {
    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/conflicts/${conflictId}/review`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        const updated = await res.json();
        setConflicts((prev) =>
          prev.map((c) => (c.id === conflictId ? { ...c, status: updated.status } : c))
        );
        if (activeConflictDetail && activeConflictDetail.id === conflictId) {
          setActiveConflictDetail((prev) => prev ? { ...prev, status: updated.status } : null);
        }
      }
    } catch (e) {
      console.error("Failed to update conflict status", e);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError("Please select a document file (.pdf, .jpg, .png)");
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("document_type", selectedDocType);

    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        setUploadError(data.detail || "Upload or OCR processing failed");
      } else {
        setUploadResult(data);
        setSelectedFile(null);
        fetchDocuments(activeIdentity);
      }
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Network error during upload");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (id: string) => {
    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/documents/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        fetchDocuments(activeIdentity);
        fetchConflicts(activeIdentity);
      }
    } catch (e) {
      console.error("Failed to delete document", e);
    }
  };

  const fetchDrafts = async (role: "citizen" | "officer" | "admin" = activeIdentity) => {
    setLoadingDrafts(true);
    try {
      const token = getSimulatedToken(role);
      const res = await fetch(`${apiUrl}/api/v1/correction-drafts`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setDraftList(data.items || []);
      }
    } catch (e) {
      console.error("Failed to fetch drafts", e);
    } finally {
      setLoadingDrafts(false);
    }
  };

  const handleGenerateDraft = async () => {
    if (!selectedConflictForDraft) {
      setDraftError("Please select an identified conflict first.");
      return;
    }
    setGeneratingDraft(true);
    setDraftError(null);
    setSaveSuccessMsg(null);

    const targetCategory = selectedConflictForDraft.field_name.toLowerCase().includes("pan")
      ? "pan"
      : selectedConflictForDraft.field_name.toLowerCase().includes("passport")
      ? "passport"
      : "pan";

    const payload = {
      conflict_id: selectedConflictForDraft.id,
      document_type: draftDocType,
      document_category: targetCategory,
      confirmed_fields: {
        applicant_name: confirmedApplicantName || "Applicant",
        requested_value: confirmedRequestedValue || selectedConflictForDraft.value_a,
        current_recorded_value: selectedConflictForDraft.value_b,
        reason_for_discrepancy: userDraftExplanation || "Typographical clerical discrepancy."
      }
    };

    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/correction-drafts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) {
        setDraftError(data.detail || "Assistant service is not currently available. Please try again later.");
      } else {
        setActiveDraft(data);
        setEditingContent(data.content);
        fetchDrafts(activeIdentity);
      }
    } catch (err: unknown) {
      setDraftError(err instanceof Error ? err.message : "Assistant service is not currently available. Please try again later.");
    } finally {
      setGeneratingDraft(false);
    }
  };

  const handleSaveDraftEdit = async () => {
    if (!activeDraft) return;
    setSavingEdit(true);
    setSaveSuccessMsg(null);
    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/correction-drafts/${activeDraft.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ content: editingContent, status: "user_edited" })
      });
      if (res.ok) {
        const updated = await res.json();
        setActiveDraft(updated);
        setSaveSuccessMsg("Draft edits saved as a new version.");
        fetchDrafts(activeIdentity);
      }
    } catch (e) {
      console.error("Failed to save draft edits", e);
    } finally {
      setSavingEdit(false);
    }
  };

  const handleDeleteDraft = async (draftId: string) => {
    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/correction-drafts/${draftId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        if (activeDraft?.id === draftId) {
          setActiveDraft(null);
          setEditingContent("");
        }
        fetchDrafts(activeIdentity);
      }
    } catch (e) {
      console.error("Failed to delete draft", e);
    }
  };

  const handleDownloadDraft = async (draftId: string, format: "pdf" | "docx") => {
    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/correction-drafts/${draftId}/download?format=${format}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `correction_draft_${draftId.slice(0, 8)}.${format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
      }
    } catch (e) {
      console.error("Download failed", e);
    }
  };

  // Module 8: Officer Verification Workflow API Handlers
  const fetchCitizenCases = async () => {
    setLoadingCases(true);
    try {
      const token = getSimulatedToken("citizen");
      const res = await fetch(`${apiUrl}/api/v1/cases/my-cases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCitizenCases(data.items || []);
      }
    } catch (e) {
      console.error("Failed to fetch citizen cases", e);
    } finally {
      setLoadingCases(false);
    }
  };

  const fetchOfficerCasesList = async () => {
    setLoadingCases(true);
    try {
      const token = getSimulatedToken("officer");
      const res = await fetch(`${apiUrl}/api/v1/officer/cases`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setOfficerCases(data.items || []);
        if (data.items?.length > 0 && !activeDossier) {
          fetchDossier(data.items[0].id);
        }
      }
    } catch (e) {
      console.error("Failed to fetch officer cases", e);
    } finally {
      setLoadingCases(false);
    }
  };

  const fetchDossier = async (caseId: string) => {
    setLoadingDossier(true);
    setActionSuccessMsg(null);
    setActionErrorMsg(null);
    try {
      const token = getSimulatedToken("officer");
      const res = await fetch(`${apiUrl}/api/v1/officer/cases/${caseId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setActiveDossier(data);
      }
    } catch (e) {
      console.error("Failed to fetch dossier", e);
    } finally {
      setLoadingDossier(false);
    }
  };

  const fetchAdminWorkload = async () => {
    setLoadingAdminView(true);
    try {
      const token = getSimulatedToken("admin");
      const [offRes, caseRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/admin/officers`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${apiUrl}/api/v1/admin/cases`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      if (offRes.ok) {
        const offs = await offRes.json();
        setAdminOfficers(offs);
        if (offs.length > 0 && !selectedOfficerForAssign) {
          setSelectedOfficerForAssign(offs[0].officer_id);
        }
      }
      if (caseRes.ok) {
        const cs = await caseRes.json();
        setAdminCases(cs.items || []);
      }
    } catch (e) {
      console.error("Failed to fetch admin workload", e);
    } finally {
      setLoadingAdminView(false);
    }
  };

  const handleStartReview = async (caseId: string) => {
    setActionSuccessMsg(null);
    setActionErrorMsg(null);
    try {
      const token = getSimulatedToken("officer");
      const res = await fetch(`${apiUrl}/api/v1/officer/cases/${caseId}/start-review`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        setActionSuccessMsg("Review started. Case marked 'under_review'.");
        fetchDossier(caseId);
        fetchOfficerCasesList();
      } else {
        const err = await res.json().catch(() => ({}));
        setActionErrorMsg(err.detail || "Failed to start review.");
      }
    } catch (e) {
      setActionErrorMsg("Network error.");
    }
  };

  const handleRequestInfo = async (caseId: string) => {
    if (!infoRequestReason.trim() || !reviewActionNote.trim()) {
      setActionErrorMsg("Please specify both Request Reason and Explanation Details.");
      return;
    }
    setActionSuccessMsg(null);
    setActionErrorMsg(null);
    try {
      const token = getSimulatedToken("officer");
      const res = await fetch(`${apiUrl}/api/v1/officer/cases/${caseId}/request-information`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          request_reason: infoRequestReason,
          request_details: reviewActionNote
        })
      });
      if (res.ok) {
        setActionSuccessMsg("Clarification requested from citizen.");
        setInfoRequestReason("");
        setReviewActionNote("");
        fetchDossier(caseId);
        fetchOfficerCasesList();
      } else {
        const err = await res.json().catch(() => ({}));
        setActionErrorMsg(err.detail || "Failed to request clarification.");
      }
    } catch (e) {
      setActionErrorMsg("Network error.");
    }
  };

  const handleOfficerDecision = async (caseId: string, decision: "approve" | "reject") => {
    if (!reviewActionNote.trim()) {
      setActionErrorMsg("A recorded justification reason is mandatory.");
      return;
    }
    setActionSuccessMsg(null);
    setActionErrorMsg(null);
    try {
      const token = getSimulatedToken("officer");
      const res = await fetch(`${apiUrl}/api/v1/officer/cases/${caseId}/${decision}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          decision_reason: reviewActionNote,
          officer_notes: `Application verification review outcome: ${decision.toUpperCase()}`
        })
      });
      if (res.ok) {
        setActionSuccessMsg(`Case successfully marked as ${decision.toUpperCase()}. Audited immutably.`);
        setReviewActionNote("");
        fetchDossier(caseId);
        fetchOfficerCasesList();
      } else {
        const err = await res.json().catch(() => ({}));
        setActionErrorMsg(err.detail || `Failed to record ${decision}.`);
      }
    } catch (e) {
      setActionErrorMsg("Network error.");
    }
  };

  const handleCitizenSubmitCase = async (title: string, conflictId?: string, draftId?: string) => {
    try {
      const token = getSimulatedToken("citizen");
      const res = await fetch(`${apiUrl}/api/v1/cases`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          title: title || "Identity Discrepancy Correction Case",
          conflict_id: conflictId || null,
          correction_draft_id: draftId || null,
          evidence_notes: "Submitted by citizen for officer verification review."
        })
      });
      if (res.ok) {
        fetchCitizenCases();
      }
    } catch (e) {
      console.error("Submit case failed", e);
    }
  };

  const handleCitizenRespondClarification = async (caseId: string, requestId: string) => {
    if (!citizenClarificationText.trim()) return;
    setSubmittingClarification(true);
    try {
      const token = getSimulatedToken("citizen");
      const res = await fetch(`${apiUrl}/api/v1/cases/${caseId}/review-requests/${requestId}/respond`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ citizen_response: citizenClarificationText })
      });
      if (res.ok) {
        setCitizenClarificationText("");
        setActiveRequestId(null);
        fetchCitizenCases();
      }
    } catch (e) {
      console.error("Respond clarification failed", e);
    } finally {
      setSubmittingClarification(false);
    }
  };

  const handleAdminAssign = async (caseId: string) => {
    if (!selectedOfficerForAssign) return;
    try {
      const token = getSimulatedToken("admin");
      const res = await fetch(`${apiUrl}/api/v1/admin/cases/${caseId}/assign`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ officer_id: selectedOfficerForAssign })
      });
      if (res.ok) {
        setSelectedCaseToAssign(null);
        fetchAdminWorkload();
      }
    } catch (e) {
      console.error("Admin assign failed", e);
    }
  };

  // Module 9: Ed25519 PKI & Verification Handlers
  const fetchPKIData = async (role = activeIdentity) => {
    setLoadingPKI(true);
    try {
      const token = getSimulatedToken(role);
      const [statsRes, keysRes, attRes, verRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/pki/stats`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${apiUrl}/api/v1/pki/keys`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${apiUrl}/api/v1/attestations`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${apiUrl}/api/v1/verifications/recent`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      if (statsRes.ok) setPkiStats(await statsRes.json());
      if (keysRes.ok) setSigningKeys(await keysRes.json());
      if (attRes.ok) {
        const attList = await attRes.json();
        setAttestations(attList);
        if (attList.length > 0 && !selectedAttestation) {
          setSelectedAttestation(attList[0]);
        }
      }
      if (verRes.ok) setRecentVerifications(await verRes.json());
    } catch (e) {
      console.error("Failed to fetch PKI data", e);
    } finally {
      setLoadingPKI(false);
    }
  };

  const handleVerifyAttestation = async (attestationId: string, simulateTamper: boolean) => {
    setVerifyingAttestation(true);
    setPkiSuccessMsg(null);
    setPkiErrorMsg(null);
    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/attestations/${attestationId}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ simulate_tamper: simulateTamper })
      });
      if (res.ok) {
        const result = await res.json();
        setVerificationResult(result);
        if (result.is_valid) {
          setPkiSuccessMsg("Cryptographic verification PASSED: Ed25519 signature is mathematically valid, key is trusted, and document hash is intact.");
        } else {
          setPkiErrorMsg(`Verification Alert: ${result.verification_status} — ${result.human_readable_summary}`);
        }
        fetchPKIData(activeIdentity);
      } else {
        const err = await res.json().catch(() => ({}));
        setPkiErrorMsg(err.detail || "Verification request failed.");
      }
    } catch (e) {
      setPkiErrorMsg("Network error during verification.");
    } finally {
      setVerifyingAttestation(false);
    }
  };

  const handleOfficerAttestDocument = async (docId?: string) => {
    setAttestingDoc(true);
    setPkiSuccessMsg(null);
    setPkiErrorMsg(null);
    try {
      const targetDoc = documents.find(d => d.id === docId) || documents[0];
      if (!targetDoc) {
        setPkiErrorMsg("No uploaded document available to attest. Please upload a document in Module 4 first.");
        return;
      }
      const token = getSimulatedToken("officer");
      const res = await fetch(`${apiUrl}/api/v1/attestations?citizen_id=${targetDoc.user_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          document_id: targetDoc.id,
          document_type: targetDoc.document_type,
          document_fingerprint: targetDoc.file_hash,
          signing_purpose: "officer_verification_attestation",
          expires_in_days: 365
        })
      });
      if (res.ok) {
        const newAtt = await res.json();
        setPkiSuccessMsg(`Document attested successfully! Ed25519 signature generated with Key ${newAtt.key_id}.`);
        setSelectedAttestation(newAtt);
        fetchPKIData(activeIdentity);
      } else {
        const err = await res.json().catch(() => ({}));
        setPkiErrorMsg(err.detail || "Failed to attest document.");
      }
    } catch (e) {
      setPkiErrorMsg("Network error during attestation.");
    } finally {
      setAttestingDoc(false);
    }
  };

  const handleRotateKey = async (oldKeyId: string) => {
    if (!newKeyIdInput.trim()) return;
    setRotatingKey(true);
    setPkiSuccessMsg(null);
    setPkiErrorMsg(null);
    try {
      const token = getSimulatedToken("admin");
      const res = await fetch(`${apiUrl}/api/v1/pki/keys/${oldKeyId}/rotate`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ new_key_id: newKeyIdInput.trim(), purpose: "officer_attestation" })
      });
      if (res.ok) {
        setPkiSuccessMsg(`Key ${oldKeyId} rotated to ${newKeyIdInput.trim()} successfully.`);
        setNewKeyIdInput("");
        fetchPKIData(activeIdentity);
      } else {
        const err = await res.json().catch(() => ({}));
        setPkiErrorMsg(err.detail || "Key rotation failed.");
      }
    } catch (e) {
      setPkiErrorMsg("Network error rotating key.");
    } finally {
      setRotatingKey(false);
    }
  };

  const handleRevokeKey = async (keyId: string) => {
    if (!revokeReasonInput.trim()) return;
    setPkiSuccessMsg(null);
    setPkiErrorMsg(null);
    try {
      const token = getSimulatedToken("admin");
      const res = await fetch(`${apiUrl}/api/v1/pki/keys/${keyId}/revoke`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ reason: revokeReasonInput.trim() })
      });
      if (res.ok) {
        setPkiSuccessMsg(`Key ${keyId} revoked successfully.`);
        setRevokingKeyId(null);
        setRevokeReasonInput("");
        fetchPKIData(activeIdentity);
      } else {
        const err = await res.json().catch(() => ({}));
        setPkiErrorMsg(err.detail || "Key revocation failed.");
      }
    } catch (e) {
      setPkiErrorMsg("Network error revoking key.");
    }
  };

  useEffect(() => {
    checkHealth();
    syncIdentityAndTestRoutes("citizen");
    fetchDocuments("citizen");
    fetchConflicts("citizen");
    fetchDrafts("citizen");
    fetchCitizenCases();
    fetchOfficerCasesList();
    fetchAdminWorkload();
    fetchPKIData("citizen");
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);


  const getStatusBadge = (svcStatus?: string) => {
    if (svcStatus === "up" || svcStatus === "configured") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
          <CheckCircle2 className="w-3.5 h-3.5" /> Operational
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-950/80 text-rose-400 border border-rose-800/60">
        <AlertCircle className="w-3.5 h-3.5" /> Offline / Degraded
      </span>
    );
  };

  return (
    <main className="min-h-screen p-6 md:p-12 max-w-7xl mx-auto flex flex-col justify-between">
      {/* Header */}
      <div>
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-8 border-b border-border/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-600/20 border border-blue-500/30 rounded-xl text-blue-400">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-white">Consolith</h1>
                <span className="text-xs px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                  Module 7: Correction Document Generator
                </span>
              </div>
              <p className="text-sm text-gray-400 mt-0.5">
                AI-Powered Identity Document Conflict Detection & Government Correction Assistance
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              id="refresh-health-btn"
              onClick={checkHealth}
              disabled={loading}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-gray-200 bg-surface border border-border rounded-lg hover:bg-surface-card hover:border-gray-600 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-blue-400" : ""}`} />
              Check Status
            </button>
            <div className="text-xs text-gray-400">
              Last check: <span className="text-gray-300 font-mono">{lastChecked || "Checking..."}</span>
            </div>
          </div>
        </header>

        {/* Live Authentication & RBAC Verification Console */}
        <section className="mt-8 p-6 rounded-2xl bg-surface/80 border border-border backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/60">
            <div className="flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-blue-400" />
              <h2 className="text-base font-semibold text-white">Live Identity & Role-Based Access Control (RBAC) Console</h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Simulate Identity:</span>
              {(["citizen", "officer", "admin"] as const).map((role) => (
                <button
                  key={role}
                  id={`role-btn-${role}`}
                  onClick={() => syncIdentityAndTestRoutes(role)}
                  disabled={testingAuth}
                  className={`px-3 py-1 text-xs font-medium rounded-lg border transition ${
                    activeIdentity === role 
                      ? "bg-blue-600 text-white border-blue-500 shadow-sm shadow-blue-500/20" 
                      : "bg-surface text-gray-300 border-border hover:bg-surface-card"
                  }`}
                >
                  {role.charAt(0).toUpperCase() + role.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Active Session Identity */}
            <div className="p-4 rounded-xl bg-surface-card/60 border border-border">
              <div className="flex items-center gap-2 text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                <UserCheck className="w-4 h-4 text-emerald-400" /> Active Verified Profile
              </div>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Name:</span>
                  <span className="text-white font-medium">{activeProfile?.full_name || "Syncing..."}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Role:</span>
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    {activeProfile?.role || activeIdentity}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Firebase UID:</span>
                  <span className="font-mono text-xs text-gray-300">{activeProfile?.firebase_uid || "Pending"}</span>
                </div>
              </div>
            </div>

            {/* Server-Side RBAC Enforcement Status */}
            <div className="p-4 rounded-xl bg-surface-card/60 border border-border md:col-span-2">
              <div className="flex items-center gap-2 text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                <ShieldAlert className="w-4 h-4 text-cyan-400" /> Server-Side Route Access Checks (FastAPI)
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                {[
                  { key: "citizen", label: "/api/v1/auth/citizen-only" },
                  { key: "officer", label: "/api/v1/auth/officer-only" },
                  { key: "admin", label: "/api/v1/auth/admin-only" }
                ].map(({ key, label }) => {
                  const res = authTestOutput[key];
                  const isOk = res?.status === 200;
                  return (
                    <div key={key} className={`p-2.5 rounded-lg border text-xs flex flex-col justify-between ${
                      isOk 
                        ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
                        : "bg-rose-950/30 border-rose-800/50 text-rose-300"
                    }`}>
                      <span className="font-mono text-[11px] truncate">{label}</span>
                      <div className="mt-2 flex items-center justify-between font-medium">
                        <span>HTTP {res?.status || "..."}</span>
                        <span>{isOk ? "Allowed (200)" : "Forbidden (403)"}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        {/* System Health Grid */}
        <section className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-400" /> System Architecture & Services
            </h2>
            <div className="text-xs text-gray-400">Docker Compose Managed</div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Frontend Card */}
            <div id="status-frontend-card" className="p-5 rounded-xl bg-surface/70 border border-border backdrop-blur-sm">
              <div className="flex items-start justify-between">
                <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <Cpu className="w-5 h-5" />
                </div>
                {getStatusBadge("up")}
              </div>
              <h3 className="text-base font-medium text-white mt-4">Next.js Web App</h3>
              <p className="text-xs text-gray-400 mt-1">App Router, TypeScript, Tailwind CSS</p>
              <div className="mt-4 pt-3 border-t border-border/60 flex justify-between text-xs text-gray-400">
                <span>Port</span>
                <span className="font-mono text-gray-300">3000</span>
              </div>
            </div>

            {/* Backend Card */}
            <div id="status-backend-card" className="p-5 rounded-xl bg-surface/70 border border-border backdrop-blur-sm">
              <div className="flex items-start justify-between">
                <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                  <Server className="w-5 h-5" />
                </div>
                {getStatusBadge(health?.services?.backend?.status)}
              </div>
              <h3 className="text-base font-medium text-white mt-4">FastAPI Backend</h3>
              <p className="text-xs text-gray-400 mt-1">Pydantic v2 & Firebase Auth Re-verification</p>
              <div className="mt-4 pt-3 border-t border-border/60 flex justify-between text-xs text-gray-400">
                <span>Port</span>
                <span className="font-mono text-gray-300">8000</span>
              </div>
            </div>

            {/* PostgreSQL Card */}
            <div id="status-postgres-card" className="p-5 rounded-xl bg-surface/70 border border-border backdrop-blur-sm">
              <div className="flex items-start justify-between">
                <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                  <Database className="w-5 h-5" />
                </div>
                {getStatusBadge(health?.services?.postgres?.status)}
              </div>
              <h3 className="text-base font-medium text-white mt-4">PostgreSQL 16</h3>
              <p className="text-xs text-gray-400 mt-1">Non-Superuser Role & Forced RLS</p>
              <div className="mt-4 pt-3 border-t border-border/60 flex justify-between text-xs text-gray-400">
                <span>Port</span>
                <span className="font-mono text-gray-300">5432</span>
              </div>
            </div>

            {/* Qdrant Card */}
            <div id="status-qdrant-card" className="p-5 rounded-xl bg-surface/70 border border-border backdrop-blur-sm">
              <div className="flex items-start justify-between">
                <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
                  <FileSearch className="w-5 h-5" />
                </div>
                {getStatusBadge(health?.services?.qdrant?.status)}
              </div>
              <h3 className="text-base font-medium text-white mt-4">Qdrant Vector DB</h3>
              <p className="text-xs text-gray-400 mt-1">Vector store for BGE-M3 RAG embeddings</p>
              <div className="mt-4 pt-3 border-t border-border/60 flex justify-between text-xs text-gray-400">
                <span>Port</span>
                <span className="font-mono text-gray-300">6333</span>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-4 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 text-sm flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
              <div>
                <p className="font-medium">Backend Health Check Notice</p>
                <p className="text-xs text-rose-300/80 mt-0.5">{error}</p>
              </div>
            </div>
          )}
        </section>

        {/* Module 4: Secure Document Upload & OCR Pipeline Console */}
        <section className="mt-8 p-6 rounded-2xl bg-surface/50 border border-border backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-border/80 gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider rounded bg-indigo-950 text-indigo-400 border border-indigo-800/60">
                  Module 4
                </span>
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                  <UploadCloud className="w-5 h-5 text-indigo-400" /> Secure Document Upload & OCR Extraction
                </h2>
              </div>
              <p className="text-sm text-gray-400 mt-1">
                Upload Indian identity documents with content validation, Tesseract OCR extraction, Aadhaar masking, and RLS enforcement.
              </p>
            </div>
            <button
              onClick={() => fetchDocuments(activeIdentity)}
              disabled={loadingDocs}
              className="px-3 py-1.5 rounded-lg border border-border text-xs text-gray-300 hover:text-white flex items-center gap-1.5 hover:bg-surface transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingDocs ? "animate-spin" : ""}`} /> Refresh Library
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            {/* Upload Form Card */}
            <div className="p-5 rounded-xl bg-surface/80 border border-border flex flex-col justify-between">
              <form onSubmit={handleUpload} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5">Document Type</label>
                  <select
                    value={selectedDocType}
                    onChange={(e) => setSelectedDocType(e.target.value)}
                    className="w-full bg-slate-900 border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="aadhaar">Aadhaar Card (UIDAI)</option>
                    <option value="pan">PAN Card (Income Tax)</option>
                    <option value="passport">Indian Passport</option>
                    <option value="education_10th">Class 10 Certificate</option>
                    <option value="education_12th">Class 12 Certificate</option>
                    <option value="epf_record">EPFO / UAN Record</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5">Document File (PDF, JPEG, PNG - Max 10MB)</label>
                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-gray-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                  />
                  {selectedFile && (
                    <p className="text-xs text-indigo-300 mt-1.5 flex items-center gap-1">
                      <FileCheck className="w-3.5 h-3.5" /> {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                    </p>
                  )}
                </div>

                {uploadError && (
                  <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                    <span>{uploadError}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={uploading || !selectedFile}
                  className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Processing OCR...
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-4 h-4" /> Upload & Run OCR
                    </>
                  )}
                </button>
              </form>

              {uploadResult && (
                <div className="mt-4 p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-xs text-emerald-300">
                  <div className="flex items-center gap-1.5 font-medium">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" /> OCR {uploadResult.ocr_status.toUpperCase()}
                  </div>
                  <p className="mt-1 font-mono text-[11px] text-gray-300">Masked ID: {uploadResult.masked_id || "N/A"}</p>
                  <p className="text-[11px] text-emerald-400/80 mt-0.5">Temp file securely unlinked per privacy policy.</p>
                </div>
              )}
            </div>

            {/* Document Library Table (RLS scoped) */}
            <div className="lg:col-span-2 p-5 rounded-xl bg-surface/80 border border-border flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Database className="w-4 h-4 text-indigo-400" /> Document Repository ({documents.length})
                  </h3>
                  <span className="text-[11px] font-mono text-gray-400">Scoped to: {activeIdentity}</span>
                </div>

                {documents.length === 0 ? (
                  <div className="py-10 text-center text-sm text-gray-500 border border-dashed border-border rounded-xl">
                    No documents uploaded for this identity yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-border/80 text-gray-400">
                          <th className="pb-2">Type</th>
                          <th className="pb-2">Identifier</th>
                          <th className="pb-2">Status</th>
                          <th className="pb-2">Extracted Fields</th>
                          <th className="pb-2 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/40 text-gray-300">
                        {documents.map((doc) => (
                          <tr key={doc.id} className="hover:bg-slate-900/40">
                            <td className="py-2.5 font-medium uppercase text-white">{doc.document_type}</td>
                            <td className="py-2.5 font-mono text-indigo-300">{doc.masked_id || "—"}</td>
                            <td className="py-2.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                doc.ocr_status === "completed" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-amber-950 text-amber-400 border border-amber-800"
                              }`}>
                                {doc.ocr_status}
                              </span>
                            </td>
                            <td className="py-2.5 max-w-[200px] truncate text-gray-400 font-mono text-[11px]">
                              {JSON.stringify(doc.extracted_fields)}
                            </td>
                            <td className="py-2.5 text-right">
                              <button
                                onClick={() => handleDeleteDocument(doc.id)}
                                className="p-1 rounded hover:bg-rose-950/60 text-gray-400 hover:text-rose-400 transition"
                                title="Delete document"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Module 5: Deterministic Conflict Detection Engine Console */}
        <section id="module-5-conflicts" className="mt-8 p-6 rounded-2xl bg-surface/50 border border-border backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-border/80 gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider rounded bg-amber-950 text-amber-400 border border-amber-800/60">
                  Module 5
                </span>
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                  <GitCompare className="w-5 h-5 text-amber-400" /> Deterministic Conflict Detection Engine
                </h2>
              </div>
              <p className="text-sm text-gray-400 mt-1">
                Cross-document verification using RapidFuzz fuzzy matching, Jellyfish phonetic analysis, and deterministic calendar comparison under forced RLS.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchConflicts(activeIdentity)}
                disabled={loadingConflicts}
                className="px-3 py-1.5 rounded-lg border border-border text-xs text-gray-300 hover:text-white flex items-center gap-1.5 hover:bg-surface transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingConflicts ? "animate-spin" : ""}`} /> Refresh
              </button>
              <button
                onClick={handleRunDetection}
                disabled={detectingConflicts || documents.length < 2}
                className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-medium text-xs transition flex items-center gap-1.5 shadow-sm"
              >
                {detectingConflicts ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Analyzing Records...
                  </>
                ) : (
                  <>
                    <Sliders className="w-3.5 h-3.5" /> Run Conflict Detection
                  </>
                )}
              </button>
            </div>
          </div>

          {detectionMessage && (
            <div className="mt-4 p-3 rounded-lg bg-amber-950/40 border border-amber-800/50 text-xs text-amber-300 flex items-center gap-2">
              <Info className="w-4 h-4 shrink-0 text-amber-400" />
              <span>{detectionMessage}</span>
            </div>
          )}

          {/* Conflicts List */}
          <div className="mt-6">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400" /> Detected Discrepancies ({conflicts.length})
              </h3>
              <span className="text-[11px] font-mono text-gray-400">Identity scope: {activeIdentity}</span>
            </div>

            {conflicts.length === 0 ? (
              <div className="py-12 text-center text-sm text-gray-400 border border-dashed border-border rounded-xl bg-surface/30">
                <GitCompare className="w-8 h-8 text-gray-500 mx-auto mb-2 opacity-50" />
                <p className="font-medium text-gray-300">No Discrepancies Found</p>
                <p className="text-xs text-gray-500 mt-1 max-w-md mx-auto">
                  {documents.length < 2
                    ? "Upload at least 2 completed documents in Module 4 above to execute pairwise cross-document verification."
                    : "No conflicts detected across your uploaded documents. All mutually comparable fields match or are compatible."}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-border bg-surface/80">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-border/80 bg-slate-900/60 text-gray-400">
                      <th className="py-3 px-4">Severity & Field</th>
                      <th className="py-3 px-4">Discrepancy (Value A vs Value B)</th>
                      <th className="py-3 px-4">Method & Score</th>
                      <th className="py-3 px-4">Explanation</th>
                      <th className="py-3 px-4">Review Status</th>
                      <th className="py-3 px-4 text-right">Details</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/40 text-gray-300">
                    {conflicts.map((conf) => {
                      const sevClass =
                        conf.severity === "critical"
                          ? "bg-rose-950/80 text-rose-400 border-rose-800/60"
                          : conf.severity === "high"
                          ? "bg-orange-950/80 text-orange-400 border-orange-800/60"
                          : conf.severity === "medium"
                          ? "bg-amber-950/80 text-amber-400 border-amber-800/60"
                          : "bg-blue-950/80 text-blue-400 border-blue-800/60";

                      return (
                        <tr key={conf.id} className="hover:bg-slate-900/40 transition">
                          <td className="py-3 px-4 whitespace-nowrap">
                            <div className="flex flex-col gap-1">
                              <span className={`inline-block w-fit px-2 py-0.5 rounded text-[10px] font-semibold border ${sevClass}`}>
                                {conf.severity.toUpperCase()}
                              </span>
                              <span className="font-mono text-gray-200 font-semibold">{conf.field_name}</span>
                              <span className="text-[10px] text-gray-400 font-mono">Type: {conf.conflict_type}</span>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex flex-col gap-1 text-xs">
                              <div className="flex items-center gap-1.5">
                                <span className="text-[10px] font-mono text-gray-400 uppercase">Doc A:</span>
                                <span className="font-medium text-white">{conf.value_a}</span>
                              </div>
                              <div className="flex items-center gap-1.5">
                                <span className="text-[10px] font-mono text-gray-400 uppercase">Doc B:</span>
                                <span className="font-medium text-amber-300">{conf.value_b}</span>
                              </div>
                            </div>
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <div className="flex flex-col gap-0.5">
                              <span className="text-gray-300 font-medium">{conf.comparison_method || "deterministic"}</span>
                              <span className="text-[11px] font-mono text-indigo-400">
                                {conf.similarity_score !== null && conf.similarity_score !== undefined
                                  ? `Score: ${conf.similarity_score}%`
                                  : "Score: N/A"}
                              </span>
                            </div>
                          </td>
                          <td className="py-3 px-4 max-w-xs text-gray-300 text-xs">
                            <p className="line-clamp-2" title={conf.description}>{conf.description}</p>
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            <select
                              value={conf.status}
                              onChange={(e) => handleUpdateReviewStatus(conf.id, e.target.value)}
                              className="bg-slate-900 border border-border text-gray-200 text-xs rounded-lg px-2.5 py-1 focus:outline-none focus:border-amber-500 cursor-pointer"
                            >
                              <option value="detected">Detected</option>
                              <option value="in_review">In Review</option>
                              <option value="resolved">Resolved</option>
                              <option value="ignored">Ignored</option>
                            </select>
                          </td>
                          <td className="py-3 px-4 text-right whitespace-nowrap">
                            <button
                              onClick={() => setActiveConflictDetail(conf)}
                              className="px-2.5 py-1 rounded bg-surface hover:bg-slate-800 border border-border text-gray-300 hover:text-white transition text-xs inline-flex items-center gap-1"
                            >
                              <Eye className="w-3.5 h-3.5 text-indigo-400" /> View
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Conflict Inspection Detail Modal */}
          {activeConflictDetail && (
            <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-border rounded-2xl max-w-lg w-full p-6 shadow-2xl relative text-left">
                <div className="flex items-start justify-between pb-4 border-b border-border">
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-400 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-800/60">
                      Discrepancy Inspection
                    </span>
                    <h3 className="text-lg font-semibold text-white mt-1.5 flex items-center gap-2">
                      <GitCompare className="w-4 h-4 text-amber-400" /> Field: {activeConflictDetail.field_name}
                    </h3>
                  </div>
                  <button
                    onClick={() => setActiveConflictDetail(null)}
                    className="p-1 rounded-lg text-gray-400 hover:text-white hover:bg-surface transition"
                  >
                    ✕
                  </button>
                </div>

                <div className="mt-4 space-y-3 text-xs">
                  <div className="p-3 rounded-lg bg-surface/80 border border-border space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Severity:</span>
                      <span className="font-semibold uppercase text-rose-400">{activeConflictDetail.severity}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Classification:</span>
                      <span className="font-mono text-gray-300">{activeConflictDetail.conflict_type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Comparison Engine:</span>
                      <span className="font-medium text-gray-300">{activeConflictDetail.comparison_method}</span>
                    </div>
                    {activeConflictDetail.similarity_score !== null && (
                      <div className="flex justify-between">
                        <span className="text-gray-400">Similarity Metric:</span>
                        <span className="font-mono text-indigo-400">{activeConflictDetail.similarity_score}%</span>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-slate-950/80 border border-border">
                      <span className="text-[10px] uppercase font-mono text-gray-400">Document A Value</span>
                      <p className="font-semibold text-white mt-1 break-words">{activeConflictDetail.value_a}</p>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-950/80 border border-border">
                      <span className="text-[10px] uppercase font-mono text-gray-400">Document B Value</span>
                      <p className="font-semibold text-amber-300 mt-1 break-words">{activeConflictDetail.value_b}</p>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-slate-950/80 border border-border">
                    <span className="text-[10px] uppercase font-mono text-gray-400">Explainable Analysis</span>
                    <p className="text-gray-300 mt-1 leading-relaxed">{activeConflictDetail.description}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-surface/60 border border-border flex items-center justify-between">
                    <div>
                      <span className="text-gray-400 block text-[10px]">Review Status</span>
                      <span className="font-medium text-white capitalize">{activeConflictDetail.status}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {["detected", "in_review", "resolved", "ignored"].map((st) => (
                        <button
                          key={st}
                          onClick={() => handleUpdateReviewStatus(activeConflictDetail.id, st)}
                          className={`px-2 py-1 rounded text-[10px] font-medium transition ${
                            activeConflictDetail.status === st
                              ? "bg-amber-600 text-white"
                              : "bg-surface hover:bg-slate-800 text-gray-400 border border-border"
                          }`}
                        >
                          {st.replace("_", " ")}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="text-[10px] text-gray-500 pt-1">
                    Conflict Record ID: <span className="font-mono text-gray-400">{activeConflictDetail.id}</span>
                  </div>
                </div>

                <div className="mt-5 pt-3 border-t border-border flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        const c = activeConflictDetail;
                        setActiveConflictDetail(null);
                        handleExplainConflict(c);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 border border-indigo-500/50 text-xs text-indigo-300 flex items-center gap-1.5 transition"
                    >
                      <Bot className="w-3.5 h-3.5" /> Explain with AI
                    </button>
                    <button
                      onClick={() => {
                        const c = activeConflictDetail;
                        setActiveConflictDetail(null);
                        handleResolveConflict(c);
                      }}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600/30 hover:bg-emerald-600/50 border border-emerald-500/50 text-xs text-emerald-300 flex items-center gap-1.5 transition"
                    >
                      <Sparkles className="w-3.5 h-3.5" /> Step-by-Step Resolution
                    </button>
                  </div>
                  <button
                    onClick={() => setActiveConflictDetail(null)}
                    className="px-4 py-1.5 rounded-lg bg-surface hover:bg-slate-800 border border-border text-xs text-white transition"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Module 6: Advanced Context-Aware RAG & AI Resolution Assistant */}
        <section className="mt-8 p-6 rounded-2xl bg-surface/30 border border-border">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-border/60">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-wider text-indigo-400 font-semibold flex items-center gap-1.5">
                <Bot className="w-3.5 h-3.5" /> Module 6 — Active
              </span>
              <h2 className="text-xl font-bold text-white mt-1">Context-Aware AI Resolution Assistant & RAG</h2>
              <p className="text-xs text-gray-400 mt-0.5">
                Multi-category hybrid retrieval (Qdrant 1024-dim dense + lexical boost) grounded in official UIDAI, NSDL, MEA, and EPFO procedures.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={fetchOfficialForms}
                disabled={loadingForms}
                className="px-3.5 py-2 rounded-xl bg-surface hover:bg-slate-800 border border-border text-xs font-medium text-gray-200 flex items-center gap-2 transition"
              >
                <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                {loadingForms ? "Loading Forms..." : "Official Forms Catalog"}
              </button>
            </div>
          </div>

          {/* Active Context Banner */}
          {activeAssistantConflict && (
            <div className="mt-4 p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/30 flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
                <span className="text-gray-300">
                  Active Discrepancy Context: <strong className="text-white">{activeAssistantConflict.field_name}</strong> ({activeAssistantConflict.value_a} vs {activeAssistantConflict.value_b})
                </span>
              </div>
              <button
                onClick={() => setActiveAssistantConflict(null)}
                className="text-gray-400 hover:text-white underline text-[11px]"
              >
                Clear Context
              </button>
            </div>
          )}

          {/* Assistant Chat Console */}
          <div className="mt-5 grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 flex flex-col h-[520px] rounded-xl bg-slate-950/60 border border-border overflow-hidden">
              {/* Messages viewport */}
              <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs">
                {chatMessages.length === 0 ? (
                  <div className="h-full flex flex-col items-center justify-center text-center p-6 text-gray-400">
                    <Bot className="w-10 h-10 text-indigo-400 mb-2 opacity-60" />
                    <p className="font-medium text-sm text-gray-300">AI Document Correction Assistant</p>
                    <p className="text-xs text-gray-500 max-w-sm mt-1">
                      Ask about document discrepancies, official UIDAI / NSDL / Passport / EPF update procedures, forms, or potential future verification risks.
                    </p>
                    <div className="flex flex-wrap gap-2 mt-4 justify-center">
                      {[
                        "How do I correct my name in PAN card?",
                        "What is Aadhaar update lifetime limit?",
                        "What is Joint Declaration for EPFO?",
                        "What documents are needed for minor name change in Passport?"
                      ].map((promptText, i) => (
                        <button
                          key={i}
                          onClick={() => {
                            setChatInput(promptText);
                          }}
                          className="px-2.5 py-1 rounded-full bg-surface hover:bg-slate-800 border border-border text-[11px] text-gray-300 transition"
                        >
                          {promptText}
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  chatMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex flex-col ${
                        msg.role === "user" ? "items-end" : "items-start"
                      }`}
                    >
                      <div
                        className={`max-w-[88%] p-3.5 rounded-2xl ${
                          msg.role === "user"
                            ? "bg-indigo-600 text-white rounded-br-none"
                            : "bg-surface/80 border border-border text-gray-200 rounded-bl-none"
                        }`}
                      >
                        <p className="whitespace-pre-line leading-relaxed">{msg.content}</p>

                        {/* Structured Output Components (Resolution steps, forms, citations) */}
                        {msg.response && (
                          <div className="mt-3 pt-3 border-t border-border/40 space-y-3">
                            {/* Resolution Steps */}
                            {msg.response.resolution_steps && msg.response.resolution_steps.length > 0 && (
                              <div>
                                <span className="font-semibold text-emerald-400 text-[11px] block mb-1.5 flex items-center gap-1">
                                  <Sparkles className="w-3 h-3" /> Grounded Resolution Steps:
                                </span>
                                <ol className="space-y-1.5 pl-4 list-decimal text-[11px] text-gray-300">
                                  {msg.response.resolution_steps.map((st: any, sIdx: number) => (
                                    <li key={sIdx}>
                                      <strong>{st.title}:</strong> {st.description}
                                      {st.required_documents && st.required_documents.length > 0 && (
                                        <div className="text-[10px] text-gray-400 mt-0.5">
                                          Docs: {st.required_documents.join(", ")}
                                        </div>
                                      )}
                                    </li>
                                  ))}
                                </ol>
                              </div>
                            )}

                            {/* Relevant Forms */}
                            {msg.response.relevant_forms && msg.response.relevant_forms.length > 0 && (
                              <div>
                                <span className="font-semibold text-blue-400 text-[11px] block mb-1">
                                  Official Government Form:
                                </span>
                                <div className="space-y-1">
                                  {msg.response.relevant_forms.map((f: any, fIdx: number) => (
                                    <a
                                      key={fIdx}
                                      href={f.official_download_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-blue-950/60 border border-blue-500/40 text-blue-300 hover:text-white text-[10px] transition"
                                    >
                                      <FileText className="w-3 h-3" />
                                      {f.form_name}
                                      <ExternalLink className="w-2.5 h-2.5" />
                                    </a>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Traceable Citations */}
                            {msg.response.citations && msg.response.citations.length > 0 && (
                              <div className="pt-1">
                                <span className="text-[10px] uppercase font-mono text-gray-400 block mb-1">
                                  Official Citations:
                                </span>
                                <div className="flex flex-wrap gap-1.5">
                                  {msg.response.citations.map((c: any, cIdx: number) => (
                                    <a
                                      key={cIdx}
                                      href={c.source_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="px-2 py-0.5 rounded bg-slate-900 border border-border text-gray-300 hover:text-indigo-300 text-[10px] flex items-center gap-1 transition"
                                    >
                                      <span>{c.issuing_authority}</span>
                                      <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                                    </a>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
                {sendingChat && (
                  <div className="flex items-center gap-2 text-indigo-400 text-xs">
                    <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
                    Searching verified government knowledge and formulating grounded response...
                  </div>
                )}
              </div>

              {/* Chat Input form */}
              <form onSubmit={handleSendChatMessage} className="p-3 bg-surface/60 border-t border-border flex items-center gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask the AI Resolution Assistant..."
                  disabled={sendingChat}
                  className="flex-1 bg-slate-950 border border-border rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
                <button
                  type="submit"
                  disabled={sendingChat || !chatInput.trim()}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs flex items-center gap-1.5 transition"
                >
                  <Send className="w-3.5 h-3.5" /> Send
                </button>
              </form>
            </div>

            {/* Official Forms & Guidelines Sidebar */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-border flex flex-col h-[520px] overflow-hidden">
              <h4 className="text-xs font-semibold text-gray-300 flex items-center gap-1.5 pb-2 border-b border-border">
                <BookOpen className="w-3.5 h-3.5 text-blue-400" /> Official Government Forms
              </h4>
              <div className="flex-1 overflow-y-auto mt-3 space-y-2.5 text-xs pr-1">
                {officialForms.length === 0 ? (
                  <div className="p-4 text-center text-gray-500">
                    Click &ldquo;Official Forms Catalog&rdquo; above to load verified downloadable forms.
                  </div>
                ) : (
                  officialForms.map((frm) => (
                    <div key={frm.form_id} className="p-2.5 rounded-lg bg-surface/50 border border-border flex flex-col gap-1">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-900">
                          {frm.document_category}
                        </span>
                        <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                          <CheckCircle2 className="w-2.5 h-2.5" /> verified
                        </span>
                      </div>
                      <p className="font-medium text-white text-[11px] mt-0.5">{frm.form_name}</p>
                      <p className="text-[10px] text-gray-400 line-clamp-2">{frm.purpose}</p>
                      <div className="mt-1 flex items-center justify-between pt-1 border-t border-border/40">
                        <span className="text-[9px] text-gray-500">{frm.issuing_authority}</span>
                        <a
                          href={frm.official_download_url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[10px] text-indigo-400 hover:text-white flex items-center gap-1"
                        >
                          Download <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Module 7: Correction Document Generator Workspace */}
        <section className="mt-8 p-6 rounded-2xl bg-surface/80 border border-border backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/60">
            <div>
              <div className="flex items-center gap-2">
                <FileEdit className="w-5 h-5 text-indigo-400" />
                <h2 className="text-base font-semibold text-white">Module 7: Correction Document Generator Workspace</h2>
                <span className="text-xs px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                  Gemini-Only
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Prepare official correction request letters, checklists, and declaration drafts grounded in verified government circulars with forced Row-Level Security.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => fetchDrafts(activeIdentity)}
                disabled={loadingDrafts}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-200 bg-surface border border-border rounded-lg hover:bg-surface-card transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingDrafts ? "animate-spin text-indigo-400" : ""}`} />
                Refresh Saved Drafts
              </button>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Step 1 & 2: Conflict Selection & Case Confirmation (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-border space-y-3">
                <h4 className="text-xs font-semibold text-gray-200 flex items-center justify-between">
                  <span>1. Select Discrepancy Case</span>
                  <span className="text-[10px] text-gray-400">{conflicts.length} detected</span>
                </h4>

                {conflicts.length === 0 ? (
                  <div className="p-4 rounded-lg bg-surface/30 border border-border/60 text-center text-xs text-gray-500">
                    No discrepancies detected yet. Upload documents in Module 4 to analyze.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {conflicts.map((c) => {
                      const isSelected = selectedConflictForDraft?.id === c.id;
                      return (
                        <div
                          key={c.id}
                          onClick={() => {
                            setSelectedConflictForDraft(c);
                            setConfirmedRequestedValue(c.value_a);
                          }}
                          className={`p-3 rounded-lg border text-xs cursor-pointer transition flex flex-col gap-1 ${
                            isSelected
                              ? "bg-indigo-950/40 border-indigo-500 text-white shadow-sm shadow-indigo-500/20"
                              : "bg-surface/50 border-border text-gray-300 hover:bg-surface-card"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold capitalize text-indigo-300">
                              {c.field_name.replace("_", " ")} Mismatch
                            </span>
                            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface border border-border text-gray-400 uppercase">
                              {c.severity}
                            </span>
                          </div>
                          <div className="text-[11px] text-gray-400 flex items-center justify-between mt-1">
                            <span>Doc A: <strong className="text-gray-200">{c.value_a}</strong></span>
                            <span>Doc B: <strong className="text-rose-300">{c.value_b}</strong></span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Step 2: Information Confirmation Form */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-border space-y-3">
                <h4 className="text-xs font-semibold text-gray-200">2. Case & Document Specifications</h4>

                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Target Document Type:</label>
                  <select
                    value={draftDocType}
                    onChange={(e) => setDraftDocType(e.target.value)}
                    className="w-full text-xs p-2 rounded-lg bg-surface border border-border text-gray-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="correction_request_letter">Formal Correction Request Letter</option>
                    <option value="supporting_document_checklist">Supporting Document Checklist & Guide</option>
                    <option value="declaration_draft">Self-Declaration / Affidavit Format</option>
                    <option value="general_correction_application">General Rectification Application</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Applicant Full Name (Confirmed):</label>
                  <input
                    type="text"
                    value={confirmedApplicantName}
                    onChange={(e) => setConfirmedApplicantName(e.target.value)}
                    placeholder="e.g. RAJESH KUMAR SHARMA"
                    className="w-full text-xs p-2 rounded-lg bg-surface border border-border text-gray-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Requested Correct Value:</label>
                  <input
                    type="text"
                    value={confirmedRequestedValue}
                    onChange={(e) => setConfirmedRequestedValue(e.target.value)}
                    placeholder="Enter the accurate, user-verified value"
                    className="w-full text-xs p-2 rounded-lg bg-surface border border-border text-gray-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Context / Explanation for Authority:</label>
                  <textarea
                    rows={2}
                    value={userDraftExplanation}
                    onChange={(e) => setUserDraftExplanation(e.target.value)}
                    placeholder="Brief explanation (e.g. Typographical error during initial card issuance)"
                    className="w-full text-xs p-2 rounded-lg bg-surface border border-border text-gray-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>

                {draftError && (
                  <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-xs text-rose-300 flex items-start gap-2">
                    <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                    <span>{draftError}</span>
                  </div>
                )}

                <button
                  onClick={handleGenerateDraft}
                  disabled={generatingDraft || !selectedConflictForDraft}
                  className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-2 transition disabled:opacity-50 shadow-md shadow-indigo-600/20"
                >
                  <Sparkles className={`w-4 h-4 ${generatingDraft ? "animate-spin" : ""}`} />
                  {generatingDraft ? "Generating Draft via Gemini..." : "Generate Grounded Correction Draft"}
                </button>
              </div>

              {/* Saved Drafts List */}
              <div className="p-4 rounded-xl bg-slate-950/60 border border-border">
                <h4 className="text-xs font-semibold text-gray-200 mb-2">Saved Citizen Drafts ({draftList.length})</h4>
                {draftList.length === 0 ? (
                  <p className="text-xs text-gray-500 italic">No drafts generated yet.</p>
                ) : (
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
                    {draftList.map((d) => (
                      <div
                        key={d.id}
                        className={`p-2.5 rounded-lg border text-xs flex items-center justify-between ${
                          activeDraft?.id === d.id
                            ? "bg-indigo-950/40 border-indigo-500 text-white"
                            : "bg-surface/40 border-border text-gray-300"
                        }`}
                      >
                        <div
                          className="flex-1 cursor-pointer truncate mr-2"
                          onClick={() => {
                            setActiveDraft(d);
                            setEditingContent(d.content);
                          }}
                        >
                          <p className="font-medium truncate">{d.title}</p>
                          <span className="text-[10px] text-gray-400 font-mono">v{d.version} • {d.status}</span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <button
                            title="Download PDF"
                            onClick={() => handleDownloadDraft(d.id, "pdf")}
                            className="p-1 rounded bg-surface hover:bg-indigo-600/20 text-gray-300 hover:text-indigo-300"
                          >
                            <FileDown className="w-3.5 h-3.5" />
                          </button>
                          <button
                            title="Delete Draft"
                            onClick={() => handleDeleteDraft(d.id)}
                            className="p-1 rounded bg-surface hover:bg-rose-950 text-gray-400 hover:text-rose-400"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Step 3: Draft Editor & Download Actions (7 cols) */}
            <div className="lg:col-span-7 flex flex-col h-full space-y-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-border flex flex-col flex-1 h-[620px]">
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-indigo-400" />
                    <span className="text-xs font-semibold text-white">
                      {activeDraft ? activeDraft.title : "Draft Document Preview & Editor"}
                    </span>
                    {activeDraft && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-400 border border-indigo-900">
                        Version {activeDraft.version}
                      </span>
                    )}
                  </div>

                  {activeDraft && (
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleDownloadDraft(activeDraft.id, "pdf")}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600 hover:text-white transition"
                      >
                        <Download className="w-3.5 h-3.5" /> PDF
                      </button>
                      <button
                        onClick={() => handleDownloadDraft(activeDraft.id, "docx")}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg bg-blue-600/20 text-blue-300 border border-blue-500/30 hover:bg-blue-600 hover:text-white transition"
                      >
                        <Download className="w-3.5 h-3.5" /> DOCX
                      </button>
                    </div>
                  )}
                </div>

                {/* Validation Warnings Banner */}
                {activeDraft?.validation_status?.warnings && activeDraft.validation_status.warnings.length > 0 && (
                  <div className="mt-3 p-2.5 rounded-lg bg-amber-950/30 border border-amber-800/40 text-xs text-amber-300 space-y-1">
                    <div className="font-semibold flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-400" /> Validation Notice:
                    </div>
                    <ul className="list-disc list-inside text-[11px] text-amber-200/80">
                      {activeDraft.validation_status.warnings.map((w: string, idx: number) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Textarea Editor */}
                <div className="flex-1 mt-3 flex flex-col">
                  {activeDraft ? (
                    <textarea
                      value={editingContent}
                      onChange={(e) => setEditingContent(e.target.value)}
                      className="w-full flex-1 p-3 rounded-lg bg-surface border border-border text-gray-200 font-mono text-xs leading-relaxed focus:outline-none focus:border-indigo-500 resize-none"
                    />
                  ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-center p-8 text-gray-500 text-xs">
                      <FileEdit className="w-8 h-8 text-gray-600 mb-2" />
                      <p>Select a conflict and click &ldquo;Generate Grounded Correction Draft&rdquo;.</p>
                      <p className="text-[11px] text-gray-600 mt-1">Generated drafts can be edited, versioned, and exported to PDF/DOCX.</p>
                    </div>
                  )}
                </div>

                {/* Footer Controls */}
                {activeDraft && (
                  <div className="mt-3 pt-3 border-t border-border flex items-center justify-between">
                    <div className="text-[11px] text-emerald-400 flex items-center gap-1">
                      {saveSuccessMsg && (
                        <>
                          <CheckCircle2 className="w-3 h-3" />
                          <span>{saveSuccessMsg}</span>
                        </>
                      )}
                    </div>
                    <button
                      onClick={handleSaveDraftEdit}
                      disabled={savingEdit}
                      className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition disabled:opacity-50"
                    >
                      {savingEdit ? "Saving Version..." : "Save Edits as New Version"}
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* ========================================================================= */}
        {/* MODULE 8: OFFICER VERIFICATION WORKFLOW CONSOLE */}
        {/* ========================================================================= */}
        <section className="mt-8 p-6 rounded-2xl bg-surface/60 border border-border backdrop-blur-md shadow-xl relative overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-border/60">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  MODULE 8 VERIFIED
                </span>
                <span className="text-xs text-gray-400">Assigned Case Verification & Immutable Audit Trail</span>
              </div>
              <h2 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
                <ClipboardCheck className="w-5 h-5 text-emerald-400" /> Officer Verification Workspace
              </h2>
            </div>

            {/* Role-adaptive tab indicator */}
            <div className="flex items-center gap-2 text-xs">
              <span className="text-gray-400">Active Console View:</span>
              <span className="px-3 py-1 rounded-full bg-surface border border-border font-mono text-emerald-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                {activeIdentity.toUpperCase()} PERSPECTIVE
              </span>
            </div>
          </div>

          {/* Action alerts */}
          {actionSuccessMsg && (
            <div className="mt-4 p-3 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{actionSuccessMsg}</span>
            </div>
          )}
          {actionErrorMsg && (
            <div className="mt-4 p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{actionErrorMsg}</span>
            </div>
          )}

          {/* 1. CITIZEN VIEW: My Submitted Cases & Review Requests */}
          {activeIdentity === "citizen" && (
            <div className="mt-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">My Submitted Verification Cases</h3>
                  <p className="text-xs text-gray-400">Track verification status, review decisions, and reply to officer requests.</p>
                </div>
                <div className="flex gap-2">
                  {draftList.length > 0 && (
                    <button
                      onClick={() => handleCitizenSubmitCase(`Verification for Draft: ${draftList[0].title}`, draftList[0].conflict_id, draftList[0].id)}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition flex items-center gap-1.5 shadow"
                    >
                      <Send className="w-3.5 h-3.5" /> Submit Latest Draft for Review
                    </button>
                  )}
                  <button
                    onClick={fetchCitizenCases}
                    className="p-1.5 rounded-lg bg-surface border border-border text-gray-400 hover:text-white transition"
                    title="Refresh cases"
                  >
                    <RefreshCw className={`w-4 h-4 ${loadingCases ? "animate-spin" : ""}`} />
                  </button>
                </div>
              </div>

              {citizenCases.length === 0 ? (
                <div className="p-8 rounded-xl border border-dashed border-border text-center text-gray-400 text-xs">
                  <FileSearch className="w-8 h-8 text-gray-500 mx-auto mb-2 opacity-60" />
                  No verification cases submitted yet. Generate a correction draft above and click &quot;Submit Latest Draft for Review&quot;.
                </div>
              ) : (
                <div className="space-y-4">
                  {citizenCases.map((cs) => (
                    <div key={cs.id} className="p-4 rounded-xl bg-surface/50 border border-border/80">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white text-sm">{cs.title}</span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-surface border border-border text-gray-300">
                            ID: {cs.id.slice(0, 8)}
                          </span>
                        </div>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          cs.status === "approved" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                          cs.status === "rejected" ? "bg-rose-950 text-rose-400 border border-rose-800" :
                          cs.status === "additional_information_requested" ? "bg-amber-950 text-amber-400 border border-amber-800 animate-pulse" :
                          "bg-blue-950 text-blue-400 border border-blue-800"
                        }`}>
                          {cs.status.replace(/_/g, " ").toUpperCase()}
                        </span>
                      </div>

                      {cs.evidence_notes && (
                        <p className="text-xs text-gray-400 mb-2">Citizen Note: {cs.evidence_notes}</p>
                      )}

                      {/* Decision Details if finalized */}
                      {cs.decision && (
                        <div className="mt-3 p-3 rounded-lg bg-surface/80 border border-border text-xs">
                          <div className="font-semibold text-white flex items-center gap-1.5 mb-1">
                            {cs.decision === "approved" ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <XCircle className="w-3.5 h-3.5 text-rose-400" />}
                            Officer Review Outcome: {cs.decision.toUpperCase()}
                          </div>
                          <p className="text-gray-300">{cs.decision_reason}</p>
                          <p className="text-[10px] text-gray-500 mt-1 italic">
                            *Note: This is an application verification outcome assisting your government submission, not an official statutory decree.
                          </p>
                        </div>
                      )}

                      {/* Clarification prompt if requested */}
                      {cs.status === "additional_information_requested" && (
                        <div className="mt-3 p-3 rounded-lg bg-amber-950/40 border border-amber-800/80">
                          <div className="flex items-center gap-1.5 text-amber-400 text-xs font-semibold mb-2">
                            <HelpCircle className="w-4 h-4" /> Officer Clarification Requested
                          </div>
                          <div className="space-y-2">
                            <textarea
                              value={citizenClarificationText}
                              onChange={(e) => setCitizenClarificationText(e.target.value)}
                              placeholder="Provide clarification explanation or reference additional documents..."
                              rows={2}
                              className="w-full px-3 py-2 rounded-lg bg-background border border-border text-xs text-white placeholder-gray-500 focus:outline-none focus:border-amber-500"
                            />
                            <button
                              onClick={() => handleCitizenRespondClarification(cs.id, cs.review_requests?.[0]?.id || "active")}
                              disabled={submittingClarification || !citizenClarificationText.trim()}
                              className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium transition disabled:opacity-50"
                            >
                              {submittingClarification ? "Submitting..." : "Send Response to Officer"}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* 2. OFFICER VIEW: Assigned Cases & Case Dossier Workspace */}
          {activeIdentity === "officer" && (
            <div className="mt-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
              {/* Left Column: Assigned Case Queue */}
              <div className="lg:col-span-4 space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-border">
                  <span className="text-xs font-semibold text-white">Assigned Queue ({officerCases.length})</span>
                  <button
                    onClick={fetchOfficerCasesList}
                    className="p-1 rounded bg-surface border border-border text-gray-400 hover:text-white"
                    title="Refresh queue"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${loadingCases ? "animate-spin" : ""}`} />
                  </button>
                </div>

                {officerCases.length === 0 ? (
                  <div className="p-6 rounded-xl border border-dashed border-border text-center text-xs text-gray-500">
                    No cases assigned to your officer account. Switch to Admin simulator to assign pending cases.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
                    {officerCases.map((c) => (
                      <div
                        key={c.id}
                        onClick={() => fetchDossier(c.id)}
                        className={`p-3 rounded-xl border transition cursor-pointer text-xs ${
                          activeDossier?.case?.id === c.id
                            ? "bg-emerald-950/40 border-emerald-700/80 text-white"
                            : "bg-surface/40 border-border text-gray-300 hover:bg-surface"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium truncate max-w-[160px]">{c.title}</span>
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface border border-border">
                            {c.status.slice(0, 10)}
                          </span>
                        </div>
                        <div className="text-[10px] text-gray-500">Updated: {new Date(c.updated_at).toLocaleTimeString()}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Right Column: Active Case Dossier Workspace */}
              <div className="lg:col-span-8 p-5 rounded-xl bg-background/50 border border-border space-y-4">
                {loadingDossier ? (
                  <div className="p-12 text-center text-gray-400 text-xs">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-emerald-400" />
                    Loading assigned case dossier under Row-Level Security...
                  </div>
                ) : !activeDossier ? (
                  <div className="p-12 text-center text-gray-500 text-xs">
                    Select a case from the queue on the left to begin verification review.
                  </div>
                ) : (
                  <>
                    {/* Dossier Header */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
                      <div>
                        <h4 className="text-sm font-bold text-white">{activeDossier.case.title}</h4>
                        <span className="text-[11px] font-mono text-gray-400">Case ID: {activeDossier.case.id}</span>
                      </div>
                      <span className="px-3 py-1 rounded-full text-xs font-semibold uppercase bg-surface border border-border text-emerald-400">
                        {activeDossier.case.status.replace(/_/g, " ")}
                      </span>
                    </div>

                    {/* Discrepancy Evidence & OCR vs Confirmed Comparison */}
                    {activeDossier.conflict ? (
                      <div className="p-4 rounded-xl bg-surface/40 border border-border text-xs space-y-2">
                        <div className="font-semibold text-amber-400 flex items-center gap-1.5">
                          <AlertTriangle className="w-3.5 h-3.5" /> Discrepancy Evidence Under Review
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-gray-300">
                          <div>
                            <span className="text-gray-500">Category:</span> {activeDossier.conflict.conflict_type}
                          </div>
                          <div>
                            <span className="text-gray-500">Severity:</span> {activeDossier.conflict.severity}
                          </div>
                          <div className="col-span-2">
                            <span className="text-gray-500">Explanation:</span> {activeDossier.conflict.explanation}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-3 rounded-lg bg-surface/20 border border-border text-xs text-gray-400">
                        No direct conflict linked. Reviewing custom verification submission.
                      </div>
                    )}

                    {/* Correction Draft Content Preview */}
                    {activeDossier.correction_draft && (
                      <div className="p-4 rounded-xl bg-surface/40 border border-border text-xs space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-indigo-400 flex items-center gap-1.5">
                            <FileEdit className="w-3.5 h-3.5" /> Correction Draft v{activeDossier.correction_draft.version}
                          </span>
                          <span className="text-[10px] text-gray-400">Status: {activeDossier.correction_draft.status}</span>
                        </div>
                        <div className="p-3 rounded-lg bg-background/80 font-mono text-[11px] text-gray-300 max-h-36 overflow-y-auto whitespace-pre-wrap border border-border">
                          {activeDossier.correction_draft.content}
                        </div>
                      </div>
                    )}

                    {/* Officer Actions Bar */}
                    <div className="p-4 rounded-xl bg-surface/50 border border-border space-y-3">
                      <span className="text-xs font-semibold text-white">Record Verification Action</span>

                      <div className="space-y-2">
                        <input
                          type="text"
                          value={infoRequestReason}
                          onChange={(e) => setInfoRequestReason(e.target.value)}
                          placeholder="Action reason / Missing document query (e.g., Unclear Class 10 certificate scan)..."
                          className="w-full px-3 py-1.5 rounded-lg bg-background border border-border text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
                        />
                        <textarea
                          value={reviewActionNote}
                          onChange={(e) => setReviewActionNote(e.target.value)}
                          placeholder="Officer justification notes (Mandatory for approvals, rejections, or requests)..."
                          rows={2}
                          className="w-full px-3 py-2 rounded-lg bg-background border border-border text-xs text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500"
                        />
                      </div>

                      <div className="flex flex-wrap gap-2 pt-2">
                        {activeDossier.case.status === "assigned" && (
                          <button
                            onClick={() => handleStartReview(activeDossier.case.id)}
                            className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition"
                          >
                            Start Review
                          </button>
                        )}
                        <button
                          onClick={() => handleRequestInfo(activeDossier.case.id)}
                          className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-medium transition flex items-center gap-1"
                        >
                          <HelpCircle className="w-3.5 h-3.5" /> Request Clarification
                        </button>
                        <button
                          onClick={() => handleOfficerDecision(activeDossier.case.id, "approve")}
                          className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition flex items-center gap-1"
                        >
                          <CheckSquare className="w-3.5 h-3.5" /> Approve Draft
                        </button>
                        <button
                          onClick={() => handleOfficerDecision(activeDossier.case.id, "reject")}
                          className="px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-medium transition flex items-center gap-1"
                        >
                          <XCircle className="w-3.5 h-3.5" /> Reject Draft
                        </button>
                      </div>
                    </div>

                    {/* Immutable Audit Log Trail for this Case */}
                    {activeDossier.audit_events && activeDossier.audit_events.length > 0 && (
                      <div className="p-4 rounded-xl bg-surface/30 border border-border text-xs space-y-2">
                        <div className="font-semibold text-gray-300 flex items-center gap-1.5">
                          <History className="w-3.5 h-3.5 text-blue-400" /> Tamper-Evident SHA-256 Audit Trail ({activeDossier.audit_events.length} Events)
                        </div>
                        <div className="space-y-1.5 max-h-32 overflow-y-auto">
                          {activeDossier.audit_events.map((ev: any) => (
                            <div key={ev.id} className="p-2 rounded bg-background/50 border border-border text-[11px] font-mono flex items-center justify-between text-gray-300">
                              <div>
                                <span className="text-emerald-400 font-bold">{ev.action}</span> by {ev.user_id ? ev.user_id.slice(0, 8) : "system"}
                              </div>
                              <span className="text-[10px] text-gray-500 truncate max-w-[140px]" title={ev.current_hash}>
                                #{ev.current_hash.slice(0, 12)}...
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {/* 3. ADMIN VIEW: Officer Workload & Case Assignment */}
          {activeIdentity === "admin" && (
            <div className="mt-6 space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Case Assignment & Officer Workload Management</h3>
                  <p className="text-xs text-gray-400">Inspect pending cases across all citizens, monitor officer queues, and assign cases.</p>
                </div>
                <button
                  onClick={fetchAdminWorkload}
                  className="p-1.5 rounded-lg bg-surface border border-border text-gray-400 hover:text-white"
                  title="Refresh workload"
                >
                  <RefreshCw className={`w-4 h-4 ${loadingAdminView ? "animate-spin" : ""}`} />
                </button>
              </div>

              {/* Officer Workload Overview Table */}
              <div className="p-4 rounded-xl bg-surface/40 border border-border">
                <span className="text-xs font-semibold text-white mb-3 block">Officer Fleet Workload</span>
                {adminOfficers.length === 0 ? (
                  <div className="text-xs text-gray-500 py-3">No active verification officers found.</div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                    {adminOfficers.map((off) => (
                      <div key={off.officer_id} className="p-3 rounded-lg bg-background/60 border border-border text-xs flex items-center justify-between">
                        <div>
                          <div className="font-semibold text-white">{off.full_name}</div>
                          <div className="text-[10px] text-gray-400">{off.email}</div>
                        </div>
                        <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-indigo-950 text-indigo-300 border border-indigo-800">
                          {off.assigned_count} Active
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Cases Management Table */}
              <div className="p-4 rounded-xl bg-surface/40 border border-border">
                <span className="text-xs font-semibold text-white mb-3 block">All Discrepancy Verification Cases</span>
                {adminCases.length === 0 ? (
                  <div className="text-xs text-gray-500 py-3 text-center">No cases found in system.</div>
                ) : (
                  <div className="space-y-3">
                    {adminCases.map((cs) => (
                      <div key={cs.id} className="p-3 rounded-lg bg-background/60 border border-border text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div>
                          <div className="font-semibold text-white">{cs.title}</div>
                          <div className="text-[10px] text-gray-400 flex items-center gap-2 mt-0.5">
                            <span>Case: {cs.id.slice(0, 8)}</span>
                            <span>•</span>
                            <span>Citizen: {cs.citizen_id.slice(0, 8)}</span>
                            <span>•</span>
                            <span>Assigned Officer: {cs.assigned_officer_id ? cs.assigned_officer_id.slice(0, 8) : "Unassigned"}</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-semibold ${
                            cs.status === "approved" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                            cs.status === "pending_assignment" ? "bg-amber-950 text-amber-400 border border-amber-800" :
                            "bg-surface border border-border text-gray-300"
                          }`}>
                            {cs.status.replace(/_/g, " ")}
                          </span>

                          {/* Assignment Select */}
                          <div className="flex items-center gap-1.5">
                            <select
                              value={selectedCaseToAssign === cs.id ? selectedOfficerForAssign : ""}
                              onChange={(e) => {
                                setSelectedCaseToAssign(cs.id);
                                setSelectedOfficerForAssign(e.target.value);
                              }}
                              className="px-2 py-1 rounded bg-surface border border-border text-xs text-white focus:outline-none"
                            >
                              <option value="">Select Officer...</option>
                              {adminOfficers.map((o) => (
                                <option key={o.officer_id} value={o.officer_id}>{o.full_name}</option>
                              ))}
                            </select>
                            {selectedCaseToAssign === cs.id && selectedOfficerForAssign && (
                              <button
                                onClick={() => handleAdminAssign(cs.id)}
                                className="px-2.5 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition"
                              >
                                Assign
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </section>

        {/* ========================================================================= */}
        {/* MODULE 9: DOCUMENT AUTHENTICITY, Ed25519 PKI & VERIFICATION CONSOLE */}
        {/* ========================================================================= */}
        <section className="mt-8 p-6 rounded-2xl bg-surface/60 border border-border backdrop-blur-md shadow-xl relative overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-border/60">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded text-[11px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  MODULE 9 ACTIVE • Ed25519 PKI
                </span>
                <span className="text-xs text-gray-400">Cryptographic Document Authenticity & Tamper Detection</span>
              </div>
              <h2 className="text-xl font-bold text-white mt-1 flex items-center gap-2">
                <KeyRound className="w-5 h-5 text-cyan-400" /> Document Authenticity & Digital Signatures
              </h2>
              <p className="text-xs text-gray-400 mt-1 max-w-3xl">
                Deterministic SHA-256 fingerprinting, canonical JSON attestations, mathematical Ed25519 verification, and tamper detection with hash-chained audit logging.
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <button
                onClick={() => fetchPKIData(activeIdentity)}
                disabled={loadingPKI}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-200 bg-surface border border-border rounded-lg hover:bg-surface-card transition"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingPKI ? "animate-spin text-cyan-400" : ""}`} />
                Refresh PKI Keystore
              </button>
            </div>
          </div>

          {/* Statutory Authority Disclaimer Notice */}
          <div className="mt-4 p-3 rounded-lg bg-blue-950/40 border border-blue-800/60 text-blue-300 text-xs flex items-center gap-2">
            <Info className="w-4 h-4 shrink-0 text-blue-400" />
            <span>
              <strong>Cryptographic Trust Model Notice:</strong> A valid Ed25519 digital signature establishes that the signed document payload has not been modified since signing and corresponds to a registered public key. It does not constitute statutory government authorization or official certification by UIDAI, NSDL, MEA, EPFO, or CBSE.
            </span>
          </div>

          {/* Action alerts */}
          {pkiSuccessMsg && (
            <div className="mt-4 p-3 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{pkiSuccessMsg}</span>
            </div>
          )}
          {pkiErrorMsg && (
            <div className="mt-4 p-3 rounded-lg bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{pkiErrorMsg}</span>
            </div>
          )}

          {/* PKI Metrics Dashboard Grid */}
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-950/60 border border-border">
              <div className="flex items-center justify-between text-gray-400 text-xs mb-1">
                <span>Total Attestations</span>
                <FileCheck className="w-4 h-4 text-cyan-400" />
              </div>
              <div className="text-2xl font-bold text-white">{pkiStats?.total_attestations ?? 0}</div>
              <div className="text-[10px] text-emerald-400 mt-1">{pkiStats?.valid_attestations ?? 0} Valid in Keystore</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-border">
              <div className="flex items-center justify-between text-gray-400 text-xs mb-1">
                <span>Verifications Performed</span>
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white">{pkiStats?.total_verifications ?? 0}</div>
              <div className="text-[10px] text-gray-400 mt-1">{pkiStats?.valid_verifications ?? 0} Mathematical Checks Passed</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-rose-900/40">
              <div className="flex items-center justify-between text-gray-400 text-xs mb-1">
                <span>Tampering Detected</span>
                <ShieldAlert className="w-4 h-4 text-rose-400" />
              </div>
              <div className="text-2xl font-bold text-rose-400">{pkiStats?.tampered_detections ?? 0}</div>
              <div className="text-[10px] text-rose-400/80 mt-1">SHA-256 Digest Mismatches Blocked</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950/60 border border-border">
              <div className="flex items-center justify-between text-gray-400 text-xs mb-1">
                <span>Active Signing Keys</span>
                <KeyRound className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-white">{pkiStats?.active_keys ?? 0}</div>
              <div className="text-[10px] text-gray-400 mt-1">{pkiStats?.revoked_keys ?? 0} Revoked / Decommissioned</div>
            </div>
          </div>

          {/* Main Workspace (Attestations Directory & Verification Lab) */}
          <div className="mt-6 grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column: Attestations List & Officer Sign Action (5 cols) */}
            <div className="lg:col-span-5 space-y-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-border space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-gray-200 flex items-center gap-1.5">
                    <FileCheck className="w-4 h-4 text-cyan-400" />
                    <span>Signed Attestations Directory</span>
                  </h4>
                  <span className="text-[10px] text-gray-400">{attestations.length} signed records</span>
                </div>

                {attestations.length === 0 ? (
                  <div className="p-6 rounded-lg bg-surface/30 border border-border/60 text-center text-xs text-gray-500">
                    No signed attestations found. Upload documents and sign an attestation below.
                  </div>
                ) : (
                  <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
                    {attestations.map((att) => {
                      const isSelected = selectedAttestation?.id === att.id;
                      return (
                        <div
                          key={att.id}
                          onClick={() => {
                            setSelectedAttestation(att);
                            setVerificationResult(null);
                          }}
                          className={`p-3 rounded-lg border text-xs cursor-pointer transition flex flex-col gap-1.5 ${
                            isSelected
                              ? "bg-cyan-950/40 border-cyan-500 text-white shadow-sm shadow-cyan-500/20"
                              : "bg-surface/40 border-border text-gray-300 hover:border-border/80"
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-semibold uppercase tracking-wider text-[11px] text-cyan-300">
                              {att.document_type} Attestation
                            </span>
                            <span className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-mono ${
                              att.status === "valid" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                              "bg-rose-950 text-rose-400 border border-rose-800"
                            }`}>
                              {att.status}
                            </span>
                          </div>

                          <div className="font-mono text-[10px] text-gray-400 truncate">
                            SHA-256: {att.document_fingerprint.slice(0, 24)}...
                          </div>

                          <div className="flex items-center justify-between text-[10px] text-gray-500 mt-1">
                            <span>Key: {att.key_id}</span>
                            <span>{new Date(att.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {/* Officer Quick Attest Box */}
                {(activeIdentity === "officer" || activeIdentity === "admin") && documents.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-border/60">
                    <span className="text-xs font-semibold text-white mb-2 block">Officer Document Signing Action</span>
                    <p className="text-[11px] text-gray-400 mb-3">
                      Sign an official Ed25519 attestation over a verified document representation.
                    </p>
                    <button
                      onClick={() => handleOfficerAttestDocument()}
                      disabled={attestingDoc}
                      className="w-full py-2 px-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-xs transition flex items-center justify-center gap-2"
                    >
                      <KeyRound className={`w-3.5 h-3.5 ${attestingDoc ? "animate-spin" : ""}`} />
                      {attestingDoc ? "Generating Ed25519 Signature..." : "Sign Document Attestation"}
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Right Column: Verification Dossier & Real-time Verification Lab (7 cols) */}
            <div className="lg:col-span-7 space-y-4">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-border flex flex-col h-full">
                <div className="flex items-center justify-between pb-3 border-b border-border">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-cyan-400" />
                    <span className="text-xs font-semibold text-white">Cryptographic Verification Laboratory</span>
                  </div>
                  {selectedAttestation && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                      Attestation ID: {selectedAttestation.id.slice(0, 8)}
                    </span>
                  )}
                </div>

                {selectedAttestation ? (
                  <div className="mt-4 space-y-4">
                    {/* Attestation Metadata & Canonical Payload */}
                    <div className="p-3 rounded-lg bg-surface/30 border border-border text-xs space-y-2">
                      <div className="grid grid-cols-2 gap-2 text-[11px]">
                        <div>
                          <span className="text-gray-400">Document Type:</span>{" "}
                          <span className="text-white font-semibold uppercase">{selectedAttestation.document_type}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Algorithm:</span>{" "}
                          <span className="text-cyan-400 font-mono font-bold">{selectedAttestation.algorithm}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Signing Key ID:</span>{" "}
                          <span className="text-white font-mono">{selectedAttestation.key_id}</span>
                        </div>
                        <div>
                          <span className="text-gray-400">Issued Timestamp:</span>{" "}
                          <span className="text-gray-300">{new Date(selectedAttestation.created_at).toLocaleString()}</span>
                        </div>
                      </div>

                      <div className="pt-2 border-t border-border/40">
                        <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                          Document SHA-256 Fingerprint
                        </span>
                        <div className="p-2 rounded bg-black/50 border border-border font-mono text-[11px] text-cyan-300 break-all select-all">
                          {selectedAttestation.document_fingerprint}
                        </div>
                      </div>

                      <div className="pt-2 border-t border-border/40">
                        <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                          Ed25519 Digital Signature
                        </span>
                        <div className="p-2 rounded bg-black/50 border border-border font-mono text-[10px] text-gray-400 break-all select-all">
                          {selectedAttestation.signature}
                        </div>
                      </div>

                      <div className="pt-2 border-t border-border/40">
                        <span className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block mb-1">
                          RFC 8785 Canonical JSON Payload
                        </span>
                        <pre className="p-2.5 rounded bg-black/60 border border-border font-mono text-[10px] text-gray-300 overflow-x-auto max-h-36">
                          {JSON.stringify(selectedAttestation.canonical_payload, null, 2)}
                        </pre>
                      </div>
                    </div>

                    {/* Verification Action Buttons */}
                    <div className="p-3 rounded-lg bg-surface/50 border border-border space-y-2">
                      <span className="text-xs font-semibold text-white block">Test Signature & Tamper Detection</span>
                      <p className="text-[11px] text-gray-400">
                        Execute live cryptographic verification to validate mathematical signature correctness and document integrity.
                      </p>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                        <button
                          onClick={() => handleVerifyAttestation(selectedAttestation.id, false)}
                          disabled={verifyingAttestation}
                          className="py-2 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition flex items-center justify-center gap-1.5"
                        >
                          <ShieldCheck className={`w-3.5 h-3.5 ${verifyingAttestation ? "animate-spin" : ""}`} />
                          Verify Authenticity (Intact Document)
                        </button>

                        <button
                          onClick={() => handleVerifyAttestation(selectedAttestation.id, true)}
                          disabled={verifyingAttestation}
                          className="py-2 px-3 rounded-lg bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-rose-300 font-medium text-xs transition flex items-center justify-center gap-1.5"
                        >
                          <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                          Simulate Tampering (Test Rejection)
                        </button>
                      </div>
                    </div>

                    {/* Live Verification Result Banner */}
                    {verificationResult && (
                      <div className={`p-4 rounded-xl border text-xs space-y-3 ${
                        verificationResult.is_valid
                          ? "bg-emerald-950/40 border-emerald-700 text-emerald-200"
                          : "bg-rose-950/50 border-rose-700 text-rose-200"
                      }`}>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {verificationResult.is_valid ? (
                              <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />
                            ) : (
                              <XCircle className="w-5 h-5 text-rose-400 shrink-0" />
                            )}
                            <div>
                              <div className="font-bold uppercase tracking-wider text-sm">
                                {verificationResult.verification_status}
                              </div>
                              <div className="text-[11px] text-gray-300 mt-0.5">
                                {verificationResult.human_readable_summary}
                              </div>
                            </div>
                          </div>
                          <span className="text-[10px] font-mono text-gray-400">
                            {new Date(verificationResult.verified_at).toLocaleTimeString()}
                          </span>
                        </div>

                        {/* Multi-Factor Cryptographic Checks Table */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-border/40 text-[10px]">
                          <div className="p-2 rounded bg-black/40 border border-border/50">
                            <span className="text-gray-400 block">Ed25519 Math</span>
                            <span className={`font-bold font-mono ${verificationResult.signature_valid ? "text-emerald-400" : "text-rose-400"}`}>
                              {verificationResult.signature_valid ? "VALID SIGNATURE" : "FAILED"}
                            </span>
                          </div>

                          <div className="p-2 rounded bg-black/40 border border-border/50">
                            <span className="text-gray-400 block">Document Hash</span>
                            <span className={`font-bold font-mono ${verificationResult.document_integrity_valid ? "text-emerald-400" : "text-rose-400"}`}>
                              {verificationResult.document_integrity_valid ? "MATCHED" : "TAMPERED"}
                            </span>
                          </div>

                          <div className="p-2 rounded bg-black/40 border border-border/50">
                            <span className="text-gray-400 block">Keystore Trust</span>
                            <span className={`font-bold font-mono ${verificationResult.key_trusted ? "text-emerald-400" : "text-amber-400"}`}>
                              {verificationResult.key_trusted ? "TRUSTED KEY" : "UNTRUSTED"}
                            </span>
                          </div>

                          <div className="p-2 rounded bg-black/40 border border-border/50">
                            <span className="text-gray-400 block">Key Status</span>
                            <span className="font-bold font-mono text-gray-200 uppercase">
                              {verificationResult.key_status}
                            </span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="py-20 text-center text-xs text-gray-500">
                    Select an attestation from the left panel to inspect canonical payload and verify authenticity.
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Admin PKI Key Management Section */}
          <div className="mt-8 pt-6 border-t border-border/60">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                  <KeyRound className="w-4 h-4 text-cyan-400" /> PKI Key Management & Lifecycle Keystore
                </h3>
                <p className="text-xs text-gray-400">
                  Inspect registered Ed25519 public keys, rotate active keys, or revoke compromised key identifiers.
                </p>
              </div>

              {activeIdentity === "admin" && (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="New Key ID..."
                    value={newKeyIdInput}
                    onChange={(e) => setNewKeyIdInput(e.target.value)}
                    className="px-2.5 py-1 text-xs rounded bg-surface border border-border text-white focus:outline-none"
                  />
                  <button
                    onClick={() => handleRotateKey(signingKeys[0]?.key_id || "consolith-officer-key-2026-v1")}
                    disabled={rotatingKey || !newKeyIdInput.trim()}
                    className="px-3 py-1 text-xs font-medium rounded bg-cyan-600 hover:bg-cyan-500 text-white disabled:opacity-50 transition"
                  >
                    Rotate Key
                  </button>
                </div>
              )}
            </div>

            <div className="p-4 rounded-xl bg-surface/40 border border-border">
              {signingKeys.length === 0 ? (
                <div className="text-xs text-gray-500 text-center py-4">No signing keys found in keystore.</div>
              ) : (
                <div className="space-y-3">
                  {signingKeys.map((k) => (
                    <div key={k.id} className="p-3 rounded-lg bg-background/60 border border-border text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-white font-mono">{k.key_id}</span>
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            k.status === "active" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                            k.status === "revoked" ? "bg-rose-950 text-rose-400 border border-rose-800" :
                            "bg-surface border border-border text-gray-400"
                          }`}>
                            {k.status}
                          </span>
                        </div>
                        <div className="text-[10px] text-gray-400 font-mono mt-1">
                          Fingerprint: {k.fingerprint}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {activeIdentity === "admin" && k.status === "active" && (
                          <div className="flex items-center gap-1.5">
                            {revokingKeyId === k.key_id ? (
                              <div className="flex items-center gap-1">
                                <input
                                  type="text"
                                  placeholder="Reason for revocation..."
                                  value={revokeReasonInput}
                                  onChange={(e) => setRevokeReasonInput(e.target.value)}
                                  className="px-2 py-0.5 text-[11px] rounded bg-surface border border-border text-white focus:outline-none"
                                />
                                <button
                                  onClick={() => handleRevokeKey(k.key_id)}
                                  className="px-2 py-0.5 rounded bg-rose-600 hover:bg-rose-500 text-white text-[11px] font-semibold"
                                >
                                  Confirm Revoke
                                </button>
                                <button
                                  onClick={() => setRevokingKeyId(null)}
                                  className="px-2 py-0.5 rounded bg-surface border border-border text-gray-400 text-[11px]"
                                >
                                  Cancel
                                </button>
                              </div>
                            ) : (
                              <button
                                onClick={() => {
                                  setRevokingKeyId(k.key_id);
                                  setRevokeReasonInput("");
                                }}
                                className="px-2.5 py-1 rounded bg-rose-950/80 hover:bg-rose-900 border border-rose-800 text-rose-300 text-xs font-medium transition"
                              >
                                Revoke Key
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Verification Audit Trail Log */}
          {recentVerifications.length > 0 && (
            <div className="mt-6 pt-4 border-t border-border/40">
              <span className="text-xs font-semibold text-white mb-2 block flex items-center gap-1.5">
                <History className="w-3.5 h-3.5 text-cyan-400" /> Recent Verification Audit Trail
              </span>
              <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                {recentVerifications.map((v) => (
                  <div key={v.id} className="p-2 rounded bg-surface/30 border border-border/40 text-[11px] flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold font-mono ${
                        v.verification_status === "VALID" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" :
                        "bg-rose-950 text-rose-400 border border-rose-800"
                      }`}>
                        {v.verification_status}
                      </span>
                      <span className="text-gray-300 truncate max-w-xs">{v.details?.summary || "Verification performed"}</span>
                    </div>
                    <span className="text-[10px] text-gray-500 font-mono">
                      {new Date(v.verified_at).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Foundation Overview & Scope Cards */}

        <section className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-xl bg-surface/40 border border-border">
            <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-blue-400" /> Supported Identity Documents (Tier 1)
            </h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> Aadhaar Card (Masked & Encrypted at rest)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> PAN Card (Income Tax Department / NSDL)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> Indian Passport (Passport Seva)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> 10th & 12th Educational Certificates
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> EPFO Records (EPF Member Passbook / UAN)
              </li>
            </ul>
          </div>

          <div className="p-6 rounded-xl bg-surface/40 border border-border">
            <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-3">
              <Lock className="w-4 h-4 text-emerald-400" /> Security & Integrity Architecture
            </h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> PostgreSQL Native Row-Level Security (Forced)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Dedicated Non-Superuser DB Connection (consolith_app)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Server-side Firebase JWT Re-verification on every route
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Append-only tamper-evident audit log with hash chain
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Role escalation defense trigger on users table
              </li>
            </ul>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-border/60 text-xs text-gray-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p>Consolith — Final Year Academic Project</p>
        <p className="font-mono">Tamper-Evident Architecture • Fail-Safe Verification</p>
      </footer>
    </main>
  );
}

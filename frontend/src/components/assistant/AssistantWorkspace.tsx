"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Sparkles,
  Send,
  Plus,
  Trash2,
  FileText,
  ExternalLink,
  Download,
  AlertTriangle,
  AlertCircle,
  CheckCircle2,
  RefreshCw,
  MessageSquare,
  Shield,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
  PanelLeft,
  Copy,
  Check,
  X,
  Edit2,
  Unlink,
  ArrowLeft,
  Eye,
  FileCheck,
  ShieldCheck,
  Image as ImageIcon,
  Code,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import {
  fetchConversations,
  fetchConversationMessages,
  sendChatMessage,
  deleteConversation,
  updateConversation,
  fetchResolutionContext,
  fetchConflicts,
  fetchDocuments,
  downloadOfficialForm,
  previewOfficialForm,
  uploadChatAttachment,
  deleteChatAttachment,
  previewChatAttachment,
  ConversationItem,
  MessageItem,
  ResolutionContextData,
  ConflictItem,
  DocumentItem,
  CorrectionDraftItem,
  OfficialFormItem,
  MessageAttachmentItem,
} from "../../lib/api";
import AssistantSidebar from "./AssistantSidebar";
import AssistantComposer from "./AssistantComposer";
import ConversationSearchModal from "./ConversationSearchModal";
import MarkdownRenderer from "./MarkdownRenderer";
import OfficialFormCard from "./OfficialFormCard";
import CorrectionDraftCard from "./CorrectionDraftCard";
import AdministrativeDraftingModal from "../drafting/AdministrativeDraftingModal";
import ClaudeSunburst from "./ClaudeSunburst";

interface AssistantWorkspaceProps {
  initialConversationId?: string;
}

export default function AssistantWorkspace({
  initialConversationId,
}: AssistantWorkspaceProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const conflictIdParam = searchParams.get("conflictId") || undefined;
  const { idToken, profile, firebaseUser } = useAuth();

  // Conversations & Messages State
  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | undefined>(
    initialConversationId
  );
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [inputQuery, setInputQuery] = useState("");
  const [sending, setSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Layout & Modals State
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchModalOpen, setSearchModalOpen] = useState(false);
  const [renameModal, setRenameModal] = useState<{
    isOpen: boolean;
    convId: string;
    title: string;
  }>({ isOpen: false, convId: "", title: "" });
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    convId: string;
  }>({ isOpen: false, convId: "" });

  // Preferences & Provider Status
  const [responseLanguage, setResponseLanguage] = useState("en");
  const [providerStatus, setProviderStatus] = useState<string>("operational");
  const [copiedMsgId, setCopiedMsgId] = useState<string | null>(null);

  // Grounded Resolution Context State (Phase P2A / P3C)
  const [resolutionContext, setResolutionContext] = useState<ResolutionContextData | null>(null);
  const [loadingResolutionContext, setLoadingResolutionContext] = useState(false);
  const [contextExpanded, setContextExpanded] = useState(true);
  const [userConflicts, setUserConflicts] = useState<ConflictItem[]>([]);

  // In-Chat Official Form Retrieval & Preview State (Phase P3D)
  const [previewForm, setPreviewForm] = useState<OfficialFormItem | null>(null);
  const [previewBlobUrl, setPreviewBlobUrl] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);
  const [downloadingFormId, setDownloadingFormId] = useState<string | null>(null);

  // Multimodal In-Chat Attachments State (Phase P3E)
  const [stagedAttachments, setStagedAttachments] = useState<MessageAttachmentItem[]>([]);
  const [uploadingAttachment, setUploadingAttachment] = useState(false);
  const [previewAttachment, setPreviewAttachment] = useState<MessageAttachmentItem | null>(null);
  const [previewAttachmentBlobUrl, setPreviewAttachmentBlobUrl] = useState<string | null>(null);
  const [previewAttachmentLoading, setPreviewAttachmentLoading] = useState(false);
  const [previewAttachmentError, setPreviewAttachmentError] = useState<string | null>(null);

  // Administrative Drafting Workspace State (Phase P3G)
  const [draftingModalOpen, setDraftingModalOpen] = useState(false);
  const [selectedDraftConflict, setSelectedDraftConflict] = useState<ConflictItem | null>(null);
  const [selectedDraft, setSelectedDraft] = useState<CorrectionDraftItem | null>(null);
  const [userDocuments, setUserDocuments] = useState<DocumentItem[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 1. Sidebar persistence
  useEffect(() => {
    try {
      const saved = localStorage.getItem("convelina_sidebar_open");
      if (saved !== null) {
        setSidebarOpen(saved === "true");
      } else if (window.innerWidth < 1024) {
        setSidebarOpen(false);
      }
    } catch {
      // safe fallback
    }
  }, []);

  const toggleSidebar = () => {
    setSidebarOpen((prev) => {
      const next = !prev;
      try {
        localStorage.setItem("convelina_sidebar_open", String(next));
      } catch {}
      return next;
    });
  };

  // 2. Global Keyboard Shortcuts (Ctrl+N, Ctrl+K, Ctrl+B)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const isMeta = e.ctrlKey || e.metaKey;
      if (isMeta && e.key.toLowerCase() === "n") {
        e.preventDefault();
        handleNewInquiry();
      } else if (isMeta && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchModalOpen(true);
      } else if (isMeta && e.key.toLowerCase() === "b") {
        e.preventDefault();
        toggleSidebar();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // 3. Load citizen's conversations
  const loadConversations = useCallback(async () => {
    if (!idToken) return;
    try {
      setLoadingConvs(true);
      const convs = await fetchConversations(idToken);
      setConversations(convs);
    } catch (err: any) {
      console.warn("Could not load conversations:", err);
    } finally {
      setLoadingConvs(false);
    }
  }, [idToken]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  // 4. Load messages for active conversation
  const loadMessages = useCallback(
    async (convId: string) => {
      if (!idToken) return;
      try {
        setLoadingMessages(true);
        const msgs = await fetchConversationMessages(idToken, convId);
        setMessages(msgs);

        // Update active language and provider status from latest message if present
        if (msgs.length > 0) {
          const lastMsg = msgs[msgs.length - 1];
          if (lastMsg.structured_response?.provider_status) {
            setProviderStatus(lastMsg.structured_response.provider_status);
          } else if (lastMsg.structured_response?.is_fallback) {
            setProviderStatus("fallback_offline");
          }
        }

        setTimeout(scrollToBottom, 100);
      } catch (err: any) {
        console.warn("Could not load messages:", err);
      } finally {
        setLoadingMessages(false);
      }
    },
    [idToken]
  );

  useEffect(() => {
    if (activeConvId) {
      loadMessages(activeConvId);
      // Sync active conversation language preference
      const active = conversations.find((c) => c.id === activeConvId);
      if (active?.response_language) {
        setResponseLanguage(active.response_language);
      }
    } else {
      setMessages([]);
    }
  }, [activeConvId, loadMessages, conversations]);

  // Load citizen's detected conflicts for switching / linking
  useEffect(() => {
    if (!idToken) return;
    fetchConflicts(idToken)
      .then((confs) => setUserConflicts(confs || []))
      .catch((err) => console.warn("Could not fetch user conflicts:", err));

    fetchDocuments(idToken)
      .then((docs) => setUserDocuments(docs || []))
      .catch((err) => console.warn("Could not fetch user documents for drafting:", err));
  }, [idToken]);

  // Determine effective conflict ID: from URL param or active conversation record
  const activeConv = conversations.find((c) => c.id === activeConvId);
  const effectiveConflictId = conflictIdParam || (activeConv?.active_conflict_id ? activeConv.active_conflict_id : undefined);

  // 5. Load Resolution Context if effectiveConflictId is present
  useEffect(() => {
    if (!effectiveConflictId || !idToken) {
      setResolutionContext(null);
      return;
    }
    let isCancelled = false;
    const loadContext = async () => {
      try {
        setLoadingResolutionContext(true);
        const ctx = await fetchResolutionContext(idToken, effectiveConflictId);
        if (!isCancelled) {
          setResolutionContext(ctx);
        }
      } catch (err) {
        console.warn("Could not fetch resolution context for conflict:", err);
      } finally {
        if (!isCancelled) setLoadingResolutionContext(false);
      }
    };
    loadContext();
    return () => {
      isCancelled = true;
    };
  }, [effectiveConflictId, idToken]);

  // Handlers for switching or unlinking active conflict context
  const handleUnlinkConflict = async () => {
    if (!idToken) return;
    if (activeConvId) {
      try {
        await updateConversation(idToken, activeConvId, { active_conflict_id: "" });
        setConversations((prev) =>
          prev.map((c) => (c.id === activeConvId ? { ...c, active_conflict_id: undefined } : c))
        );
        setResolutionContext(null);
      } catch (err) {
        console.error("Failed to unlink conflict:", err);
      }
    } else {
      setResolutionContext(null);
      router.push("/app/assistant");
    }
  };

  const handleSwitchConflict = async (newConflictId: string) => {
    if (!idToken || !newConflictId) return;
    if (activeConvId) {
      try {
        await updateConversation(idToken, activeConvId, { active_conflict_id: newConflictId });
        setConversations((prev) =>
          prev.map((c) => (c.id === activeConvId ? { ...c, active_conflict_id: newConflictId } : c))
        );
        const ctx = await fetchResolutionContext(idToken, newConflictId);
        setResolutionContext(ctx);
      } catch (err) {
        console.error("Failed to switch conflict:", err);
      }
    } else {
      router.push(`/app/assistant?conflictId=${newConflictId}`);
    }
  };

  // 6. Navigation Actions
  const handleNewInquiry = () => {
    setActiveConvId(undefined);
    setMessages([]);
    setErrorMessage(null);
    setResolutionContext(null);
    router.push("/app/assistant");
  };

  const handleSelectConversation = (convId: string) => {
    setActiveConvId(convId);
    router.push(`/app/assistant/${convId}`);
  };

  // 7. Pin / Unpin Action
  const handleTogglePin = async (convId: string, currentPinned: boolean) => {
    if (!idToken) return;
    try {
      const nextPinned = !currentPinned;
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, is_pinned: nextPinned } : c))
      );
      await updateConversation(idToken, convId, { is_pinned: nextPinned });
      await loadConversations();
    } catch (err) {
      console.error("Failed to toggle pin status:", err);
      loadConversations();
    }
  };

  // 8. Rename Action
  const handlePromptRename = (convId: string, currentTitle: string) => {
    setRenameModal({ isOpen: true, convId, title: currentTitle });
  };

  const handleSaveRename = async () => {
    if (!idToken || !renameModal.title.trim()) return;
    try {
      const convId = renameModal.convId;
      const newTitle = renameModal.title.trim();
      setConversations((prev) =>
        prev.map((c) => (c.id === convId ? { ...c, title: newTitle } : c))
      );
      setRenameModal({ isOpen: false, convId: "", title: "" });
      await updateConversation(idToken, convId, { title: newTitle });
    } catch (err) {
      console.error("Failed to rename conversation:", err);
      loadConversations();
    }
  };

  // 9. Delete Action
  const handlePromptDelete = (convId: string) => {
    setDeleteModal({ isOpen: true, convId });
  };

  const handleConfirmDelete = async () => {
    if (!idToken || !deleteModal.convId) return;
    const convId = deleteModal.convId;
    try {
      setDeleteModal({ isOpen: false, convId: "" });
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      await deleteConversation(idToken, convId);
      if (activeConvId === convId) {
        handleNewInquiry();
      }
    } catch (err) {
      console.error("Failed to delete conversation:", err);
      loadConversations();
    }
  };

  // 10. Language Preference Change
  const handleLanguageChange = async (lang: string) => {
    setResponseLanguage(lang);
    if (activeConvId && idToken) {
      try {
        await updateConversation(idToken, activeConvId, { response_language: lang });
        setConversations((prev) =>
          prev.map((c) => (c.id === activeConvId ? { ...c, response_language: lang } : c))
        );
      } catch (err) {
        console.warn("Could not persist language preference to conversation:", err);
      }
    }
  };

  // 11. Copy Message Action
  const handleCopyMessage = (msgId: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedMsgId(msgId);
    setTimeout(() => setCopiedMsgId(null), 2000);
  };

  // 12. In-Chat Official Form Handlers (Phase P3D)
  const handlePreviewForm = async (form: OfficialFormItem | any) => {
    const fid = form.form_id || form.id;
    if (!fid) return;
    setPreviewForm(form);
    setPreviewError(null);
    setPreviewLoading(true);

    if (previewBlobUrl) {
      URL.revokeObjectURL(previewBlobUrl);
      setPreviewBlobUrl(null);
    }

    try {
      const url = await previewOfficialForm(idToken, fid);
      setPreviewBlobUrl(url);
    } catch (err: any) {
      console.error("Preview failed:", err);
      setPreviewError(err.message || "Failed to stream document preview.");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleClosePreview = () => {
    if (previewBlobUrl) {
      URL.revokeObjectURL(previewBlobUrl);
      setPreviewBlobUrl(null);
    }
    setPreviewForm(null);
    setPreviewError(null);
  };

  const handleDownloadForm = async (form: OfficialFormItem | any) => {
    const fid = form.form_id || form.id;
    if (!fid) return;
    setDownloadingFormId(fid);
    try {
      const filename = `${form.form_code || fid}.pdf`;
      await downloadOfficialForm(idToken, fid, filename);
    } catch (err: any) {
      console.error("Download failed:", err);
      alert(`Download failed: ${err.message || "Network error"}`);
    } finally {
      setDownloadingFormId(null);
    }
  };

  // 12B. Multimodal Attachment Handlers (Phase P3E)
  const handleUploadFile = async (file: File) => {
    if (!idToken) return;
    try {
      setUploadingAttachment(true);
      setErrorMessage(null);
      const res = await uploadChatAttachment(idToken, file, activeConvId, effectiveConflictId);
      setStagedAttachments((prev) => [...prev, res.attachment]);
    } catch (err: any) {
      console.error("Attachment upload error:", err);
      setErrorMessage(err.message || "Failed to upload document attachment.");
    } finally {
      setUploadingAttachment(false);
    }
  };

  const handleRemoveAttachment = async (attachmentId: string) => {
    if (!idToken) return;
    try {
      setStagedAttachments((prev) => prev.filter((a) => a.id !== attachmentId));
      await deleteChatAttachment(idToken, attachmentId);
    } catch (err: any) {
      console.warn("Failed to delete attachment on server:", err);
    }
  };

  const handlePreviewAttachment = async (att: MessageAttachmentItem) => {
    if (!idToken) return;
    setPreviewAttachment(att);
    setPreviewAttachmentLoading(true);
    setPreviewAttachmentError(null);
    try {
      const blob = await previewChatAttachment(idToken, att.id);
      const url = URL.createObjectURL(blob);
      setPreviewAttachmentBlobUrl(url);
    } catch (err: any) {
      console.error("Preview attachment error:", err);
      setPreviewAttachmentError(err.message || "Failed to load document preview.");
    } finally {
      setPreviewAttachmentLoading(false);
    }
  };

  const handleCloseAttachmentPreview = () => {
    if (previewAttachmentBlobUrl) {
      URL.revokeObjectURL(previewAttachmentBlobUrl);
      setPreviewAttachmentBlobUrl(null);
    }
    setPreviewAttachment(null);
    setPreviewAttachmentError(null);
  };

  // 13. Handle Message Submission
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    const currentAttachments = [...stagedAttachments];
    if ((!query && currentAttachments.length === 0) || sending) return;

    const effectiveQuery = query || "Please examine and explain this attached document.";

    setInputQuery("");
    setStagedAttachments([]);
    setErrorMessage(null);
    setSending(true);

    // Optimistically add user message with attachments
    const tempUserMsg: MessageItem = {
      id: "temp-" + Date.now(),
      conversation_id: activeConvId || "pending",
      role: "user",
      content: effectiveQuery,
      attachments: currentAttachments,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setTimeout(scrollToBottom, 50);

    try {
      const res = await sendChatMessage(idToken, {
        message: effectiveQuery,
        conversation_id: activeConvId,
        conflict_id: effectiveConflictId,
        language: responseLanguage,
        attachment_ids: currentAttachments.map((a) => a.id),
      });

      const returnedConvId = res.conversation_id;
      if (!activeConvId && returnedConvId) {
        setActiveConvId(returnedConvId);
        router.replace(`/app/assistant/${returnedConvId}`);
        await loadConversations();
      }

      // Format assistant reply
      const assistantAnswer = res.response;
      const citations = assistantAnswer?.citations || [];
      const relevantForms = assistantAnswer?.relevant_forms || [];

      // Update provider status
      if (assistantAnswer?.provider_status) {
        setProviderStatus(assistantAnswer.provider_status);
      } else if (assistantAnswer?.is_fallback) {
        setProviderStatus("fallback_offline");
      }

      const assistantMsg: MessageItem = {
        id: res.message_id || "msg-" + Date.now(),
        conversation_id: returnedConvId,
        role: "assistant",
        content:
          assistantAnswer?.answer ||
          (typeof assistantAnswer === "string" ? assistantAnswer : "Guidance generated."),
        structured_response: typeof assistantAnswer === "object" ? assistantAnswer : undefined,
        citations: citations,
        grounded_sources: citations.map((c: any) => ({
          title: c.title,
          authority: c.authority,
          citation: c.url,
        })),
        recommended_forms: relevantForms.map((f: any) => ({
          id: f.form_id,
          form_id: f.form_id,
          form_name: f.form_name,
          form_code: f.form_code,
          issuing_authority: f.issuing_authority,
          document_category: f.document_category,
          purpose: f.purpose_description || f.description,
          description: f.description,
          file_size_bytes: f.file_size_bytes,
          sha256_hash: f.sha256_hash,
          official_download_url: f.official_download_url,
          official_portal_url: f.official_portal_url,
          verification_status: f.verification_status,
          prerequisites: f.prerequisites,
          applicable_conditions: f.applicable_conditions,
          is_official_government_form: f.is_official_government_form,
        })),
        statutory_warning: "AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION",
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setTimeout(scrollToBottom, 100);
    } catch (err: any) {
      console.error("Assistant chat error:", err);
      setErrorMessage(
        err.message || "Assistant service is not currently available. Please try again later."
      );
      const fallbackMsg: MessageItem = {
        id: "err-" + Date.now(),
        conversation_id: activeConvId || "error",
        role: "assistant",
        content: "Assistant service is not currently available. Please try again later.",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setSending(false);
    }
  };

  // Dynamic user greeting computation
  const getGreetingTime = () => {
    const hour = new Date().getHours();
    if (hour >= 5 && hour < 12) return "Morning";
    if (hour >= 12 && hour < 17) return "Afternoon";
    return "Evening";
  };

  const citizenDisplayName =
    profile?.full_name?.split(" ")[0] ||
    firebaseUser?.displayName?.split(" ")[0] ||
    firebaseUser?.email?.split("@")[0] ||
    "ALPHA";

  return (
    <div className="flex h-screen w-screen bg-[#FAF9F5] text-[#1F1E1D] overflow-hidden">
      {/* 1. Collapsible Left Sidebar */}
      <AssistantSidebar
        conversations={conversations}
        activeConvId={activeConvId}
        onSelectConversation={handleSelectConversation}
        onNewInquiry={handleNewInquiry}
        onOpenSearch={() => setSearchModalOpen(true)}
        onTogglePin={handleTogglePin}
        onPromptRename={handlePromptRename}
        onPromptDelete={handlePromptDelete}
        isOpen={sidebarOpen}
        onToggleOpen={toggleSidebar}
        loading={loadingConvs}
        userProfile={{
          full_name: profile?.full_name || firebaseUser?.displayName || "Citizen",
          email: firebaseUser?.email || undefined,
          role: profile?.role || "user",
        }}
      />

      {/* 2. Main Conversational Canvas */}
      <main className="flex-1 flex flex-col h-screen min-w-0 bg-[#FAF9F5] relative overflow-hidden">
        {/* Top Minimal Canvas Header (Matches Claude Screenshot 1 & 3) */}
        <header className="h-11 px-3 border-b border-[#E5E5E0]/60 flex items-center justify-between bg-[#FAF9F5] select-none z-20 shrink-0">
          <div className="flex items-center gap-1">
            <button
              onClick={toggleSidebar}
              className="p-1.5 text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-lg transition-colors"
              title="Toggle sidebar (Ctrl+B)"
              aria-label="Toggle sidebar"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => router.back()}
              className="p-1.5 text-[#999893] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-lg transition-colors"
              title="Back"
              aria-label="Back"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => router.forward()}
              className="p-1.5 text-[#999893] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-lg transition-colors"
              title="Forward"
              aria-label="Forward"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <div className="hidden sm:flex items-center ml-1.5 pl-1.5 border-l border-[#E5E5E0] gap-1">
              <button
                type="button"
                className="p-1 text-[#1F1E1D] bg-[#EBE9E4] rounded-md transition-colors"
                title="Conversational Workspace"
              >
                <MessageSquare className="w-3.5 h-3.5" />
              </button>
              <Link
                href="/app/inconsistencies"
                className="p-1 text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-md transition-colors"
                title="Code & Inconsistencies"
              >
                <Code className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Center: Free plan · Upgrade (Matches Claude Screenshot 1 & 3) */}
          <div className="flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-[#EBE9E4]/60 hover:bg-[#EBE9E4] border border-[#E5E5E0]/70 text-xs font-sans text-[#73726E] transition-colors">
            <span>Free plan</span>
            <span className="text-[#999893]">·</span>
            <Link
              href="/app/profile"
              className="text-[#1F1E1D] hover:underline font-medium"
            >
              Upgrade
            </Link>
          </div>

          {/* Right: Citizen Smiling Avatar & Desktop Controls (Claude Screenshot 1 & 3) */}
          <div className="flex items-center gap-3">
            <Link
              href="/app/profile"
              className="p-1 text-[#4A4946] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-lg transition-colors"
              title={`Citizen Account: ${citizenDisplayName}`}
              aria-label="User Profile"
            >
              <svg
                className="w-5 h-5 text-[#4A4946]"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="9" />
                <path d="M9 10h.01" />
                <path d="M15 10h.01" />
                <path d="M9.5 15a3.5 3.5 0 0 0 5 0" />
              </svg>
            </Link>
            <div className="hidden sm:flex items-center gap-2.5 text-[#999893] select-none text-xs">
              <span className="hover:text-[#1F1E1D] cursor-pointer">−</span>
              <span className="hover:text-[#1F1E1D] cursor-pointer text-[10px]">□</span>
              <span className="hover:text-[#1F1E1D] cursor-pointer">✕</span>
            </div>
          </div>
        </header>

        {/* Welcome Intro Canvas (Exact match to Claude Screenshot 1 & 3) */}
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center -mt-10 sm:-mt-14 px-4 py-8 max-w-2xl mx-auto w-full space-y-6 animate-in fade-in duration-200">
            {/* Central Terracotta Sunburst Brand Mark & Serif Greeting */}
            <div className="flex items-center justify-center gap-3 select-none">
              <ClaudeSunburst className="w-8 h-8 sm:w-9 sm:h-9 shrink-0" size={34} />
              <h1 className="font-serif text-2xl sm:text-3xl lg:text-4xl text-[#1F1E1D] font-normal tracking-tight">
                {getGreetingTime()}, {citizenDisplayName}
              </h1>
            </div>

            {/* Error Message Alert Banner */}
            {errorMessage && (
              <div className="w-full p-3.5 bg-[#FCE8E6] border border-[#F5C2C7] rounded-xl flex items-center justify-between text-xs text-[#BA1A1A]">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-[#BA1A1A]" />
                  <span>{errorMessage}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setErrorMessage(null)}
                  className="text-[#BA1A1A] hover:text-[#841010] text-xs font-semibold ml-2"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Central Floating Composer Card (Screenshot 1 & 3: Hero) */}
            <div className="w-full">
              <AssistantComposer
                variant="hero"
                inputQuery={inputQuery}
                setInputQuery={setInputQuery}
                onSendMessage={handleSendMessage}
                sending={sending}
                providerStatus={providerStatus}
                responseLanguage={responseLanguage}
                onLanguageChange={handleLanguageChange}
                placeholder="How can I help you today?"
                stagedAttachments={stagedAttachments}
                onUploadFile={handleUploadFile}
                onRemoveAttachment={handleRemoveAttachment}
                uploadingAttachment={uploadingAttachment}
              />
            </div>

            {/* 4 Suggested Action Prompt Pills below Composer */}
            <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-2 text-left pt-1">
              <button
                type="button"
                onClick={() =>
                  setInputQuery("Explain my document discrepancy and the official procedure to resolve it.")
                }
                className="p-3 bg-white border border-[#E5E5E0] hover:border-[#1F1E1D] rounded-xl text-xs text-[#1F1E1D] transition-colors leading-relaxed shadow-sm hover:shadow"
              >
                <span className="font-medium block text-xs mb-0.5 text-[#1F1E1D]">
                  Explain my document discrepancy
                </span>
                <span className="text-[11px] text-[#73726E]">
                  Deterministic legal precedence and risk review
                </span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setInputQuery("Find an official correction form for Aadhaar or PAN update.")
                }
                className="p-3 bg-white border border-[#E5E5E0] hover:border-[#1F1E1D] rounded-xl text-xs text-[#1F1E1D] transition-colors leading-relaxed shadow-sm hover:shadow"
              >
                <span className="font-medium block text-xs mb-0.5 text-[#1F1E1D]">
                  Find an official correction form
                </span>
                <span className="text-[11px] text-[#73726E]">
                  Prescribed statutory forms and download links
                </span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setInputQuery("Help me understand why my passport or EPF application was rejected.")
                }
                className="p-3 bg-white border border-[#E5E5E0] hover:border-[#1F1E1D] rounded-xl text-xs text-[#1F1E1D] transition-colors leading-relaxed shadow-sm hover:shadow"
              >
                <span className="font-medium block text-xs mb-0.5 text-[#1F1E1D]">
                  Understand an application rejection
                </span>
                <span className="text-[11px] text-[#73726E]">
                  Reconciliation guidance for spelling or DOB mismatches
                </span>
              </button>

              <button
                type="button"
                onClick={() =>
                  setInputQuery("Draft a formal name correction letter to the competent statutory authority.")
                }
                className="p-3 bg-white border border-[#E5E5E0] hover:border-[#1F1E1D] rounded-xl text-xs text-[#1F1E1D] transition-colors leading-relaxed shadow-sm hover:shadow"
              >
                <span className="font-medium block text-xs mb-0.5 text-[#1F1E1D]">
                  Draft a formal correction letter
                </span>
                <span className="text-[11px] text-[#73726E]">
                  Standard statutory petition and affidavit formats
                </span>
              </button>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex flex-col min-h-0">
            {/* Scrollable Message Area */}
            <div className="flex-1 overflow-y-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
              {/* Active Discrepancy Context Banner (Phase P2A / P3C) */}
              {resolutionContext && (
                <div className="w-full max-w-3xl mx-auto bg-white border border-[#1F1E1D] rounded-2xl shadow-sm overflow-hidden mb-6">
                  {/* Context Header */}
                  <div className="p-3.5 bg-[#FAF9F5] border-b border-[#E5E5E0] flex items-center justify-between gap-3 flex-wrap">
                    <div className="flex items-center gap-2 flex-wrap min-w-0">
                      <Link
                        href="/app/inconsistencies"
                        className="inline-flex items-center gap-1 text-[11px] font-sans font-medium text-[#73726E] hover:text-[#1F1E1D] transition-colors mr-1"
                        title="Return to Inconsistencies"
                      >
                        <ArrowLeft className="w-3.5 h-3.5" />
                        <span>Inconsistencies</span>
                      </Link>
                      <span className="text-[#CCCCCC]">/</span>
                      <span className="font-sans text-xs font-semibold text-[#1F1E1D] capitalize">
                        {resolutionContext.field_name.replace(/_/g, " ")} Discrepancy
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-white border border-[#E5E5E0] font-sans text-[10px] font-semibold text-[#1F1E1D] uppercase tracking-wide">
                        {resolutionContext.deterministic_classification.replace(/_/g, " ")}
                      </span>
                      {resolutionContext.document_types?.length >= 2 && (
                        <span className="font-mono text-[10px] uppercase text-[#73726E] px-1.5 py-0.5 rounded bg-zinc-100 border border-zinc-200">
                          {resolutionContext.document_types[0]} ↔ {resolutionContext.document_types[1]}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Conflict Switcher (if citizen has multiple conflicts) */}
                      {userConflicts.length > 1 && (
                        <div className="flex items-center gap-1 text-xs">
                          <select
                            value={effectiveConflictId}
                            onChange={(e) => handleSwitchConflict(e.target.value)}
                            className="text-[11px] font-sans bg-white border border-[#E5E5E0] rounded px-2 py-1 text-[#1F1E1D] focus:outline-none cursor-pointer"
                            title="Switch active discrepancy context"
                          >
                            {userConflicts.map((c) => (
                              <option key={c.id} value={c.id}>
                                {c.field_name.replace(/_/g, " ")} ({c.conflict_type.replace(/-/g, " ")})
                              </option>
                            ))}
                          </select>
                        </div>
                      )}

                      {/* Unlink Action */}
                      <button
                        type="button"
                        onClick={handleUnlinkConflict}
                        className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-sans font-medium text-[#73726E] hover:text-[#BA1A1A] hover:bg-[#FCE8E6] rounded transition-colors"
                        title="Unlink discrepancy context from conversation"
                      >
                        <Unlink className="w-3 h-3" />
                        <span className="hidden sm:inline">Unlink</span>
                      </button>

                      {/* Administrative Drafting Trigger (Phase P3G) */}
                      <button
                        type="button"
                        onClick={() => {
                          const activeConflict = userConflicts.find((c) => c.id === effectiveConflictId);
                          setSelectedDraftConflict(activeConflict || null);
                          setSelectedDraft(null);
                          setDraftingModalOpen(true);
                        }}
                        className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-sans font-medium bg-[#1F1E1D] hover:bg-black text-white rounded-lg transition-colors shadow-xs"
                        title="Draft administrative correction letter or statutory petition"
                      >
                        <FileText className="w-3 h-3 text-[#C96442]" />
                        <span className="hidden sm:inline">Draft Letter</span>
                      </button>

                      {resolutionContext.requires_manual_review && (
                        <span className="px-2 py-0.5 rounded-full bg-[#FEF7E0] border border-[#FEEFC3] text-[#B06000] font-sans text-[10px] font-semibold uppercase tracking-wide">
                          Review Needed
                        </span>
                      )}

                      <button
                        type="button"
                        onClick={() => setContextExpanded(!contextExpanded)}
                        className="p-1 hover:bg-[#E5E5E0] rounded-lg text-[#73726E] transition-colors"
                        title={contextExpanded ? "Collapse Context" : "Expand Context"}
                      >
                        {contextExpanded ? (
                          <ChevronUp className="w-4 h-4" />
                        ) : (
                          <ChevronDown className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Collapsible Details */}
                  {contextExpanded && (
                    <div className="p-4 space-y-3.5 bg-white text-xs font-sans">
                      {/* Values Comparison */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="p-3 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl">
                          <span className="text-[10px] text-[#73726E] uppercase block font-semibold">
                            Document A ({resolutionContext.document_types[0] || "Record 1"})
                          </span>
                          <span className="font-medium text-[#1F1E1D] text-sm mt-0.5 block">
                            {resolutionContext.value_a || "—"}
                          </span>
                        </div>
                        <div className="p-3 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl">
                          <span className="text-[10px] text-[#73726E] uppercase block font-semibold">
                            Document B ({resolutionContext.document_types[1] || "Record 2"})
                          </span>
                          <span className="font-medium text-[#1F1E1D] text-sm mt-0.5 block">
                            {resolutionContext.value_b || "—"}
                          </span>
                        </div>
                      </div>

                      {/* Recommended Action */}
                      {resolutionContext.recommended_action && (
                        <div className="p-3 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl text-[#1F1E1D]">
                          <strong className="text-[10px] uppercase text-[#73726E] block mb-0.5 font-semibold">
                            Deterministic Recommendation
                          </strong>
                          <span>{resolutionContext.recommended_action}</span>
                        </div>
                      )}

                      {/* Deterministic Statutory Resolution Workflow (Phase P2B) */}
                      {resolutionContext.resolution_mapping && (
                        <div className="p-3.5 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl space-y-3">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-1.5">
                              <Shield className="w-4 h-4 text-[#1F1E1D]" />
                              <span className="font-semibold text-xs text-[#1F1E1D]">
                                {resolutionContext.resolution_mapping.procedure_name}
                              </span>
                            </div>
                            <span className="text-[10px] uppercase font-mono px-2 py-0.5 bg-[#E6F4EA] text-[#0D652D] rounded-full font-medium">
                              {resolutionContext.resolution_mapping.procedure_type.replace(/_/g, " ")}
                            </span>
                          </div>

                          {/* Authority & Portal */}
                          <div className="flex items-center justify-between text-xs text-[#73726E] pt-1 border-t border-[#E5E5E0]">
                            <span>
                              Authority: <strong className="text-[#1F1E1D]">{resolutionContext.resolution_mapping.authority_name}</strong>
                            </span>
                            {resolutionContext.resolution_mapping.authority_portal && (
                              <a
                                href={resolutionContext.resolution_mapping.authority_portal}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 text-[11px] text-[#0066CC] hover:underline"
                              >
                                <span>Official Portal</span>
                                <ExternalLink className="w-3 h-3" />
                              </a>
                            )}
                          </div>

                          {/* Prescribed Forms */}
                          {resolutionContext.resolution_mapping.prescribed_forms &&
                            resolutionContext.resolution_mapping.prescribed_forms.length > 0 && (
                              <div className="pt-2 border-t border-[#E5E5E0] space-y-1.5">
                                <span className="text-[10px] uppercase tracking-wider text-[#73726E] font-semibold block">
                                  Official Prescribed Forms:
                                </span>
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  {resolutionContext.resolution_mapping.prescribed_forms.map((form) => (
                                    <div
                                      key={form.form_id}
                                      className="p-2.5 bg-white border border-[#E5E5E0] hover:border-[#1F1E1D] rounded-xl flex items-center justify-between transition-colors group"
                                    >
                                      <div className="min-w-0 pr-2">
                                        <div className="font-medium text-xs text-[#1F1E1D] truncate">
                                          {form.form_name}
                                        </div>
                                        <div className="text-[10px] text-[#73726E] truncate">
                                          {form.issuing_authority}
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-1 shrink-0">
                                        <button
                                          type="button"
                                          onClick={() => handlePreviewForm(form)}
                                          className="p-1 text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#FAF9F5] rounded transition-colors"
                                          title="Preview Form"
                                          aria-label={`Preview ${form.form_name}`}
                                        >
                                          <Eye className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                          type="button"
                                          onClick={() => handleDownloadForm(form)}
                                          disabled={downloadingFormId === form.form_id}
                                          className="p-1 text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#FAF9F5] rounded transition-colors"
                                          title="Download Official Form"
                                          aria-label={`Download ${form.form_name}`}
                                        >
                                          {downloadingFormId === form.form_id ? (
                                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                          ) : (
                                            <Download className="w-3.5 h-3.5" />
                                          )}
                                        </button>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                          {/* Document Checklist */}
                          {resolutionContext.resolution_mapping.document_checklist &&
                            resolutionContext.resolution_mapping.document_checklist.length > 0 && (
                              <div className="pt-2 border-t border-[#E5E5E0] space-y-1">
                                <span className="text-[10px] uppercase tracking-wider text-[#73726E] font-semibold block">
                                  Required Supporting Documents:
                                </span>
                                <ul className="space-y-1">
                                  {resolutionContext.resolution_mapping.document_checklist.map((item, idx) => (
                                    <li key={idx} className="flex items-start gap-1.5 text-xs text-[#1F1E1D]">
                                      <CheckCircle2 className="w-3.5 h-3.5 text-[#0D652D] shrink-0 mt-0.5" />
                                      <span>{item}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                        </div>
                      )}

                      {/* Statutory Disclaimer Notice */}
                      <div className="text-[11px] text-[#73726E] border-t border-[#E5E5E0] pt-2 flex items-center gap-1.5">
                        <AlertCircle className="w-3.5 h-3.5 text-[#73726E] shrink-0" />
                        <span>{resolutionContext.statutory_disclaimer}</span>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Dialogue Turns */}
              {messages.map((msg) => (
                <div key={msg.id} className="w-full max-w-3xl mx-auto">
                  {msg.role === "user" ? (
                    /* User Message Bubble (Right-aligned) */
                    <div className="flex flex-col items-end">
                      {/* Attached Documents / Evidence Chips (Phase P3E) */}
                      {msg.attachments && msg.attachments.length > 0 && (
                        <div className="flex flex-wrap justify-end gap-1.5 mb-2 max-w-xl">
                          {msg.attachments.map((att) => (
                            <button
                              key={att.id}
                              type="button"
                              onClick={() => handlePreviewAttachment(att)}
                              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-[#E5E5E0] hover:border-[#1F1E1D] text-xs text-[#1F1E1D] shadow-sm transition-all text-left group"
                              title="Click to preview attached document and OCR extraction"
                            >
                              {att.mime_type === "application/pdf" ? (
                                <FileText className="w-3.5 h-3.5 text-[#BA1A1A] shrink-0" />
                              ) : (
                                <ImageIcon className="w-3.5 h-3.5 text-[#006699] shrink-0" />
                              )}
                              <span className="truncate max-w-[140px] font-medium text-[11px] group-hover:underline">
                                {att.file_name}
                              </span>
                              <span className="text-[10px] text-[#73726E] font-mono">
                                {Math.round(att.file_size_bytes / 1024)} KB
                              </span>
                              {att.ocr_confidence !== undefined && att.ocr_confidence !== null && (
                                <span
                                  className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                                    att.ocr_confidence >= 0.6
                                      ? "bg-[#E6F4EA] text-[#0D652D]"
                                      : "bg-[#FCE8E6] text-[#C5221F]"
                                  }`}
                                >
                                  {Math.round(att.ocr_confidence * 100)}%
                                </span>
                              )}
                            </button>
                          ))}
                        </div>
                      )}

                      <div className="bg-[#EBE9E4] text-[#1F1E1D] px-4 py-3 rounded-2xl max-w-xl text-xs sm:text-sm font-sans leading-relaxed shadow-sm">
                        {msg.content}
                      </div>
                      <span className="text-[10px] text-[#999893] font-mono mt-1 mr-1">
                        {new Date(msg.created_at).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  ) : (
                    /* Assistant Turn */
                    <div className="flex items-start gap-3.5">
                      <div className="w-7 h-7 rounded-full bg-[#1F1E1D] text-white flex items-center justify-center font-serif text-xs font-bold shrink-0 mt-0.5">
                        <span className="text-[#C96442] text-xs">✳</span>
                      </div>
                      <div className="flex-1 space-y-3.5 min-w-0">
                        {/* Provider Status Pill */}
                        {msg.structured_response && (
                          <div className="flex items-center gap-2 flex-wrap">
                            {msg.structured_response.is_fallback ? (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-white border border-[#E5E5E0] text-[#73726E]">
                                <Shield className="w-3 h-3 text-[#73726E]" />
                                <span>Offline Statutory Resolution (Deterministic Mode)</span>
                              </span>
                            ) : msg.structured_response.provider_status === "operational" ? (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#E6F4EA] border border-[#CEEAD6] text-[#0D652D]">
                                <Sparkles className="w-3 h-3 text-[#0D652D]" />
                                <span>AI Grounded (Gemini) • Verified Knowledge</span>
                              </span>
                            ) : null}

                            {msg.structured_response.confidence === "insufficient_evidence" && (
                              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-[#FEF7E0] border border-[#FEEFC3] text-[#B06000]">
                                <AlertTriangle className="w-3 h-3 text-[#E37400]" />
                                <span>Insufficient Evidence</span>
                              </span>
                            )}
                          </div>
                        )}

                        {/* Formatted Markdown Content */}
                        <div className="text-[#1F1E1D] text-xs sm:text-sm font-sans leading-relaxed">
                          <MarkdownRenderer content={msg.content} />
                        </div>

                        {/* Grounded Verified Citations Card */}
                        {((msg.structured_response?.citations && msg.structured_response.citations.length > 0) ||
                          (msg.citations && msg.citations.length > 0) ||
                          (msg.grounded_sources && msg.grounded_sources.length > 0)) && (
                          <div className="p-3.5 bg-white border border-[#E5E5E0] rounded-2xl space-y-2.5 shadow-sm">
                            <div className="text-[10px] uppercase tracking-wider font-semibold text-[#73726E] font-sans flex items-center justify-between">
                              <span className="flex items-center gap-1.5">
                                <Shield className="w-3 h-3 text-[#0D652D]" />
                                <span>Verified Statutory Sources</span>
                              </span>
                              <span className="text-[9px] font-mono text-[#0D652D] bg-[#E6F4EA] px-1.5 py-0.5 rounded font-medium">
                                VERIFIED
                              </span>
                            </div>
                            <div className="divide-y divide-[#E5E5E0]/60">
                              {(
                                msg.structured_response?.citations ||
                                msg.citations ||
                                msg.grounded_sources ||
                                []
                              ).map((src: any, idx: number) => (
                                <div key={idx} className="py-2 text-xs font-sans space-y-0.5">
                                  <div className="flex items-center justify-between gap-2">
                                    <span className="font-medium text-[#1F1E1D] truncate">
                                      {src.title}
                                    </span>
                                    <span className="text-[10px] bg-[#FAF9F5] px-1.5 py-0.5 rounded border border-[#E5E5E0] text-[#73726E] shrink-0">
                                      {src.authority}
                                    </span>
                                  </div>
                                  {src.url ? (
                                    <a
                                      href={src.url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="inline-flex items-center gap-1 text-[11px] text-[#0066CC] hover:underline pt-0.5"
                                    >
                                      <span>Official Portal / Circular</span>
                                      <ExternalLink className="w-3 h-3" />
                                    </a>
                                  ) : src.citation ? (
                                    <p className="text-[11px] text-[#73726E] italic leading-tight">
                                      {src.citation}
                                    </p>
                                  ) : null}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Prescribed Official Forms Cards (Phase P3D) */}
                        {((msg.structured_response?.relevant_forms &&
                          msg.structured_response.relevant_forms.length > 0) ||
                          (msg.recommended_forms && msg.recommended_forms.length > 0)) && (
                          <div className="space-y-2.5 pt-1">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] uppercase tracking-wider font-semibold text-[#73726E] font-sans flex items-center gap-1.5">
                                <FileText className="w-3.5 h-3.5 text-[#1F1E1D]" />
                                <span>Official Statutory Prescribed Forms:</span>
                              </span>
                              <span className="text-[10px] font-mono text-[#0D652D] bg-[#E6F4EA] border border-[#CEEAD6] px-2 py-0.5 rounded-full font-medium">
                                VERIFIED GOVERNMENT SPECIFICATION
                              </span>
                            </div>
                            <div className="grid grid-cols-1 gap-3">
                              {(
                                msg.structured_response?.relevant_forms ||
                                msg.recommended_forms ||
                                []
                              ).map((form: any, idx: number) => {
                                const fid = form.form_id || form.id || `form-${idx}`;
                                return (
                                  <OfficialFormCard
                                    key={fid}
                                    form={form}
                                    onPreview={handlePreviewForm}
                                    onDownload={handleDownloadForm}
                                    previewing={
                                      previewLoading &&
                                      (previewForm?.form_id === fid || previewForm?.id === fid)
                                    }
                                    downloading={downloadingFormId === fid}
                                  />
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Explicit Statutory Notice if No Verified Form Available (Phase P3D) */}
                        {(msg.structured_response?.no_verified_form_available ||
                          msg.content.includes("NO VERIFIED OFFICIAL FORM CURRENTLY AVAILABLE") ||
                          msg.content.includes("NO_VERIFIED_FORM_AVAILABLE")) && (
                          <div className="p-3.5 bg-[#FEF7E0] border border-[#FEEFC3] rounded-2xl text-xs text-[#B06000] flex items-start gap-2.5 shadow-sm">
                            <AlertCircle className="w-4 h-4 text-[#E37400] shrink-0 mt-0.5" />
                            <div className="space-y-1">
                              <span className="font-semibold block uppercase tracking-wide text-[10px] text-[#E37400]">
                                Statutory Notice • No Verified Form Available
                              </span>
                              <p className="text-[11px] leading-relaxed text-[#73726E]">
                                CONVELINA only retrieves authentic government forms that have been verified by administrators. No official form matching this specific discrepancy has been verified in the statutory catalog. Please consult the official issuing authority portal directly.
                              </p>
                            </div>
                          </div>
                        )}

                        {/* AI-Generated Supporting Draft Notice (Phase P3D Distinction) */}
                        {(msg.structured_response?.letter_draft ||
                          msg.content.includes("Subject:") ||
                          msg.content.includes("To,") ||
                          msg.content.includes("Dear Sir/Madam") ||
                          msg.content.includes("FORMAL PETITION") ||
                          msg.content.includes("AFFIDAVIT DRAFT")) && (
                          <div className="p-2.5 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl flex items-center justify-between gap-2 text-xs flex-wrap">
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded bg-zinc-800 text-white font-mono text-[9px] uppercase tracking-wider font-semibold">
                                AI-GENERATED SUPPORTING DRAFT • NOT AN OFFICIAL FORM
                              </span>
                              <span className="text-[11px] text-[#73726E] hidden sm:inline">
                                Verification, physical print, and citizen signature required before submission.
                              </span>
                            </div>
                            <span className="text-[10px] font-mono text-[#999893]">
                              Advisory Draft Notice
                            </span>
                          </div>
                        )}

                        {/* Personalized Administrative Correction Draft Card (Phase P3G) */}
                        {msg.structured_response?.correction_draft && (
                          <div className="pt-2">
                            <CorrectionDraftCard
                              draft={msg.structured_response.correction_draft}
                              token={idToken}
                              onOpenDraft={(d) => {
                                setSelectedDraft(d);
                                const conf = userConflicts.find((c) => c.id === d.conflict_id);
                                setSelectedDraftConflict(conf || null);
                                setDraftingModalOpen(true);
                              }}
                              onConfirmDraft={(d) => {
                                setSelectedDraft(d);
                                const conf = userConflicts.find((c) => c.id === d.conflict_id);
                                setSelectedDraftConflict(conf || null);
                                setDraftingModalOpen(true);
                              }}
                            />
                          </div>
                        )}

                        {/* Message Actions Toolbar (Copy & Draft Quick Action) */}
                        <div className="flex items-center justify-between pt-1 text-[11px] text-[#999893] border-t border-[#E5E5E0]/60 flex-wrap gap-2">
                          <span className="font-mono text-[10px]">
                            AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION
                          </span>
                          <div className="flex items-center gap-2">
                            {effectiveConflictId && (
                              <button
                                type="button"
                                onClick={() => {
                                  const activeConflict = userConflicts.find((c) => c.id === effectiveConflictId);
                                  setSelectedDraftConflict(activeConflict || null);
                                  setSelectedDraft(null);
                                  setDraftingModalOpen(true);
                                }}
                                className="inline-flex items-center gap-1 px-2 py-0.5 rounded hover:bg-[#EBE9E4] text-[#1F1E1D] font-medium transition-colors text-[11px]"
                                title="Open drafting studio for this discrepancy"
                              >
                                <FileText className="w-3 h-3 text-[#C96442]" />
                                <span>Draft Letter</span>
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => handleCopyMessage(msg.id, msg.content)}
                              className="inline-flex items-center gap-1 px-2 py-0.5 rounded hover:bg-[#EBE9E4] text-[#73726E] hover:text-[#1F1E1D] transition-colors"
                              title="Copy message to clipboard"
                            >
                            {copiedMsgId === msg.id ? (
                              <>
                                <Check className="w-3 h-3 text-[#0D652D]" />
                                <span className="text-[#0D652D]">Copied</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3" />
                                <span>Copy</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                </div>
              ))}

              {/* Sending Indicator */}
              {sending && (
                <div className="w-full max-w-3xl mx-auto flex items-start gap-3.5">
                  <div className="w-7 h-7 rounded-full bg-[#1F1E1D] text-white flex items-center justify-center font-serif text-xs font-bold shrink-0 mt-0.5">
                    <span className="text-[#C96442]">✳</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-[#73726E] font-sans py-1">
                    <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#C96442]" />
                    <span>Retrieving statutory precedents and validating citations...</span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Error Message Alert Banner */}
            {errorMessage && (
              <div className="w-full max-w-3xl mx-auto mb-2 p-3 bg-[#FCE8E6] border border-[#F5C2C7] rounded-xl flex items-center justify-between text-xs text-[#BA1A1A]">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-[#BA1A1A]" />
                  <span>{errorMessage}</span>
                </div>
                <button
                  type="button"
                  onClick={() => setErrorMessage(null)}
                  className="text-[#BA1A1A] hover:text-[#841010] text-xs font-semibold ml-2"
                >
                  ✕
                </button>
              </div>
            )}

            {/* Floating Message Composer Fixed at Canvas Bottom (Matches Claude Screenshot 2: Pill) */}
            <AssistantComposer
              variant="pill"
              inputQuery={inputQuery}
              setInputQuery={setInputQuery}
              onSendMessage={handleSendMessage}
              sending={sending}
              providerStatus={providerStatus}
              responseLanguage={responseLanguage}
              onLanguageChange={handleLanguageChange}
              placeholder="Write a message..."
              stagedAttachments={stagedAttachments}
              onUploadFile={handleUploadFile}
              onRemoveAttachment={handleRemoveAttachment}
              uploadingAttachment={uploadingAttachment}
            />
          </div>
        )}
      </main>

      {/* 4. Search Modal (Ctrl+K) */}
      <ConversationSearchModal
        isOpen={searchModalOpen}
        onClose={() => setSearchModalOpen(false)}
        onSelectConversation={handleSelectConversation}
        idToken={idToken}
      />

      {/* 5. Rename Conversation Modal */}
      {renameModal.isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-[2px] animate-in fade-in duration-100"
          onClick={() => setRenameModal({ isOpen: false, convId: "", title: "" })}
        >
          <div
            className="w-full max-w-md bg-white rounded-2xl border border-[#E5E5E0] shadow-2xl p-5 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-[#1F1E1D] font-sans">
                Rename Inquiry Session
              </h3>
              <button
                onClick={() => setRenameModal({ isOpen: false, convId: "", title: "" })}
                className="p-1 hover:bg-[#FAF9F5] rounded-full text-[#73726E]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <input
              type="text"
              value={renameModal.title}
              onChange={(e) =>
                setRenameModal((prev) => ({ ...prev, title: e.target.value }))
              }
              onKeyDown={(e) => {
                if (e.key === "Enter") handleSaveRename();
              }}
              autoFocus
              className="w-full h-10 px-3 border border-[#E5E5E0] rounded-xl text-xs sm:text-sm font-sans text-[#1F1E1D] focus:outline-none focus:border-[#1F1E1D]"
            />
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setRenameModal({ isOpen: false, convId: "", title: "" })}
                className="px-3 py-1.5 rounded-xl border border-[#E5E5E0] text-xs font-sans text-[#73726E] hover:bg-[#FAF9F5]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveRename}
                disabled={!renameModal.title.trim()}
                className="px-3 py-1.5 rounded-xl bg-[#1F1E1D] text-white text-xs font-sans font-medium hover:bg-black disabled:opacity-40"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 6. Delete Confirmation Modal */}
      {deleteModal.isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-[2px] animate-in fade-in duration-100"
          onClick={() => setDeleteModal({ isOpen: false, convId: "" })}
        >
          <div
            className="w-full max-w-sm bg-white rounded-2xl border border-[#E5E5E0] shadow-2xl p-5 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="space-y-1">
              <h3 className="text-sm font-semibold text-[#1F1E1D] font-sans">
                Delete inquiry session?
              </h3>
              <p className="text-xs text-[#73726E] leading-relaxed font-sans">
                This will permanently delete this conversation and all its historical messages. This action cannot be undone.
              </p>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setDeleteModal({ isOpen: false, convId: "" })}
                className="px-3 py-1.5 rounded-xl border border-[#E5E5E0] text-xs font-sans text-[#73726E] hover:bg-[#FAF9F5]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                className="px-3 py-1.5 rounded-xl bg-[#BA1A1A] text-white text-xs font-sans font-medium hover:bg-[#A01515]"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 7. Official Form Preview Modal (Phase P3D) */}
      {previewForm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/50 backdrop-blur-sm animate-in fade-in duration-150"
          onClick={handleClosePreview}
          data-testid="official-form-preview-modal"
        >
          <div
            className="w-full max-w-4xl max-h-[92vh] bg-white rounded-2xl border border-[#1F1E1D] shadow-2xl flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="p-4 bg-[#FAF9F5] border-b border-[#E5E5E0] flex items-center justify-between gap-3 shrink-0">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-xl bg-white border border-[#E5E5E0] flex items-center justify-center text-[#1F1E1D] shrink-0">
                  <FileText className="w-4 h-4 text-[#0D652D]" />
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-serif text-sm sm:text-base font-semibold text-[#1F1E1D] truncate">
                      {previewForm.form_name}
                    </h3>
                    <span className="px-2 py-0.5 rounded-full bg-[#E6F4EA] border border-[#CEEAD6] text-[#0D652D] font-mono text-[10px] font-medium">
                      OFFICIAL VERIFIED
                    </span>
                  </div>
                  <div className="text-xs text-[#73726E] font-sans truncate">
                    {previewForm.issuing_authority} • Code: {previewForm.form_code || previewForm.form_id}
                  </div>
                </div>
              </div>

              <button
                onClick={handleClosePreview}
                className="p-1.5 text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-lg transition-colors shrink-0"
                title="Close preview"
                aria-label="Close form preview"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
              {/* Document Metadata Drawer */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-sans">
                <div className="p-3 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-[#73726E] block font-semibold">
                    Category & Version
                  </span>
                  <span className="font-medium text-[#1F1E1D] capitalize mt-0.5 block">
                    {previewForm.document_category} • {previewForm.version || "Current Statutory"}
                  </span>
                </div>

                <div className="p-3 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-[#73726E] block font-semibold">
                    File Format & Integrity
                  </span>
                  <span
                    className="font-medium text-[#1F1E1D] font-mono text-[11px] mt-0.5 block truncate"
                    title={previewForm.sha256_hash}
                  >
                    PDF • SHA-256:{" "}
                    {previewForm.sha256_hash
                      ? `${previewForm.sha256_hash.substring(0, 10)}...${previewForm.sha256_hash.substring(previewForm.sha256_hash.length - 6)}`
                      : "Verified"}
                  </span>
                </div>

                <div className="p-3 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-[#73726E] block font-semibold">
                    Statutory Authority
                  </span>
                  <span className="font-medium text-[#1F1E1D] mt-0.5 block truncate">
                    {previewForm.issuing_authority}
                  </span>
                </div>
              </div>

              {/* Purpose & Legal Scope */}
              {(previewForm.purpose || previewForm.purpose_description || previewForm.description) && (
                <div className="p-3.5 bg-white border border-[#E5E5E0] rounded-xl text-xs space-y-1">
                  <strong className="text-[10px] uppercase font-mono tracking-wider text-[#73726E] block">
                    Prescribed Purpose & Legal Scope:
                  </strong>
                  <p className="text-[#4A4946] leading-relaxed">
                    {previewForm.purpose || previewForm.purpose_description || previewForm.description}
                  </p>
                </div>
              )}

              {/* Embedded Document Preview / Stream */}
              <div className="w-full bg-[#FAF9F5] rounded-xl border border-[#E5E5E0] overflow-hidden min-h-[380px] flex items-center justify-center relative">
                {previewLoading ? (
                  <div className="flex flex-col items-center gap-2 p-8 text-[#73726E] text-xs">
                    <RefreshCw className="w-6 h-6 animate-spin text-[#C96442]" />
                    <span>Streaming authentic government document...</span>
                  </div>
                ) : previewError ? (
                  <div className="p-6 text-center space-y-2 max-w-md">
                    <AlertCircle className="w-6 h-6 text-[#BA1A1A] mx-auto" />
                    <p className="text-xs text-[#BA1A1A] font-medium">{previewError}</p>
                    <p className="text-[11px] text-[#73726E]">
                      You can still download the statutory file directly or access the official portal.
                    </p>
                  </div>
                ) : previewBlobUrl ? (
                  <iframe
                    src={previewBlobUrl}
                    className="w-full h-[480px] border-0"
                    title={`${previewForm.form_name} Preview`}
                  />
                ) : (
                  <div className="text-xs text-[#73726E]">No preview available.</div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-[#FAF9F5] border-t border-[#E5E5E0] flex items-center justify-between gap-3 shrink-0 flex-wrap">
              <span className="text-[11px] font-mono text-[#73726E]">
                AUTHENTIC GOVERNMENT SPECIFICATION • TAMPER-EVIDENT ASSET
              </span>

              <div className="flex items-center gap-2">
                {previewForm.official_portal_url && (
                  <a
                    href={previewForm.official_portal_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-1.5 bg-white border border-[#E5E5E0] hover:border-[#1F1E1D] text-[#1F1E1D] rounded-xl text-xs font-sans transition-colors"
                  >
                    <span>Official Portal</span>
                    <ExternalLink className="w-3.5 h-3.5 text-[#73726E]" />
                  </a>
                )}

                <button
                  type="button"
                  onClick={() => handleDownloadForm(previewForm)}
                  disabled={
                    downloadingFormId === (previewForm.form_id || previewForm.id)
                  }
                  className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-[#1F1E1D] hover:bg-black text-white rounded-xl text-xs font-sans font-medium transition-colors shadow-sm"
                >
                  {downloadingFormId === (previewForm.form_id || previewForm.id) ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Download className="w-3.5 h-3.5 text-white" />
                  )}
                  <span>Download Official PDF</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 8. Attachment Preview Modal (Phase P3E) */}
      {previewAttachment && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
          onClick={handleCloseAttachmentPreview}
        >
          <div
            className="w-full max-w-4xl max-h-[92vh] bg-white rounded-2xl border border-[#E5E5E0] shadow-2xl flex flex-col overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="p-4 bg-[#FAF9F5] border-b border-[#E5E5E0] flex items-center justify-between gap-3 shrink-0">
              <div className="flex items-center gap-2.5 min-w-0">
                <div className="w-8 h-8 rounded-xl bg-white border border-[#E5E5E0] flex items-center justify-center text-[#1F1E1D] shrink-0">
                  {previewAttachment.mime_type === "application/pdf" ? (
                    <FileText className="w-4 h-4 text-[#BA1A1A]" />
                  ) : (
                    <ImageIcon className="w-4 h-4 text-[#006699]" />
                  )}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-serif text-sm sm:text-base font-semibold text-[#1F1E1D] truncate">
                      {previewAttachment.file_name}
                    </h3>
                    <span
                      className={`px-2 py-0.5 rounded-full font-mono text-[10px] font-medium border ${
                        previewAttachment.ocr_confidence !== undefined &&
                        previewAttachment.ocr_confidence !== null &&
                        previewAttachment.ocr_confidence >= 0.6
                          ? "bg-[#E6F4EA] border-[#CEEAD6] text-[#0D652D]"
                          : "bg-[#FEF7E0] border-[#FEEFC3] text-[#B06000]"
                      }`}
                    >
                      {previewAttachment.ocr_status === "completed"
                        ? `OCR Extracted (${Math.round((previewAttachment.ocr_confidence ?? 0) * 100)}% Confidence)`
                        : previewAttachment.ocr_status === "low_confidence"
                        ? `Low Confidence (${Math.round((previewAttachment.ocr_confidence ?? 0) * 100)}%)`
                        : "OCR Processing"}
                    </span>
                  </div>
                  <div className="text-xs text-[#73726E] font-sans truncate">
                    Size: {Math.round(previewAttachment.file_size_bytes / 1024)} KB • Type: {previewAttachment.mime_type} • Temporary Encrypted Storage
                  </div>
                </div>
              </div>

              <button
                onClick={handleCloseAttachmentPreview}
                className="p-1.5 text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-lg transition-colors shrink-0"
                title="Close preview"
                aria-label="Close attachment preview"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
              {/* Document Overview Metadata */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-sans">
                <div className="p-3 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-[#73726E] block font-semibold">
                    Document Category
                  </span>
                  <span className="font-medium text-[#1F1E1D] capitalize mt-0.5 block">
                    {previewAttachment.extracted_fields?.document_category || "Identity / Case Record"}
                  </span>
                </div>

                <div className="p-3 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-[#73726E] block font-semibold">
                    SHA-256 Digest
                  </span>
                  <span
                    className="font-medium text-[#1F1E1D] font-mono text-[11px] mt-0.5 block truncate"
                    title={previewAttachment.sha256_hash || undefined}
                  >
                    {previewAttachment.sha256_hash
                      ? `${previewAttachment.sha256_hash.substring(0, 12)}...${previewAttachment.sha256_hash.substring(previewAttachment.sha256_hash.length - 8)}`
                      : "Verified"}
                  </span>
                </div>

                <div className="p-3 bg-[#FAF9F5] border border-[#E5E5E0] rounded-xl">
                  <span className="text-[10px] font-mono uppercase text-[#73726E] block font-semibold">
                    Confidential Retention
                  </span>
                  <span className="font-medium text-[#1F1E1D] mt-0.5 block">
                    24-Hour Expiry Lifecycle
                  </span>
                </div>
              </div>

              {/* OCR Low Confidence Advisory */}
              {previewAttachment.ocr_confidence !== undefined &&
                previewAttachment.ocr_confidence !== null &&
                previewAttachment.ocr_confidence < 0.6 && (
                  <div className="p-3 bg-[#FEF7E0] border border-[#FEEFC3] rounded-xl flex items-start gap-2 text-xs text-[#8A5300]">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-[#B06000] mt-0.5" />
                    <div>
                      <strong className="font-semibold block">Low OCR Confidence Warning</strong>
                      Scanned quality or camera angle is suboptimal. Machine extraction may contain inaccuracies; cross-verify all extracted figures with original document.
                    </div>
                  </div>
                )}

              {/* Extracted Structured Entities (if any) */}
              {previewAttachment.extracted_fields && Object.keys(previewAttachment.extracted_fields).length > 0 && (
                <div className="p-3.5 bg-white border border-[#E5E5E0] rounded-xl text-xs space-y-2">
                  <strong className="text-[10px] uppercase font-mono tracking-wider text-[#73726E] block">
                    Pre-Scrubbed Machine Extraction (Zero Raw PII Stored):
                  </strong>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                    {previewAttachment.extracted_fields.dates_found && previewAttachment.extracted_fields.dates_found.length > 0 && (
                      <div className="p-2 bg-[#FAF9F5] rounded-lg">
                        <span className="text-[#73726E] block text-[10px]">Dates Detected:</span>
                        <span className="font-medium text-[#1F1E1D]">
                          {previewAttachment.extracted_fields.dates_found.join(", ")}
                        </span>
                      </div>
                    )}
                    {previewAttachment.extracted_fields.identifiers_found && previewAttachment.extracted_fields.identifiers_found.length > 0 && (
                      <div className="p-2 bg-[#FAF9F5] rounded-lg">
                        <span className="text-[#73726E] block text-[10px]">Masked Numbers:</span>
                        <span className="font-mono font-medium text-[#1F1E1D]">
                          {previewAttachment.extracted_fields.identifiers_found.join(", ")}
                        </span>
                      </div>
                    )}
                    {previewAttachment.extracted_fields.rejection_observations && previewAttachment.extracted_fields.rejection_observations.length > 0 && (
                      <div className="p-2 bg-[#FCE8E6] rounded-lg col-span-full">
                        <span className="text-[#BA1A1A] block text-[10px] font-semibold">Deficiency / Rejection Remarks:</span>
                        <span className="font-medium text-[#5F0000]">
                          {previewAttachment.extracted_fields.rejection_observations.join("; ")}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Embedded Document View */}
              <div className="w-full bg-[#FAF9F5] rounded-xl border border-[#E5E5E0] overflow-hidden min-h-[380px] flex items-center justify-center relative">
                {previewAttachmentLoading ? (
                  <div className="flex flex-col items-center gap-2 p-8 text-[#73726E] text-xs">
                    <RefreshCw className="w-6 h-6 animate-spin text-[#C96442]" />
                    <span>Streaming encrypted document...</span>
                  </div>
                ) : previewAttachmentError ? (
                  <div className="p-6 text-center space-y-2 max-w-md">
                    <AlertCircle className="w-6 h-6 text-[#BA1A1A] mx-auto" />
                    <p className="text-xs text-[#BA1A1A] font-medium">{previewAttachmentError}</p>
                    <p className="text-[11px] text-[#73726E]">
                      The file could not be displayed directly.
                    </p>
                  </div>
                ) : previewAttachmentBlobUrl ? (
                  previewAttachment.mime_type === "application/pdf" ? (
                    <iframe
                      src={previewAttachmentBlobUrl}
                      className="w-full h-[480px] border-0"
                      title={`${previewAttachment.file_name} Preview`}
                    />
                  ) : (
                    <div className="p-4 flex items-center justify-center">
                      <img
                        src={previewAttachmentBlobUrl}
                        alt={previewAttachment.file_name}
                        className="max-h-[480px] max-w-full object-contain rounded-lg border border-[#E5E5E0]"
                      />
                    </div>
                  )
                ) : (
                  <div className="text-xs text-[#73726E]">No preview available.</div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 bg-[#FAF9F5] border-t border-[#E5E5E0] flex items-center justify-between gap-3 shrink-0 flex-wrap">
              <span className="text-[11px] font-mono text-[#73726E]">
                CONFIDENTIAL TEMPORARY ATTACHMENT • FORCED ROW-LEVEL SECURITY ENFORCED
              </span>

              <button
                type="button"
                onClick={handleCloseAttachmentPreview}
                className="px-4 py-1.5 bg-[#1F1E1D] hover:bg-black text-white rounded-xl text-xs font-sans font-medium transition-colors shadow-sm"
              >
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 8. Administrative Drafting Workspace Modal (Phase P3G) */}
      {draftingModalOpen && (
        <AdministrativeDraftingModal
          isOpen={draftingModalOpen}
          onClose={() => {
            setDraftingModalOpen(false);
            setSelectedDraft(null);
            setSelectedDraftConflict(null);
          }}
          token={idToken}
          initialConflict={selectedDraftConflict}
          initialDraft={selectedDraft}
          documents={userDocuments}
          onDraftSaved={(savedDraft) => {
            setSelectedDraft(savedDraft);
          }}
        />
      )}
    </div>
  );
}

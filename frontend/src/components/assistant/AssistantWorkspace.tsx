"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
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
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import {
  fetchConversations,
  fetchConversationMessages,
  sendChatMessage,
  deleteConversation,
  fetchResolutionContext,
  ConversationItem,
  MessageItem,
  ResolutionContextData,
} from "../../lib/api";

interface AssistantWorkspaceProps {
  initialConversationId?: string;
}

export default function AssistantWorkspace({
  initialConversationId,
}: AssistantWorkspaceProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const conflictIdParam = searchParams.get("conflictId") || undefined;
  const { idToken, profile } = useAuth();

  // Conversations & Discourse State
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

  // Grounded Resolution Context State (Phase P2A)
  const [resolutionContext, setResolutionContext] = useState<ResolutionContextData | null>(null);
  const [loadingResolutionContext, setLoadingResolutionContext] = useState(false);
  const [contextExpanded, setContextExpanded] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // 1. Load citizen's conversations
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

  // 2. Load messages for active conversation
  const loadMessages = useCallback(
    async (convId: string) => {
      if (!idToken) return;
      try {
        setLoadingMessages(true);
        const msgs = await fetchConversationMessages(idToken, convId);
        setMessages(msgs);
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
    } else {
      setMessages([]);
    }
  }, [activeConvId, loadMessages]);

  // Load Resolution Context if conflictIdParam is present
  useEffect(() => {
    if (!conflictIdParam || !idToken) {
      setResolutionContext(null);
      return;
    }
    let isCancelled = false;
    const loadContext = async () => {
      try {
        setLoadingResolutionContext(true);
        const ctx = await fetchResolutionContext(idToken, conflictIdParam);
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
  }, [conflictIdParam, idToken]);

  // Handle New Inquiry
  const handleNewInquiry = () => {
    setActiveConvId(undefined);
    setMessages([]);
    setErrorMessage(null);
    setResolutionContext(null);
    router.push("/app/assistant");
  };

  // Handle Delete Conversation
  const handleDeleteConversation = async (e: React.MouseEvent, convId: string) => {
    e.stopPropagation();
    if (!confirm("Delete this conversation and its historical messages?")) return;
    try {
      await deleteConversation(idToken, convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        handleNewInquiry();
      }
    } catch (err) {
      console.error("Error deleting conversation:", err);
    }
  };

  // Handle Message Submission
  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || sending) return;

    setInputQuery("");
    setErrorMessage(null);
    setSending(true);

    // Optimistically add user message
    const tempUserMsg: MessageItem = {
      id: "temp-" + Date.now(),
      conversation_id: activeConvId || "pending",
      role: "user",
      content: query,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setTimeout(scrollToBottom, 50);

    try {
      const res = await sendChatMessage(idToken, {
        message: query,
        conversation_id: activeConvId,
        conflict_id: conflictIdParam,
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

      const assistantMsg: MessageItem = {
        id: res.message_id || "msg-" + Date.now(),
        conversation_id: returnedConvId,
        role: "assistant",
        content: assistantAnswer?.answer || (typeof assistantAnswer === "string" ? assistantAnswer : "Guidance generated."),
        structured_response: typeof assistantAnswer === "object" ? assistantAnswer : undefined,
        citations: citations,
        grounded_sources: citations.map((c: any) => ({
          title: c.title,
          authority: c.authority,
          citation: c.url,
        })),
        recommended_forms: relevantForms.map((f: any) => ({
          form_id: f.form_id,
          form_name: f.form_name,
          issuing_authority: f.issuing_authority,
          download_url: f.official_download_url,
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
      // Remove optimistic message on hard failure or append error note
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

  return (
    <div className="max-w-7xl mx-auto w-full h-[calc(100vh-3.5rem)] flex flex-col lg:flex-row divide-y lg:divide-y-0 lg:divide-x divide-[#E7E5E0]">
      {/* Column 1: Conversations History Panel (Desktop w-72 or lg:col-span-3) */}
      <aside className="w-full lg:w-72 shrink-0 bg-[#FAF9F6] p-4 lg:p-6 flex flex-col justify-between overflow-y-auto max-h-[30vh] lg:max-h-full">
        <div className="space-y-4">
          {/* New Inquiry Action */}
          <button
            onClick={handleNewInquiry}
            className="w-full h-10 px-3.5 bg-white border border-[#E7E5E0] hover:border-[#111111] transition-colors flex items-center justify-between rounded-[4px] text-xs font-sans font-medium text-[#111111]"
            type="button"
          >
            <span className="flex items-center gap-2">
              <Plus className="w-4 h-4 text-[#111111]" />
              <span>New Inquiry</span>
            </span>
          </button>

          {/* Sessions List */}
          <div className="space-y-1.5 pt-2">
            <div className="text-[11px] font-sans uppercase tracking-wider text-[#777777] font-semibold px-2 pb-1">
              Inquiry History
            </div>

            {loadingConvs ? (
              <div className="px-2 py-3 text-xs text-[#777777] font-sans">
                Loading history...
              </div>
            ) : conversations.length > 0 ? (
              <div className="space-y-1">
                {conversations.map((conv) => {
                  const isActive = conv.id === activeConvId;
                  return (
                    <div
                      key={conv.id}
                      onClick={() => {
                        setActiveConvId(conv.id);
                        router.push(`/app/assistant/${conv.id}`);
                      }}
                      className={`group w-full px-3 py-2.5 rounded-[4px] flex items-center justify-between cursor-pointer transition-colors text-left ${
                        isActive
                          ? "bg-[#EFEEEB] text-[#111111] font-medium"
                          : "text-[#5E5E5E] hover:bg-[#F4F3EF] hover:text-[#111111]"
                      }`}
                    >
                      <div className="min-w-0 flex-1 pr-2">
                        <div className="text-xs truncate font-sans">
                          {conv.title || "Inquiry Session"}
                        </div>
                        <div className="text-[10px] text-[#999999] truncate mt-0.5">
                          {new Date(conv.updated_at).toLocaleDateString("en-IN", {
                            month: "short",
                            day: "numeric",
                          })}
                        </div>
                      </div>
                      <button
                        onClick={(e) => handleDeleteConversation(e, conv.id)}
                        className="opacity-0 group-hover:opacity-100 p-1 text-[#777777] hover:text-[#BA1A1A] transition-opacity"
                        aria-label="Delete inquiry"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="px-2 py-4 text-xs text-[#777777] font-sans leading-relaxed">
                No past consultations recorded. Ask a question below to start your first session.
              </div>
            )}
          </div>
        </div>

        {/* Subtle Disclaimer Badge at Sidebar Bottom */}
        <div className="pt-4 border-t border-[#E7E5E0] text-[11px] text-[#777777] font-sans flex items-center gap-1.5">
          <Shield className="w-3.5 h-3.5 text-[#777777]" />
          <span>Source-grounded RAG</span>
        </div>
      </aside>

      {/* Column 2: Discourse Stream (Chat Area) */}
      <section className="flex-1 flex flex-col justify-between bg-[#FAF9F6] overflow-hidden">
        {/* Messages Scrollable Container */}
        <div className="flex-1 overflow-y-auto px-4 lg:px-8 py-6 space-y-8">
          {/* Active Discrepancy Context Banner (Phase P2A) */}
          {resolutionContext && (
            <div className="w-full max-w-3xl mx-auto bg-white border border-[#111111] rounded-[6px] shadow-sm overflow-hidden mb-6">
              {/* Context Header */}
              <div className="p-4 bg-[#FAF9F6] border-b border-[#E7E5E0] flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-sans text-[11px] uppercase tracking-wider text-[#777777] font-semibold">
                    Active Discrepancy Context
                  </span>
                  <span className="text-[#CCCCCC]">•</span>
                  <span className="font-sans text-xs font-semibold text-[#111111] capitalize">
                    {resolutionContext.field_name.replace(/_/g, " ")}
                  </span>
                  <span className="text-[#CCCCCC]">•</span>
                  <span className="px-2 py-0.5 rounded-[2px] bg-[#F4F3EF] border border-[#E7E5E0] font-sans text-[10px] font-semibold text-[#111111] uppercase tracking-wide">
                    {resolutionContext.deterministic_classification.replace(/_/g, " ")}
                  </span>
                  <span className="text-[11px] font-sans text-[#5E5E5E]">
                    ({Math.round(resolutionContext.confidence_score * 100)}% Confidence)
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  {resolutionContext.requires_manual_review && (
                    <span className="px-2 py-0.5 rounded-[2px] bg-[#FEF7E0] border border-[#FEEFC3] text-[#B06000] font-sans text-[10px] font-semibold uppercase tracking-wide">
                      Manual Review Required
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={() => setContextExpanded(!contextExpanded)}
                    className="p-1 hover:bg-[#E7E5E0] rounded text-[#777777] transition-colors"
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
                    <div className="p-2.5 bg-[#FAF9F6] border border-[#E7E5E0] rounded-[3px]">
                      <span className="text-[10px] text-[#777777] uppercase block font-semibold">
                        Document A ({resolutionContext.document_types[0] || "Record 1"})
                      </span>
                      <span className="font-medium text-[#111111] text-sm mt-0.5 block">
                        {resolutionContext.value_a || "—"}
                      </span>
                    </div>
                    <div className="p-2.5 bg-[#FAF9F6] border border-[#E7E5E0] rounded-[3px]">
                      <span className="text-[10px] text-[#777777] uppercase block font-semibold">
                        Document B ({resolutionContext.document_types[1] || "Record 2"})
                      </span>
                      <span className="font-medium text-[#111111] text-sm mt-0.5 block">
                        {resolutionContext.value_b || "—"}
                      </span>
                    </div>
                  </div>

                  {/* Recommended Action */}
                  {resolutionContext.recommended_action && (
                    <div className="p-2.5 bg-[#F4F3EF] border border-[#E7E5E0] rounded-[3px] text-[#111111]">
                      <strong className="text-[10px] uppercase text-[#777777] block mb-0.5 font-semibold">
                        Deterministic Recommendation
                      </strong>
                      <span>{resolutionContext.recommended_action}</span>
                    </div>
                  )}

                  {/* Deterministic Statutory Resolution Workflow (Phase P2B) */}
                  {resolutionContext.resolution_mapping && (
                    <div className="p-3 bg-[#FAF9F6] border border-[#E7E5E0] rounded-[3px] space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <Shield className="w-3.5 h-3.5 text-[#111111]" />
                          <span className="font-semibold text-xs text-[#111111]">
                            {resolutionContext.resolution_mapping.procedure_name}
                          </span>
                        </div>
                        <span className="text-[10px] uppercase font-mono px-2 py-0.5 bg-[#E6F4EA] text-[#0D652D] rounded-[2px] font-medium">
                          {resolutionContext.resolution_mapping.procedure_type.replace(/_/g, " ")}
                        </span>
                      </div>

                      {/* Authority & Portal */}
                      <div className="flex items-center justify-between text-xs text-[#5E5E5E] pt-1 border-t border-[#E7E5E0]">
                        <span>Authority: <strong className="text-[#111111]">{resolutionContext.resolution_mapping.authority_name}</strong></span>
                        {resolutionContext.resolution_mapping.authority_portal && (
                          <a
                            href={resolutionContext.resolution_mapping.authority_portal}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[11px] text-[#111111] underline hover:text-[#5E5E5E]"
                          >
                            <span>Official Portal</span>
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        )}
                      </div>

                      {/* Prescribed Forms */}
                      {resolutionContext.resolution_mapping.prescribed_forms && resolutionContext.resolution_mapping.prescribed_forms.length > 0 && (
                        <div className="pt-2 border-t border-[#E7E5E0] space-y-1.5">
                          <span className="text-[10px] uppercase tracking-wider text-[#777777] font-semibold block">
                            Official Prescribed Forms:
                          </span>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {resolutionContext.resolution_mapping.prescribed_forms.map((form) => (
                              <a
                                key={form.form_id}
                                href={form.official_download_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 bg-white border border-[#E7E5E0] hover:border-[#111111] rounded-[2px] flex items-center justify-between transition-colors group"
                              >
                                <div className="min-w-0 pr-2">
                                  <div className="font-medium text-[11px] text-[#111111] truncate">
                                    {form.form_name}
                                  </div>
                                  <div className="text-[10px] text-[#777777] truncate">
                                    {form.issuing_authority}
                                  </div>
                                </div>
                                <Download className="w-3.5 h-3.5 text-[#5E5E5E] group-hover:text-[#111111] shrink-0" />
                              </a>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Document Checklist */}
                      {resolutionContext.resolution_mapping.document_checklist && resolutionContext.resolution_mapping.document_checklist.length > 0 && (
                        <div className="pt-2 border-t border-[#E7E5E0] space-y-1">
                          <span className="text-[10px] uppercase tracking-wider text-[#777777] font-semibold block">
                            Required Supporting Documents:
                          </span>
                          <ul className="space-y-1">
                            {resolutionContext.resolution_mapping.document_checklist.map((item, idx) => (
                              <li key={idx} className="flex items-start gap-1.5 text-[11px] text-[#333333]">
                                <CheckCircle2 className="w-3.5 h-3.5 text-[#0D652D] shrink-0 mt-0.5" />
                                <span>{item}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Statutory Rules / Limitations */}
                      {resolutionContext.resolution_mapping.statutory_rules && resolutionContext.resolution_mapping.statutory_rules.length > 0 && (
                        <div className="pt-2 border-t border-[#E7E5E0] space-y-1">
                          <span className="text-[10px] uppercase tracking-wider text-[#777777] font-semibold block">
                            Statutory Rules & Limits:
                          </span>
                          <ul className="space-y-0.5">
                            {resolutionContext.resolution_mapping.statutory_rules.map((rule, idx) => (
                              <li key={idx} className="text-[10px] text-[#777777] list-disc list-inside">
                                {rule}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* OCR Quality Warning */}
                  {resolutionContext.ocr_quality_warning && (
                    <div className="p-2.5 bg-[#FEF7E0] border border-[#FEEFC3] rounded-[3px] text-[#B06000] flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-[#E37400] shrink-0 mt-0.5" />
                      <span>{resolutionContext.ocr_quality_warning}</span>
                    </div>
                  )}

                  {/* Non-Latin Script Warning */}
                  {resolutionContext.non_latin_warning && (
                    <div className="p-2.5 bg-[#FEF7E0] border border-[#FEEFC3] rounded-[3px] text-[#B06000] flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-[#E37400] shrink-0 mt-0.5" />
                      <span>{resolutionContext.non_latin_warning}</span>
                    </div>
                  )}

                  {/* Statutory Disclaimer Notice */}
                  <div className="text-[11px] text-[#777777] border-t border-[#E7E5E0] pt-2 flex items-center gap-1.5">
                    <AlertCircle className="w-3.5 h-3.5 text-[#777777] shrink-0" />
                    <span>{resolutionContext.statutory_disclaimer}</span>
                  </div>

                  {/* Quick Starter Chips */}
                  <div className="pt-2 border-t border-[#E7E5E0] flex flex-wrap items-center gap-2">
                    <span className="text-[11px] text-[#777777] font-medium mr-1">Ask Assistant:</span>
                    <button
                      type="button"
                      onClick={() => {
                        setInputQuery(`Why was my ${resolutionContext.field_name.replace(/_/g, " ")} marked as a ${resolutionContext.deterministic_classification.replace(/_/g, " ")}?`);
                      }}
                      className="px-2.5 py-1 bg-[#FAF9F6] border border-[#E7E5E0] hover:border-[#111111] text-[#111111] rounded-[3px] text-xs transition-colors"
                    >
                      Why was this marked as a discrepancy?
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setInputQuery(`What official government forms or procedures apply to resolve this ${resolutionContext.field_name.replace(/_/g, " ")} discrepancy?`);
                      }}
                      className="px-2.5 py-1 bg-[#FAF9F6] border border-[#E7E5E0] hover:border-[#111111] text-[#111111] rounded-[3px] text-xs transition-colors"
                    >
                      What official forms are required?
                    </button>
                    <button
                      type="button"
                      onClick={() => {
                        setInputQuery(`Is this ${resolutionContext.field_name.replace(/_/g, " ")} discrepancy considered high risk, and what should I review first?`);
                      }}
                      className="px-2.5 py-1 bg-[#FAF9F6] border border-[#E7E5E0] hover:border-[#111111] text-[#111111] rounded-[3px] text-xs transition-colors"
                    >
                      Is this a serious discrepancy?
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Welcome Intro Banner when no messages */}
          {messages.length === 0 && (
            <div className="max-w-2xl mx-auto py-12 text-center space-y-4">
              <div className="w-10 h-10 bg-[#111111] text-white flex items-center justify-center font-serif text-sm font-bold rounded-[2px] mx-auto">
                C
              </div>
              <h2 className="font-serif text-2xl text-[#111111] font-light">
                Statutory AI Assistant
              </h2>
              <p className="font-sans text-xs sm:text-sm text-[#5E5E5E] max-w-lg mx-auto leading-relaxed">
                Ask about official document precedence, gazette notification requirements, or step-by-step resolution procedures across UIDAI, NSDL, Passport Seva, and EPFO.
              </p>

              {/* Sample Inquiries */}
              <div className="pt-4 grid grid-cols-1 sm:grid-cols-2 gap-2 text-left max-w-lg mx-auto">
                <button
                  onClick={() => {
                    setInputQuery("Which document has legal precedence for passport verification if names differ?");
                  }}
                  className="p-3 bg-white border border-[#E7E5E0] rounded-[4px] text-xs text-[#111111] hover:border-[#111111] transition-colors leading-relaxed"
                >
                  "Which document has legal precedence for passport verification?"
                </button>
                <button
                  onClick={() => {
                    setInputQuery("How do I update an initial in my PAN card to match my Aadhaar full name?");
                  }}
                  className="p-3 bg-white border border-[#E7E5E0] rounded-[4px] text-xs text-[#111111] hover:border-[#111111] transition-colors leading-relaxed"
                >
                  "How do I expand an initial in my PAN card to match Aadhaar?"
                </button>
              </div>
            </div>
          )}

          {/* Dialogue Turns */}
          {messages.map((msg) => (
            <div key={msg.id} className="w-full max-w-3xl mx-auto">
              {msg.role === "user" ? (
                /* User Message Bubble (Right-aligned) */
                <div className="flex flex-col items-end">
                  <div className="bg-[#EFEEEB] text-[#111111] px-4 py-3 rounded-[4px] max-w-xl text-xs sm:text-sm font-sans leading-relaxed">
                    {msg.content}
                  </div>
                  <span className="text-[10px] text-[#999999] font-mono mt-1 mr-0.5">
                    {new Date(msg.created_at).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              ) : (
                /* Assistant Turn */
                <div className="flex items-start gap-3.5">
                  <div className="w-6 h-6 rounded-[2px] bg-[#111111] text-white flex items-center justify-center font-serif text-xs font-bold shrink-0 mt-0.5">
                    C
                  </div>
                  <div className="flex-1 space-y-4 min-w-0">
                    {/* Provider Status Pill */}
                    {msg.structured_response && (
                      <div className="flex items-center gap-2">
                        {msg.structured_response.is_fallback ? (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] text-[10px] font-mono bg-[#FAF9F6] border border-[#E7E5E0] text-[#777777]">
                            <Shield className="w-3 h-3 text-[#777777]" />
                            <span>Offline Statutory Resolution (Deterministic Mode)</span>
                          </span>
                        ) : msg.structured_response.provider_status === "operational" ? (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] text-[10px] font-mono bg-[#E6F4EA] border border-[#CEEAD6] text-[#0D652D]">
                            <Sparkles className="w-3 h-3 text-[#0D652D]" />
                            <span>AI Grounded (Gemini) • Verified Knowledge</span>
                          </span>
                        ) : null}

                        {msg.structured_response.confidence === "insufficient_evidence" && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-[2px] text-[10px] font-mono bg-[#FEF7E0] border border-[#FEEFC3] text-[#B06000]">
                            <AlertTriangle className="w-3 h-3 text-[#E37400]" />
                            <span>Insufficient Evidence</span>
                          </span>
                        )}
                      </div>
                    )}

                    {/* Content */}
                    <div className="font-sans text-xs sm:text-sm text-[#1A1C1A] leading-relaxed whitespace-pre-line">
                      {msg.content}
                    </div>

                    {/* Grounded Verified Citations */}
                    {((msg.structured_response?.citations && msg.structured_response.citations.length > 0) ||
                      (msg.citations && msg.citations.length > 0) ||
                      (msg.grounded_sources && msg.grounded_sources.length > 0)) && (
                      <div className="p-3 bg-white border border-[#E7E5E0] rounded-[4px] space-y-2">
                        <div className="text-[10px] uppercase tracking-wider font-semibold text-[#777777] font-sans flex items-center justify-between">
                          <span>Verified Statutory Sources</span>
                          <span className="text-[9px] font-mono text-[#0D652D] bg-[#E6F4EA] px-1.5 py-0.2 rounded">VERIFIED</span>
                        </div>
                        <div className="divide-y divide-[#E7E5E0]/60">
                          {(msg.structured_response?.citations || msg.citations || msg.grounded_sources || []).map((src: any, idx: number) => (
                            <div key={idx} className="py-2 text-xs font-sans space-y-0.5">
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-[#111111]">
                                  {src.title}
                                </span>
                                <span className="text-[10px] bg-[#F4F3EF] px-1.5 py-0.5 rounded text-[#5E5E5E]">
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
                                <p className="text-[11px] text-[#777777] italic leading-tight">
                                  {src.citation}
                                </p>
                              ) : null}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Recommended Forms */}
                    {((msg.structured_response?.relevant_forms && msg.structured_response.relevant_forms.length > 0) ||
                      (msg.recommended_forms && msg.recommended_forms.length > 0)) && (
                      <div className="space-y-1.5 pt-1">
                        <span className="text-[10px] uppercase tracking-wider font-semibold text-[#777777] font-sans block">
                          Prescribed Official Forms:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {(msg.structured_response?.relevant_forms || msg.recommended_forms || []).map((form: any, idx: number) => (
                            <a
                              key={idx}
                              href={form.official_download_url || form.download_url || `/app/forms/${form.form_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#E7E5E0] hover:border-[#111111] rounded-[4px] text-xs font-sans text-[#111111] transition-colors"
                            >
                              <Download className="w-3.5 h-3.5 text-[#5E5E5E]" />
                              <span className="font-medium">{form.form_name}</span>
                              <span className="text-[10px] text-[#777777]">
                                ({form.issuing_authority})
                              </span>
                              <ExternalLink className="w-3 h-3 text-[#777777]" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Statutory Disclaimer */}
                    <div className="text-[11px] text-[#777777] font-sans border-t border-[#E7E5E0] pt-2">
                      AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Sending Indicator */}
          {sending && (
            <div className="w-full max-w-3xl mx-auto flex items-start gap-3.5">
              <div className="w-6 h-6 rounded-[2px] bg-[#111111] text-white flex items-center justify-center font-serif text-xs font-bold shrink-0 mt-0.5">
                C
              </div>
              <div className="flex items-center gap-2 text-xs text-[#777777] font-sans py-1">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Retrieving statutory precedents and validating citations...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar Fixed to Bottom */}
        <div className="p-4 lg:p-6 border-t border-[#E7E5E0] bg-white">
          <form
            onSubmit={handleSendMessage}
            className="max-w-3xl mx-auto flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask about document precedence, name correction rules, or verified forms..."
              disabled={sending}
              className="flex-1 h-11 px-4 bg-[#FAF9F6] border border-[#E7E5E0] rounded-[4px] text-sm font-sans text-[#111111] placeholder:text-[#999999] focus:outline-none focus:border-[#111111] transition-colors"
            />
            <button
              type="submit"
              disabled={sending || !inputQuery.trim()}
              className="h-11 px-4 bg-[#111111] text-white rounded-[4px] text-xs font-sans font-medium hover:bg-black/90 active:bg-black disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5 shrink-0"
            >
              <Send className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Send</span>
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}


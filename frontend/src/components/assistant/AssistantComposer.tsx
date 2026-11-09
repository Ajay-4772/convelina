"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Plus,
  Send,
  Sparkles,
  Shield,
  AlertTriangle,
  Globe,
  Mic,
  MicOff,
  Paperclip,
  Image as ImageIcon,
  Check,
  ChevronDown,
  Loader2,
  Sliders,
  FileText,
  X,
  UploadCloud,
} from "lucide-react";
import { MessageAttachmentItem } from "../../lib/api";

interface AssistantComposerProps {
  inputQuery: string;
  setInputQuery: React.Dispatch<React.SetStateAction<string>> | ((val: string) => void);
  onSendMessage: (e?: React.FormEvent) => void;
  sending: boolean;
  providerStatus?: "operational" | "fallback_offline" | "insufficient_evidence" | string;
  responseLanguage: string;
  onLanguageChange: (lang: string) => void;
  disabled?: boolean;
  variant?: "hero" | "pill";
  placeholder?: string;
  stagedAttachments?: MessageAttachmentItem[];
  onUploadFile?: (file: File) => Promise<void>;
  onRemoveAttachment?: (attachmentId: string) => void;
  uploadingAttachment?: boolean;
}

const LANGUAGES = [
  { code: "en", name: "English", native: "English" },
  { code: "ta", name: "Tamil", native: "தமிழ்" },
  { code: "hi", name: "Hindi", native: "हिन्दी" },
  { code: "te", name: "Telugu", native: "తెలుగు" },
  { code: "kn", name: "Kannada", native: "ಕನ್ನಡ" },
  { code: "ml", name: "Malayalam", native: "മലയാളம்" },
  { code: "bn", name: "Bengali", native: "বাংলা" },
  { code: "mr", name: "Marathi", native: "मराठी" },
];

export default function AssistantComposer({
  inputQuery,
  setInputQuery,
  onSendMessage,
  sending,
  providerStatus = "operational",
  responseLanguage = "en",
  onLanguageChange,
  disabled = false,
  variant = "pill",
  placeholder,
  stagedAttachments = [],
  onUploadFile,
  onRemoveAttachment,
  uploadingAttachment = false,
}: AssistantComposerProps) {
  const [attachMenuOpen, setAttachMenuOpen] = useState(false);
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const attachMenuRef = useRef<HTMLDivElement>(null);
  const modelMenuRef = useRef<HTMLDivElement>(null);

  // Auto-resize textarea smoothly
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const maxHeight = variant === "hero" ? 140 : 120;
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, maxHeight)}px`;
    }
  }, [inputQuery, variant]);

  // Close menus on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (attachMenuRef.current && !attachMenuRef.current.contains(e.target as Node)) {
        setAttachMenuOpen(false);
      }
      if (modelMenuRef.current && !modelMenuRef.current.contains(e.target as Node)) {
        setModelMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const isAttachmentProcessing =
    stagedAttachments.some((a) => a.status === "PROCESSING" || a.status === "UPLOADED") ||
    uploadingAttachment;

  const canSubmit =
    !sending &&
    !disabled &&
    !isAttachmentProcessing &&
    (inputQuery.trim().length > 0 || stagedAttachments.length > 0);

  // Handle Enter to send, Shift+Enter for newline
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSubmit) {
        onSendMessage();
      }
    }
  };

  // Drag and drop handlers
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (onUploadFile && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      for (const file of Array.from(e.dataTransfer.files)) {
        await onUploadFile(file);
      }
    }
  };

  // Clipboard image / document paste (Ctrl+V)
  const handlePaste = async (e: React.ClipboardEvent) => {
    if (!onUploadFile) return;
    if (e.clipboardData.files && e.clipboardData.files.length > 0) {
      e.preventDefault();
      for (const file of Array.from(e.clipboardData.files)) {
        await onUploadFile(file);
      }
    }
  };

  // Hidden file input change handler
  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onUploadFile && e.target.files && e.target.files.length > 0) {
      for (const file of Array.from(e.target.files)) {
        await onUploadFile(file);
      }
      e.target.value = "";
    }
  };

  // Browser speech recognition
  const toggleSpeechRecognition = () => {
    if (typeof window === "undefined") return;
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert("Voice input is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang =
        responseLanguage === "ta"
          ? "ta-IN"
          : responseLanguage === "hi"
          ? "hi-IN"
          : responseLanguage === "te"
          ? "te-IN"
          : "en-IN";
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInputQuery(inputQuery ? `${inputQuery} ${transcript}` : transcript);
      };

      recognition.start();
    } catch (err) {
      console.warn("Speech recognition error:", err);
      setIsListening(false);
    }
  };

  const currentLang = LANGUAGES.find((l) => l.code === responseLanguage) || LANGUAGES[0];

  // Render attachment popover menu
  const renderAttachmentPopover = () => (
    <div className="absolute bottom-11 left-0 w-72 bg-white rounded-2xl border border-[#E5E5E0] shadow-xl p-3 z-50 animate-in fade-in slide-in-from-bottom-2 duration-150">
      <div className="text-[11px] font-semibold text-[#1F1E1D] uppercase tracking-wider mb-2 font-sans">
        Document Attachments
      </div>
      <div className="space-y-1.5 text-xs">
        <button
          type="button"
          onClick={() => {
            fileInputRef.current?.click();
            setAttachMenuOpen(false);
          }}
          className="w-full text-left p-2 rounded-xl bg-[#FAF9F5] hover:bg-[#F3F2EE] border border-[#E5E5E0] space-y-1 transition-colors"
        >
          <div className="flex items-center gap-2 text-[#1F1E1D] font-medium">
            <Paperclip className="w-3.5 h-3.5 text-[#C96442]" />
            <span>Upload Document / Scan (PDF, Image)</span>
          </div>
          <p className="text-[11px] text-[#73726E] leading-relaxed">
            Attach Aadhaar, PAN, Passport, EPF, or rejection notice for OCR extraction.
          </p>
        </button>

        <button
          type="button"
          onClick={() => {
            setAttachMenuOpen(false);
            textareaRef.current?.focus();
          }}
          className="w-full text-left p-2 rounded-xl hover:bg-[#FAF9F5] flex items-center gap-2 text-[#4A4946] transition-colors"
        >
          <ImageIcon className="w-3.5 h-3.5 text-[#73726E]" />
          <span>Paste Screenshot (Ctrl+V)</span>
        </button>
      </div>
    </div>
  );

  // Render Claude-style model & preference popover menu
  const renderModelMenu = () => (
    <div className="absolute bottom-9 right-0 w-64 bg-white rounded-2xl border border-[#E5E5E0] shadow-xl p-2 z-50 animate-in fade-in duration-100">
      <div className="px-2 py-1 text-[10px] uppercase font-semibold text-[#999893] border-b border-[#E5E5E0]/60">
        AI Grounding Engine
      </div>
      <div className="p-2 space-y-1">
        <div className="p-2 rounded-xl bg-[#FAF9F5] border border-[#E5E5E0]">
          <div className="flex items-center justify-between text-xs font-medium text-[#1F1E1D]">
            <span>Sonnet 5.5 / Gemini 2.5</span>
            <span className="text-[10px] font-mono text-[#0D652D] bg-[#E6F4EA] px-1.5 py-0.2 rounded font-medium">
              ACTIVE
            </span>
          </div>
          <p className="text-[10px] text-[#73726E] mt-0.5 leading-snug">
            Deterministic statutory verification with ground-truth citations.
          </p>
        </div>
      </div>

      <div className="px-2 pt-2 pb-1 text-[10px] uppercase font-semibold text-[#999893] border-t border-[#E5E5E0]/60">
        Response Language
      </div>
      <div className="max-h-40 overflow-y-auto space-y-0.5 px-1 py-1">
        {LANGUAGES.map((lang) => {
          const isSelected = lang.code === responseLanguage;
          return (
            <button
              key={lang.code}
              type="button"
              onClick={() => {
                onLanguageChange(lang.code);
                setModelMenuOpen(false);
              }}
              className={`w-full px-2 py-1.5 rounded-lg text-left text-xs flex items-center justify-between transition-colors ${
                isSelected
                  ? "bg-[#FAF9F5] text-[#C96442] font-medium"
                  : "text-[#4A4946] hover:bg-[#FAF9F5] hover:text-[#1F1E1D]"
              }`}
            >
              <span>
                {lang.native} <span className="text-[#999893]">({lang.name})</span>
              </span>
              {isSelected && <Check className="w-3 h-3 text-[#C96442]" />}
            </button>
          );
        })}
      </div>
    </div>
  );

  // Audio Waveform Indicator (matches Claude Screenshot 1, 2, 3)
  const renderWaveform = () => (
    <div
      onClick={toggleSpeechRecognition}
      className="flex items-center gap-[2px] h-5 px-1 py-0.5 text-[#73726E] hover:text-[#1F1E1D] cursor-pointer transition-colors"
      title="Audio voice mode"
      aria-label="Audio voice mode"
    >
      <span className="w-[2px] h-2 bg-current rounded-full" />
      <span className="w-[2px] h-3.5 bg-current rounded-full" />
      <span className="w-[2px] h-2.5 bg-current rounded-full" />
      <span className="w-[2px] h-1.5 bg-current rounded-full" />
    </div>
  );

  // Render Staged Attachment Previews (Claude-style card tray)
  const renderStagedAttachments = () => {
    if ((!stagedAttachments || stagedAttachments.length === 0) && !uploadingAttachment) {
      return null;
    }

    return (
      <div className="flex flex-wrap gap-2 pb-2.5 pt-0.5 animate-in fade-in duration-150">
        {stagedAttachments.map((att) => {
          const isPdf = att.mime_type === "application/pdf" || att.file_name.endsWith(".pdf");
          const isProcessing = att.status === "PROCESSING" || att.status === "UPLOADED";
          const isFailed = att.status === "FAILED";
          const isLowConf = att.ocr_status === "low_confidence";

          return (
            <div
              key={att.id}
              className="group relative flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-[#FAF9F5] border border-[#E5E5E0] hover:border-[#1F1E1D]/30 transition-all text-xs max-w-xs shadow-sm"
            >
              <div className="shrink-0 w-6 h-6 rounded-lg bg-white border border-[#E5E5E0] flex items-center justify-center">
                {isPdf ? (
                  <FileText className="w-3.5 h-3.5 text-[#BA1A1A]" />
                ) : (
                  <ImageIcon className="w-3.5 h-3.5 text-[#006699]" />
                )}
              </div>

              <div className="min-w-0 flex-1">
                <div className="truncate font-medium text-[#1F1E1D] text-[11px]" title={att.file_name}>
                  {att.file_name}
                </div>
                <div className="flex items-center gap-1.5 text-[10px] text-[#73726E]">
                  <span>{Math.round(att.file_size_bytes / 1024)} KB</span>
                  <span>•</span>
                  {isProcessing ? (
                    <span className="flex items-center gap-1 text-[#C96442]">
                      <Loader2 className="w-2.5 h-2.5 animate-spin" />
                      <span>Extracting OCR...</span>
                    </span>
                  ) : isFailed ? (
                    <span className="text-[#BA1A1A] font-medium">Failed</span>
                  ) : isLowConf ? (
                    <span className="text-[#B35900] font-medium" title="OCR confidence < 60%">
                      Low OCR ({att.ocr_confidence ? Math.round(att.ocr_confidence * 100) : 50}%)
                    </span>
                  ) : (
                    <span className="text-[#0D652D] font-medium">
                      Ready ({att.ocr_confidence ? Math.round(att.ocr_confidence * 100) : 95}%)
                    </span>
                  )}
                </div>
              </div>

              {onRemoveAttachment && (
                <button
                  type="button"
                  onClick={() => onRemoveAttachment(att.id)}
                  className="p-1 text-[#999893] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-full transition-colors ml-0.5"
                  title="Remove file"
                  aria-label="Remove attachment"
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </div>
          );
        })}

        {uploadingAttachment && (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#FAF9F5] border border-dashed border-[#C96442] text-xs text-[#C96442] animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span className="text-[11px]">Uploading document...</span>
          </div>
        )}
      </div>
    );
  };

  // =========================================================================
  // 1. HERO VARIANT (Claude Home Screen - Screenshot 1 & 3)
  // =========================================================================
  if (variant === "hero") {
    return (
      <div className="w-full max-w-2xl mx-auto px-4">
        {/* Hidden file input */}
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileInputChange}
          accept=".pdf,.png,.jpg,.jpeg"
          multiple
          className="hidden"
        />

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (canSubmit) onSendMessage(e);
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onPaste={handlePaste}
          className={`relative bg-white rounded-2xl border transition-all shadow-sm hover:shadow focus-within:border-[#1F1E1D]/40 focus-within:ring-1 focus-within:ring-[#1F1E1D]/10 p-3 sm:p-4 flex flex-col justify-between min-h-[120px] ${
            isDragging
              ? "border-dashed border-[#C96442] bg-[#FAF9F5]/70"
              : "border-[#E5E5E0]"
          }`}
        >
          {/* Staged Attachments Preview Cards */}
          {renderStagedAttachments()}

          {/* Top Textarea */}
          <div className="w-full">
            <textarea
              ref={textareaRef}
              rows={2}
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              placeholder={
                stagedAttachments.length > 0
                  ? "Ask about this document, summarize rejection reasons, or check discrepancy..."
                  : placeholder || "How can I help you today?"
              }
              disabled={sending || disabled}
              className="w-full bg-transparent text-sm sm:text-[15px] font-sans text-[#1F1E1D] placeholder:text-[#999893] resize-none focus:outline-none leading-relaxed"
            />
          </div>

          {/* Bottom Controls Row inside card */}
          <div className="flex items-center justify-between pt-2">
            {/* Left: Attachment + Button */}
            <div className="relative shrink-0" ref={attachMenuRef}>
              <button
                type="button"
                onClick={() => setAttachMenuOpen(!attachMenuOpen)}
                className="w-7 h-7 rounded-full text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#FAF9F5] flex items-center justify-center transition-colors"
                title="Add attachment or scan"
                aria-label="Add attachment"
              >
                <Plus className="w-4 h-4" />
              </button>
              {attachMenuOpen && renderAttachmentPopover()}
            </div>

            {/* Right: Model Selector, Mic, Waveform, Send */}
            <div className="flex items-center gap-1.5 sm:gap-2">
              {/* Model Selector (Matches Claude Sonnet 5.5 Medium pill) */}
              <div className="relative" ref={modelMenuRef}>
                <button
                  type="button"
                  onClick={() => setModelMenuOpen(!modelMenuOpen)}
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-sans text-[#4A4946] hover:bg-[#FAF9F5] hover:text-[#1F1E1D] transition-colors"
                  title="Model and response preferences"
                >
                  <span className="font-medium text-[#1F1E1D]">Sonnet 5.5</span>
                  <span className="text-[#999893] text-[11px] font-normal">Medium</span>
                  <ChevronDown className="w-3 h-3 text-[#999893]" />
                </button>
                {modelMenuOpen && renderModelMenu()}
              </div>

              {/* Microphone with Chevron */}
              <button
                type="button"
                onClick={toggleSpeechRecognition}
                className={`inline-flex items-center gap-0.5 p-1 rounded-full transition-colors ${
                  isListening
                    ? "bg-[#C96442] text-white animate-pulse"
                    : "text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#FAF9F5]"
                }`}
                title={isListening ? "Listening... click to stop" : "Voice dictation"}
                aria-label="Voice input"
              >
                <Mic className="w-4 h-4" />
                <ChevronDown className="w-3 h-3 text-[#999893]" />
              </button>

              {/* Audio Waveform */}
              {renderWaveform()}

              {/* Submit button (visible when query or attachments present) */}
              {(inputQuery.trim() || stagedAttachments.length > 0) && (
                <button
                  type="submit"
                  disabled={!canSubmit}
                  className="h-7 px-3 rounded-full bg-[#1F1E1D] text-white hover:bg-black disabled:opacity-40 transition-all flex items-center gap-1 text-xs font-medium shadow-sm ml-1"
                  aria-label="Send inquiry"
                >
                  {sending || isAttachmentProcessing ? (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  ) : (
                    <Send className="w-3 h-3" />
                  )}
                  <span>Send</span>
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    );
  }

  // =========================================================================
  // 2. PILL VARIANT (Claude Active Chat Screen - Screenshot 2)
  // =========================================================================
  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-3">
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileInputChange}
        accept=".pdf,.png,.jpg,.jpeg"
        multiple
        className="hidden"
      />

      <div className="space-y-1.5">
        {/* Staged Attachments Preview Cards */}
        {renderStagedAttachments()}

        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (canSubmit) onSendMessage(e);
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onPaste={handlePaste}
          className={`relative bg-white rounded-full border transition-all shadow-sm hover:shadow focus-within:border-[#1F1E1D]/40 focus-within:ring-1 focus-within:ring-[#1F1E1D]/10 px-3 py-1.5 sm:py-2 flex items-center gap-2 ${
            isDragging
              ? "border-dashed border-[#C96442] bg-[#FAF9F5]/70"
              : "border-[#E5E5E0]"
          }`}
        >
          {/* Left: Attachment + Button */}
          <div className="relative shrink-0" ref={attachMenuRef}>
            <button
              type="button"
              onClick={() => setAttachMenuOpen(!attachMenuOpen)}
              className="w-7 h-7 rounded-full text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#FAF9F5] flex items-center justify-center transition-colors"
              title="Add attachment or scan"
              aria-label="Add attachment"
            >
              <Plus className="w-4 h-4" />
            </button>
            {attachMenuOpen && renderAttachmentPopover()}
          </div>

          {/* Center: Input / Textarea */}
          <div className="flex-1 min-w-0">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              placeholder={
                stagedAttachments.length > 0
                  ? "Ask about attached document(s)..."
                  : placeholder || "Write a message..."
              }
              disabled={sending || disabled}
              className="w-full max-h-32 py-1 px-1 bg-transparent text-sm sm:text-[15px] font-sans text-[#1F1E1D] placeholder:text-[#999893] resize-none focus:outline-none leading-normal"
            />
          </div>

          {/* Right Action Icons: Microphone, Waveform, and Send */}
          <div className="flex items-center gap-1 shrink-0">
            {/* Microphone with Chevron */}
            <button
              type="button"
              onClick={toggleSpeechRecognition}
              className={`inline-flex items-center gap-0.5 p-1 rounded-full transition-colors ${
                isListening
                  ? "bg-[#C96442] text-white animate-pulse"
                  : "text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#FAF9F5]"
              }`}
              title={isListening ? "Listening... click to stop" : "Voice dictation"}
              aria-label="Voice input"
            >
              <Mic className="w-4 h-4" />
              <ChevronDown className="w-3 h-3 text-[#999893]" />
            </button>

            {/* Audio Waveform */}
            {renderWaveform()}

            {/* Send Button */}
            {inputQuery.trim() || stagedAttachments.length > 0 ? (
              <button
                type="submit"
                disabled={!canSubmit}
                className="w-7 h-7 rounded-full bg-[#1F1E1D] text-white hover:bg-black disabled:opacity-30 disabled:cursor-not-allowed transition-all flex items-center justify-center shadow-sm ml-1"
                aria-label="Send message"
              >
                {sending || isAttachmentProcessing ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Send className="w-3.5 h-3.5" />
                )}
              </button>
            ) : null}
          </div>
        </form>
      </div>
    </div>
  );
}

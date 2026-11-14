"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Plus,
  ArrowUp,
  Globe,
  Mic,
  MicOff,
  Paperclip,
  Image as ImageIcon,
  Check,
  ChevronDown,
  Loader2,
  FileText,
  X,
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
  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const attachMenuRef = useRef<HTMLDivElement>(null);
  const langMenuRef = useRef<HTMLDivElement>(null);

  const isHero = variant === "hero";

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      const maxHeight = isHero ? 150 : 128;
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, maxHeight)}px`;
    }
  }, [inputQuery, isHero]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (attachMenuRef.current && !attachMenuRef.current.contains(e.target as Node)) {
        setAttachMenuOpen(false);
      }
      if (langMenuRef.current && !langMenuRef.current.contains(e.target as Node)) {
        setLangMenuOpen(false);
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

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSubmit) {
        onSendMessage();
      }
    }
  };

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

  const handlePaste = async (e: React.ClipboardEvent) => {
    if (!onUploadFile) return;
    if (e.clipboardData.files && e.clipboardData.files.length > 0) {
      e.preventDefault();
      for (const file of Array.from(e.clipboardData.files)) {
        await onUploadFile(file);
      }
    }
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (onUploadFile && e.target.files && e.target.files.length > 0) {
      for (const file of Array.from(e.target.files)) {
        await onUploadFile(file);
      }
      e.target.value = "";
    }
  };

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

  const renderAttachmentPopover = () => (
    <div className="absolute bottom-10 left-0 w-72 bg-white rounded-2xl border border-[#E5E5E0] shadow-xl p-3 z-50 animate-in fade-in slide-in-from-bottom-2 duration-150">
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
            <Paperclip className="w-3.5 h-3.5 text-[#1F1E1D]" />
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

  const renderLanguageMenu = () => (
    <div className="absolute bottom-9 right-0 w-52 bg-white rounded-2xl border border-[#E5E5E0] shadow-xl p-2 z-50 animate-in fade-in duration-100">
      <div className="px-2 py-1 text-[10px] uppercase font-semibold text-[#999893] border-b border-[#E5E5E0]/60">
        Response Language
      </div>
      <div className="max-h-48 overflow-y-auto space-y-0.5 pt-1">
        {LANGUAGES.map((lang) => {
          const isSelected = lang.code === responseLanguage;
          return (
            <button
              key={lang.code}
              type="button"
              onClick={() => {
                onLanguageChange(lang.code);
                setLangMenuOpen(false);
              }}
              className={`w-full px-2.5 py-1.5 rounded-lg text-left text-xs flex items-center justify-between transition-colors ${
                isSelected
                  ? "bg-[#F4F3EF] text-[#1F1E1D] font-medium"
                  : "text-[#4A4946] hover:bg-[#FAF9F5] hover:text-[#1F1E1D]"
              }`}
            >
              <span>
                {lang.native} <span className="text-[#999893]">({lang.name})</span>
              </span>
              {isSelected && <Check className="w-3 h-3 text-[#1F1E1D]" />}
            </button>
          );
        })}
      </div>
    </div>
  );

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
              className="group relative flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-[#FAF9F5] border border-[#E5E5E0] hover:border-[#1F1E1D]/30 transition-all text-xs max-w-xs shadow-2xs"
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
                    <span className="flex items-center gap-1 text-[#73726E]">
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
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#FAF9F5] border border-dashed border-[#1F1E1D]/40 text-xs text-[#4A4946] animate-pulse">
            <Loader2 className="w-3 h-3 animate-spin" />
            <span className="text-[11px]">Uploading document...</span>
          </div>
        )}
      </div>
    );
  };

  const defaultPlaceholder = isHero
    ? placeholder || "How can I help you today?"
    : placeholder || "Write a message...";

  return (
    <div className={isHero ? "w-full max-w-2xl mx-auto" : "w-full max-w-3xl mx-auto px-4 pb-4 pt-1"}>
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
        className={`relative bg-white rounded-2xl border transition-all shadow-sm hover:shadow focus-within:border-[#1F1E1D]/40 focus-within:ring-1 focus-within:ring-[#1F1E1D]/10 flex flex-col justify-between ${
          isHero ? "p-3.5 sm:p-4 min-h-[120px]" : "px-3.5 py-2.5"
        } ${
          isDragging
            ? "border-dashed border-[#1F1E1D] bg-[#FAF9F5]/80"
            : "border-[#E5E5E0]"
        }`}
      >
        {renderStagedAttachments()}

        <div className="w-full">
          <textarea
            ref={textareaRef}
            rows={isHero ? 2 : 1}
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            onPaste={handlePaste}
            placeholder={
              stagedAttachments.length > 0
                ? isHero
                  ? "Ask about this document, summarize rejection reasons, or check discrepancy..."
                  : "Ask about attached document(s)..."
                : defaultPlaceholder
            }
            disabled={sending || disabled}
            className="w-full bg-transparent text-sm sm:text-[15px] font-sans text-[#1F1E1D] placeholder:text-[#999893] resize-none focus:outline-none leading-relaxed"
          />
        </div>

        <div className="flex items-center justify-between pt-2">
          {/* Left Toolbar: Attachment */}
          <div className="flex items-center gap-1">
            <div className="relative shrink-0" ref={attachMenuRef}>
              <button
                type="button"
                onClick={() => setAttachMenuOpen(!attachMenuOpen)}
                className="w-8 h-8 rounded-full text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#F4F3EF] flex items-center justify-center transition-colors"
                title="Add document or scan"
                aria-label="Add attachment"
              >
                <Plus className="w-4 h-4" />
              </button>
              {attachMenuOpen && renderAttachmentPopover()}
            </div>
          </div>

          {/* Right Toolbar: Language, Dictation Mic, Send */}
          <div className="flex items-center gap-1.5">
            <div className="relative" ref={langMenuRef}>
              <button
                type="button"
                onClick={() => setLangMenuOpen(!langMenuOpen)}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-sans text-[#5E5E5E] hover:bg-[#F4F3EF] hover:text-[#1F1E1D] transition-colors"
                title="Select response language"
                aria-label="Select response language"
              >
                <Globe className="w-3.5 h-3.5 text-[#73726E]" />
                <span>{currentLang.native}</span>
                <ChevronDown className="w-3 h-3 text-[#999893]" />
              </button>
              {langMenuOpen && renderLanguageMenu()}
            </div>

            <button
              type="button"
              onClick={toggleSpeechRecognition}
              className={`w-8 h-8 rounded-full flex items-center justify-center transition-colors ${
                isListening
                  ? "bg-[#BA1A1A] text-white animate-pulse"
                  : "text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#F4F3EF]"
              }`}
              title={isListening ? "Listening... click to stop" : "Voice dictation"}
              aria-label="Voice input"
            >
              {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>

            <button
              type="submit"
              disabled={!canSubmit}
              className="h-8 px-3 rounded-full bg-[#1F1E1D] text-white hover:bg-black disabled:bg-[#EBE9E4] disabled:text-[#999893] disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-1.5 text-xs font-medium shadow-2xs"
              aria-label="Send message"
            >
              {sending || isAttachmentProcessing ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ArrowUp className="w-3.5 h-3.5" />
              )}
              <span className={isHero ? "" : "sr-only"}>Send</span>
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}

"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Search, X, MessageSquare, Pin, ArrowRight, Loader2 } from "lucide-react";
import { searchConversations, ConversationItem, MessageItem } from "../../lib/api";

interface ConversationSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectConversation: (conversationId: string) => void;
  idToken: string | null;
}

interface SearchResultItem {
  conversation: ConversationItem;
  matched_messages: MessageItem[];
}

export default function ConversationSearchModal({
  isOpen,
  onClose,
  onSelectConversation,
  idToken,
}: ConversationSearchModalProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setResults([]);
      setHasSearched(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Handle Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Debounced search
  const performSearch = useCallback(
    async (searchTerm: string) => {
      const trimmed = searchTerm.trim();
      if (!trimmed || !idToken) {
        setResults([]);
        setHasSearched(false);
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const resp = await searchConversations(idToken, trimmed);
        setResults(resp.results || []);
        setHasSearched(true);
      } catch (err) {
        console.error("Search conversations failed:", err);
        setResults([]);
        setHasSearched(true);
      } finally {
        setLoading(false);
      }
    },
    [idToken]
  );

  useEffect(() => {
    const timer = setTimeout(() => {
      if (query.trim()) {
        performSearch(query);
      } else {
        setResults([]);
        setHasSearched(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [query, performSearch]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 sm:pt-28 px-4 bg-black/40 backdrop-blur-[2px] animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl bg-white rounded-2xl border border-[#E5E5E0] shadow-2xl overflow-hidden flex flex-col max-h-[75vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Bar Header */}
        <div className="p-3.5 sm:p-4 border-b border-[#E5E5E0] flex items-center gap-3 bg-[#FAF9F5]">
          <Search className="w-5 h-5 text-[#73726E] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search inquiries, message notes, or statutory questions..."
            className="flex-1 bg-transparent text-sm sm:text-base font-sans text-[#1F1E1D] placeholder:text-[#999893] focus:outline-none"
          />
          {loading && <Loader2 className="w-4 h-4 text-[#C96442] animate-spin shrink-0" />}
          {query && !loading && (
            <button
              onClick={() => {
                setQuery("");
                inputRef.current?.focus();
              }}
              className="p-1 hover:bg-[#E5E5E0] rounded-full text-[#73726E] transition-colors"
              aria-label="Clear search"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <span className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-mono text-[#73726E] bg-white border border-[#E5E5E0] rounded">
            ESC
          </span>
        </div>

        {/* Results Stream */}
        <div className="flex-1 overflow-y-auto p-2 divide-y divide-[#E5E5E0]/60">
          {loading && results.length === 0 ? (
            <div className="p-8 text-center text-xs text-[#73726E] font-sans">
              Searching your conversations...
            </div>
          ) : hasSearched && results.length === 0 ? (
            <div className="p-8 text-center space-y-1">
              <p className="text-sm font-medium text-[#1F1E1D]">No inquiries found</p>
              <p className="text-xs text-[#73726E]">
                No conversation titles or messages match &ldquo;{query}&rdquo;.
              </p>
            </div>
          ) : results.length > 0 ? (
            results.map(({ conversation, matched_messages }) => (
              <div
                key={conversation.id}
                onClick={() => {
                  onSelectConversation(conversation.id);
                  onClose();
                }}
                className="group p-3 hover:bg-[#FAF9F5] rounded-xl cursor-pointer transition-colors space-y-1"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    {conversation.is_pinned ? (
                      <Pin className="w-3.5 h-3.5 text-[#C96442] shrink-0 fill-[#C96442]" />
                    ) : (
                      <MessageSquare className="w-3.5 h-3.5 text-[#73726E] shrink-0" />
                    )}
                    <span className="text-xs sm:text-sm font-medium text-[#1F1E1D] group-hover:text-[#C96442] truncate transition-colors">
                      {conversation.title || "Inquiry Session"}
                    </span>
                  </div>
                  <div className="flex items-center gap-1.5 shrink-0 text-[10px] text-[#999893]">
                    <span>
                      {new Date(conversation.updated_at).toLocaleDateString("en-IN", {
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                    <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity text-[#C96442]" />
                  </div>
                </div>

                {/* Snippets of matched message content */}
                {matched_messages && matched_messages.length > 0 && (
                  <div className="pl-5 space-y-0.5">
                    {matched_messages.slice(0, 2).map((msg, midx) => (
                      <p key={midx} className="text-[11px] text-[#73726E] truncate font-sans">
                        <span className="font-semibold text-[#4A4946]">
                          {msg.role === "user" ? "You: " : "Assistant: "}
                        </span>
                        {msg.content}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-xs text-[#73726E] font-sans leading-relaxed">
              Type to search through your past inquiry sessions and statutory messages.
              <div className="mt-2 text-[11px] text-[#999893]">
                Shortcut: press <kbd className="px-1 py-0.5 bg-[#FAF9F5] border border-[#E5E5E0] rounded">Ctrl+K</kbd> anywhere to search.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


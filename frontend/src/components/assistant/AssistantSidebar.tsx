"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Plus,
  Search,
  Pin,
  PinOff,
  Trash2,
  Edit2,
  ChevronDown,
  ChevronRight,
  Box,
  Layers,
  Briefcase,
  SlidersHorizontal,
  PanelLeftClose,
  ListFilter,
  Check,
  Globe,
} from "lucide-react";
import { ConversationItem } from "../../lib/api";
import ClaudeSunburst from "./ClaudeSunburst";

interface AssistantSidebarProps {
  conversations: ConversationItem[];
  activeConvId?: string;
  onSelectConversation: (id: string) => void;
  onNewInquiry: () => void;
  onOpenSearch: () => void;
  onTogglePin: (id: string, currentPinned: boolean) => void;
  onPromptRename: (id: string, currentTitle: string) => void;
  onPromptDelete: (id: string) => void;
  isOpen: boolean;
  onToggleOpen: () => void;
  loading?: boolean;
  userProfile?: {
    full_name?: string;
    email?: string;
    role?: string;
  };
  onOpenCustomize?: () => void;
}

interface GroupedConvs {
  today: ConversationItem[];
  yesterday: ConversationItem[];
  previous7Days: ConversationItem[];
  older: ConversationItem[];
}

function groupConversations(convs: ConversationItem[]): GroupedConvs {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const startOfYesterday = startOfToday - 24 * 60 * 60 * 1000;
  const startOf7Days = startOfToday - 7 * 24 * 60 * 60 * 1000;

  const groups: GroupedConvs = {
    today: [],
    yesterday: [],
    previous7Days: [],
    older: [],
  };

  for (const c of convs) {
    const updated = new Date(c.updated_at).getTime();
    if (updated >= startOfToday) {
      groups.today.push(c);
    } else if (updated >= startOfYesterday) {
      groups.yesterday.push(c);
    } else if (updated >= startOf7Days) {
      groups.previous7Days.push(c);
    } else {
      groups.older.push(c);
    }
  }

  return groups;
}

export default function AssistantSidebar({
  conversations,
  activeConvId,
  onSelectConversation,
  onNewInquiry,
  onOpenSearch,
  onTogglePin,
  onPromptRename,
  onPromptDelete,
  isOpen,
  onToggleOpen,
  loading = false,
  userProfile,
  onOpenCustomize,
}: AssistantSidebarProps) {
  const [pinnedExpanded, setPinnedExpanded] = useState(true);
  const [chatsExpanded, setChatsExpanded] = useState(true);

  const pinnedConvs = conversations.filter((c) => c.is_pinned);
  const unpinnedConvs = conversations.filter((c) => !c.is_pinned && !c.is_archived);
  const groupedChats = groupConversations(unpinnedConvs);

  // If sidebar is collapsed on desktop, return null (the canvas handles the toggle button)
  if (!isOpen) return null;

  return (
    <aside className="w-64 shrink-0 h-screen bg-[#FBFBFA] border-r border-[#E5E5E0] flex flex-col justify-between select-none z-30 transition-all duration-200">
      {/* Top Header & Navigation */}
      <div className="flex-1 flex flex-col min-h-0 overflow-y-auto">
        {/* Brand & Collapse Header */}
        <div className="h-12 px-3.5 flex items-center justify-between border-b border-[#E5E5E0]/60">
          <Link href="/app" className="flex items-center gap-2 group">
            {/* Terracotta brand sunburst mark */}
            <ClaudeSunburst className="w-5 h-5 shrink-0" size={20} />
            <span className="font-serif text-[#1F1E1D] text-sm tracking-tight font-medium">
              CONVELINA
            </span>
          </Link>
          <button
            onClick={onToggleOpen}
            className="p-1 text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-lg transition-colors"
            title="Collapse sidebar (Ctrl+B)"
            aria-label="Collapse sidebar"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* Primary Action: + New Button (Matches Claude Screenshot 3) */}
        <div className="p-3 pb-2 space-y-1">
          <button
            onClick={onNewInquiry}
            className="w-full h-9 px-3 bg-[#EBE9E4] hover:bg-[#E2DFD9] text-[#1F1E1D] rounded-xl flex items-center justify-between text-xs font-sans font-medium transition-colors group"
            type="button"
            title="Start new inquiry (Ctrl+N)"
          >
            <span className="flex items-center gap-2">
              <Plus className="w-4 h-4 text-[#1F1E1D]" />
              <span>New</span>
            </span>
            <span className="text-[11px] font-sans text-[#73726E]">
              Ctrl+N
            </span>
          </button>

          {/* Quick Menu (Matches Claude Screenshot 3: Search, Projects, Artifacts, Customize) */}
          <div className="pt-1.5 space-y-0.5">
            {/* Search */}
            <button
              onClick={onOpenSearch}
              className="w-full h-8 px-2.5 rounded-lg flex items-center justify-between text-xs text-[#4A4946] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] transition-colors"
              type="button"
              title="Search inquiries (Ctrl+K)"
            >
              <span className="flex items-center gap-2.5">
                <Search className="w-3.5 h-3.5 text-[#73726E]" />
                <span>Search</span>
              </span>
              <kbd className="text-[9px] font-mono text-[#999893] bg-white/70 border border-[#E5E5E0] px-1 py-0.2 rounded">
                Ctrl+K
              </kbd>
            </button>

            {/* Projects -> Inconsistencies */}
            <Link
              href="/app/inconsistencies"
              className="w-full h-8 px-2.5 rounded-lg flex items-center gap-2.5 text-xs text-[#4A4946] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] transition-colors"
              title="Document Projects & Inconsistencies"
            >
              <Box className="w-3.5 h-3.5 text-[#73726E]" />
              <span>Projects</span>
            </Link>

            {/* Artifacts -> Forms Repository */}
            <Link
              href="/app/forms"
              className="w-full h-8 px-2.5 rounded-lg flex items-center gap-2.5 text-xs text-[#4A4946] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] transition-colors"
              title="Statutory Artifacts & Prescribed Forms"
            >
              <Layers className="w-3.5 h-3.5 text-[#73726E]" />
              <span>Artifacts</span>
            </Link>

            {/* Customize / Preferences (Matches Briefcase in Claude Screenshot 3) */}
            <button
              type="button"
              onClick={onOpenCustomize}
              className="w-full h-8 px-2.5 rounded-lg flex items-center gap-2.5 text-xs text-[#4A4946] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] transition-colors"
              title="Customize language and response preferences"
            >
              <Briefcase className="w-3.5 h-3.5 text-[#73726E]" />
              <span>Customize</span>
            </button>
          </div>
        </div>

        {/* Pinned Section (Matches Claude Screenshot 3) */}
        <div className="px-3 pt-2">
          <div
            onClick={() => setPinnedExpanded(!pinnedExpanded)}
            className="flex items-center justify-between py-1 px-1 cursor-pointer text-[#73726E] hover:text-[#1F1E1D] group"
          >
            <div className="flex items-center gap-1">
              <span className="text-[11px] font-sans font-medium text-[#73726E]">
                Pinned
              </span>
              {pinnedExpanded ? (
                <ChevronDown className="w-3 h-3 text-[#999893]" />
              ) : (
                <ChevronRight className="w-3 h-3 text-[#999893]" />
              )}
            </div>
          </div>

          {pinnedExpanded && (
            <div className="mt-0.5 space-y-0.5">
              {pinnedConvs.length > 0 ? (
                pinnedConvs.map((conv) => {
                  const isActive = conv.id === activeConvId;
                  return (
                    <div
                      key={conv.id}
                      onClick={() => onSelectConversation(conv.id)}
                      className={`group w-full px-2 py-1.5 rounded-lg flex items-center justify-between cursor-pointer transition-colors text-xs ${
                        isActive
                          ? "bg-[#EBE9E4] text-[#1F1E1D] font-medium"
                          : "text-[#4A4946] hover:bg-[#EBE9E4]/60 hover:text-[#1F1E1D]"
                      }`}
                    >
                      <div className="min-w-0 flex-1 flex items-center gap-2">
                        <Box className="w-3.5 h-3.5 text-[#73726E] shrink-0" />
                        <span className="truncate">{conv.title || "Inquiry Session"}</span>
                      </div>
                      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onTogglePin(conv.id, true);
                          }}
                          className="p-1 hover:text-[#C96442] rounded transition-colors"
                          title="Unpin conversation"
                        >
                          <PinOff className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onPromptRename(conv.id, conv.title || "Inquiry Session");
                          }}
                          className="p-1 hover:text-[#1F1E1D] rounded transition-colors"
                          title="Rename inquiry"
                        >
                          <Edit2 className="w-3 h-3" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onPromptDelete(conv.id);
                          }}
                          className="p-1 hover:text-[#BA1A1A] rounded transition-colors"
                          title="Delete inquiry"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="px-2 py-1 text-[11px] text-[#999893] italic">
                  No pinned inquiries
                </div>
              )}
            </div>
          )}
        </div>

        {/* Chats History Section (Matches Claude Screenshot 3) */}
        <div className="px-3 pt-3 flex-1">
          <div
            onClick={() => setChatsExpanded(!chatsExpanded)}
            className="flex items-center justify-between py-1 px-1 cursor-pointer text-[#73726E] hover:text-[#1F1E1D] group"
          >
            <div className="flex items-center gap-1">
              <span className="text-[11px] font-sans font-medium text-[#73726E]">
                Chats
              </span>
              {chatsExpanded ? (
                <ChevronDown className="w-3 h-3 text-[#999893]" />
              ) : (
                <ChevronRight className="w-3 h-3 text-[#999893]" />
              )}
            </div>
            <ListFilter className="w-3.5 h-3.5 text-[#999893] group-hover:text-[#1F1E1D] transition-colors" />
          </div>

          {chatsExpanded && (
            <div className="mt-0.5 pb-4 space-y-2.5">
              {loading ? (
                <div className="px-2 py-2 text-xs text-[#73726E] font-sans">
                  Loading inquiries...
                </div>
              ) : unpinnedConvs.length > 0 ? (
                <>
                  {/* Today */}
                  {groupedChats.today.length > 0 && (
                    <ConversationGroup
                      label="Today"
                      items={groupedChats.today}
                      activeId={activeConvId}
                      onSelect={onSelectConversation}
                      onPin={(id) => onTogglePin(id, false)}
                      onRename={onPromptRename}
                      onDelete={onPromptDelete}
                    />
                  )}

                  {/* Yesterday */}
                  {groupedChats.yesterday.length > 0 && (
                    <ConversationGroup
                      label="Yesterday"
                      items={groupedChats.yesterday}
                      activeId={activeConvId}
                      onSelect={onSelectConversation}
                      onPin={(id) => onTogglePin(id, false)}
                      onRename={onPromptRename}
                      onDelete={onPromptDelete}
                    />
                  )}

                  {/* Previous 7 Days */}
                  {groupedChats.previous7Days.length > 0 && (
                    <ConversationGroup
                      label="Previous 7 Days"
                      items={groupedChats.previous7Days}
                      activeId={activeConvId}
                      onSelect={onSelectConversation}
                      onPin={(id) => onTogglePin(id, false)}
                      onRename={onPromptRename}
                      onDelete={onPromptDelete}
                    />
                  )}

                  {/* Older */}
                  {groupedChats.older.length > 0 && (
                    <ConversationGroup
                      label="Older"
                      items={groupedChats.older}
                      activeId={activeConvId}
                      onSelect={onSelectConversation}
                      onPin={(id) => onTogglePin(id, false)}
                      onRename={onPromptRename}
                      onDelete={onPromptDelete}
                    />
                  )}
                </>
              ) : (
                <div className="px-2 py-2 text-xs text-[#999893] leading-relaxed">
                  No previous sessions.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer User Profile & Settings */}
      <div className="p-3 border-t border-[#E5E5E0] bg-[#FBFBFA]">
        <Link
          href="/app/profile"
          className="w-full p-1.5 hover:bg-[#EBE9E4] rounded-xl flex items-center justify-between transition-colors group"
        >
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-7 h-7 rounded-full bg-[#1F1E1D] text-white flex items-center justify-center text-xs font-medium shrink-0">
              {userProfile?.full_name ? userProfile.full_name[0].toUpperCase() : "C"}
            </div>
            <div className="min-w-0 text-left">
              <div className="text-xs font-medium text-[#1F1E1D] truncate">
                {userProfile?.full_name || "Citizen Account"}
              </div>
              <div className="text-[10px] text-[#73726E] truncate">
                {userProfile?.email || "Source-Grounded"}
              </div>
            </div>
          </div>
          <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-white border border-[#E5E5E0] text-[#73726E]">
            {userProfile?.role || "USER"}
          </span>
        </Link>
      </div>
    </aside>
  );
}

interface ConversationGroupProps {
  label: string;
  items: ConversationItem[];
  activeId?: string;
  onSelect: (id: string) => void;
  onPin: (id: string) => void;
  onRename: (id: string, currentTitle: string) => void;
  onDelete: (id: string) => void;
}

function ConversationGroup({
  label,
  items,
  activeId,
  onSelect,
  onPin,
  onRename,
  onDelete,
}: ConversationGroupProps) {
  return (
    <div className="space-y-0.5">
      <div className="text-[10px] text-[#999893] font-medium uppercase tracking-wider px-2 py-0.5">
        {label}
      </div>
      {items.map((conv) => {
        const isActive = conv.id === activeId;
        return (
          <div
            key={conv.id}
            onClick={() => onSelect(conv.id)}
            className={`group w-full px-2 py-1.5 rounded-lg flex items-center justify-between cursor-pointer transition-colors text-xs ${
              isActive
                ? "bg-[#EBE9E4] text-[#1F1E1D] font-medium"
                : "text-[#4A4946] hover:bg-[#EBE9E4]/60 hover:text-[#1F1E1D]"
            }`}
          >
            {/* Claude-style hollow circle bullet (Screenshot 3) */}
            <div className="min-w-0 flex-1 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full border border-[#999893] shrink-0" />
              <span className="truncate pr-1">{conv.title || "Inquiry Session"}</span>
            </div>
            <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onPin(conv.id);
                }}
                className="p-1 hover:text-[#C96442] rounded transition-colors"
                title="Pin inquiry"
              >
                <Pin className="w-3 h-3" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onRename(conv.id, conv.title || "Inquiry Session");
                }}
                className="p-1 hover:text-[#1F1E1D] rounded transition-colors"
                title="Rename inquiry"
              >
                <Edit2 className="w-3 h-3" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conv.id);
                }}
                className="p-1 hover:text-[#BA1A1A] rounded transition-colors"
                title="Delete inquiry"
              >
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}


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
  PanelLeftClose,
} from "lucide-react";
import { ConversationItem } from "../../lib/api";
import Logo from "../ui/Logo";

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
}: AssistantSidebarProps) {
  const [pinnedExpanded, setPinnedExpanded] = useState(true);
  const [chatsExpanded, setChatsExpanded] = useState(true);

  const pinnedConvs = conversations.filter((c) => c.is_pinned);
  const unpinnedConvs = conversations.filter((c) => !c.is_pinned && !c.is_archived);
  const groupedChats = groupConversations(unpinnedConvs);

  if (!isOpen) return null;

  return (
    <aside className="w-64 shrink-0 h-screen bg-[#F7F6F2] border-r border-[#E5E5E0] flex flex-col justify-between select-none z-30 transition-all duration-200">
      <div className="flex-1 flex flex-col min-h-0 overflow-y-auto">
        {/* CONVELINA Brand & Collapse Control */}
        <div className="h-12 px-3.5 flex items-center justify-between border-b border-[#E5E5E0]/70 shrink-0">
          <Logo
            size={20}
            showText={true}
            href="/app"
            textClassName="font-serif text-[#1F1E1D] text-sm tracking-tight font-medium"
          />
          <button
            onClick={onToggleOpen}
            className="p-1.5 text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-lg transition-colors"
            title="Hide sidebar (Ctrl+B)"
            aria-label="Collapse sidebar"
            type="button"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* Primary Action: New Chat */}
        <div className="p-3 pb-2">
          <button
            onClick={onNewInquiry}
            className="w-full h-9 px-3 bg-white hover:bg-[#EBE9E4] text-[#1F1E1D] border border-[#E5E5E0] rounded-xl flex items-center gap-2 text-xs font-sans font-medium transition-colors shadow-2xs"
            type="button"
            title="Start a new chat (Ctrl+N)"
          >
            <Plus className="w-4 h-4 text-[#1F1E1D]" />
            <span>New Chat</span>
          </button>
        </div>

        {/* Pinned Chats (rendered only when pinned chats exist) */}
        {pinnedConvs.length > 0 && (
          <div className="px-3 pt-2">
            <button
              type="button"
              onClick={() => setPinnedExpanded(!pinnedExpanded)}
              className="w-full flex items-center gap-1 py-1 px-1 text-[#73726E] hover:text-[#1F1E1D] transition-colors"
            >
              <span className="text-[11px] font-sans font-medium">Pinned</span>
              {pinnedExpanded ? (
                <ChevronDown className="w-3 h-3 text-[#999893]" />
              ) : (
                <ChevronRight className="w-3 h-3 text-[#999893]" />
              )}
            </button>

            {pinnedExpanded && (
              <div className="mt-0.5 space-y-0.5">
                {pinnedConvs.map((conv) => (
                  <SidebarChatRow
                    key={conv.id}
                    conv={conv}
                    isActive={conv.id === activeConvId}
                    isPinned={true}
                    onSelect={onSelectConversation}
                    onTogglePin={() => onTogglePin(conv.id, true)}
                    onRename={onPromptRename}
                    onDelete={onPromptDelete}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Chronological Left-Side Chat History */}
        <div className="px-3 pt-2 flex-1">
          <div className="flex items-center justify-between py-1 px-1">
            <button
              type="button"
              onClick={() => setChatsExpanded(!chatsExpanded)}
              className="flex items-center gap-1 text-[#73726E] hover:text-[#1F1E1D] transition-colors"
            >
              <span className="text-[11px] font-sans font-medium">Chats</span>
              {chatsExpanded ? (
                <ChevronDown className="w-3 h-3 text-[#999893]" />
              ) : (
                <ChevronRight className="w-3 h-3 text-[#999893]" />
              )}
            </button>
            <button
              type="button"
              onClick={onOpenSearch}
              className="p-1 text-[#73726E] hover:text-[#1F1E1D] hover:bg-[#EBE9E4] rounded-md transition-colors"
              title="Search chat history (Ctrl+K)"
              aria-label="Search chat history"
            >
              <Search className="w-3.5 h-3.5" />
            </button>
          </div>

          {chatsExpanded && (
            <div className="mt-1 pb-4 space-y-3">
              {loading ? (
                <div className="px-2 py-2 text-xs text-[#73726E] font-sans">
                  Loading chat history...
                </div>
              ) : unpinnedConvs.length > 0 ? (
                <>
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
                  No past chats yet.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Footer Citizen Account */}
      <div className="p-3 border-t border-[#E5E5E0] bg-[#F7F6F2] shrink-0">
        <Link
          href="/app/profile"
          className="w-full p-1.5 hover:bg-[#EBE9E4] rounded-xl flex items-center justify-between transition-colors"
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
                {userProfile?.email || "CONVELINA Workspace"}
              </div>
            </div>
          </div>
          <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-white border border-[#E5E5E0] text-[#73726E] shrink-0">
            {userProfile?.role || "USER"}
          </span>
        </Link>
      </div>
    </aside>
  );
}

interface SidebarChatRowProps {
  conv: ConversationItem;
  isActive: boolean;
  isPinned: boolean;
  onSelect: (id: string) => void;
  onTogglePin: () => void;
  onRename: (id: string, currentTitle: string) => void;
  onDelete: (id: string) => void;
}

function SidebarChatRow({
  conv,
  isActive,
  isPinned,
  onSelect,
  onTogglePin,
  onRename,
  onDelete,
}: SidebarChatRowProps) {
  const title = conv.title || "Untitled Chat";
  return (
    <div
      onClick={() => onSelect(conv.id)}
      className={`group w-full px-2.5 py-1.5 rounded-lg flex items-center justify-between cursor-pointer transition-colors text-xs ${
        isActive
          ? "bg-[#EBE9E4] text-[#1F1E1D] font-medium"
          : "text-[#4A4946] hover:bg-[#EBE9E4]/70 hover:text-[#1F1E1D]"
      }`}
    >
      <div className="min-w-0 flex-1 flex items-center gap-2">
        {isPinned && <Pin className="w-3 h-3 text-[#73726E] shrink-0" />}
        <span className="truncate pr-1">{title}</span>
      </div>
      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onTogglePin();
          }}
          className="p-1 hover:text-[#1F1E1D] rounded transition-colors"
          title={isPinned ? "Unpin chat" : "Pin chat"}
          aria-label={isPinned ? "Unpin chat" : "Pin chat"}
        >
          {isPinned ? <PinOff className="w-3 h-3" /> : <Pin className="w-3 h-3" />}
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRename(conv.id, title);
          }}
          className="p-1 hover:text-[#1F1E1D] rounded transition-colors"
          title="Rename chat"
          aria-label="Rename chat"
        >
          <Edit2 className="w-3 h-3" />
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDelete(conv.id);
          }}
          className="p-1 hover:text-[#BA1A1A] rounded transition-colors"
          title="Delete chat"
          aria-label="Delete chat"
        >
          <Trash2 className="w-3 h-3" />
        </button>
      </div>
    </div>
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
      <div className="text-[10px] text-[#999893] font-medium uppercase tracking-wider px-2.5 py-0.5">
        {label}
      </div>
      {items.map((conv) => (
        <SidebarChatRow
          key={conv.id}
          conv={conv}
          isActive={conv.id === activeId}
          isPinned={false}
          onSelect={onSelect}
          onTogglePin={() => onPin(conv.id)}
          onRename={onRename}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}

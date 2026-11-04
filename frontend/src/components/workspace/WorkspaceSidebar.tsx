"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Scale,
  Sparkles,
  FolderOpen,
  User,
  X,
} from "lucide-react";

interface WorkspaceSidebarProps {
  mobileOpen?: boolean;
  onCloseMobile?: () => void;
}

const NAV_ITEMS = [
  {
    name: "Overview",
    href: "/app",
    icon: LayoutDashboard,
    exact: true,
  },
  {
    name: "Inconsistencies",
    href: "/app/inconsistencies",
    icon: Scale,
    exact: false,
  },
  {
    name: "AI Assistant",
    href: "/app/assistant",
    icon: Sparkles,
    exact: false,
  },
  {
    name: "Forms Repository",
    href: "/app/forms",
    icon: FolderOpen,
    exact: false,
  },
  {
    name: "Profile",
    href: "/app/profile",
    icon: User,
    exact: false,
  },
];

export default function WorkspaceSidebar({
  mobileOpen = false,
  onCloseMobile,
}: WorkspaceSidebarProps) {
  const pathname = usePathname();

  const isLinkActive = (item: (typeof NAV_ITEMS)[0]) => {
    if (item.exact) {
      return pathname === item.href;
    }
    return pathname.startsWith(item.href);
  };

  const navContent = (
    <div className="flex flex-col h-full bg-[#FAF9F6] border-r border-[#E7E5E0] select-none">
      {/* Brand Header */}
      <div className="h-14 px-6 flex items-center justify-between border-b border-[#E7E5E0]">
        <Link href="/app" className="flex items-center gap-2.5 group">
          <span className="w-5 h-5 bg-[#111111] text-white flex items-center justify-center font-serif text-[11px] font-bold rounded-[2px]">
            C
          </span>
          <span className="font-serif text-[#111111] text-[15px] tracking-tight font-normal">
            CONVELINA
          </span>
          <span className="font-sans text-[10px] text-[#5E5E5E] uppercase tracking-widest px-1.5 py-0.5 rounded-[2px] bg-[#EFEEEB] border border-[#E7E5E0] font-medium ml-1">
            Workspace
          </span>
        </Link>
        {onCloseMobile && (
          <button
            onClick={onCloseMobile}
            className="lg:hidden p-1 text-[#5E5E5E] hover:text-[#111111] transition-colors"
            aria-label="Close menu"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Navigation Items */}
      <nav className="flex-1 px-3 py-6 flex flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = isLinkActive(item);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onCloseMobile}
              className={`flex items-center px-3 py-2 rounded-[4px] text-sm transition-colors ${
                active
                  ? "bg-[#111111] text-white font-medium shadow-none"
                  : "text-[#5E5E5E] hover:bg-[#F4F3EF] hover:text-[#111111]"
              }`}
            >
              <Icon
                className={`w-4 h-4 mr-3 shrink-0 ${
                  active ? "text-white" : "text-[#777777]"
                }`}
              />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Subtle Bottom Metadata */}
      <div className="px-6 py-4 border-t border-[#E7E5E0] text-[11px] text-[#777777] font-sans flex items-center justify-between">
        <span>Statutory Assistant</span>
        <span className="font-mono text-[10px] text-[#999999]">v1.0</span>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Sidebar (Fixed Left) */}
      <aside className="hidden lg:block fixed left-0 top-0 h-full w-64 z-40">
        {navContent}
      </aside>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50 flex">
          <div
            className="fixed inset-0 bg-black/20 transition-opacity"
            onClick={onCloseMobile}
          />
          <div className="relative w-64 max-w-[80vw] h-full z-10 shadow-lg">
            {navContent}
          </div>
        </div>
      )}
    </>
  );
}


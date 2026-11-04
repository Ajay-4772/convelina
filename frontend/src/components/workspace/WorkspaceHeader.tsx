"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Menu, ChevronDown, User, LogOut, LayoutDashboard } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

interface WorkspaceHeaderProps {
  onOpenMobile?: () => void;
}

export default function WorkspaceHeader({ onOpenMobile }: WorkspaceHeaderProps) {
  const router = useRouter();
  const { profile, firebaseUser, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setDropdownOpen(false);
    try {
      await logout();
      router.push("/login");
    } catch (err) {
      console.error("Logout error:", err);
      router.push("/login");
    }
  };

  const displayName = profile?.full_name || firebaseUser?.displayName || "Citizen";
  const displayEmail = profile?.email || firebaseUser?.email || "";
  const initials = displayName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0].toUpperCase())
    .join("") || "C";

  return (
    <header className="fixed top-0 left-0 lg:left-64 right-0 h-14 bg-[#FAF9F6]/90 backdrop-blur-md z-30 border-b border-[#E7E5E0] px-4 lg:px-8 flex items-center justify-between">
      {/* Left side: Mobile menu toggle & page branding */}
      <div className="flex items-center gap-3">
        <button
          onClick={onOpenMobile}
          className="lg:hidden p-1.5 rounded-[4px] text-[#5E5E5E] hover:text-[#111111] hover:bg-[#F4F3EF] transition-colors"
          aria-label="Open navigation menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <span className="lg:hidden font-serif text-[#111111] text-sm font-medium">
          CONVELINA
        </span>
      </div>

      {/* Right side: Compact User Profile Dropdown */}
      <div className="flex items-center gap-3" ref={dropdownRef}>
        <div className="relative">
          <button
            onClick={() => setDropdownOpen((prev) => !prev)}
            aria-label="User account menu"
            className="flex items-center gap-2 py-1 px-1.5 rounded-[4px] hover:bg-[#F4F3EF] transition-colors group focus:outline-none"
            type="button"
          >
            <div className="w-7 h-7 rounded-full bg-[#111111] flex items-center justify-center text-white font-sans font-medium text-xs select-none">
              {initials}
            </div>
            <span className="hidden sm:inline font-sans text-xs text-[#111111] font-medium max-w-[120px] truncate">
              {displayName}
            </span>
            <ChevronDown className="w-3.5 h-3.5 text-[#777777] group-hover:text-[#111111] transition-colors" />
          </button>

          {/* Dropdown Menu */}
          {dropdownOpen && (
            <div className="absolute right-0 top-full mt-1.5 w-60 bg-white rounded-[4px] border border-[#E7E5E0] shadow-[0_2px_10px_rgba(0,0,0,0.06)] py-1 z-50 animate-in fade-in zoom-in-95 duration-100">
              {/* User Identity Info */}
              <div className="px-4 py-2.5 border-b border-[#E7E5E0]">
                <div className="font-sans text-xs font-semibold text-[#111111] truncate">
                  {displayName}
                </div>
                {displayEmail && (
                  <div className="font-sans text-[11px] text-[#777777] truncate mt-0.5">
                    {displayEmail}
                  </div>
                )}
              </div>

              {/* Navigation Options */}
              <div className="py-1">
                <Link
                  href="/app/profile"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-xs font-sans text-[#444748] hover:bg-[#F4F3EF] hover:text-[#111111] transition-colors"
                >
                  <User className="w-4 h-4 text-[#777777]" />
                  <span>View Profile</span>
                </Link>
                <Link
                  href="/app"
                  onClick={() => setDropdownOpen(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-xs font-sans text-[#444748] hover:bg-[#F4F3EF] hover:text-[#111111] transition-colors"
                >
                  <LayoutDashboard className="w-4 h-4 text-[#777777]" />
                  <span>Overview</span>
                </Link>
              </div>

              {/* Log Out */}
              <div className="pt-1 border-t border-[#E7E5E0]">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2.5 px-4 py-2 text-xs font-sans text-[#BA1A1A] hover:bg-[#FFDAD6]/30 transition-colors text-left"
                >
                  <LogOut className="w-4 h-4 text-[#BA1A1A]" />
                  <span>Log Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}


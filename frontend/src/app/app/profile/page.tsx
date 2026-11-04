"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  User,
  Mail,
  Phone,
  Calendar,
  MapPin,
  Lock,
  Trash2,
  Check,
  Edit2,
  AlertTriangle,
  X,
  Shield,
  RefreshCw,
} from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { updateProfile, deleteAccount } from "../../../lib/api";

export default function ProfilePage() {
  const router = useRouter();
  const { profile, firebaseUser, idToken, refreshProfile, logout } = useAuth();

  const [isEditing, setIsEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    full_name: "",
    date_of_birth: "",
    phone_number: "",
    father_name: "",
    mother_name: "",
    address: "",
  });

  // Sync form data with real authenticated user profile
  useEffect(() => {
    if (profile) {
      setFormData({
        full_name: profile.full_name || "",
        date_of_birth: profile.date_of_birth || "",
        phone_number: profile.phone_number || "",
        father_name: profile.father_name || "",
        mother_name: profile.mother_name || "",
        address: profile.address || "",
      });
    } else if (firebaseUser) {
      setFormData((prev) => ({
        ...prev,
        full_name: firebaseUser.displayName || "",
      }));
    }
  }, [profile, firebaseUser]);

  const displayName = profile?.full_name || firebaseUser?.displayName || "Citizen";
  const displayEmail = profile?.email || firebaseUser?.email || "";
  const initials = displayName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0].toUpperCase())
    .join("") || "C";

  // Handle Profile Save
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatusMessage(null);

    const activeToken = idToken || (typeof window !== "undefined" ? localStorage.getItem("convelina_test_token") : null);

    try {
      await updateProfile(activeToken, formData);
      await refreshProfile();
      setIsEditing(false);
      setStatusMessage({
        type: "success",
        text: "Profile updated successfully.",
      });
    } catch (err: any) {
      setStatusMessage({
        type: "error",
        text: err.message || "Failed to update profile.",
      });
    } finally {
      setSaving(false);
    }
  };

  // Handle Account Deletion
  const handleDeleteAccount = async () => {
    setDeleting(true);
    const activeToken = idToken || (typeof window !== "undefined" ? localStorage.getItem("convelina_test_token") : null);
    try {
      await deleteAccount(activeToken);
      await logout();
      router.push("/");
    } catch (err: any) {
      alert(err.message || "Failed to delete account. Please try again.");
      setDeleting(false);
      setDeleteModalOpen(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto w-full py-10 px-4 sm:px-6 lg:px-8 pb-32">
      {/* Top Page Header */}
      <header className="pb-6 mb-8 border-b border-[#E7E5E0] space-y-1">
        <h1 className="font-serif text-3xl sm:text-4xl text-[#111111] font-light tracking-tight">
          Profile & Account Settings
        </h1>
        <p className="font-sans text-sm text-[#5E5E5E]">
          Manage your personal identity credentials, contact coordinates, and security preferences.
        </p>
      </header>

      {/* Status Alert */}
      {statusMessage && (
        <div
          className={`mb-6 p-4 rounded-[4px] border text-xs font-sans flex items-center justify-between ${
            statusMessage.type === "success"
              ? "bg-[#FAF9F6] border-[#111111] text-[#111111]"
              : "bg-[#FFDAD6]/30 border-[#BA1A1A] text-[#BA1A1A]"
          }`}
        >
          <span>{statusMessage.text}</span>
          <button
            onClick={() => setStatusMessage(null)}
            className="text-[#777777] hover:text-[#111111]"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      <div className="space-y-12">
        {/* SECTION 1: Personal Information */}
        <section className="space-y-6">
          <div className="flex items-center justify-between pb-3 border-b border-[#E7E5E0]">
            <div>
              <h2 className="font-serif text-xl text-[#111111] font-normal">
                Personal Information
              </h2>
              <p className="font-sans text-xs text-[#777777] mt-0.5">
                Ensure these coordinates accurately match your official government identity documents.
              </p>
            </div>

            <div>
              {!isEditing ? (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="h-9 px-4 bg-[#111111] text-white rounded-[4px] text-xs font-sans font-medium hover:bg-black/90 transition-colors flex items-center gap-1.5"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                  <span>Edit Profile</span>
                </button>
              ) : (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="h-9 px-3 text-xs font-sans text-[#777777] hover:text-[#111111] rounded-[4px]"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveProfile}
                    disabled={saving}
                    className="h-9 px-4 bg-[#111111] text-white rounded-[4px] text-xs font-sans font-medium hover:bg-black/90 transition-colors flex items-center gap-1.5"
                  >
                    {saving ? (
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Check className="w-3.5 h-3.5" />
                    )}
                    <span>Save Changes</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* User Identity Card */}
          <div className="p-5 bg-white rounded-[4px] border border-[#E7E5E0] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-[#111111] flex items-center justify-center text-white font-serif text-lg select-none">
                {initials}
              </div>
              <div>
                <h3 className="font-sans text-base font-semibold text-[#111111] leading-snug">
                  {displayName}
                </h3>
                <p className="font-sans text-xs text-[#777777] mt-0.5">
                  {displayEmail}
                </p>
                <span className="inline-block mt-1.5 font-sans text-[10px] text-[#5E5E5E] uppercase tracking-wider bg-[#F4F3EF] px-2 py-0.5 rounded-[2px]">
                  Verified Citizen Workspace
                </span>
              </div>
            </div>
          </div>

          {/* Profile Form Grid */}
          <form onSubmit={handleSaveProfile}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5 pt-2">
              {/* Full Name */}
              <div>
                <label className="block font-sans text-xs font-medium text-[#111111] mb-1.5">
                  Full Name (Official)
                </label>
                <input
                  type="text"
                  value={formData.full_name}
                  onChange={(e) =>
                    setFormData({ ...formData, full_name: e.target.value })
                  }
                  readOnly={!isEditing}
                  className={`w-full h-10 px-3 rounded-[4px] border border-[#E7E5E0] text-sm font-sans text-[#111111] focus:outline-none focus:border-[#111111] transition-colors ${
                    !isEditing ? "bg-[#F4F3EF]/60 cursor-default" : "bg-white"
                  }`}
                />
              </div>

              {/* Date of Birth */}
              <div>
                <label className="block font-sans text-xs font-medium text-[#111111] mb-1.5">
                  Date of Birth (YYYY-MM-DD)
                </label>
                <input
                  type="text"
                  placeholder="YYYY-MM-DD"
                  value={formData.date_of_birth}
                  onChange={(e) =>
                    setFormData({ ...formData, date_of_birth: e.target.value })
                  }
                  readOnly={!isEditing}
                  className={`w-full h-10 px-3 rounded-[4px] border border-[#E7E5E0] text-sm font-sans text-[#111111] focus:outline-none focus:border-[#111111] transition-colors ${
                    !isEditing ? "bg-[#F4F3EF]/60 cursor-default" : "bg-white"
                  }`}
                />
              </div>

              {/* Registered Email */}
              <div>
                <label className="block font-sans text-xs font-medium text-[#111111] mb-1.5">
                  Registered Email Address
                </label>
                <input
                  type="email"
                  value={displayEmail}
                  readOnly
                  className="w-full h-10 px-3 rounded-[4px] border border-[#E7E5E0] bg-[#F4F3EF]/60 text-sm font-sans text-[#777777] cursor-default select-all"
                />
              </div>

              {/* Mobile Number */}
              <div>
                <label className="block font-sans text-xs font-medium text-[#111111] mb-1.5">
                  Mobile Number
                </label>
                <input
                  type="tel"
                  placeholder="+91 XXXXX XXXXX"
                  value={formData.phone_number}
                  onChange={(e) =>
                    setFormData({ ...formData, phone_number: e.target.value })
                  }
                  readOnly={!isEditing}
                  className={`w-full h-10 px-3 rounded-[4px] border border-[#E7E5E0] text-sm font-sans text-[#111111] focus:outline-none focus:border-[#111111] transition-colors ${
                    !isEditing ? "bg-[#F4F3EF]/60 cursor-default" : "bg-white"
                  }`}
                />
              </div>

              {/* Father's Name */}
              <div>
                <label className="block font-sans text-xs font-medium text-[#111111] mb-1.5">
                  Father's Name (Optional)
                </label>
                <input
                  type="text"
                  value={formData.father_name}
                  onChange={(e) =>
                    setFormData({ ...formData, father_name: e.target.value })
                  }
                  readOnly={!isEditing}
                  className={`w-full h-10 px-3 rounded-[4px] border border-[#E7E5E0] text-sm font-sans text-[#111111] focus:outline-none focus:border-[#111111] transition-colors ${
                    !isEditing ? "bg-[#F4F3EF]/60 cursor-default" : "bg-white"
                  }`}
                />
              </div>

              {/* Mother's Name */}
              <div>
                <label className="block font-sans text-xs font-medium text-[#111111] mb-1.5">
                  Mother's Name (Optional)
                </label>
                <input
                  type="text"
                  value={formData.mother_name}
                  onChange={(e) =>
                    setFormData({ ...formData, mother_name: e.target.value })
                  }
                  readOnly={!isEditing}
                  className={`w-full h-10 px-3 rounded-[4px] border border-[#E7E5E0] text-sm font-sans text-[#111111] focus:outline-none focus:border-[#111111] transition-colors ${
                    !isEditing ? "bg-[#F4F3EF]/60 cursor-default" : "bg-white"
                  }`}
                />
              </div>

              {/* Address */}
              <div className="md:col-span-2">
                <label className="block font-sans text-xs font-medium text-[#111111] mb-1.5">
                  Residential Address
                </label>
                <textarea
                  rows={2}
                  value={formData.address}
                  onChange={(e) =>
                    setFormData({ ...formData, address: e.target.value })
                  }
                  readOnly={!isEditing}
                  className={`w-full p-3 rounded-[4px] border border-[#E7E5E0] text-sm font-sans text-[#111111] focus:outline-none focus:border-[#111111] transition-colors resize-none ${
                    !isEditing ? "bg-[#F4F3EF]/60 cursor-default" : "bg-white"
                  }`}
                />
              </div>
            </div>
          </form>
        </section>

        {/* SECTION 2: Security & Authentication */}
        <section className="space-y-4 pt-6 border-t border-[#E7E5E0]">
          <div>
            <h2 className="font-serif text-xl text-[#111111] font-normal">
              Security & Credentials
            </h2>
            <p className="font-sans text-xs text-[#777777] mt-0.5">
              Your identity session is secured via Firebase Authentication and server-enforced PostgreSQL Row-Level Security.
            </p>
          </div>

          <div className="p-4 bg-white border border-[#E7E5E0] rounded-[4px] flex items-center justify-between">
            <div className="space-y-0.5">
              <span className="font-sans text-xs font-medium text-[#111111]">
                Authentication Provider
              </span>
              <p className="font-sans text-[11px] text-[#777777]">
                Authenticated as <strong className="text-[#111111]">{displayEmail}</strong>
              </p>
            </div>
            <span className="font-sans text-xs text-[#5E5E5E] bg-[#F4F3EF] px-2.5 py-1 rounded-[2px] border border-[#E7E5E0]">
              Active Session
            </span>
          </div>
        </section>

        {/* SECTION 3: Danger Zone */}
        <section className="pt-6 border-t border-[#E7E5E0] space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="font-serif text-xl text-[#BA1A1A] font-normal">
                Danger Zone
              </h2>
              <p className="font-sans text-xs text-[#777777] mt-0.5">
                Permanently delete your citizen profile, uploaded documents, and conflict history.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setDeleteModalOpen(true)}
              className="h-9 px-4 border border-[#BA1A1A]/40 text-[#BA1A1A] hover:bg-[#FFDAD6]/30 transition-colors rounded-[4px] text-xs font-sans font-medium flex items-center gap-1.5 self-start sm:self-auto"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete Account</span>
            </button>
          </div>
        </section>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/20 transition-opacity"
            onClick={() => setDeleteModalOpen(false)}
          />
          <div className="relative w-full max-w-md bg-white rounded-[4px] border border-[#E7E5E0] shadow-xl p-6 space-y-4 z-10">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-full bg-[#FFDAD6] flex items-center justify-center text-[#BA1A1A] shrink-0">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <div className="space-y-1">
                <h3 className="font-sans text-sm font-semibold text-[#111111]">
                  Permanently delete account?
                </h3>
                <p className="font-sans text-xs text-[#5E5E5E] leading-relaxed">
                  This action triggers cascading deletion of your account, all uploaded identity credentials, extracted OCR fields, and conflict analysis records. This operation cannot be undone.
                </p>
              </div>
            </div>

            <div className="pt-4 flex items-center justify-end gap-2 border-t border-[#E7E5E0]">
              <button
                type="button"
                onClick={() => setDeleteModalOpen(false)}
                disabled={deleting}
                className="px-3.5 py-2 text-xs font-sans text-[#777777] hover:text-[#111111] rounded-[4px]"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteAccount}
                disabled={deleting}
                className="h-9 px-4 bg-[#BA1A1A] text-white rounded-[4px] text-xs font-sans font-medium hover:bg-[#93000A] transition-colors flex items-center gap-1.5"
              >
                {deleting && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                <span>Confirm Permanent Deletion</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


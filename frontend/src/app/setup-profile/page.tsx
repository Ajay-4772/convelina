"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { User, AlertCircle, ArrowRight, CheckCircle2, ShieldCheck } from "lucide-react";
import AuthLayout from "../../components/auth/AuthLayout";
import { useAuth } from "../../context/AuthContext";

export default function SetupProfilePage() {
  const router = useRouter();
  const { firebaseUser, profile, completeProfile, loading, error, clearError } = useAuth();

  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [dob, setDob] = useState("");
  const [address, setAddress] = useState("");
  const [fatherName, setFatherName] = useState("");
  const [motherName, setMotherName] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // Prepopulate if Firebase user has displayName or existing partial profile
  useEffect(() => {
    if (profile?.full_name) {
      setFullName(profile.full_name);
      if (profile.phone_number) setPhone(profile.phone_number);
      if (profile.date_of_birth) setDob(profile.date_of_birth);
      if (profile.address) setAddress(profile.address);
      if (profile.father_name) setFatherName(profile.father_name);
      if (profile.mother_name) setMotherName(profile.mother_name);
    } else if (firebaseUser?.displayName) {
      setFullName(firebaseUser.displayName);
    }
  }, [profile, firebaseUser]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    const cleanName = fullName.trim();
    if (!cleanName) {
      setLocalError("Please enter your legal full name as recorded on official records.");
      return;
    }

    setSubmitting(true);
    try {
      const saved = await completeProfile({
        full_name: cleanName,
        phone_number: phone.trim() || undefined,
        date_of_birth: dob.trim() || undefined,
        address: address.trim() || undefined,
        father_name: fatherName.trim() || undefined,
        mother_name: motherName.trim() || undefined,
      });

      if (saved.role === "admin") {
        router.push("/admin");
      } else {
        router.push("/app");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save profile.";
      setLocalError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const displayError = localError || error;

  return (
    <AuthLayout
      title="Complete your profile"
      subtitle="Establish your citizen identity under PostgreSQL Row-Level Security."
    >
      {/* Error Banner */}
      {displayError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1">{displayError}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-zinc-700 mb-1">
            Full Legal Name <span className="text-rose-500">*</span>
          </label>
          <input
            type="text"
            required
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="e.g. Ajay Ramanathan"
            className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 transition"
          />
          <p className="text-[11px] text-zinc-500 mt-1">Used as baseline comparison identity across your records.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">Phone Number (Optional)</label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="+91 98765 43210"
              className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">Date of Birth (Optional)</label>
            <input
              type="date"
              value={dob}
              onChange={(e) => setDob(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 transition"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-700 mb-1">Primary Residential Address (Optional)</label>
          <textarea
            rows={2}
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="House/Apartment, Street, City, State, PIN Code"
            className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 transition resize-none"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">Father&apos;s Name (Optional)</label>
            <input
              type="text"
              value={fatherName}
              onChange={(e) => setFatherName(e.target.value)}
              placeholder="e.g. Ramanathan K."
              className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 transition"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">Mother&apos;s Name (Optional)</label>
            <input
              type="text"
              value={motherName}
              onChange={(e) => setMotherName(e.target.value)}
              placeholder="e.g. Lakshmi Raman"
              className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 transition"
            />
          </div>
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={submitting || loading || !fullName.trim()}
            className="w-full py-2.5 rounded-xl bg-[#18181b] text-white text-xs font-medium hover:bg-zinc-800 disabled:opacity-50 transition shadow-xs flex items-center justify-center gap-1.5"
          >
            {submitting ? (
              <span>Saving Profile...</span>
            ) : (
              <>
                <span>Save Profile & Enter Workspace</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </form>
    </AuthLayout>
  );
}

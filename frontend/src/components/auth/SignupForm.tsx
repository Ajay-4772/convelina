"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Eye, EyeOff, AlertCircle, ArrowRight, ShieldCheck } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { User as FirebaseUser } from "firebase/auth";

interface SignupFormProps {
  onSuccess?: (user: FirebaseUser) => void;
  redirectTo?: string;
}

export default function SignupForm({ onSuccess, redirectTo }: SignupFormProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnUrl = redirectTo || searchParams.get("returnUrl") || "/app";

  const { signUpWithEmail, sendEmailOtp, loginWithGoogle, loading, error, clearError } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [agreeTerms, setAgreeTerms] = useState(false);

  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail) {
      setLocalError("Please enter your official email address.");
      return;
    }
    if (password.length < 6) {
      setLocalError("Password must be at least 6 characters in length.");
      return;
    }
    if (password !== confirmPassword) {
      setLocalError("Passwords do not match. Please verify.");
      return;
    }
    if (!agreeTerms) {
      setLocalError("You must acknowledge the terms and data privacy policy.");
      return;
    }

    setSubmitting(true);
    try {
      // 1. Create account in Firebase
      const user = await signUpWithEmail(cleanEmail, password);

      // 2. Dispatch OTP to the email address if email verification flow is enabled
      try {
        await sendEmailOtp(cleanEmail);
        router.push(`/verify-email?email=${encodeURIComponent(cleanEmail)}`);
      } catch {
        // If OTP service is unconfigured or skipped in local testing, continue to profile setup
        if (onSuccess) {
          onSuccess(user);
        } else {
          router.push("/setup-profile");
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Account registration failed.";
      setLocalError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoogleSignUp = async () => {
    setLocalError(null);
    clearError();
    setSubmitting(true);
    try {
      const profile = await loginWithGoogle();
      if (!profile || !profile.full_name) {
        router.push("/setup-profile");
      } else if (profile.role === "admin") {
        router.push("/admin");
      } else {
        router.push(returnUrl);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Google sign-up failed.";
      setLocalError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const displayError = localError || error;

  return (
    <div className="w-full space-y-4">
      {/* Error Banner */}
      {displayError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1 leading-relaxed">{displayError}</div>
        </div>
      )}

      {/* Google Sign-up Option */}
      <div>
        <button
          type="button"
          disabled={submitting || loading}
          onClick={handleGoogleSignUp}
          className="w-full py-2.5 px-4 rounded-xl border border-[#e5e2dc] bg-[#faf9f6] text-xs font-medium text-zinc-800 hover:bg-zinc-100 disabled:opacity-50 transition flex items-center justify-center gap-2.5 shadow-2xs"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span>Sign up with Google</span>
        </button>
      </div>

      <div className="relative flex items-center justify-center">
        <div className="border-t border-[#e5e2dc] w-full" />
        <span className="bg-white px-3 text-[11px] font-medium text-zinc-400 uppercase tracking-wider shrink-0">
          or register with email
        </span>
        <div className="border-t border-[#e5e2dc] w-full" />
      </div>

      {/* Main Registration Form */}
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-zinc-700 mb-1">Email Address</label>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="yourname@gmail.com"
            className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 transition"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-700 mb-1">Create Password</label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              required
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 6 characters"
              className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 pr-9 transition"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-700 transition"
            >
              {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-zinc-700 mb-1">Confirm Password</label>
          <input
            type={showPassword ? "text" : "password"}
            required
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="Re-enter your password"
            className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 transition"
          />
        </div>

        {/* Security & Terms Checkbox */}
        <div className="pt-1">
          <label className="flex items-start gap-2.5 cursor-pointer">
            <input
              type="checkbox"
              checked={agreeTerms}
              onChange={(e) => setAgreeTerms(e.target.checked)}
              className="mt-0.5 rounded border-[#e5e2dc] text-zinc-900 focus:ring-0 focus:ring-offset-0 transition"
            />
            <span className="text-[11px] text-zinc-600 leading-tight">
              I agree to CONVELINA&apos;s privacy terms, acknowledging that all uploaded identity data is isolated under forced database row-level security and deleted post-verification.
            </span>
          </label>
        </div>

        <button
          type="submit"
          disabled={submitting || loading}
          className="w-full py-2.5 rounded-xl bg-[#18181b] text-white text-xs font-medium hover:bg-zinc-800 disabled:opacity-50 transition shadow-xs flex items-center justify-center gap-1.5"
        >
          {submitting ? (
            <span>Creating account...</span>
          ) : (
            <>
              <span>Create account</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </form>

      {/* Switch to Login Link */}
      <div className="text-center pt-2 border-t border-zinc-100 text-xs text-zinc-600">
        Already have an account?{" "}
        <Link href="/login" className="font-semibold text-black hover:underline">
          Sign in
        </Link>
      </div>
    </div>
  );
}

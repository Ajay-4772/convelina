"use client";

import React, { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Mail, AlertCircle, CheckCircle2, ArrowRight, RefreshCw, KeyRound } from "lucide-react";
import AuthLayout from "../../components/auth/AuthLayout";
import { useAuth } from "../../context/AuthContext";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { verifyEmailOtp, sendEmailOtp, loading, error, clearError } = useAuth();

  const emailParam = searchParams.get("email") || "";
  const [email, setEmail] = useState(emailParam);
  const [otp, setOtp] = useState("");
  const [countdown, setCountdown] = useState(300); // 5 minutes
  const [resendCooldown, setResendCooldown] = useState(60);

  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(
    "A 6-digit verification code has been dispatched to your email."
  );

  // Countdown timer for code validity
  useEffect(() => {
    if (countdown <= 0) return;
    const timer = setInterval(() => setCountdown((c) => c - 1), 1000);
    return () => clearInterval(timer);
  }, [countdown]);

  // Resend cooldown timer
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => setResendCooldown((c) => c - 1), 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    const cleanOtp = otp.trim();
    if (cleanOtp.length !== 6) {
      setLocalError("Please enter the complete 6-digit verification code.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await verifyEmailOtp(email, cleanOtp);
      if (res.verified) {
        setSuccessMsg("Email verified successfully! Proceeding to profile setup...");
        setTimeout(() => {
          router.push("/setup-profile");
        }, 1000);
      } else {
        setLocalError(res.message || "Invalid or expired code.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Verification failed.";
      setLocalError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleResend = async () => {
    if (resendCooldown > 0) return;
    setLocalError(null);
    clearError();
    try {
      await sendEmailOtp(email);
      setSuccessMsg("A new 6-digit code has been dispatched to your email.");
      setCountdown(300);
      setResendCooldown(60);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to resend code.";
      setLocalError(msg);
    }
  };

  const formatTime = (secs: number) => {
    const mins = Math.floor(secs / 60);
    const remainder = secs % 60;
    return `${mins}:${remainder < 10 ? "0" : ""}${remainder}`;
  };

  const displayError = localError || error;

  return (
    <AuthLayout
      title="Verify your email"
      subtitle={`Enter the 6-digit verification code sent to ${email || "your address"}.`}
    >
      {/* Success Notification */}
      {successMsg && (
        <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600" />
          <div className="flex-1">{successMsg}</div>
        </div>
      )}

      {/* Error Notification */}
      {displayError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1">{displayError}</div>
        </div>
      )}

      {/* Main OTP Entry Form */}
      <form onSubmit={handleVerify} className="space-y-5">
        <div>
          <label className="block text-xs font-medium text-zinc-700 mb-1.5 text-center">
            Verification Code (6-Digits)
          </label>
          <div className="relative">
            <input
              type="text"
              required
              autoFocus
              maxLength={6}
              value={otp}
              onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
              placeholder="123456"
              className="w-full py-3 px-4 text-center tracking-[0.4em] font-mono text-xl border border-[#e5e2dc] rounded-xl focus:border-zinc-900 bg-[#faf9f6]/40 transition"
            />
          </div>
          <div className="flex items-center justify-between text-[11px] text-zinc-500 mt-2 px-1">
            <span>Valid for: {formatTime(countdown)}</span>
            <span>Test Mode: OTP &quot;123456&quot;</span>
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting || otp.length !== 6}
          className="w-full py-2.5 rounded-xl bg-[#18181b] text-white text-xs font-medium hover:bg-zinc-800 disabled:opacity-50 transition shadow-xs flex items-center justify-center gap-1.5"
        >
          {submitting ? (
            <span>Verifying...</span>
          ) : (
            <>
              <span>Verify & Continue</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </form>

      {/* Resend Action */}
      <div className="pt-2 border-t border-zinc-100 flex items-center justify-between text-xs">
        <span className="text-zinc-500">Didn&apos;t receive code?</span>
        <button
          type="button"
          disabled={resendCooldown > 0}
          onClick={handleResend}
          className="font-medium text-zinc-900 hover:text-black disabled:text-zinc-400 transition inline-flex items-center gap-1"
        >
          <RefreshCw className={`w-3 h-3 ${resendCooldown > 0 ? "" : "animate-spin"}`} />
          <span>{resendCooldown > 0 ? `Resend in ${resendCooldown}s` : "Resend code"}</span>
        </button>
      </div>

      <div className="text-center text-xs text-zinc-500 pt-1">
        Wrong email?{" "}
        <Link href="/signup" className="text-black font-semibold hover:underline">
          Re-enter address
        </Link>
      </div>
    </AuthLayout>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#faf9f6] flex items-center justify-center">
          <div className="text-xs text-zinc-500">Loading verification...</div>
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}

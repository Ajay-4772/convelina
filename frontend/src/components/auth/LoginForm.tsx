"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Eye, EyeOff, AlertCircle, ArrowRight, CheckCircle2, KeyRound } from "lucide-react";
import { useAuth, UserProfile } from "../../context/AuthContext";

interface LoginFormProps {
  onSuccess?: (profile: UserProfile | null) => void;
  redirectTo?: string;
}

export default function LoginForm({ onSuccess, redirectTo }: LoginFormProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnUrl = redirectTo || searchParams.get("returnUrl") || "/app";

  const { loginWithEmail, loginWithGoogle, resetPassword, loading, error, clearError } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  // Forgot Password state
  const [isResetMode, setIsResetMode] = useState(false);
  const [resetSuccess, setResetSuccess] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    setResetSuccess(null);
    clearError();

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setLocalError("Please enter your email address.");
      return;
    }
    if (!password) {
      setLocalError("Please enter your password.");
      return;
    }

    setSubmitting(true);
    try {
      const profile = await loginWithEmail(cleanEmail, password);
      if (onSuccess) {
        onSuccess(profile);
      } else {
        if (!profile || !profile.full_name) {
          router.push("/setup-profile");
        } else if (profile.role === "admin") {
          router.push("/admin");
        } else {
          router.push(returnUrl);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to sign in. Please verify your credentials.";
      setLocalError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    setResetSuccess(null);
    clearError();

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setLocalError("Please enter your email address to receive password reset instructions.");
      return;
    }

    setSubmitting(true);
    try {
      await resetPassword(cleanEmail);
      setResetSuccess(`Password reset email sent to ${cleanEmail}. Please check your inbox and follow the link.`);
      setIsResetMode(false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to dispatch password reset email.";
      setLocalError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLocalError(null);
    setResetSuccess(null);
    clearError();
    setSubmitting(true);
    try {
      const profile = await loginWithGoogle();
      if (onSuccess) {
        onSuccess(profile);
      } else {
        if (!profile || !profile.full_name) {
          router.push("/setup-profile");
        } else if (profile.role === "admin") {
          router.push("/admin");
        } else {
          router.push(returnUrl);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Google sign-in was cancelled or failed.";
      setLocalError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const displayError = localError || error;

  return (
    <div className="w-full space-y-4">
      {/* Error Alert */}
      {displayError && (
        <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-start gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="flex-1 leading-relaxed">{displayError}</div>
        </div>
      )}

      {/* Reset Success Notice */}
      {resetSuccess && (
        <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 flex items-start gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5 text-emerald-600" />
          <div className="flex-1 leading-relaxed">{resetSuccess}</div>
        </div>
      )}

      {isResetMode ? (
        /* Password Reset Form */
        <form onSubmit={handleResetPassword} noValidate className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-zinc-700 mb-1">Account Email</label>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="yourname@gmail.com"
              className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 bg-[#faf9f6]/40 transition"
            />
            <p className="mt-1 text-[11px] text-zinc-500">
              We will send you a secure link to reset your account password.
            </p>
          </div>

          <div className="flex items-center gap-2 pt-1">
            <button
              type="submit"
              disabled={submitting || loading}
              className="flex-1 py-2.5 rounded-xl bg-[#18181b] text-white text-xs font-medium hover:bg-zinc-800 disabled:opacity-50 transition shadow-xs flex items-center justify-center gap-1.5"
            >
              <KeyRound className="w-3.5 h-3.5" />
              <span>{submitting ? "Sending..." : "Send Reset Email"}</span>
            </button>
            <button
              type="button"
              disabled={submitting}
              onClick={() => {
                setIsResetMode(false);
                setLocalError(null);
              }}
              className="py-2.5 px-3 rounded-xl border border-zinc-200 text-zinc-700 text-xs font-medium hover:bg-zinc-100 transition"
            >
              Cancel
            </button>
          </div>
        </form>
      ) : (
        /* Standard Login Form */
        <>
          {/* Google OAuth Button */}
          <div>
            <button
              type="button"
              disabled={submitting || loading}
              onClick={handleGoogleSignIn}
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
              <span>Continue with Google</span>
            </button>
          </div>

          <div className="relative flex items-center justify-center">
            <div className="border-t border-[#e5e2dc] w-full" />
            <span className="bg-white px-3 text-[11px] font-medium text-zinc-400 uppercase tracking-wider shrink-0">
              or sign in with email
            </span>
            <div className="border-t border-[#e5e2dc] w-full" />
          </div>

          <form onSubmit={handleLogin} noValidate className="space-y-4">
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
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-medium text-zinc-700">Password</label>
                <button
                  type="button"
                  onClick={() => {
                    setIsResetMode(true);
                    setLocalError(null);
                  }}
                  className="text-[11px] text-zinc-500 hover:text-zinc-900 transition"
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
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

            <button
              type="submit"
              disabled={submitting || loading}
              className="w-full py-2.5 rounded-xl bg-[#18181b] text-white text-xs font-medium hover:bg-zinc-800 disabled:opacity-50 transition shadow-xs flex items-center justify-center gap-1.5"
            >
              {submitting ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <span>Sign in</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>
        </>
      )}

      {/* Switch to Signup Link */}
      <div className="text-center pt-2 border-t border-zinc-100 text-xs text-zinc-600">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="font-semibold text-black hover:underline">
          Create one now
        </Link>
      </div>
    </div>
  );
}

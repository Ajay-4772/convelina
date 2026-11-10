"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Lock, Mail, Eye, EyeOff, AlertCircle, ArrowLeft } from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import Logo from "../../../components/ui/Logo";

export default function AdminLoginPage() {
  const router = useRouter();
  const { loginWithEmail, logout } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const userProfile = await loginWithEmail(email.trim(), password);
      if (!userProfile) {
        throw new Error("Unable to establish authenticated session.");
      }

      if (userProfile.role !== "admin") {
        await logout();
        setError("Access Denied: The authenticated account does not possess administrator privileges.");
        setLoading(false);
        return;
      }

      router.push("/admin");
    } catch (err: any) {
      console.error("Admin sign in failure:", err);
      if (err.code === "auth/invalid-credential" || err.code === "auth/user-not-found" || err.code === "auth/wrong-password") {
        setError("Invalid administrative credentials.");
      } else {
        setError(err.message || "An authentication error occurred.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#faf9f6] flex flex-col justify-center py-12 sm:px-6 lg:px-8 font-sans selection:bg-[#111111] selection:text-white">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center space-y-3">
        <div className="flex justify-center mb-2">
          <Logo size={40} showText={false} />
        </div>
        <h2 className="text-2xl font-serif text-zinc-900 tracking-tight">
          CONVELINA Administration
        </h2>
        <p className="text-xs text-zinc-500">
          Restricted administrative access. Authorized personnel only.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4">
        <div className="bg-white py-8 px-6 shadow-elevated border border-[#e5e2dc] rounded-3xl sm:px-10">
          {error && (
            <div className="mb-6 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-2.5 text-xs text-rose-700">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-500" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleAdminLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1.5">
                Admin Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@convelina.com"
                  className="w-full px-3.5 py-2.5 pl-10 text-xs border border-[#e5e2dc] rounded-xl focus:outline-none focus:ring-1 focus:ring-zinc-900 bg-white"
                />
                <Mail className="w-4 h-4 text-zinc-400 absolute left-3.5 top-3" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1.5">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 pl-10 pr-10 text-xs border border-[#e5e2dc] rounded-xl focus:outline-none focus:ring-1 focus:ring-zinc-900 bg-white"
                />
                <Lock className="w-4 h-4 text-zinc-400 absolute left-3.5 top-3" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-3 text-zinc-400 hover:text-zinc-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-[#111111] text-white text-xs font-semibold rounded-full hover:bg-zinc-800 transition shadow-sm disabled:opacity-50 flex items-center justify-center gap-2 mt-2"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Lock className="w-3.5 h-3.5" />
                  Sign In to Admin Console
                </>
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-[#f4f4f5] text-center">
            <Link
              href="/"
              className="inline-flex items-center gap-1.5 text-xs text-zinc-500 hover:text-zinc-800 transition"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Return to Public Portal
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

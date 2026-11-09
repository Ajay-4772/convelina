"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "../../context/AuthContext";
import { ShieldAlert, Loader2 } from "lucide-react";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: "user" | "admin";
  redirectTo?: string;
}

export default function ProtectedRoute({
  children,
  requiredRole,
  redirectTo,
}: ProtectedRouteProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { firebaseUser, profile, loading, isProfileComplete } = useAuth();

  useEffect(() => {
    if (loading) return;

    // 1. Not signed in: redirect to login
    if (!firebaseUser) {
      const targetUrl = redirectTo || `/login?returnUrl=${encodeURIComponent(pathname || "/app")}`;
      router.replace(targetUrl);
      return;
    }

    // 2. Profile not completed: redirect to profile setup (unless already on setup-profile)
    if (!isProfileComplete && pathname !== "/setup-profile") {
      router.replace("/setup-profile");
      return;
    }

    // 3. Role enforcement
    if (requiredRole && profile) {
      const userRole = profile.role === "citizen" ? "user" : profile.role;
      if (requiredRole === "admin" && userRole !== "admin") {
        router.replace("/app");
      }
    }
  }, [firebaseUser, profile, loading, isProfileComplete, requiredRole, redirectTo, pathname, router]);

  if (loading) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center p-6 text-center">
        <Loader2 className="w-6 h-6 animate-spin text-zinc-500 mb-3" />
        <p className="text-xs text-zinc-500 font-medium tracking-wide">
          Verifying secure session...
        </p>
      </div>
    );
  }

  // Not authenticated fallback
  if (!firebaseUser) {
    return null;
  }

  // Role mismatch fallback
  if (requiredRole && profile) {
    const userRole = profile.role === "citizen" ? "user" : profile.role;
    if (requiredRole === "admin" && userRole !== "admin") {
      return (
        <div className="min-h-[50vh] flex flex-col items-center justify-center p-6 text-center">
          <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-600 flex items-center justify-center mb-4">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h2 className="text-base font-semibold text-zinc-900 mb-1">Access Restricted</h2>
          <p className="text-xs text-zinc-600 max-w-sm">
            Administrative permissions are required to access this console. Your account is registered with standard user privileges.
          </p>
        </div>
      );
    }
  }

  return <>{children}</>;
}

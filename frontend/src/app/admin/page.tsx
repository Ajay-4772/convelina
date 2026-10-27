"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Shield, 
  Users, 
  FileText, 
  AlertTriangle, 
  Key, 
  Activity, 
  LogOut, 
  Search, 
  ShieldAlert, 
  ArrowLeft,
  RefreshCw,
  CheckCircle2
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import Logo from "../../components/ui/Logo";

interface AdminStats {
  users: { total: number; citizens: number; admins: number };
  documents: { total_uploaded: number };
  conflicts: { total_detected: number };
  assistant: { total_messages: number; forms_available: number };
  pki: { total_attestations: number; active_signing_keys: number };
  audit: { total_events: number };
}

export default function AdminPage() {
  const router = useRouter();
  const { firebaseUser, profile, idToken, loading, logout } = useAuth();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);
  const [pkiKeys, setPkiKeys] = useState<any[]>([]);
  const [loadingData, setLoadingData] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const getAuthHeaders = useCallback(() => {
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${idToken || ""}`,
    };
  }, [idToken]);

  const fetchAdminData = useCallback(async () => {
    if (!idToken) return;
    setLoadingData(true);
    try {
      const [statsRes, usersRes, actRes, pkiRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/admin/overview-stats`, { headers: getAuthHeaders() }),
        fetch(`${apiUrl}/api/v1/admin/users`, { headers: getAuthHeaders() }),
        fetch(`${apiUrl}/api/v1/admin/system-activity`, { headers: getAuthHeaders() }),
        fetch(`${apiUrl}/api/v1/pki/keys`, { headers: getAuthHeaders() }),
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }
      if (usersRes.ok) {
        const usersData = await usersRes.json();
        setUsers(usersData || []);
      }
      if (actRes.ok) {
        const actData = await actRes.json();
        setActivities(actData || []);
      }
      if (pkiRes.ok) {
        const pkiData = await pkiRes.json();
        setPkiKeys(pkiData || []);
      }
    } catch (e) {
      console.error("Admin data fetch error:", e);
    } finally {
      setLoadingData(false);
    }
  }, [apiUrl, idToken, getAuthHeaders]);

  const [isDemoMode, setIsDemoMode] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && window.location.search.includes("demo=true")) {
      setIsDemoMode(true);
      setStats({
        users: { total: 42, citizens: 39, admins: 3 },
        documents: { total_uploaded: 148 },
        conflicts: { total_detected: 32 },
        assistant: { total_messages: 184, forms_available: 12 },
        pki: { total_attestations: 28, active_signing_keys: 2 },
        audit: { total_events: 412 },
      });
      setUsers([
        { id: "u-1", email: "ajay.m@velhightech.com", full_name: "AJAY M", role: "admin", created_at: "2025-10-12T10:00:00Z" },
        { id: "u-2", email: "adithya.b@velhightech.com", full_name: "ADITHYA B", role: "admin", created_at: "2025-10-12T10:05:00Z" },
        { id: "u-3", email: "kamesh.g@velhightech.com", full_name: "KAMESH G", role: "citizen", created_at: "2025-10-12T10:10:00Z" },
        { id: "u-4", email: "citizen.vikram@gmail.com", full_name: "VIKRAM RAMAN", role: "citizen", created_at: "2025-10-14T08:30:00Z" },
        { id: "u-5", email: "citizen.priya@outlook.com", full_name: "PRIYA SUNDAR", role: "citizen", created_at: "2025-10-15T11:20:00Z" },
      ]);
      setActivities([
        { id: "act-1", action: "document.ocr_parsed", entity_type: "document", details: { doc_type: "aadhaar", status: "success" }, created_at: new Date(Date.now() - 600000).toISOString() },
        { id: "act-2", action: "conflict.detected", entity_type: "conflict", details: { field: "full_name", severity: "high" }, created_at: new Date(Date.now() - 500000).toISOString() },
        { id: "act-3", action: "pki.attestation_signed", entity_type: "pki_cert", details: { key_algorithm: "Ed25519" }, created_at: new Date(Date.now() - 300000).toISOString() },
      ]);
    }
  }, []);

  useEffect(() => {
    if (isDemoMode) return;
    if (!loading) {
      if (!firebaseUser) {
        router.replace("/login");
      } else if (profile && profile.role === "admin") {
        fetchAdminData();
      }
    }
  }, [loading, firebaseUser, profile, router, fetchAdminData, isDemoMode]);

  if (loading && !isDemoMode) {
    return (
      <div className="min-h-screen bg-[#faf9f6] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-pulse">
            <Logo size={40} showText={false} />
          </div>
          <span className="text-xs font-medium text-zinc-500">Authenticating administrator...</span>
        </div>
      </div>
    );
  }

  // Role Guard
  if ((!profile || profile.role !== "admin") && !isDemoMode) {
    return (
      <div className="min-h-screen bg-[#faf9f6] flex items-center justify-center p-4">
        <div className="bg-white border border-[#e5e2dc] rounded-2xl max-w-md w-full p-8 text-center space-y-4 shadow-elevated">
          <div className="w-12 h-12 rounded-xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-serif text-zinc-900">Access Denied</h2>
          <p className="text-xs text-zinc-600 leading-relaxed">
            The CONVELINA Administrator Console is restricted strictly to verified system administrators. Your account ({profile?.email || "Unknown"}) is registered as a Citizen.
          </p>
          <div className="pt-2 flex justify-center gap-3">
            <Link
              href="/app"
              className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-xl hover:bg-zinc-800 transition"
            >
              Return to Citizen Workspace
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const filteredUsers = users.filter((u) => {
    const q = searchQuery.toLowerCase();
    return (
      u.email?.toLowerCase().includes(q) ||
      u.full_name?.toLowerCase().includes(q) ||
      u.role?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="min-h-screen bg-[#faf9f6] text-[#18181b] flex flex-col font-sans selection:bg-[#18181b] selection:text-white">
      {/* Top Admin Header */}
      <header className="sticky top-0 z-30 h-16 bg-white border-b border-[#e5e2dc] px-4 sm:px-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/app" className="p-1.5 rounded-lg text-zinc-500 hover:text-black hover:bg-zinc-100 transition" title="Go to Citizen View">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="flex items-center gap-2">
            <Logo size={24} showText={false} />
            <span className="font-bold text-sm text-[#18181b]">CONVELINA Admin Console</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchAdminData}
            disabled={loadingData}
            className="p-1.5 rounded-lg text-zinc-500 hover:text-black hover:bg-zinc-100 transition"
            title="Refresh Metrics"
          >
            <RefreshCw className={`w-4 h-4 ${loadingData ? "animate-spin" : ""}`} />
          </button>

          <div className="text-right hidden sm:block">
            <div className="text-xs font-semibold text-zinc-900">{profile?.full_name || "AJAY M (Admin Officer)"}</div>
            <div className="text-[10px] text-purple-700 font-mono">System Administrator</div>
          </div>

          <button
            onClick={async () => {
              await logout();
              router.replace("/");
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 text-rose-700 hover:bg-rose-100 rounded-lg text-xs font-medium transition"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign out</span>
          </button>
        </div>
      </header>

      {/* Admin Content Body */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Metric Cards Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-1">
            <div className="flex items-center justify-between text-xs text-zinc-500">
              <span>Total Users</span>
              <Users className="w-4 h-4 text-zinc-600" />
            </div>
            <div className="text-2xl font-semibold text-zinc-900">{stats?.users?.total || users.length}</div>
            <div className="text-[11px] text-zinc-400">
              {stats?.users?.citizens || 0} Citizens • {stats?.users?.admins || 0} Admins
            </div>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-1">
            <div className="flex items-center justify-between text-xs text-zinc-500">
              <span>Documents Processed</span>
              <FileText className="w-4 h-4 text-zinc-600" />
            </div>
            <div className="text-2xl font-semibold text-zinc-900">{stats?.documents?.total_uploaded || 0}</div>
            <div className="text-[11px] text-zinc-400">Aadhaar, PAN, Passports</div>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-1">
            <div className="flex items-center justify-between text-xs text-zinc-500">
              <span>Conflicts Detected</span>
              <AlertTriangle className="w-4 h-4 text-amber-600" />
            </div>
            <div className="text-2xl font-semibold text-zinc-900">{stats?.conflicts?.total_detected || 0}</div>
            <div className="text-[11px] text-zinc-400">Multi-dimensional matching</div>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-1">
            <div className="flex items-center justify-between text-xs text-zinc-500">
              <span>Active Signing Keys</span>
              <Key className="w-4 h-4 text-purple-600" />
            </div>
            <div className="text-2xl font-semibold text-zinc-900">{pkiKeys.length || 1}</div>
            <div className="text-[11px] text-zinc-400">Ed25519 PKI Attestation</div>
          </div>
        </div>

        {/* Users Management Section */}
        <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold text-zinc-900">User Account Directory</h3>
              <p className="text-xs text-zinc-500">All provisioned user profiles under PostgreSQL Forced RLS.</p>
            </div>
            <div className="relative w-full sm:w-64">
              <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search users..."
                className="w-full pl-8 pr-3 py-1.5 text-xs border border-[#e5e2dc] rounded-lg bg-[#faf9f6]"
              />
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#faf9f6] text-zinc-500 border-b border-[#e5e2dc]">
                <tr>
                  <th className="py-2.5 px-3 font-medium">Name</th>
                  <th className="py-2.5 px-3 font-medium">Email</th>
                  <th className="py-2.5 px-3 font-medium">Role</th>
                  <th className="py-2.5 px-3 font-medium">Created At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {filteredUsers.map((u) => (
                  <tr key={u.id} className="hover:bg-zinc-50/50">
                    <td className="py-2.5 px-3 font-medium text-zinc-900">{u.full_name || "Unassigned"}</td>
                    <td className="py-2.5 px-3 text-zinc-600 font-mono">{u.email}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono capitalize ${
                        u.role === "admin" ? "bg-purple-100 text-purple-800" : "bg-zinc-100 text-zinc-700"
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-zinc-400 text-[11px]">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* PKI Public Key Keystore Section */}
        <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-zinc-900">Ed25519 PKI Public Keystore</h3>
              <p className="text-xs text-zinc-500">Cryptographic public keys for verifying citizen document attestations.</p>
            </div>
            <span className="text-[10px] font-mono bg-purple-50 text-purple-700 px-2 py-0.5 rounded border border-purple-200">
              RFC 8032 Compliant
            </span>
          </div>

          <div className="space-y-2">
            {pkiKeys.map((k) => (
              <div key={k.id || k.key_id} className="p-3 rounded-xl bg-[#faf9f6] border border-[#e5e2dc] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-xs">
                <div>
                  <div className="font-semibold text-zinc-900 font-mono">{k.key_id}</div>
                  <div className="text-[11px] text-zinc-500 font-mono truncate max-w-xl">
                    Public Key (Base64): {k.public_key_bytes_base64 || k.public_key_hex || "Verified"}
                  </div>
                </div>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 shrink-0">
                  {k.status || "active"}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Immutable Audit Trail Section */}
        <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-zinc-900">System Security & Audit Activity</h3>
              <p className="text-xs text-zinc-500">Append-only log protected by PostgreSQL rejection triggers.</p>
            </div>
            <span className="text-[10px] font-mono text-zinc-400">SHA-256 Hash Chained</span>
          </div>

          <div className="divide-y divide-zinc-100 text-xs">
            {activities.slice(0, 10).map((act) => (
              <div key={act.id} className="py-2.5 flex items-center justify-between">
                <div>
                  <span className="font-semibold text-zinc-800 capitalize">{act.action?.replace("_", " ")}</span>
                  <span className="text-zinc-500 text-[11px] ml-2">Target: {act.entity_type}</span>
                </div>
                <span className="text-[10px] font-mono text-zinc-400">
                  {new Date(act.created_at).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

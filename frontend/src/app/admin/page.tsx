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
  CheckCircle2,
  Download,
  ExternalLink,
  FileCheck,
  Check,
  Loader2,
  History,
  UploadCloud,
  BookOpen,
  X,
  Layers,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import Logo from "../../components/ui/Logo";
import {
  syncAdminOfficialForms,
  updateAdminOfficialFormVerification,
  downloadOfficialForm,
  fetchOfficialFormHistory,
  replaceOfficialForm,
  verifyAndPublishOfficialForm,
  ingestKnowledgeFile,
} from "../../lib/api";

interface AdminStats {
  users: { total: number; users?: number; citizens?: number; admins: number };
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
  const [forms, setForms] = useState<any[]>([]);
  const [loadingData, setLoadingData] = useState(false);
  const [syncingForms, setSyncingForms] = useState(false);
  const [updatingFormId, setUpdatingFormId] = useState<string | null>(null);
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
      const [statsRes, usersRes, actRes, pkiRes, formsRes] = await Promise.all([
        fetch(`${apiUrl}/api/v1/admin/overview-stats`, { headers: getAuthHeaders() }),
        fetch(`${apiUrl}/api/v1/admin/users`, { headers: getAuthHeaders() }),
        fetch(`${apiUrl}/api/v1/admin/system-activity`, { headers: getAuthHeaders() }),
        fetch(`${apiUrl}/api/v1/pki/keys`, { headers: getAuthHeaders() }),
        fetch(`${apiUrl}/api/v1/knowledge/admin/forms`, { headers: getAuthHeaders() }),
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
      if (formsRes.ok) {
        const formsData = await formsRes.json();
        setForms(formsData.forms || []);
      }
    } catch (e) {
      console.error("Admin data fetch error:", e);
    } finally {
      setLoadingData(false);
    }
  }, [apiUrl, idToken, getAuthHeaders]);

  const handleSyncForms = async () => {
    if (!idToken || syncingForms) return;
    setSyncingForms(true);
    try {
      await syncAdminOfficialForms(idToken);
      await fetchAdminData();
    } catch (e: any) {
      console.error("Sync error:", e);
      alert("Failed to sync forms catalog: " + (e.message || "Unknown error"));
    } finally {
      setSyncingForms(false);
    }
  };

  const handleToggleVerification = async (form: any) => {
    if (!idToken) return;
    const formId = form.form_id || form.id;
    setUpdatingFormId(formId);
    const nextStatus = form.verification_status === "verified" ? "needs_review" : "verified";
    try {
      await updateAdminOfficialFormVerification(
        idToken,
        formId,
        nextStatus,
        `Updated to ${nextStatus} via admin console`
      );
      await fetchAdminData();
    } catch (e: any) {
      console.error("Update verification error:", e);
      alert("Failed to update status: " + (e.message || "Unknown error"));
    } finally {
      setUpdatingFormId(null);
    }
  };

  const handleAdminDownloadForm = async (form: any) => {
    const formId = form.form_id || form.id;
    try {
      await downloadOfficialForm(idToken, formId, `${form.form_code || formId}.pdf`);
    } catch (e: any) {
      console.error("Download error:", e);
      alert("Download failed: " + (e.message || "Unknown error"));
    }
  };

  const [historyModalForm, setHistoryModalForm] = useState<any | null>(null);
  const [formHistory, setFormHistory] = useState<any[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const [replaceModalForm, setReplaceModalForm] = useState<any | null>(null);
  const [replaceFile, setReplaceFile] = useState<File | null>(null);
  const [replaceVersion, setReplaceVersion] = useState("2.0");
  const [replaceProvenance, setReplaceProvenance] = useState("OFFICIAL_ORIGINAL");
  const [replaceAuthority, setReplaceAuthority] = useState("");
  const [replaceUrl, setReplaceUrl] = useState("");
  const [replaceNotes, setReplaceNotes] = useState("");
  const [replacing, setReplacing] = useState(false);

  const [ingestModalOpen, setIngestModalOpen] = useState(false);
  const [ingestFile, setIngestFile] = useState<File | null>(null);
  const [ingestTitle, setIngestTitle] = useState("");
  const [ingestCategory, setIngestCategory] = useState("aadhaar");
  const [ingestAuthority, setIngestAuthority] = useState("UIDAI");
  const [ingestUrl, setIngestUrl] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<any | null>(null);

  const handleOpenHistory = async (form: any) => {
    const formId = form.form_id || form.id;
    setHistoryModalForm(form);
    setLoadingHistory(true);
    try {
      const data = await fetchOfficialFormHistory(idToken, formId);
      setFormHistory(data.versions || []);
    } catch (e: any) {
      console.error("Fetch history error:", e);
      alert("Failed to load history: " + (e.message || "Unknown error"));
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleOpenReplace = (form: any) => {
    setReplaceModalForm(form);
    setReplaceVersion(form.version ? `${(parseFloat(form.version || "1.0") + 1.0).toFixed(1)}` : "2.0");
    setReplaceAuthority(form.issuing_authority || "");
    setReplaceUrl(form.official_download_url || "");
    setReplaceProvenance("OFFICIAL_ORIGINAL");
    setReplaceNotes("");
    setReplaceFile(null);
  };

  const handleExecuteReplace = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!replaceModalForm || !replaceFile || !idToken) return;
    setReplacing(true);
    try {
      const formData = new FormData();
      formData.append("file", replaceFile);
      formData.append("version", replaceVersion);
      formData.append("provenance", replaceProvenance);
      formData.append("verification_status", "unverified");
      if (replaceAuthority) formData.append("issuing_authority", replaceAuthority);
      if (replaceUrl) formData.append("official_download_url", replaceUrl);
      if (replaceNotes) formData.append("provenance_notes", replaceNotes);

      await replaceOfficialForm(idToken, replaceModalForm.form_id || replaceModalForm.id, formData);
      alert("Form replaced and historical version archived successfully.");
      setReplaceModalForm(null);
      await fetchAdminData();
    } catch (e: any) {
      console.error("Replace form error:", e);
      alert("Failed to replace form: " + (e.message || "Unknown error"));
    } finally {
      setReplacing(false);
    }
  };

  const handleExecuteIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ingestFile || !idToken) return;
    setIngesting(true);
    setIngestResult(null);
    try {
      const formData = new FormData();
      formData.append("file", ingestFile);
      formData.append("title", ingestTitle);
      formData.append("document_category", ingestCategory);
      formData.append("issuing_authority", ingestAuthority);
      if (ingestUrl) formData.append("source_url", ingestUrl);

      const res = await ingestKnowledgeFile(idToken, formData);
      setIngestResult(res);
      await fetchAdminData();
    } catch (e: any) {
      console.error("Ingestion error:", e);
      alert("Ingestion failed: " + (e.message || "Unknown error"));
    } finally {
      setIngesting(false);
    }
  };

  useEffect(() => {
    if (!loading) {
      if (!firebaseUser) {
        router.replace("/login");
      } else if (profile && profile.role === "admin") {
        fetchAdminData();
      }
    }
  }, [loading, firebaseUser, profile, router, fetchAdminData]);

  if (loading) {
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
  if (!profile || profile.role !== "admin") {
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
            <div className="text-xs font-semibold text-zinc-900">{profile?.full_name || "AJAY M (Platform Administrator)"}</div>
            <div className="text-[10px] text-purple-700 font-mono">Platform Administrator</div>
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
              {stats?.users?.users ?? stats?.users?.citizens ?? 0} Users • {stats?.users?.admins || 0} Admins
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
            <div className="text-[11px] text-zinc-400">Ed25519 Platform Attestation</div>
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

        {/* Official Forms Repository & Statutory Catalog Section (Phase P3D) */}
        <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-semibold text-zinc-900">
                  Statutory Forms & Official Repository
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-800 border border-emerald-200">
                  {forms.length} Assets Registered
                </span>
              </div>
              <p className="text-xs text-zinc-500">
                Official Indian government forms verified by administrators under PostgreSQL Forced RLS.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setIngestModalOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-[#e5e2dc] text-zinc-800 hover:bg-zinc-50 rounded-lg text-xs font-medium transition"
              >
                <BookOpen className="w-3.5 h-3.5 text-zinc-500" />
                <span>Ingest Knowledge File</span>
              </button>
              <button
                onClick={handleSyncForms}
                disabled={syncingForms}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#18181b] text-white hover:bg-zinc-800 rounded-lg text-xs font-medium transition disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${syncingForms ? "animate-spin" : ""}`} />
                <span>{syncingForms ? "Syncing..." : "Sync Verified Catalog"}</span>
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#faf9f6] text-zinc-500 border-b border-[#e5e2dc]">
                <tr>
                  <th className="py-2.5 px-3 font-medium">Form / Code</th>
                  <th className="py-2.5 px-3 font-medium">Category / Authority</th>
                  <th className="py-2.5 px-3 font-medium">Provenance</th>
                  <th className="py-2.5 px-3 font-medium">SHA-256 Checksum</th>
                  <th className="py-2.5 px-3 font-medium">Status</th>
                  <th className="py-2.5 px-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {forms.map((f) => {
                  const fid = f.form_id || f.id;
                  const isVerified = f.verification_status === "verified";
                  const prov = (f.provenance || "APPLICATION_GENERATED").toUpperCase();
                  const isOfficial = prov === "OFFICIAL_ORIGINAL" || prov === "OFFICIAL_COPY";
                  return (
                    <tr key={fid} className="hover:bg-zinc-50/50">
                      <td className="py-2.5 px-3">
                        <div className="font-semibold text-zinc-900">{f.form_name}</div>
                        <div className="text-[10px] font-mono text-zinc-400">
                          {f.form_code || fid} • v{f.version || "1.0"} • {f.file_format || "PDF"} • {f.file_size_bytes ? `${(f.file_size_bytes / 1024).toFixed(1)} KB` : "~12 KB"}
                        </div>
                      </td>
                      <td className="py-2.5 px-3">
                        <div className="text-zinc-800 font-medium capitalize">{f.document_category}</div>
                        <div className="text-[11px] text-zinc-500">{f.issuing_authority}</div>
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-semibold ${
                            isOfficial
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                              : "bg-amber-50 text-amber-800 border border-amber-200"
                          }`}
                        >
                          {prov.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 font-mono text-[10px] text-zinc-600">
                        {f.sha256_hash ? (
                          <span title={f.sha256_hash}>
                            {f.sha256_hash.substring(0, 10)}...{f.sha256_hash.substring(f.sha256_hash.length - 6)}
                          </span>
                        ) : (
                          <span className="text-zinc-400 italic">None</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-semibold ${
                            isVerified
                              ? "bg-emerald-100 text-emerald-800 border border-emerald-200"
                              : "bg-zinc-100 text-zinc-700 border border-zinc-200"
                          }`}
                        >
                          {f.verification_status || "unverified"}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          <button
                            onClick={() => handleToggleVerification(f)}
                            disabled={updatingFormId === fid}
                            className={`px-2 py-1 rounded text-[11px] font-medium transition ${
                              isVerified
                                ? "bg-zinc-100 text-zinc-700 hover:bg-zinc-200"
                                : "bg-emerald-600 text-white hover:bg-emerald-700"
                            }`}
                            title="Toggle form verification status"
                          >
                            {updatingFormId === fid ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : isVerified ? (
                              "Revoke"
                            ) : (
                              "Verify"
                            )}
                          </button>
                          <button
                            onClick={() => handleOpenReplace(f)}
                            className="px-2 py-1 rounded text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200 hover:bg-amber-100 transition"
                            title="Upload authentic government PDF replacement"
                          >
                            Replace
                          </button>
                          <button
                            onClick={() => handleOpenHistory(f)}
                            className="p-1 rounded text-zinc-500 hover:text-black hover:bg-zinc-100 transition"
                            title="View version history & retired archives"
                          >
                            <History className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleAdminDownloadForm(f)}
                            className="p-1 rounded text-zinc-500 hover:text-black hover:bg-zinc-100 transition"
                            title="Download verified asset"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </button>
                          {f.official_portal_url && (
                            <a
                              href={f.official_portal_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="p-1 rounded text-zinc-500 hover:text-black hover:bg-zinc-100 transition"
                              title="Official government portal"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
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

        {/* Modal: Version History */}
        {historyModalForm && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl border border-zinc-200 shadow-2xl max-w-2xl w-full p-6 space-y-4 max-h-[85vh] flex flex-col">
              <div className="flex items-start justify-between border-b border-zinc-100 pb-3">
                <div>
                  <h3 className="text-base font-semibold text-zinc-900">
                    Version History: {historyModalForm.form_name}
                  </h3>
                  <p className="text-xs text-zinc-500">
                    Form ID: {historyModalForm.form_id} • Current Active Version: v{historyModalForm.version || "1.0"}
                  </p>
                </div>
                <button
                  onClick={() => setHistoryModalForm(null)}
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto space-y-3">
                {loadingHistory ? (
                  <div className="py-8 text-center text-xs text-zinc-500 flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Loading version history...</span>
                  </div>
                ) : formHistory.length > 0 ? (
                  formHistory.map((ver, idx) => (
                    <div key={ver.id || idx} className="p-3.5 rounded-xl border border-zinc-200 bg-zinc-50/50 space-y-1.5 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-zinc-900 font-mono">
                          v{ver.version || "1.0"}
                        </span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-200 text-zinc-700">
                          {ver.verification_status || "retired"}
                        </span>
                      </div>
                      <div className="text-[11px] text-zinc-600 font-mono truncate">
                        SHA-256: {ver.sha256_hash || "N/A"}
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-zinc-500 pt-1 border-t border-zinc-200/60">
                        <span>Provenance: {ver.provenance}</span>
                        <span>Retired: {ver.retired_at ? new Date(ver.retired_at).toLocaleDateString() : "Historical"}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="py-8 text-center text-xs text-zinc-500">
                    No superseded versions recorded yet. This is the initial version in the repository.
                  </div>
                )}
              </div>

              <div className="pt-3 border-t border-zinc-100 flex justify-end">
                <button
                  onClick={() => setHistoryModalForm(null)}
                  className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-xs font-medium hover:bg-zinc-800"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Replace Form Asset */}
        {replaceModalForm && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl border border-zinc-200 shadow-2xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-start justify-between border-b border-zinc-100 pb-3">
                <div>
                  <h3 className="text-base font-semibold text-zinc-900">
                    Replace Official Form Document
                  </h3>
                  <p className="text-xs text-zinc-500">
                    {replaceModalForm.form_name} ({replaceModalForm.form_id})
                  </p>
                </div>
                <button
                  onClick={() => setReplaceModalForm(null)}
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <form onSubmit={handleExecuteReplace} className="space-y-3.5 text-xs">
                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 text-[11px] leading-relaxed">
                  <strong>Non-destructive Archive:</strong> The existing asset (v{replaceModalForm.version || "1.0"}) will be cryptographically preserved in <code>official_form_versions</code> and logged to the tamper-evident audit trail.
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-zinc-700">New PDF Document File</label>
                  <input
                    type="file"
                    accept=".pdf"
                    required
                    onChange={(e) => setReplaceFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-zinc-700 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-zinc-100 file:text-zinc-800 hover:file:bg-zinc-200 cursor-pointer"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-medium text-zinc-700">New Version Number</label>
                    <input
                      type="text"
                      required
                      value={replaceVersion}
                      onChange={(e) => setReplaceVersion(e.target.value)}
                      placeholder="e.g. 2.0"
                      className="w-full h-8 px-2.5 bg-white border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:border-zinc-900 font-mono"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-medium text-zinc-700">Provenance</label>
                    <select
                      value={replaceProvenance}
                      onChange={(e) => setReplaceProvenance(e.target.value)}
                      className="w-full h-8 px-2 bg-white border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:border-zinc-900"
                    >
                      <option value="OFFICIAL_ORIGINAL">OFFICIAL ORIGINAL</option>
                      <option value="OFFICIAL_COPY">OFFICIAL COPY</option>
                      <option value="APPLICATION_GENERATED">APPLICATION GENERATED</option>
                      <option value="SYNTHETIC_TEST_ASSET">SYNTHETIC TEST ASSET</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-zinc-700">Issuing Authority</label>
                  <input
                    type="text"
                    value={replaceAuthority}
                    onChange={(e) => setReplaceAuthority(e.target.value)}
                    placeholder="e.g. Unique Identification Authority of India (UIDAI)"
                    className="w-full h-8 px-2.5 bg-white border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:border-zinc-900"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-zinc-700">Official Source Download URL</label>
                  <input
                    type="url"
                    value={replaceUrl}
                    onChange={(e) => setReplaceUrl(e.target.value)}
                    placeholder="https://..."
                    className="w-full h-8 px-2.5 bg-white border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:border-zinc-900 font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="font-medium text-zinc-700">Provenance / Review Notes</label>
                  <textarea
                    rows={2}
                    value={replaceNotes}
                    onChange={(e) => setReplaceNotes(e.target.value)}
                    placeholder="Source gazette notice, circular reference, or publication information"
                    className="w-full p-2 bg-white border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:border-zinc-900"
                  />
                </div>

                <div className="pt-3 border-t border-zinc-100 flex items-center justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setReplaceModalForm(null)}
                    className="px-3 py-1.5 bg-white border border-zinc-200 text-zinc-700 hover:bg-zinc-50 rounded-lg font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={replacing || !replaceFile}
                    className="px-4 py-1.5 bg-zinc-900 text-white rounded-lg font-medium hover:bg-zinc-800 disabled:opacity-50 flex items-center gap-1.5"
                  >
                    {replacing ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Replacing...</span>
                      </>
                    ) : (
                      <span>Upload & Replace Form</span>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Ingest Knowledge File */}
        {ingestModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl border border-zinc-200 shadow-2xl max-w-lg w-full p-6 space-y-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-start justify-between border-b border-zinc-100 pb-3">
                <div>
                  <h3 className="text-base font-semibold text-zinc-900">
                    Ingest Statutory Knowledge Circular
                  </h3>
                  <p className="text-xs text-zinc-500">
                    Upload official guideline, gazette notification, or procedure document into Qdrant & PostgreSQL.
                  </p>
                </div>
                <button
                  onClick={() => {
                    setIngestModalOpen(false);
                    setIngestResult(null);
                  }}
                  className="p-1 rounded-lg text-zinc-400 hover:text-zinc-700"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {ingestResult ? (
                <div className="space-y-4">
                  <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl space-y-2 text-xs text-emerald-950">
                    <div className="flex items-center gap-2 font-semibold text-emerald-800 text-sm">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                      <span>Knowledge Document Successfully Ingested!</span>
                    </div>
                    <p className="leading-relaxed">{ingestResult.message}</p>
                    <div className="grid grid-cols-2 gap-2 pt-2 border-t border-emerald-200/60 font-mono text-[11px]">
                      <div>Pages: {ingestResult.page_count}</div>
                      <div>Chunks: {ingestResult.chunk_count}</div>
                      <div>Embedding: {ingestResult.embedding_status}</div>
                      <div>Qdrant Index: {ingestResult.indexing_status}</div>
                    </div>
                    <div className="font-mono text-[10px] text-zinc-600 pt-1 truncate">
                      SHA-256: {ingestResult.sha256_hash}
                    </div>
                  </div>

                  <div className="flex justify-end">
                    <button
                      onClick={() => {
                        setIngestModalOpen(false);
                        setIngestResult(null);
                      }}
                      className="px-4 py-2 bg-zinc-900 text-white rounded-lg text-xs font-medium hover:bg-zinc-800"
                    >
                      Done
                    </button>
                  </div>
                </div>
              ) : (
                <form onSubmit={handleExecuteIngest} className="space-y-3.5 text-xs">
                  <div className="space-y-1">
                    <label className="font-medium text-zinc-700">Official Document File (PDF, TXT, MD)</label>
                    <input
                      type="file"
                      accept=".pdf,.txt,.md"
                      required
                      onChange={(e) => setIngestFile(e.target.files?.[0] || null)}
                      className="w-full text-xs text-zinc-700 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-zinc-100 file:text-zinc-800 hover:file:bg-zinc-200 cursor-pointer"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-zinc-700">Document / Circular Title</label>
                    <input
                      type="text"
                      required
                      value={ingestTitle}
                      onChange={(e) => setIngestTitle(e.target.value)}
                      placeholder="e.g. UIDAI Standard Operating Procedure for Name Update"
                      className="w-full h-8 px-2.5 bg-white border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:border-zinc-900"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1">
                      <label className="font-medium text-zinc-700">Document Category</label>
                      <select
                        value={ingestCategory}
                        onChange={(e) => setIngestCategory(e.target.value)}
                        className="w-full h-8 px-2 bg-white border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:border-zinc-900 capitalize"
                      >
                        <option value="aadhaar">Aadhaar</option>
                        <option value="pan">PAN</option>
                        <option value="passport">Passport</option>
                        <option value="epf">EPF</option>
                        <option value="education_10th">Class 10</option>
                        <option value="education_12th">Class 12</option>
                        <option value="general">General / Gazette</option>
                      </select>
                    </div>
                    <div className="space-y-1">
                      <label className="font-medium text-zinc-700">Issuing Authority</label>
                      <input
                        type="text"
                        required
                        value={ingestAuthority}
                        onChange={(e) => setIngestAuthority(e.target.value)}
                        placeholder="e.g. UIDAI"
                        className="w-full h-8 px-2.5 bg-white border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:border-zinc-900"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <label className="font-medium text-zinc-700">Official Source URL</label>
                    <input
                      type="url"
                      value={ingestUrl}
                      onChange={(e) => setIngestUrl(e.target.value)}
                      placeholder="https://..."
                      className="w-full h-8 px-2.5 bg-white border border-zinc-200 rounded-lg text-zinc-900 focus:outline-none focus:border-zinc-900 font-mono"
                    />
                  </div>

                  <div className="pt-3 border-t border-zinc-100 flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setIngestModalOpen(false)}
                      className="px-3 py-1.5 bg-white border border-zinc-200 text-zinc-700 hover:bg-zinc-50 rounded-lg font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={ingesting || !ingestFile}
                      className="px-4 py-1.5 bg-zinc-900 text-white rounded-lg font-medium hover:bg-zinc-800 disabled:opacity-50 flex items-center gap-1.5"
                    >
                      {ingesting ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          <span>Chunking & Indexing...</span>
                        </>
                      ) : (
                        <span>Ingest & Index in Qdrant</span>
                      )}
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

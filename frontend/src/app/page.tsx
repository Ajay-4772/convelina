"use client";

import { useEffect, useState } from "react";
import { 
  ShieldCheck, 
  FileSearch, 
  Server, 
  Database, 
  Layers, 
  RefreshCw,
  CheckCircle2, 
  AlertCircle, 
  Cpu, 
  FileText,
  Lock,
  UserCheck,
  KeyRound,
  ShieldAlert,
  LogOut,
  UploadCloud,
  Trash2,
  Eye,
  FileCheck
} from "lucide-react";


interface HealthData {
  status: string;
  timestamp?: number;
  services?: {
    backend?: { status: string; error?: string };
    postgres?: { status: string; error?: string };
    qdrant?: { status: string; error?: string };
    firebase_auth?: { status: string };
  };
}

interface UserProfile {
  id: string;
  firebase_uid: string;
  email: string;
  full_name: string;
  role: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>("");

  // Demo active role identity state for interactive verification
  const [activeIdentity, setActiveIdentity] = useState<"citizen" | "officer" | "admin">("citizen");
  const [activeProfile, setActiveProfile] = useState<UserProfile | null>(null);
  const [authTestOutput, setAuthTestOutput] = useState<Record<string, { status: number; message: string }>>({});
  const [testingAuth, setTestingAuth] = useState<boolean>(false);

  // Module 4: Secure Document Upload & OCR state
  const [selectedDocType, setSelectedDocType] = useState<string>("aadhaar");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loadingDocs, setLoadingDocs] = useState<boolean>(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const getSimulatedToken = (role: "citizen" | "officer" | "admin") => {
    return `test_token_:ui_demo_${role}:${role}.demo@synthetic.test:${role.toUpperCase()} User`;
  };


  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/health`, { cache: "no-store" });
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        setHealth(errorData);
        setError(`Service degraded (HTTP ${res.status})`);
      } else {
        const data = await res.json();
        setHealth(data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to connect to backend");
      setHealth(null);
    } finally {
      setLoading(false);
      setLastChecked(new Date().toLocaleTimeString());
    }
  };

  const syncIdentityAndTestRoutes = async (role: "citizen" | "officer" | "admin") => {
    setTestingAuth(true);
    setActiveIdentity(role);
    const token = getSimulatedToken(role);

    try {
      // 1. Provision / sync profile
      await fetch(`${apiUrl}/api/v1/auth/provision`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ full_name: `${role.toUpperCase()} Demo User` })
      });

      // 2. Fetch /me
      const meRes = await fetch(`${apiUrl}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (meRes.ok) {
        const profileData = await meRes.json();
        setActiveProfile(profileData);
      }

      // 3. Test RBAC endpoints
      const endpoints = [
        { key: "citizen", url: "/api/v1/auth/citizen-only" },
        { key: "officer", url: "/api/v1/auth/officer-only" },
        { key: "admin", url: "/api/v1/auth/admin-only" }
      ];

      const results: Record<string, { status: number; message: string }> = {};
      for (const ep of endpoints) {
        const r = await fetch(`${apiUrl}${ep.url}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const resJson = await r.json().catch(() => ({}));
        results[ep.key] = {
          status: r.status,
          message: r.ok ? "Access Granted" : (resJson.detail || "Forbidden")
        };
      }
      setAuthTestOutput(results);
      fetchDocuments(role);

    } catch (e: unknown) {
      console.error("Auth test failed:", e);
    } finally {
      setTestingAuth(false);
    }

  };

  const fetchDocuments = async (role = activeIdentity) => {
    setLoadingDocs(true);
    try {
      const token = getSimulatedToken(role);
      const res = await fetch(`${apiUrl}/api/v1/documents`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (e) {
      console.error("Failed to fetch documents", e);
    } finally {
      setLoadingDocs(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setUploadError("Please select a document file (.pdf, .jpg, .png)");
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("document_type", selectedDocType);

    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/documents/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        setUploadError(data.detail || "Upload or OCR processing failed");
      } else {
        setUploadResult(data);
        setSelectedFile(null);
        fetchDocuments(activeIdentity);
      }
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Network error during upload");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (id: string) => {
    try {
      const token = getSimulatedToken(activeIdentity);
      const res = await fetch(`${apiUrl}/api/v1/documents/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        fetchDocuments(activeIdentity);
      }
    } catch (e) {
      console.error("Failed to delete document", e);
    }
  };

  useEffect(() => {
    checkHealth();
    syncIdentityAndTestRoutes("citizen");
    fetchDocuments("citizen");
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);


  const getStatusBadge = (svcStatus?: string) => {
    if (svcStatus === "up" || svcStatus === "configured") {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/60">
          <CheckCircle2 className="w-3.5 h-3.5" /> Operational
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-950/80 text-rose-400 border border-rose-800/60">
        <AlertCircle className="w-3.5 h-3.5" /> Offline / Degraded
      </span>
    );
  };

  return (
    <main className="min-h-screen p-6 md:p-12 max-w-7xl mx-auto flex flex-col justify-between">
      {/* Header */}
      <div>
        <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-8 border-b border-border/80">
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-600/20 border border-blue-500/30 rounded-xl text-blue-400">
              <ShieldCheck className="w-8 h-8" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-white">Consolith</h1>
                <span className="text-xs px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
                  Module 3: Authentication & Role Scoping
                </span>
              </div>
              <p className="text-sm text-gray-400 mt-0.5">
                AI-Powered Identity Document Conflict Detection & Government Correction Assistance
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              id="refresh-health-btn"
              onClick={checkHealth}
              disabled={loading}
              className="inline-flex items-center gap-2 px-3.5 py-2 text-sm font-medium text-gray-200 bg-surface border border-border rounded-lg hover:bg-surface-card hover:border-gray-600 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-blue-400" : ""}`} />
              Check Status
            </button>
            <div className="text-xs text-gray-400">
              Last check: <span className="text-gray-300 font-mono">{lastChecked || "Checking..."}</span>
            </div>
          </div>
        </header>

        {/* Live Authentication & RBAC Verification Console */}
        <section className="mt-8 p-6 rounded-2xl bg-surface/80 border border-border backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border/60">
            <div className="flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-blue-400" />
              <h2 className="text-base font-semibold text-white">Live Identity & Role-Based Access Control (RBAC) Console</h2>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400">Simulate Identity:</span>
              {(["citizen", "officer", "admin"] as const).map((role) => (
                <button
                  key={role}
                  id={`role-btn-${role}`}
                  onClick={() => syncIdentityAndTestRoutes(role)}
                  disabled={testingAuth}
                  className={`px-3 py-1 text-xs font-medium rounded-lg border transition ${
                    activeIdentity === role 
                      ? "bg-blue-600 text-white border-blue-500 shadow-sm shadow-blue-500/20" 
                      : "bg-surface text-gray-300 border-border hover:bg-surface-card"
                  }`}
                >
                  {role.charAt(0).toUpperCase() + role.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Active Session Identity */}
            <div className="p-4 rounded-xl bg-surface-card/60 border border-border">
              <div className="flex items-center gap-2 text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                <UserCheck className="w-4 h-4 text-emerald-400" /> Active Verified Profile
              </div>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Name:</span>
                  <span className="text-white font-medium">{activeProfile?.full_name || "Syncing..."}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Role:</span>
                  <span className="font-mono text-xs px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                    {activeProfile?.role || activeIdentity}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Firebase UID:</span>
                  <span className="font-mono text-xs text-gray-300">{activeProfile?.firebase_uid || "Pending"}</span>
                </div>
              </div>
            </div>

            {/* Server-Side RBAC Enforcement Status */}
            <div className="p-4 rounded-xl bg-surface-card/60 border border-border md:col-span-2">
              <div className="flex items-center gap-2 text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                <ShieldAlert className="w-4 h-4 text-cyan-400" /> Server-Side Route Access Checks (FastAPI)
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-3">
                {[
                  { key: "citizen", label: "/api/v1/auth/citizen-only" },
                  { key: "officer", label: "/api/v1/auth/officer-only" },
                  { key: "admin", label: "/api/v1/auth/admin-only" }
                ].map(({ key, label }) => {
                  const res = authTestOutput[key];
                  const isOk = res?.status === 200;
                  return (
                    <div key={key} className={`p-2.5 rounded-lg border text-xs flex flex-col justify-between ${
                      isOk 
                        ? "bg-emerald-950/40 border-emerald-800/60 text-emerald-300"
                        : "bg-rose-950/30 border-rose-800/50 text-rose-300"
                    }`}>
                      <span className="font-mono text-[11px] truncate">{label}</span>
                      <div className="mt-2 flex items-center justify-between font-medium">
                        <span>HTTP {res?.status || "..."}</span>
                        <span>{isOk ? "Allowed (200)" : "Forbidden (403)"}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </section>

        {/* System Health Grid */}
        <section className="mt-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
              <Layers className="w-5 h-5 text-blue-400" /> System Architecture & Services
            </h2>
            <div className="text-xs text-gray-400">Docker Compose Managed</div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Frontend Card */}
            <div id="status-frontend-card" className="p-5 rounded-xl bg-surface/70 border border-border backdrop-blur-sm">
              <div className="flex items-start justify-between">
                <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400">
                  <Cpu className="w-5 h-5" />
                </div>
                {getStatusBadge("up")}
              </div>
              <h3 className="text-base font-medium text-white mt-4">Next.js Web App</h3>
              <p className="text-xs text-gray-400 mt-1">App Router, TypeScript, Tailwind CSS</p>
              <div className="mt-4 pt-3 border-t border-border/60 flex justify-between text-xs text-gray-400">
                <span>Port</span>
                <span className="font-mono text-gray-300">3000</span>
              </div>
            </div>

            {/* Backend Card */}
            <div id="status-backend-card" className="p-5 rounded-xl bg-surface/70 border border-border backdrop-blur-sm">
              <div className="flex items-start justify-between">
                <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                  <Server className="w-5 h-5" />
                </div>
                {getStatusBadge(health?.services?.backend?.status)}
              </div>
              <h3 className="text-base font-medium text-white mt-4">FastAPI Backend</h3>
              <p className="text-xs text-gray-400 mt-1">Pydantic v2 & Firebase Auth Re-verification</p>
              <div className="mt-4 pt-3 border-t border-border/60 flex justify-between text-xs text-gray-400">
                <span>Port</span>
                <span className="font-mono text-gray-300">8000</span>
              </div>
            </div>

            {/* PostgreSQL Card */}
            <div id="status-postgres-card" className="p-5 rounded-xl bg-surface/70 border border-border backdrop-blur-sm">
              <div className="flex items-start justify-between">
                <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                  <Database className="w-5 h-5" />
                </div>
                {getStatusBadge(health?.services?.postgres?.status)}
              </div>
              <h3 className="text-base font-medium text-white mt-4">PostgreSQL 16</h3>
              <p className="text-xs text-gray-400 mt-1">Non-Superuser Role & Forced RLS</p>
              <div className="mt-4 pt-3 border-t border-border/60 flex justify-between text-xs text-gray-400">
                <span>Port</span>
                <span className="font-mono text-gray-300">5432</span>
              </div>
            </div>

            {/* Qdrant Card */}
            <div id="status-qdrant-card" className="p-5 rounded-xl bg-surface/70 border border-border backdrop-blur-sm">
              <div className="flex items-start justify-between">
                <div className="p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-400">
                  <FileSearch className="w-5 h-5" />
                </div>
                {getStatusBadge(health?.services?.qdrant?.status)}
              </div>
              <h3 className="text-base font-medium text-white mt-4">Qdrant Vector DB</h3>
              <p className="text-xs text-gray-400 mt-1">Vector store for BGE-M3 RAG embeddings</p>
              <div className="mt-4 pt-3 border-t border-border/60 flex justify-between text-xs text-gray-400">
                <span>Port</span>
                <span className="font-mono text-gray-300">6333</span>
              </div>
            </div>
          </div>

          {error && (
            <div className="mt-4 p-4 rounded-xl bg-rose-950/40 border border-rose-800/50 text-rose-300 text-sm flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
              <div>
                <p className="font-medium">Backend Health Check Notice</p>
                <p className="text-xs text-rose-300/80 mt-0.5">{error}</p>
              </div>
            </div>
          )}
        </section>

        {/* Module 4: Secure Document Upload & OCR Pipeline Console */}
        <section className="mt-8 p-6 rounded-2xl bg-surface/50 border border-border backdrop-blur-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between pb-6 border-b border-border/80 gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 text-xs font-semibold uppercase tracking-wider rounded bg-indigo-950 text-indigo-400 border border-indigo-800/60">
                  Module 4
                </span>
                <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                  <UploadCloud className="w-5 h-5 text-indigo-400" /> Secure Document Upload & OCR Extraction
                </h2>
              </div>
              <p className="text-sm text-gray-400 mt-1">
                Upload Indian identity documents with content validation, Tesseract OCR extraction, Aadhaar masking, and RLS enforcement.
              </p>
            </div>
            <button
              onClick={() => fetchDocuments(activeIdentity)}
              disabled={loadingDocs}
              className="px-3 py-1.5 rounded-lg border border-border text-xs text-gray-300 hover:text-white flex items-center gap-1.5 hover:bg-surface transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingDocs ? "animate-spin" : ""}`} /> Refresh Library
            </button>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
            {/* Upload Form Card */}
            <div className="p-5 rounded-xl bg-surface/80 border border-border flex flex-col justify-between">
              <form onSubmit={handleUpload} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5">Document Type</label>
                  <select
                    value={selectedDocType}
                    onChange={(e) => setSelectedDocType(e.target.value)}
                    className="w-full bg-slate-900 border border-border rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="aadhaar">Aadhaar Card (UIDAI)</option>
                    <option value="pan">PAN Card (Income Tax)</option>
                    <option value="passport">Indian Passport</option>
                    <option value="education_10th">Class 10 Certificate</option>
                    <option value="education_12th">Class 12 Certificate</option>
                    <option value="epf_record">EPFO / UAN Record</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-400 mb-1.5">Document File (PDF, JPEG, PNG - Max 10MB)</label>
                  <input
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="w-full text-xs text-gray-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500 cursor-pointer"
                  />
                  {selectedFile && (
                    <p className="text-xs text-indigo-300 mt-1.5 flex items-center gap-1">
                      <FileCheck className="w-3.5 h-3.5" /> {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                    </p>
                  )}
                </div>

                {uploadError && (
                  <div className="p-3 rounded-lg bg-rose-950/50 border border-rose-800/60 text-xs text-rose-300 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                    <span>{uploadError}</span>
                  </div>
                )}

                <button
                  type="submit"
                  disabled={uploading || !selectedFile}
                  className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" /> Processing OCR...
                    </>
                  ) : (
                    <>
                      <UploadCloud className="w-4 h-4" /> Upload & Run OCR
                    </>
                  )}
                </button>
              </form>

              {uploadResult && (
                <div className="mt-4 p-3 rounded-lg bg-emerald-950/40 border border-emerald-800/50 text-xs text-emerald-300">
                  <div className="flex items-center gap-1.5 font-medium">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" /> OCR {uploadResult.ocr_status.toUpperCase()}
                  </div>
                  <p className="mt-1 font-mono text-[11px] text-gray-300">Masked ID: {uploadResult.masked_id || "N/A"}</p>
                  <p className="text-[11px] text-emerald-400/80 mt-0.5">Temp file securely unlinked per privacy policy.</p>
                </div>
              )}
            </div>

            {/* Document Library Table (RLS scoped) */}
            <div className="lg:col-span-2 p-5 rounded-xl bg-surface/80 border border-border flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Database className="w-4 h-4 text-indigo-400" /> Document Repository ({documents.length})
                  </h3>
                  <span className="text-[11px] font-mono text-gray-400">Scoped to: {activeIdentity}</span>
                </div>

                {documents.length === 0 ? (
                  <div className="py-10 text-center text-sm text-gray-500 border border-dashed border-border rounded-xl">
                    No documents uploaded for this identity yet.
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-border/80 text-gray-400">
                          <th className="pb-2">Type</th>
                          <th className="pb-2">Identifier</th>
                          <th className="pb-2">Status</th>
                          <th className="pb-2">Extracted Fields</th>
                          <th className="pb-2 text-right">Action</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-border/40 text-gray-300">
                        {documents.map((doc) => (
                          <tr key={doc.id} className="hover:bg-slate-900/40">
                            <td className="py-2.5 font-medium uppercase text-white">{doc.document_type}</td>
                            <td className="py-2.5 font-mono text-indigo-300">{doc.masked_id || "—"}</td>
                            <td className="py-2.5">
                              <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                                doc.ocr_status === "completed" ? "bg-emerald-950 text-emerald-400 border border-emerald-800" : "bg-amber-950 text-amber-400 border border-amber-800"
                              }`}>
                                {doc.ocr_status}
                              </span>
                            </td>
                            <td className="py-2.5 max-w-[200px] truncate text-gray-400 font-mono text-[11px]">
                              {JSON.stringify(doc.extracted_fields)}
                            </td>
                            <td className="py-2.5 text-right">
                              <button
                                onClick={() => handleDeleteDocument(doc.id)}
                                className="p-1 rounded hover:bg-rose-950/60 text-gray-400 hover:text-rose-400 transition"
                                title="Delete document"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        </section>

        {/* Foundation Overview & Scope Cards */}

        <section className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 rounded-xl bg-surface/40 border border-border">
            <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-3">
              <FileText className="w-4 h-4 text-blue-400" /> Supported Identity Documents (Tier 1)
            </h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> Aadhaar Card (Masked & Encrypted at rest)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> PAN Card (Income Tax Department / NSDL)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> Indian Passport (Passport Seva)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> 10th & 12th Educational Certificates
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-400" /> EPFO Records (EPF Member Passbook / UAN)
              </li>
            </ul>
          </div>

          <div className="p-6 rounded-xl bg-surface/40 border border-border">
            <h3 className="text-base font-semibold text-white flex items-center gap-2 mb-3">
              <Lock className="w-4 h-4 text-emerald-400" /> Security & Integrity Architecture
            </h3>
            <ul className="space-y-2 text-sm text-gray-300">
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> PostgreSQL Native Row-Level Security (Forced)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Dedicated Non-Superuser DB Connection (consolith_app)
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Server-side Firebase JWT Re-verification on every route
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Append-only tamper-evident audit log with hash chain
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Role escalation defense trigger on users table
              </li>
            </ul>
          </div>
        </section>
      </div>

      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-border/60 text-xs text-gray-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p>Consolith — Final Year Academic Project</p>
        <p className="font-mono">Tamper-Evident Architecture • Fail-Safe Verification</p>
      </footer>
    </main>
  );
}

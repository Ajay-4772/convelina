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
  Lock
} from "lucide-react";

interface HealthData {
  status: string;
  timestamp?: number;
  services?: {
    backend?: { status: string; error?: string };
    postgres?: { status: string; error?: string };
    qdrant?: { status: string; error?: string };
  };
}

export default function Home() {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>("");

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
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

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const getStatusBadge = (svcStatus?: string) => {
    if (svcStatus === "up") {
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
                <span className="text-xs px-2 py-0.5 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  Module 1: Foundation
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
              <p className="text-xs text-gray-400 mt-1">Pydantic v2 strict validation & API routes</p>
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
              <p className="text-xs text-gray-400 mt-1">Relational DB with forced RLS & Audit Logs</p>
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
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Dedicated Non-Superuser DB Connection
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Server-side JWT Re-verification on every route
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Hash-chained append-only tamper-evident audit log
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400" /> Internal PKI/CA with Ed25519 digital signatures
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

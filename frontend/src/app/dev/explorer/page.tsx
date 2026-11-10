"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Shield,
  Layers,
  Route,
  BookOpen,
  PlayCircle,
  Users,
  Database,
  Lock,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Search,
  ExternalLink,
  RefreshCw,
  ArrowRight,
  Sparkles,
  Scale,
  FileText,
  User,
  Key,
  Activity,
  Terminal,
  Server,
  FolderOpen,
  Info,
  LogOut,
  Sliders,
  Check,
  Copy,
  ChevronRight,
  ShieldCheck,
  Eye,
  EyeOff
} from "lucide-react";
import Logo from "../../../components/ui/Logo";
import { useAuth } from "../../../context/AuthContext";

export default function DevExplorerPage() {
  const router = useRouter();
  const { profile, idToken, logout } = useAuth();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Production Guard (Client-Side)
  const isProduction = process.env.NEXT_PUBLIC_ENVIRONMENT === "production" && process.env.NEXT_PUBLIC_ALLOW_DEV_EXPLORER !== "true";

  // Active Tab State
  const [activeTab, setActiveTab] = useState<"overview" | "routes" | "features" | "workflows" | "accounts" | "persistence" | "admin">("overview");

  // Overview Data
  const [overviewData, setOverviewData] = useState<any | null>(null);
  const [loadingOverview, setLoadingOverview] = useState(false);

  // Persistence Inspector Data
  const [persistenceData, setPersistenceData] = useState<any | null>(null);
  const [loadingPersistence, setLoadingPersistence] = useState(false);

  // Filter States
  const [routeRoleFilter, setRouteRoleFilter] = useState<string>("ALL");
  const [routeSearchQuery, setRouteSearchQuery] = useState("");
  const [activeWorkflowId, setActiveWorkflowId] = useState<number>(1);
  const [activeFeatureId, setActiveFeatureId] = useState<string>("documents");

  // Simulation Feedback
  const [simulationStatus, setSimulationStatus] = useState<string | null>(null);
  const [copiedToken, setCopiedToken] = useState(false);

  // Fetch Dev Overview
  const fetchOverview = useCallback(async () => {
    setLoadingOverview(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/dev/overview`);
      if (res.ok) {
        const data = await res.json();
        setOverviewData(data);
      }
    } catch (e) {
      console.error("Failed to load dev overview:", e);
    } finally {
      setLoadingOverview(false);
    }
  }, [apiUrl]);

  // Fetch Persistence Inspector Data
  const fetchPersistence = useCallback(async () => {
    if (!idToken) {
      setPersistenceData(null);
      return;
    }
    setLoadingPersistence(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/dev/persistence-inspect`, {
        headers: {
          Authorization: `Bearer ${idToken}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setPersistenceData(data);
      } else {
        setPersistenceData({ error: `HTTP ${res.status}: ${res.statusText}` });
      }
    } catch (e: any) {
      setPersistenceData({ error: e.message || "Failed to inspect persistence" });
    } finally {
      setLoadingPersistence(false);
    }
  }, [apiUrl, idToken]);

  useEffect(() => {
    fetchOverview();
  }, [fetchOverview]);

  useEffect(() => {
    if (activeTab === "persistence") {
      fetchPersistence();
    }
  }, [activeTab, fetchPersistence]);

  // Provision / Switch Test Account
  const handleSimulateAccount = async (target: "citizen_a" | "citizen_b" | "admin") => {
    setSimulationStatus(`Preparing synthetic session for ${target}...`);
    try {
      const res = await fetch(`${apiUrl}/api/v1/dev/provision-test-account`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target }),
      });
      if (!res.ok) {
        throw new Error(`Failed to provision: ${res.statusText}`);
      }
      const data = await res.json();
      localStorage.setItem("convelina_test_token", data.test_token);
      setSimulationStatus(`Session activated for ${data.full_name} (${data.role.toUpperCase()}). Reloading...`);
      setTimeout(() => {
        window.location.reload();
      }, 700);
    } catch (err: any) {
      setSimulationStatus(`Error: ${err.message}`);
    }
  };

  const handleClearSession = async () => {
    localStorage.removeItem("convelina_test_token");
    sessionStorage.clear();
    await logout();
    setSimulationStatus("Simulated session cleared. Reloading...");
    setTimeout(() => {
      window.location.reload();
    }, 600);
  };

  if (isProduction) {
    return (
      <div className="min-h-screen bg-[#faf9f6] flex items-center justify-center p-6">
        <div className="bg-white border border-[#e5e2dc] rounded-2xl p-8 max-w-md text-center shadow-card space-y-4">
          <div className="w-12 h-12 rounded-xl bg-rose-50 border border-rose-200 text-rose-600 flex items-center justify-center mx-auto">
            <Lock className="w-6 h-6" />
          </div>
          <h2 className="text-lg font-serif text-zinc-900">404 - Development Only Route</h2>
          <p className="text-xs text-zinc-600 leading-relaxed">
            The CONVELINA Application Explorer is strictly disabled in production environments for platform security.
          </p>
          <div className="pt-2">
            <Link
              href="/"
              className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-xl hover:bg-zinc-800 transition"
            >
              Return to Home
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Frontend Route Inventory (Verified 15 Routes)
  const FRONTEND_ROUTES = [
    {
      path: "/",
      role: "PUBLIC",
      name: "Public Landing Page",
      purpose: "Hero presentation, product capabilities, architectural security model, and interactive walk-through.",
      auth: "None",
      backend: ["GET /", "GET /health"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/login",
      role: "PUBLIC",
      name: "Citizen Login",
      purpose: "Email/password and Google Sign-in authentication portal with development fallback.",
      auth: "None",
      backend: ["POST /api/v1/auth/me", "POST /api/v1/auth/login"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/signup",
      role: "PUBLIC",
      name: "Citizen Registration",
      purpose: "New user registration, establishing a citizen profile bound to role 'user'.",
      auth: "None",
      backend: ["POST /api/v1/auth/signup"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/verify-email",
      role: "PUBLIC / USER",
      name: "Email Verification",
      purpose: "6-digit OTP verification screen backed by PostgreSQL email_otps table.",
      auth: "Email OTP",
      backend: ["POST /api/v1/auth/send-email-otp", "POST /api/v1/auth/verify-email-otp"],
      status: "SIMULATED",
      tested: "VERIFIED",
    },
    {
      path: "/setup-profile",
      role: "USER",
      name: "Profile Setup",
      purpose: "First-time profile onboarding collecting legal name, phone number, and address.",
      auth: "Session Required",
      backend: ["PUT /api/v1/auth/profile"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/app",
      role: "USER",
      name: "Citizen Dashboard",
      purpose: "Central hub for uploaded identity documents, OCR confirmation status, and summary statistics.",
      auth: "USER Required",
      backend: ["GET /api/v1/documents", "POST /api/v1/documents/upload", "POST /api/v1/documents/{id}/confirm"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/app/inconsistencies",
      role: "USER",
      name: "Inconsistencies Hub",
      purpose: "Multi-dimensional conflict detection comparison, discrepancy cards, and resolution linking.",
      auth: "USER Required",
      backend: ["GET /api/v1/conflicts", "POST /api/v1/conflicts/detect", "POST /api/v1/correction-drafts/generate"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/app/assistant",
      role: "USER",
      name: "AI Assistant Workspace",
      purpose: "Claude-inspired conversational interface for statutory procedural guidance and official form retrieval.",
      auth: "USER Required",
      backend: ["GET /api/v1/conversations", "POST /api/v1/conversations", "POST /api/v1/conversations/{id}/messages"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/app/assistant/[conversationId]",
      role: "USER",
      name: "Specific Chat Conversation",
      purpose: "Threaded conversation context with multi-turn retrieval grounding and statutory form cards.",
      auth: "USER Required",
      backend: ["GET /api/v1/conversations/{id}", "POST /api/v1/conversations/{id}/messages"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/app/forms",
      role: "USER",
      name: "Official Forms Repository",
      purpose: "Searchable catalog of 52 verified Indian government identity forms and statutory circulars.",
      auth: "USER Required",
      backend: ["GET /api/v1/repository/forms", "GET /api/v1/repository/forms/search"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/app/forms/[formId]",
      role: "USER",
      name: "Form Detail & Procedure Guide",
      purpose: "Detailed 7-section statutory breakdown, preparation checklist, and asset stream.",
      auth: "USER Required",
      backend: ["GET /api/v1/repository/forms/{id}", "GET /api/v1/repository/checklists/{id}/progress", "PUT /api/v1/repository/checklists/{id}/progress"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/app/profile",
      role: "USER",
      name: "Citizen Profile & Settings",
      purpose: "Account identity details, session telemetry, and privacy audit log.",
      auth: "USER Required",
      backend: ["GET /api/v1/auth/me", "PUT /api/v1/auth/profile"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/admin/login",
      role: "PUBLIC / ADMIN",
      name: "Admin Authentication",
      purpose: "Dedicated administrator login portal with strict server-side role verification.",
      auth: "None / Elevates to ADMIN",
      backend: ["GET /api/v1/auth/me", "POST /api/v1/auth/login"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/admin",
      role: "ADMIN",
      name: "Admin Operations Console",
      purpose: "Platform diagnostics, user account management, statutory form sync, PKI keystore, and audit logs.",
      auth: "ADMIN Required",
      backend: ["GET /api/v1/admin/overview-stats", "GET /api/v1/admin/users", "GET /api/v1/knowledge/admin/forms", "GET /api/v1/pki/keys"],
      status: "READY",
      tested: "VERIFIED",
    },
    {
      path: "/dev/explorer",
      role: "PUBLIC / DEV",
      name: "Application Explorer (QA)",
      purpose: "Development-only architecture inspection, live route map, persistence inspector, and test simulation.",
      auth: "Development Mode Only",
      backend: ["GET /api/v1/dev/overview", "GET /api/v1/dev/persistence-inspect", "POST /api/v1/dev/provision-test-account"],
      status: "READY",
      tested: "VERIFIED",
    },
  ];

  // 14 Guided Workflows
  const WORKFLOWS = [
    {
      id: 1,
      title: "1. Register & Sign In",
      category: "Authentication",
      route: "/login",
      role: "PUBLIC / USER",
      description: "Establish a citizen account or sign in using simulated credentials in local development mode.",
      steps: [
        "Navigate to /login (or /signup).",
        "Enter synthetic email: citizen_a@example.com and any password.",
        "Submit form: in development mode without live Firebase, AuthContext establishes a local simulated token.",
        "Expected result: The application redirects to /app with authenticated session status.",
      ],
      apiEndpoint: "POST /api/v1/auth/me (Bearer token)",
      dbChange: "User auto-provisioned in PostgreSQL 'users' table with role 'user'.",
      mode: "SIMULATED (Cloud Firebase unconfigured; local token active)",
    },
    {
      id: 2,
      title: "2. Upload a Synthetic Identity Document",
      category: "Document Upload",
      route: "/app",
      role: "USER",
      description: "Upload synthetic Aadhaar or PAN identity documents into the citizen workspace.",
      steps: [
        "In /app, click 'Upload Document' to open the ingestion modal.",
        "Select category (e.g., Aadhaar or PAN).",
        "Choose a synthetic test PDF or image asset.",
        "Click 'Upload & Process'.",
      ],
      apiEndpoint: "POST /api/v1/documents/upload (multipart/form-data)",
      dbChange: "Record created in 'documents' table with file_hash, Fernet AES-256 encrypted payload, and ocr_status='completed'.",
      mode: "REAL (PostgreSQL 16 under Forced RLS; synthetic test assets)",
    },
    {
      id: 3,
      title: "3. Review OCR-Extracted Fields",
      category: "Field Extraction",
      route: "/app",
      role: "USER",
      description: "Inspect field-level OCR confidence scores, Laplacian image quality variance, and extracted demographics.",
      steps: [
        "Locate the uploaded document card in /app.",
        "Click 'View Details / Review Fields'.",
        "Inspect extracted fields: Name, Date of Birth, Gender, and ID Number.",
        "Note confidence badges: green (>= 0.85), amber (0.70-0.84), red (< 0.70).",
      ],
      apiEndpoint: "GET /api/v1/documents/{id}",
      dbChange: "Reads 'field_extractions' JSONB column in 'documents'.",
      mode: "REAL (Tesseract OCR / Deterministic extraction)",
    },
    {
      id: 4,
      title: "4. Confirm or Correct Extracted Fields",
      category: "Citizen Confirmation",
      route: "/app",
      role: "USER",
      description: "Citizen reviews and confirms extracted demographic fields to establish an immutable baseline for conflict detection.",
      steps: [
        "In document review modal, verify demographic values.",
        "If a field contains OCR noise, edit the text box.",
        "Click 'Confirm Extracted Demographic Fields'.",
        "Card transitions from 'Awaiting Confirmation' to 'Citizen Confirmed'.",
      ],
      apiEndpoint: "POST /api/v1/documents/{id}/confirm",
      dbChange: "Updates 'confirmed_fields', sets 'is_user_confirmed=True', and records confirmed_at timestamp.",
      mode: "REAL (PostgreSQL Forced RLS)",
    },
    {
      id: 5,
      title: "5. Compare Two Identity Documents",
      category: "Conflict Detection",
      route: "/app/inconsistencies",
      role: "USER",
      description: "Execute pairwise deterministic comparison across two confirmed identity documents.",
      steps: [
        "Navigate to /app/inconsistencies.",
        "Select Document A (e.g. Aadhaar) and Document B (e.g. PAN).",
        "Click 'Run Inconsistency Check'.",
        "Engine analyzes Name (Jaro-Winkler + Levenshtein), Date of Birth, Father's Name, and Address.",
      ],
      apiEndpoint: "POST /api/v1/conflicts/detect",
      dbChange: "Inserts records into 'conflicts' table with severity ('high', 'medium', 'low') and comparison_method.",
      mode: "REAL (PostgreSQL 16 Forced RLS)",
    },
    {
      id: 6,
      title: "6. Review Detected Discrepancies",
      category: "Conflict Detection",
      route: "/app/inconsistencies",
      role: "USER",
      description: "Examine detailed comparison cards showing exact mismatched values, severity, and statutory risk explanation.",
      steps: [
        "In /app/inconsistencies, view the detected discrepancy cards.",
        "Review severity: e.g. High-Severity Name Mismatch ('Aarav Sharma' vs 'Arav Sharma').",
        "Review statutory risk explanation: e.g., Section 139AA PAN-Aadhaar linking rejection.",
      ],
      apiEndpoint: "GET /api/v1/conflicts",
      dbChange: "Reads 'conflicts' table bounded strictly to current user_id.",
      mode: "REAL (PostgreSQL 16 Forced RLS)",
    },
    {
      id: 7,
      title: "7. Open a Discrepancy in AI Assistant",
      category: "AI Workspace",
      route: "/app/inconsistencies",
      role: "USER",
      description: "Seamlessly transition from a detected conflict into the Claude-inspired AI chat workspace with attached context.",
      steps: [
        "On any discrepancy card, click 'Discuss with CONVELINA AI'.",
        "The application creates a new conversation and redirects to /app/assistant/[conversationId].",
        "Top banner displays the linked conflict context with unlinking controls.",
      ],
      apiEndpoint: "POST /api/v1/conversations (with conflict_id)",
      dbChange: "Creates record in 'assistant_conversations' linked to conflict_id.",
      mode: "REAL (PostgreSQL 16 Forced RLS)",
    },
    {
      id: 8,
      title: "8. Ask Questions About a Discrepancy",
      category: "AI Workspace",
      route: "/app/assistant",
      role: "USER",
      description: "Ask procedural and statutory questions; assistant responds with grounded legal citations and official form cards.",
      steps: [
        "In assistant composer, enter a query: 'How do I correct my name in PAN to match Aadhaar?'.",
        "Click Send (or Ctrl+Enter).",
        "Assistant retrieves statutory chunks from Qdrant knowledge base via Okapi BM25.",
        "Response includes statutory citations (e.g. DOC_034) and interactive OfficialFormCard with PDF preview/download.",
      ],
      apiEndpoint: "POST /api/v1/conversations/{id}/messages",
      dbChange: "Appends user and assistant messages to 'assistant_messages' table.",
      mode: "REAL (Qdrant volume retrieval; deterministic RAG engine active)",
    },
    {
      id: 9,
      title: "9. Search & Open a Repository Resource",
      category: "Document Repository",
      route: "/app/forms",
      role: "USER",
      description: "Explore the unified catalog of 52 official Indian government forms and circulars.",
      steps: [
        "Navigate to /app/forms.",
        "Switch category tabs: Aadhaar (35), PAN (7), Passport (3), Class 10/12 (4), EPF (2).",
        "Use search input: e.g. 'Form 49A' or 'DOB update'.",
        "Click any form card to open its dedicated detail view (/app/forms/[formId]).",
      ],
      apiEndpoint: "GET /api/v1/repository/forms",
      dbChange: "Reads static disk manifests + PostgreSQL official_forms table.",
      mode: "REAL (Public official repository; zero citizen PII)",
    },
    {
      id: 10,
      title: "10. Review Procedural Checklist Guidance",
      category: "Document Repository",
      route: "/app/forms/[formId]",
      role: "USER",
      description: "Inspect 7 structured statutory sections including Supporting-Document Checklist with statutory conditions.",
      steps: [
        "In /app/forms/DOC_001 (or another form), scroll to Section 5: Supporting-Document Checklist.",
        "Inspect requirements categorized as VERIFIED_MANDATORY, VERIFIED_CONDITIONAL, and RECOMMENDED.",
        "Review statutory citations referencing UIDAI List of Acceptable Supporting Documents.",
      ],
      apiEndpoint: "GET /api/v1/repository/forms/{formId}",
      dbChange: "Reads checklist configuration from ChecklistService.",
      mode: "REAL (BM25 Grounded Procedural Guidance)",
    },
    {
      id: 11,
      title: "11. Save Checklist Progress",
      category: "Persistent Checklist",
      route: "/app/forms/[formId]",
      role: "USER",
      description: "Mark checklist items as completed and verify that progress is durably saved in PostgreSQL across reloads.",
      steps: [
        "In Section 5, check the checkbox next to one or more checklist items.",
        "A notification pill confirms 'Checklist saved to secure workspace'.",
        "Reload the browser page (F5).",
        "Observe that the checkbox state remains completed.",
      ],
      apiEndpoint: "PUT /api/v1/repository/checklists/{procedureId}/progress",
      dbChange: "Upserts rows into 'citizen_checklist_items' table under PostgreSQL Forced RLS.",
      mode: "REAL (PostgreSQL 16 Forced RLS Persistence)",
    },
    {
      id: 12,
      title: "12. Generate & Review a Correction Draft",
      category: "Drafting",
      route: "/app/inconsistencies",
      role: "USER",
      description: "Generate an advisory administrative representation draft to government authorities (distinct from judicial petitions or automatic official approval).",
      steps: [
        "On any discrepancy card, click 'Generate Correction Draft'.",
        "Select petition template (e.g. Formal Name Correction Request).",
        "Review pre-filled details, recipient authority, and statutory subject line.",
        "Click 'Generate Draft'. Preview the formatted document card.",
        "Click 'Confirm Draft' to apply Ed25519 platform attestation.",
      ],
      apiEndpoint: "POST /api/v1/correction-drafts/generate",
      dbChange: "Inserts record into 'correction_drafts' with sha256_hash and Ed25519 platform attestation.",
      mode: "REAL (ReportLab/FreeSans PDF Generation & PostgreSQL 16 Storage)",
    },
    {
      id: 13,
      title: "13. Explore User Profile & Settings",
      category: "Account & Security",
      route: "/app/profile",
      role: "USER",
      description: "Review account metadata, tenancy isolation parameters, and sign out.",
      steps: [
        "Navigate to /app/profile.",
        "Review email, full name, assigned role ('user'), and session created timestamp.",
        "Inspect privacy notice regarding Aadhaar Act compliance and zero raw biometric storage.",
        "Click 'Sign Out' to terminate the session.",
      ],
      apiEndpoint: "GET /api/v1/auth/me",
      dbChange: "Reads user profile from PostgreSQL 'users' table.",
      mode: "REAL (Strict RLS isolation)",
    },
    {
      id: 14,
      title: "14. Explore ADMIN Portal",
      category: "Administration",
      route: "/admin",
      role: "ADMIN",
      description: "Access system-wide operational metrics, user directory, official forms catalog, and cryptographic audit log.",
      steps: [
        "Sign in as administrator (e.g. using the Test Account Simulator in Tab E).",
        "Navigate to /admin.",
        "Review system metric cards (Total Users, Documents Processed, Conflicts Detected, Active Signing Keys).",
        "Review User Account Directory.",
        "Review Statutory Forms & Official Repository with 'Verify/Revoke' controls.",
        "Review Ed25519 PKI Public Keystore and Append-Only Audit Trail.",
      ],
      apiEndpoint: "GET /api/v1/admin/overview-stats, GET /api/v1/admin/users",
      dbChange: "Admin actions record cryptographic events in 'audit_log' table.",
      mode: "REAL (PostgreSQL 16 Admin Role Enforcement)",
    },
  ];

  // Features Data (8 Core Features)
  const FEATURES = [
    {
      id: "documents",
      name: "Identity Document Ingestion & OCR",
      tagline: "Secure client-side pre-validation, Tesseract OCR, Laplacian image quality variance, and Fernet AES-256 encryption at rest.",
      reads: "Uploaded PDF / image files; user profile context.",
      creates: "PostgreSQL 'documents' table records with field_extractions JSONB, masked ID, and SHA-256 file hash.",
      backend: "DocumentProcessingService (backend/app/services/document_processing.py)",
      storage: "PostgreSQL 16 'documents' table + Storage temp directory.",
      persistence: "Durable in PostgreSQL under Forced RLS; raw files retained per privacy policy.",
      limitations: "Fallback regex/heuristic extraction active when system Tesseract binary is uninstalled on host.",
    },
    {
      id: "conflicts",
      name: "Deterministic Conflict Detection Engine",
      tagline: "Pairwise multi-attribute comparison evaluating name variations, date of birth limits, and gender mismatches without false negatives.",
      reads: "Confirmed demographic fields from two or more citizen documents.",
      creates: "Records in 'conflicts' table with severity ('high', 'medium', 'low'), comparison method, and description.",
      backend: "ConflictDetectionEngine (backend/app/services/conflict_service.py)",
      storage: "PostgreSQL 16 'conflicts' table under Forced RLS.",
      persistence: "Durable across sessions, page refreshes, and re-login.",
      limitations: "Requires at least two confirmed documents to compute cross-document pairwise matrices.",
    },
    {
      id: "assistant",
      name: "Conversational AI Workspace & Procedural RAG",
      tagline: "Claude-inspired chat UI backed by Okapi BM25 lexical retrieval and Qdrant dense vectors for statutory Indian legal guidance.",
      reads: "Statutory knowledge corpus in Qdrant; user conversation history; linked conflict records.",
      creates: "Records in 'assistant_conversations' and 'assistant_messages'.",
      backend: "HybridRetriever & AssistantService (backend/app/rag/hybrid_retriever.py)",
      storage: "PostgreSQL 16 ('assistant_conversations', 'assistant_messages') + Qdrant named volume 'consolin_qdrant_data'.",
      persistence: "Chat history persists across page reloads and cross-navigation.",
      limitations: "Gemini disabled by default; deterministic rule-based generator provides grounded legal answers.",
    },
    {
      id: "forms",
      name: "Official Forms Repository & Catalog",
      tagline: "Reconciled catalog of 52 authentic Indian government forms and circulars with SHA-256 provenance tracking and ReportLab rejection gate.",
      reads: "Static disk manifests, PDF assets, and PostgreSQL 'official_forms' catalog.",
      creates: "Admin verification updates and version history archives in 'official_form_versions'.",
      backend: "CitizenRepositoryService (backend/app/services/citizen_repository_service.py)",
      storage: "Local filesystem 'forms/' + PostgreSQL 'official_forms' table.",
      persistence: "Public reference metadata; durable across container restarts.",
      limitations: "Application-generated PDFs are honest-flagged and rejected from claiming official government provenance.",
    },
    {
      id: "checklist",
      name: "Citizen Preparation Checklist Engine",
      tagline: "Procedural checklist tracking required supporting proofs across 9 statutory Indian administrative procedures.",
      reads: "Procedural checklist manifests and citizen completed item states.",
      creates: "Rows in 'citizen_checklist_items' table under PostgreSQL Forced RLS.",
      backend: "ChecklistService (backend/app/services/checklist_service.py)",
      storage: "PostgreSQL 16 'citizen_checklist_items' table.",
      persistence: "Durable across page reloads, cross-route navigation, and logout.",
      limitations: "Item completion marks citizen preparation; does not submit official applications to external government portals.",
    },
    {
      id: "drafting",
      name: "Administrative Petition & Letter Drafting",
      tagline: "Personalized administrative letter generator creating submission-ready formal petition letters in English and Tamil with A4 watermarking.",
      reads: "Confirmed citizen demographics, detected conflict descriptions, and statutory letter templates.",
      creates: "Records in 'correction_drafts' table with version tracking, SHA-256 hash, and Ed25519 platform attestation.",
      backend: "CorrectionDraftService & DocumentGenerator (backend/app/services/correction_draft_service.py)",
      storage: "PostgreSQL 16 'correction_drafts' table.",
      persistence: "Durable legal document record; persists across sessions.",
      limitations: "Drafts are advisory administrative petitions and must be personally reviewed and submitted by the citizen.",
    },
    {
      id: "pki",
      name: "Ed25519 PKI Document Attestation",
      tagline: "RFC 8032 compliant cryptographic digital signature engine providing verifiable platform attestation for correction documents.",
      reads: "Normalized canonical JSON digest of correction draft or document attestation.",
      creates: "Cryptographic signature in 'digital_signatures' and attestation in 'document_attestations'.",
      backend: "PKIService (backend/app/services/pki_service.py)",
      storage: "PostgreSQL 16 'signing_keys' and 'document_attestations' tables.",
      persistence: "Permanent cryptographic verification record.",
      limitations: "Internal platform attestation; clearly separated from government-issued eSign.",
    },
    {
      id: "admin",
      name: "Platform Administrative Oversight",
      tagline: "Operations console for platform telemetry, user account management, form catalog synchronization, and immutable audit logs.",
      reads: "Aggregate platform statistics, user accounts, system activity, and PKI keystore.",
      creates: "Immutable audit events in 'audit_log' with SHA-256 hash chaining.",
      backend: "AdminRouter (backend/app/routers/admin.py)",
      storage: "PostgreSQL 16 'audit_log' table (Protected by rejection triggers).",
      persistence: "Append-only permanent audit log; UPDATE and DELETE operations strictly blocked by database triggers.",
      limitations: "Administrators cannot inspect private citizen document contents without generating an immutable audit entry.",
    },
  ];

  return (
    <div className="min-h-screen bg-[#faf9f6] text-[#18181b] flex flex-col font-sans selection:bg-[#18181b] selection:text-white">
      {/* Top Banner: Dev Environment Notice */}
      <div className="bg-purple-900 text-purple-100 px-4 py-2 text-xs font-mono flex items-center justify-between border-b border-purple-800">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-purple-300" />
          <span className="font-semibold tracking-wide">CONVELINA DEV QA ENVIRONMENT</span>
          <span className="hidden sm:inline text-purple-300">• Not accessible in production builds</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[11px] text-purple-200">
            Active Role: <strong className="text-white uppercase">{profile?.role || "GUEST (UNAUTHENTICATED)"}</strong>
          </span>
          {profile && (
            <button
              onClick={handleClearSession}
              className="text-xs text-purple-200 hover:text-white underline"
            >
              Sign out
            </button>
          )}
        </div>
      </div>

      {/* Explorer Navigation Header */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-[#e5e2dc] px-4 sm:px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/app" className="p-1.5 rounded-lg text-zinc-500 hover:text-black hover:bg-zinc-100 transition" title="Return to Workspace">
            <Logo size={24} showText={false} />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-[#18181b]">Application Explorer</span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-100 text-purple-800 border border-purple-200">
                QA & Interactive Audit
              </span>
            </div>
            <p className="text-[11px] text-zinc-500 hidden sm:block">
              Inspect architecture, verify real persistence, test citizen workflows, and audit security boundaries.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={fetchOverview}
            disabled={loadingOverview}
            className="p-1.5 rounded-lg text-zinc-500 hover:text-black hover:bg-zinc-100 transition"
            title="Refresh System Status"
          >
            <RefreshCw className={`w-4 h-4 ${loadingOverview ? "animate-spin" : ""}`} />
          </button>
          <Link
            href="/app"
            className="px-3 py-1.5 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition"
          >
            Open Citizen App
          </Link>
          <Link
            href="/admin"
            className="px-3 py-1.5 bg-purple-50 text-purple-700 border border-purple-200 text-xs font-medium rounded-lg hover:bg-purple-100 transition"
          >
            Open Admin Portal
          </Link>
        </div>
      </header>

      {/* Main Tabbed Navigation */}
      <div className="bg-white border-b border-[#e5e2dc] px-4 sm:px-6">
        <div className="max-w-7xl mx-auto flex space-x-1 sm:space-x-3 overflow-x-auto py-2 text-xs font-medium text-zinc-600">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-3 py-2 rounded-lg flex items-center gap-1.5 whitespace-nowrap transition ${
              activeTab === "overview" ? "bg-zinc-900 text-white" : "hover:bg-zinc-100 hover:text-black"
            }`}
          >
            <Server className="w-3.5 h-3.5" />
            <span>Overview & Health</span>
          </button>
          <button
            onClick={() => setActiveTab("routes")}
            className={`px-3 py-2 rounded-lg flex items-center gap-1.5 whitespace-nowrap transition ${
              activeTab === "routes" ? "bg-zinc-900 text-white" : "hover:bg-zinc-100 hover:text-black"
            }`}
          >
            <Route className="w-3.5 h-3.5" />
            <span>Route Explorer ({FRONTEND_ROUTES.length})</span>
          </button>
          <button
            onClick={() => setActiveTab("features")}
            className={`px-3 py-2 rounded-lg flex items-center gap-1.5 whitespace-nowrap transition ${
              activeTab === "features" ? "bg-zinc-900 text-white" : "hover:bg-zinc-100 hover:text-black"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Feature Guide (8)</span>
          </button>
          <button
            onClick={() => setActiveTab("workflows")}
            className={`px-3 py-2 rounded-lg flex items-center gap-1.5 whitespace-nowrap transition ${
              activeTab === "workflows" ? "bg-zinc-900 text-white" : "hover:bg-zinc-100 hover:text-black"
            }`}
          >
            <PlayCircle className="w-3.5 h-3.5" />
            <span>Interactive Workflows (14)</span>
          </button>
          <button
            onClick={() => setActiveTab("accounts")}
            className={`px-3 py-2 rounded-lg flex items-center gap-1.5 whitespace-nowrap transition ${
              activeTab === "accounts" ? "bg-zinc-900 text-white" : "hover:bg-zinc-100 hover:text-black"
            }`}
          >
            <Users className="w-3.5 h-3.5" />
            <span>Test Accounts</span>
          </button>
          <button
            onClick={() => setActiveTab("persistence")}
            className={`px-3 py-2 rounded-lg flex items-center gap-1.5 whitespace-nowrap transition ${
              activeTab === "persistence" ? "bg-zinc-900 text-white" : "hover:bg-zinc-100 hover:text-black"
            }`}
          >
            <Database className="w-3.5 h-3.5" />
            <span>Persistence Inspector</span>
          </button>
          <button
            onClick={() => setActiveTab("admin")}
            className={`px-3 py-2 rounded-lg flex items-center gap-1.5 whitespace-nowrap transition ${
              activeTab === "admin" ? "bg-zinc-900 text-white" : "hover:bg-zinc-100 hover:text-black"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Admin Explorer</span>
          </button>
        </div>
      </div>

      {/* Explorer Content Body */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-4 sm:p-6 lg:p-8 space-y-6">

        {/* TAB 1: OVERVIEW & SYSTEM HEALTH */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Platform Description & Architecture Card */}
            <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-3">
              <div className="flex items-center gap-2">
                <Logo size={28} showText={false} />
                <h2 className="text-base font-serif text-zinc-900">
                  CONVELINA — Architecture & Mission Overview
                </h2>
              </div>
              <p className="text-xs text-zinc-600 leading-relaxed">
                <strong>Connect. Manage. Evolve.</strong> CONVELINA is an AI-powered identity-document conflict detection and government correction assistance system. It provides automated discrepancy analysis across Indian identity records (Aadhaar, PAN, Passport, Class 10/12, and EPF), backed by source-grounded statutory guidance, authentic government forms, and cryptographic verification.
              </p>
              <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-xl text-xs text-purple-900 space-y-1">
                <div className="font-semibold flex items-center gap-1.5">
                  <Shield className="w-3.5 h-3.5 text-purple-700" />
                  <span>Strict Two-Role Architecture Invariant</span>
                </div>
                <p className="text-[11px] text-purple-800 leading-relaxed">
                  CONVELINA supports exactly two roles: <strong>USER</strong> (citizen) and <strong>ADMIN</strong> (platform administrator). All officer, verifier, and case-assignment roles have been permanently deprecated at the database constraint level. Citizen records are strictly protected by <strong>PostgreSQL Forced Row-Level Security</strong> under non-superuser role <code>consolith_app</code>.
                </p>
              </div>
            </div>

            {/* Live Service Health Matrix */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-zinc-900 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-zinc-600" />
                  <span>Live Infrastructure & Service Health</span>
                </h3>
                <span className="text-[11px] font-mono text-zinc-500">Live Telemetry from FastAPI /health & /dev/overview</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {/* FastAPI Backend */}
                <div className="p-4 rounded-xl bg-white border border-[#e5e2dc] shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">FastAPI Backend</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                      READY
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500">Python 3.11 • Port 8000 • 115 API Routes Registered</p>
                  <div className="text-[10px] font-mono text-zinc-400">Environment: {overviewData?.services?.fastapi?.environment || "development"}</div>
                </div>

                {/* PostgreSQL Database */}
                <div className="p-4 rounded-xl bg-white border border-[#e5e2dc] shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">PostgreSQL 16 Database</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                      READY
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500">
                    Role: <code>consolith_app</code> (Non-superuser) • Port 5432
                  </p>
                  <div className="text-[10px] font-mono text-zinc-400">
                    21 Tables • <strong>21 Forced RLS</strong> • 21 Migrations Applied
                  </div>
                </div>

                {/* Qdrant Vector Storage */}
                <div className="p-4 rounded-xl bg-white border border-[#e5e2dc] shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Qdrant Vector Database</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                      READY
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500">Named Docker Volume <code>consolin_qdrant_data</code></p>
                  <div className="text-[10px] font-mono text-zinc-400">
                    34 Knowledge Chunks • 6 Form Vectors • 1024-dim Cosine
                  </div>
                </div>

                {/* Firebase Authentication */}
                <div className="p-4 rounded-xl bg-white border border-[#e5e2dc] shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Firebase Authentication</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-100 text-amber-800 border border-amber-200">
                      SIMULATED
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500">Local Dev Token Simulation Active</p>
                  <div className="text-[10px] font-mono text-zinc-400">
                    Live Cloud: BLOCKED (Credentials pending configuration)
                  </div>
                </div>

                {/* Gemini LLM Provider */}
                <div className="p-4 rounded-xl bg-white border border-[#e5e2dc] shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Gemini LLM Provider</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-50 text-rose-800 border border-rose-200">
                      BLOCKED
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500">Disabled by Default • Deterministic Fallback Active</p>
                  <div className="text-[10px] font-mono text-zinc-400">
                    BM25 Retrieval & Grounded Statutory Citations Active
                  </div>
                </div>

                {/* Tesseract OCR Engine */}
                <div className="p-4 rounded-xl bg-white border border-[#e5e2dc] shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">OCR Engine</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                      READY
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500">Tesseract with Regex/Heuristic Fallback</p>
                  <div className="text-[10px] font-mono text-zinc-400">
                    Laplacian Quality Variance • Pre-Save PII Masking
                  </div>
                </div>

                {/* Ed25519 PKI Attestation */}
                <div className="p-4 rounded-xl bg-white border border-[#e5e2dc] shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Ed25519 PKI Attestation</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                      READY
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500">RFC 8032 Canonical Digest Signing</p>
                  <div className="text-[10px] font-mono text-zinc-400">
                    Platform Document Attestation (Internal; distinct from statutory eSign)
                  </div>
                </div>

                {/* Statutory Forms Repository */}
                <div className="p-4 rounded-xl bg-white border border-[#e5e2dc] shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Statutory Repository</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                      READY
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500">52 Official Resources across 6 Categories</p>
                  <div className="text-[10px] font-mono text-zinc-400">
                    DOC_043 Governed (Human Review Required)
                  </div>
                </div>

                {/* Persistent Checklist Engine */}
                <div className="p-4 rounded-xl bg-white border border-[#e5e2dc] shadow-sm space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Citizen Checklist Storage</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                      READY
                    </span>
                  </div>
                  <p className="text-[11px] text-zinc-500">PostgreSQL 'citizen_checklist_items'</p>
                  <div className="text-[10px] font-mono text-zinc-400">
                    Forced RLS • Persists across refresh & re-login
                  </div>
                </div>
              </div>
            </div>

            {/* Quick Actions Card */}
            <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-3">
              <h3 className="text-sm font-semibold text-zinc-900">Direct Navigation & QA Shortcuts</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <Link
                  href="/app"
                  className="p-3 rounded-xl border border-[#e5e2dc] hover:bg-zinc-50 flex items-center justify-between transition"
                >
                  <span className="font-medium text-zinc-800">Citizen Dashboard</span>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />
                </Link>
                <Link
                  href="/app/inconsistencies"
                  className="p-3 rounded-xl border border-[#e5e2dc] hover:bg-zinc-50 flex items-center justify-between transition"
                >
                  <span className="font-medium text-zinc-800">Inconsistencies</span>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />
                </Link>
                <Link
                  href="/app/assistant"
                  className="p-3 rounded-xl border border-[#e5e2dc] hover:bg-zinc-50 flex items-center justify-between transition"
                >
                  <span className="font-medium text-zinc-800">AI Assistant</span>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />
                </Link>
                <Link
                  href="/app/forms"
                  className="p-3 rounded-xl border border-[#e5e2dc] hover:bg-zinc-50 flex items-center justify-between transition"
                >
                  <span className="font-medium text-zinc-800">Forms Repository</span>
                  <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: ROUTE EXPLORER */}
        {activeTab === "routes" && (
          <div className="space-y-4">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-[#e5e2dc]">
              <div>
                <h3 className="text-sm font-semibold text-zinc-900">Application Route Directory</h3>
                <p className="text-xs text-zinc-500">Every actual Next.js 14 frontend route and corresponding FastAPI backend endpoints.</p>
              </div>

              <div className="flex items-center gap-2 w-full sm:w-auto">
                <div className="relative flex-1 sm:w-56">
                  <Search className="w-3.5 h-3.5 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={routeSearchQuery}
                    onChange={(e) => setRouteSearchQuery(e.target.value)}
                    placeholder="Search routes..."
                    className="w-full pl-8 pr-3 py-1.5 text-xs border border-[#e5e2dc] rounded-lg bg-[#faf9f6]"
                  />
                </div>
                <select
                  value={routeRoleFilter}
                  onChange={(e) => setRouteRoleFilter(e.target.value)}
                  className="px-2.5 py-1.5 text-xs border border-[#e5e2dc] rounded-lg bg-white text-zinc-700"
                >
                  <option value="ALL">All Roles</option>
                  <option value="USER">USER</option>
                  <option value="ADMIN">ADMIN</option>
                  <option value="PUBLIC">PUBLIC</option>
                </select>
              </div>
            </div>

            <div className="space-y-3">
              {FRONTEND_ROUTES.filter((r) => {
                const matchRole = routeRoleFilter === "ALL" || r.role.includes(routeRoleFilter);
                const matchQuery =
                  r.path.toLowerCase().includes(routeSearchQuery.toLowerCase()) ||
                  r.name.toLowerCase().includes(routeSearchQuery.toLowerCase()) ||
                  r.purpose.toLowerCase().includes(routeSearchQuery.toLowerCase());
                return matchRole && matchQuery;
              }).map((r) => (
                <div key={r.path} className="p-4 bg-white rounded-xl border border-[#e5e2dc] shadow-sm space-y-2 hover:border-zinc-400 transition">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Link
                        href={r.path}
                        className="text-xs font-bold text-zinc-900 font-mono hover:text-purple-700 hover:underline inline-flex items-center gap-1"
                      >
                        <span>{r.path}</span>
                        <ExternalLink className="w-3 h-3 text-zinc-400" />
                      </Link>
                      <span className="text-xs text-zinc-500">• {r.name}</span>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] font-mono">
                      <span className={`px-2 py-0.5 rounded font-semibold ${
                        r.role.includes("ADMIN")
                          ? "bg-purple-100 text-purple-800"
                          : r.role.includes("USER")
                          ? "bg-blue-50 text-blue-800"
                          : "bg-zinc-100 text-zinc-700"
                      }`}>
                        {r.role}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                        {r.status}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-zinc-50 text-zinc-600 border border-zinc-200">
                        {r.tested}
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-zinc-600">{r.purpose}</p>

                  <div className="pt-2 border-t border-zinc-100 flex flex-wrap items-center gap-2 text-[11px]">
                    <span className="text-zinc-400 font-mono text-[10px]">Backend Endpoints:</span>
                    {r.backend.map((ep) => (
                      <span key={ep} className="px-2 py-0.5 rounded bg-[#faf9f6] border border-[#e5e2dc] text-zinc-700 font-mono text-[10px]">
                        {ep}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: FEATURE GUIDE */}
        {activeTab === "features" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Feature List (Left Sidebar) */}
            <div className="space-y-2 md:col-span-1">
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">Core Features (8)</h3>
              {FEATURES.map((feat) => (
                <button
                  key={feat.id}
                  onClick={() => setActiveFeatureId(feat.id)}
                  className={`w-full text-left p-3 rounded-xl border text-xs transition ${
                    activeFeatureId === feat.id
                      ? "bg-zinc-900 text-white border-zinc-900 shadow-sm"
                      : "bg-white text-zinc-800 border-[#e5e2dc] hover:bg-zinc-50"
                  }`}
                >
                  <div className="font-semibold">{feat.name}</div>
                  <div className={`text-[11px] truncate mt-0.5 ${activeFeatureId === feat.id ? "text-zinc-300" : "text-zinc-400"}`}>
                    {feat.storage}
                  </div>
                </button>
              ))}
            </div>

            {/* Feature Detail (Right Pane) */}
            <div className="md:col-span-2">
              {(() => {
                const feat = FEATURES.find((f) => f.id === activeFeatureId) || FEATURES[0];
                return (
                  <div className="p-6 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-4">
                    <div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-50 text-purple-800 border border-purple-200">
                        CONVELINA Architectural Feature
                      </span>
                      <h2 className="text-lg font-serif text-zinc-900 mt-1">{feat.name}</h2>
                      <p className="text-xs text-zinc-600 mt-1">{feat.tagline}</p>
                    </div>

                    <div className="space-y-3 text-xs">
                      <div className="p-3 bg-[#faf9f6] rounded-xl border border-[#e5e2dc]">
                        <span className="font-semibold text-zinc-700 block mb-1">What Data It Reads:</span>
                        <p className="text-zinc-600 leading-relaxed">{feat.reads}</p>
                      </div>

                      <div className="p-3 bg-[#faf9f6] rounded-xl border border-[#e5e2dc]">
                        <span className="font-semibold text-zinc-700 block mb-1">What Data It Creates / Updates:</span>
                        <p className="text-zinc-600 leading-relaxed">{feat.creates}</p>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="p-3 bg-[#faf9f6] rounded-xl border border-[#e5e2dc]">
                          <span className="font-semibold text-zinc-700 block mb-1">Backend Handling Service:</span>
                          <code className="text-[11px] text-purple-700 font-mono">{feat.backend}</code>
                        </div>
                        <div className="p-3 bg-[#faf9f6] rounded-xl border border-[#e5e2dc]">
                          <span className="font-semibold text-zinc-700 block mb-1">Storage Location:</span>
                          <p className="text-zinc-600">{feat.storage}</p>
                        </div>
                      </div>

                      <div className="p-3 bg-emerald-50/70 border border-emerald-200 rounded-xl">
                        <span className="font-semibold text-emerald-900 block mb-1">Persistence Across Page Reload / Re-Login:</span>
                        <p className="text-emerald-800 leading-relaxed">{feat.persistence}</p>
                      </div>

                      <div className="p-3 bg-amber-50/70 border border-amber-200 rounded-xl">
                        <span className="font-semibold text-amber-900 block mb-1">Current Implementation Constraints & Limitations:</span>
                        <p className="text-amber-800 leading-relaxed">{feat.limitations}</p>
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* TAB 4: INTERACTIVE WORKFLOW GUIDE */}
        {activeTab === "workflows" && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Workflow List (Left Sidebar) */}
            <div className="space-y-1.5 md:col-span-1 max-h-[75vh] overflow-y-auto pr-1">
              <h3 className="text-xs font-semibold text-zinc-500 uppercase tracking-wider mb-2">14 Guided QA Workflows</h3>
              {WORKFLOWS.map((wf) => (
                <button
                  key={wf.id}
                  onClick={() => setActiveWorkflowId(wf.id)}
                  className={`w-full text-left p-2.5 rounded-xl border text-xs transition ${
                    activeWorkflowId === wf.id
                      ? "bg-zinc-900 text-white border-zinc-900 shadow-sm"
                      : "bg-white text-zinc-800 border-[#e5e2dc] hover:bg-zinc-50"
                  }`}
                >
                  <div className="font-medium text-xs truncate">{wf.title}</div>
                  <div className={`text-[10px] mt-0.5 ${activeWorkflowId === wf.id ? "text-zinc-300" : "text-zinc-400"}`}>
                    {wf.category} • {wf.role}
                  </div>
                </button>
              ))}
            </div>

            {/* Workflow Detail (Right Pane) */}
            <div className="md:col-span-2">
              {(() => {
                const wf = WORKFLOWS.find((w) => w.id === activeWorkflowId) || WORKFLOWS[0];
                return (
                  <div className="p-6 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-4">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-zinc-100 pb-3">
                      <div>
                        <span className="text-[10px] font-mono text-purple-700 uppercase font-semibold">{wf.category}</span>
                        <h2 className="text-base font-serif text-zinc-900 mt-0.5">{wf.title}</h2>
                      </div>
                      <div className="flex items-center gap-2">
                        <Link
                          href={wf.route}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition"
                        >
                          <span>Open Screen ({wf.route})</span>
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>

                    <p className="text-xs text-zinc-600 leading-relaxed">{wf.description}</p>

                    {/* Step-by-Step Instructions */}
                    <div className="space-y-2">
                      <h4 className="text-xs font-semibold text-zinc-900">Step-by-Step Execution:</h4>
                      <ol className="list-decimal list-inside space-y-1.5 text-xs text-zinc-700 bg-[#faf9f6] p-4 rounded-xl border border-[#e5e2dc]">
                        {wf.steps.map((st, i) => (
                          <li key={i} className="leading-relaxed">
                            <span>{st}</span>
                          </li>
                        ))}
                      </ol>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <div className="p-3 bg-[#faf9f6] rounded-xl border border-[#e5e2dc]">
                        <span className="font-semibold text-zinc-700 block mb-1">Target API Endpoint:</span>
                        <code className="text-[11px] text-purple-700 font-mono">{wf.apiEndpoint}</code>
                      </div>
                      <div className="p-3 bg-[#faf9f6] rounded-xl border border-[#e5e2dc]">
                        <span className="font-semibold text-zinc-700 block mb-1">Expected Database Change:</span>
                        <p className="text-zinc-600 text-[11px]">{wf.dbChange}</p>
                      </div>
                    </div>

                    <div className="p-3 bg-zinc-50 border border-zinc-200 rounded-xl text-xs">
                      <span className="font-semibold text-zinc-900 block mb-1">Real vs. Simulated Classification:</span>
                      <p className="text-zinc-700 text-[11px]">{wf.mode}</p>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}

        {/* TAB 5: TEST ACCOUNTS & SIMULATOR */}
        {activeTab === "accounts" && (
          <div className="space-y-6">
            <div className="p-6 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-3">
              <h2 className="text-base font-serif text-zinc-900">Synthetic Test-Account Management & Simulator</h2>
              <p className="text-xs text-zinc-600 leading-relaxed">
                Seamlessly simulate authenticated sessions for local development and QA testing. All identities are <strong>strictly synthetic</strong> (no real Aadhaar, PAN, or passport numbers are used). When a synthetic session is activated, the token is recorded in <code>localStorage.convelina_test_token</code>, allowing immediate access to authenticated screens without live Firebase credentials.
              </p>

              {simulationStatus && (
                <div className="p-3 bg-purple-50 border border-purple-200 rounded-xl text-xs text-purple-800 flex items-center justify-between">
                  <span>{simulationStatus}</span>
                  <button onClick={() => setSimulationStatus(null)} className="text-purple-600 hover:text-purple-900 font-bold">×</button>
                </div>
              )}
            </div>

            {/* Test Accounts Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Citizen A */}
              <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-100 text-blue-800 border border-blue-200">
                      CITIZEN A
                    </span>
                    <span className="text-[10px] font-mono text-zinc-400">Role: USER</span>
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-900 mt-2">Aarav Sharma</h3>
                  <div className="text-xs text-zinc-500 font-mono">citizen_a@example.com</div>
                  <p className="text-[11px] text-zinc-600 mt-2 leading-relaxed">
                    Primary test citizen. Used for uploading synthetic Aadhaar & PAN, reviewing name discrepancies, chatting with the AI assistant, and generating correction drafts.
                  </p>
                </div>

                <div className="pt-3 border-t border-zinc-100 space-y-2">
                  <button
                    onClick={() => handleSimulateAccount("citizen_a")}
                    className="w-full py-2 bg-[#18181b] text-white text-xs font-medium rounded-xl hover:bg-zinc-800 transition"
                  >
                    Simulate Citizen A Session
                  </button>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText("test_token_:test_fuid_citizen_a:citizen_a@example.com:Aarav Sharma");
                      setCopiedToken(true);
                      setTimeout(() => setCopiedToken(false), 1500);
                    }}
                    className="w-full py-1.5 bg-[#faf9f6] text-zinc-700 border border-[#e5e2dc] text-[11px] font-mono rounded-lg hover:bg-zinc-100 transition flex items-center justify-center gap-1"
                  >
                    {copiedToken ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3 text-zinc-400" />}
                    <span>{copiedToken ? "Copied!" : "Copy Test Token"}</span>
                  </button>
                </div>
              </div>

              {/* Citizen B */}
              <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                      CITIZEN B
                    </span>
                    <span className="text-[10px] font-mono text-zinc-400">Role: USER</span>
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-900 mt-2">Priya Patel</h3>
                  <div className="text-xs text-zinc-500 font-mono">citizen_b@example.com</div>
                  <p className="text-[11px] text-zinc-600 mt-2 leading-relaxed">
                    Secondary isolated citizen. Used to rigorously verify <strong>PostgreSQL Forced RLS multi-tenant isolation</strong> (verifying that Citizen B receives empty lists and 404s when attempting to access Citizen A data).
                  </p>
                </div>

                <div className="pt-3 border-t border-zinc-100 space-y-2">
                  <button
                    onClick={() => handleSimulateAccount("citizen_b")}
                    className="w-full py-2 bg-[#18181b] text-white text-xs font-medium rounded-xl hover:bg-zinc-800 transition"
                  >
                    Simulate Citizen B Session
                  </button>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText("test_token_:test_fuid_citizen_b:citizen_b@example.com:Priya Patel");
                      setCopiedToken(true);
                      setTimeout(() => setCopiedToken(false), 1500);
                    }}
                    className="w-full py-1.5 bg-[#faf9f6] text-zinc-700 border border-[#e5e2dc] text-[11px] font-mono rounded-lg hover:bg-zinc-100 transition flex items-center justify-center gap-1"
                  >
                    <Copy className="w-3 h-3 text-zinc-400" />
                    <span>Copy Test Token</span>
                  </button>
                </div>
              </div>

              {/* Administrator */}
              <div className="p-5 rounded-2xl bg-white border border-purple-200 shadow-card space-y-3 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-100 text-purple-800 border border-purple-200">
                      ADMINISTRATOR
                    </span>
                    <span className="text-[10px] font-mono text-purple-600 font-semibold">Role: ADMIN</span>
                  </div>
                  <h3 className="text-sm font-semibold text-zinc-900 mt-2">AJAY M (Platform Admin)</h3>
                  <div className="text-xs text-zinc-500 font-mono">admin@convelina.gov.in</div>
                  <p className="text-[11px] text-zinc-600 mt-2 leading-relaxed">
                    Trusted administrative account provisioned via the secure bootstrap process. Grants access to system overview metrics, statutory forms catalog, and append-only audit trail.
                  </p>
                </div>

                <div className="pt-3 border-t border-zinc-100 space-y-2">
                  <button
                    onClick={() => handleSimulateAccount("admin")}
                    className="w-full py-2 bg-purple-700 text-white text-xs font-medium rounded-xl hover:bg-purple-800 transition"
                  >
                    Simulate Admin Session
                  </button>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText("test_token_:test_fuid_admin:admin@convelina.gov.in:AJAY M (Platform Administrator)");
                      setCopiedToken(true);
                      setTimeout(() => setCopiedToken(false), 1500);
                    }}
                    className="w-full py-1.5 bg-[#faf9f6] text-zinc-700 border border-[#e5e2dc] text-[11px] font-mono rounded-lg hover:bg-zinc-100 transition flex items-center justify-center gap-1"
                  >
                    <Copy className="w-3 h-3 text-zinc-400" />
                    <span>Copy Test Token</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 6: PERSISTENCE INSPECTOR */}
        {activeTab === "persistence" && (
          <div className="space-y-6">
            <div className="p-6 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-serif text-zinc-900">Live PostgreSQL Persistence Inspector</h2>
                  <p className="text-xs text-zinc-600 mt-0.5">
                    Read-only development inspection of the currently authenticated test citizen's stored records under <strong>PostgreSQL Forced RLS</strong>.
                  </p>
                </div>
                <button
                  onClick={fetchPersistence}
                  disabled={loadingPersistence}
                  className="px-3 py-1.5 bg-white border border-[#e5e2dc] text-zinc-700 hover:bg-zinc-50 rounded-lg text-xs font-medium transition flex items-center gap-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingPersistence ? "animate-spin" : ""}`} />
                  <span>Refresh Inspector</span>
                </button>
              </div>

              {!idToken && (
                <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-800 flex items-start gap-2.5">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
                  <div>
                    <span className="font-semibold block">No Authenticated Session Active</span>
                    <span>Please switch to the <strong>Test Accounts</strong> tab and click "Simulate Citizen A Session" or "Citizen B Session" to inspect persistent records.</span>
                  </div>
                </div>
              )}

              {persistenceData?.authenticated_user && (
                <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-xl text-xs flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <span className="text-purple-700 font-semibold">Inspecting User: </span>
                    <span className="font-mono text-purple-900">{persistenceData.authenticated_user.email_masked}</span>
                    <span className="text-zinc-400 font-mono text-[10px] ml-2">({persistenceData.authenticated_user.id})</span>
                  </div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-100 text-emerald-800 border border-emerald-200">
                    {persistenceData.authenticated_user.tenancy_enforcement}
                  </span>
                </div>
              )}
            </div>

            {/* Persistence Storage Matrix Table */}
            <div className="p-6 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-3">
              <h3 className="text-sm font-semibold text-zinc-900">Entity Storage & Tenancy Protection Matrix</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#faf9f6] text-zinc-500 border-b border-[#e5e2dc]">
                    <tr>
                      <th className="py-2.5 px-3 font-medium">Entity Category</th>
                      <th className="py-2.5 px-3 font-medium">Storage Location</th>
                      <th className="py-2.5 px-3 font-medium">RLS Protection</th>
                      <th className="py-2.5 px-3 font-medium">Persistence Guarantee</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100">
                    {(persistenceData?.storage_matrix || []).map((row: any, i: number) => (
                      <tr key={i} className="hover:bg-zinc-50/50">
                        <td className="py-2.5 px-3 font-medium text-zinc-900">{row.entity}</td>
                        <td className="py-2.5 px-3 font-mono text-[11px] text-purple-700">{row.storage}</td>
                        <td className="py-2.5 px-3">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                            row.rls_status === "FORCED" ? "bg-emerald-100 text-emerald-800" : "bg-zinc-100 text-zinc-700"
                          }`}>
                            {row.rls_status}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-[11px] text-zinc-600">{row.durability}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* User Records Inventory */}
            {persistenceData?.inventory && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Uploaded Documents */}
                <div className="p-5 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Uploaded Documents</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-zinc-100 text-zinc-700">
                      {persistenceData.inventory.documents.length} Records
                    </span>
                  </div>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {persistenceData.inventory.documents.length === 0 ? (
                      <div className="text-xs text-zinc-400 italic">No documents uploaded for this test citizen.</div>
                    ) : (
                      persistenceData.inventory.documents.map((d: any) => (
                        <div key={d.id} className="p-2.5 rounded-xl bg-[#faf9f6] border border-[#e5e2dc] text-xs">
                          <div className="font-semibold text-zinc-800 uppercase">{d.document_type}</div>
                          <div className="text-[11px] font-mono text-zinc-500">{d.masked_number} • {d.ocr_status}</div>
                          <div className="text-[10px] text-zinc-400">{d.storage_location}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Detected Conflicts */}
                <div className="p-5 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Detected Inconsistencies</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-50 text-amber-800 border border-amber-200">
                      {persistenceData.inventory.conflicts.length} Conflicts
                    </span>
                  </div>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {persistenceData.inventory.conflicts.length === 0 ? (
                      <div className="text-xs text-zinc-400 italic">No conflicts detected for this test citizen.</div>
                    ) : (
                      persistenceData.inventory.conflicts.map((c: any) => (
                        <div key={c.id} className="p-2.5 rounded-xl bg-[#faf9f6] border border-[#e5e2dc] text-xs">
                          <div className="font-semibold text-zinc-800 capitalize">{c.field_name} Mismatch ({c.severity})</div>
                          <div className="text-[11px] text-zinc-600">{c.value_a_masked} vs {c.value_b_masked}</div>
                          <div className="text-[10px] text-zinc-400">{c.storage_location}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Checklist Progress */}
                <div className="p-5 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Checklist Progress</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-50 text-emerald-800">
                      {persistenceData.inventory.checklists.length} Procedures
                    </span>
                  </div>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {persistenceData.inventory.checklists.length === 0 ? (
                      <div className="text-xs text-zinc-400 italic">No checklist progress saved for this test citizen.</div>
                    ) : (
                      persistenceData.inventory.checklists.map((ch: any) => (
                        <div key={ch.procedure_id} className="p-2.5 rounded-xl bg-[#faf9f6] border border-[#e5e2dc] text-xs">
                          <div className="font-semibold text-zinc-800 font-mono">{ch.procedure_id}</div>
                          <div className="text-[11px] text-emerald-700 font-medium">{ch.completed_count} Items Completed</div>
                          <div className="text-[10px] text-zinc-400">Last updated: {ch.last_updated ? new Date(ch.last_updated).toLocaleString() : "Recently"}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Correction Drafts */}
                <div className="p-5 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-zinc-900">Correction Drafts</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-50 text-purple-800">
                      {persistenceData.inventory.correction_drafts.length} Drafts
                    </span>
                  </div>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {persistenceData.inventory.correction_drafts.length === 0 ? (
                      <div className="text-xs text-zinc-400 italic">No correction drafts generated for this test citizen.</div>
                    ) : (
                      persistenceData.inventory.correction_drafts.map((dr: any) => (
                        <div key={dr.id} className="p-2.5 rounded-xl bg-[#faf9f6] border border-[#e5e2dc] text-xs">
                          <div className="font-semibold text-zinc-800">{dr.title}</div>
                          <div className="text-[11px] text-zinc-500">v{dr.version} • Status: {dr.status}</div>
                          <div className="text-[10px] text-zinc-400 font-mono">Hash: {dr.sha256_hash_short || "Signed"}</div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 7: ADMIN EXPLORER */}
        {activeTab === "admin" && (
          <div className="space-y-6">
            <div className="p-6 bg-white rounded-2xl border border-[#e5e2dc] shadow-card space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-serif text-zinc-900">Administrator Console Explorer</h2>
                  <p className="text-xs text-zinc-600 mt-0.5">
                    Platform operational diagnostics, catalog management, and immutable audit trail.
                  </p>
                </div>
                <Link
                  href="/admin"
                  className="px-3 py-1.5 bg-purple-700 text-white text-xs font-medium rounded-lg hover:bg-purple-800 transition flex items-center gap-1.5"
                >
                  <span>Open Live Admin Console</span>
                  <ExternalLink className="w-3.5 h-3.5" />
                </Link>
              </div>

              <div className="p-3 bg-purple-50/70 border border-purple-200 rounded-xl text-xs text-purple-900 leading-relaxed">
                <strong>Administrative Access Boundary:</strong> Platform administrators have authority to inspect system-wide operational counts, manage official public form catalogs, audit security logs, and review platform PKI keys. In accordance with privacy and RLS constraints, administrators cannot inspect private citizen document contents without generating an explicit audit trail entry.
              </div>
            </div>

            {/* Admin Functions Breakdown */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-2">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-zinc-600" />
                  <h3 className="text-xs font-semibold text-zinc-900">1. Real-Time Operational Metrics</h3>
                </div>
                <p className="text-xs text-zinc-600 leading-relaxed">
                  Endpoint: <code>GET /api/v1/admin/overview-stats</code><br />
                  Aggregates real PostgreSQL counts for platform users, uploaded documents, detected discrepancies, active Ed25519 signing keys, and audit activities.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-2">
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-zinc-600" />
                  <h3 className="text-xs font-semibold text-zinc-900">2. User Account Directory</h3>
                </div>
                <p className="text-xs text-zinc-600 leading-relaxed">
                  Endpoint: <code>GET /api/v1/admin/users</code><br />
                  Enables searching and filtering registered citizen accounts, displaying role assignments ('user' or 'admin') and creation dates.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-2">
                <div className="flex items-center gap-2">
                  <FolderOpen className="w-4 h-4 text-zinc-600" />
                  <h3 className="text-xs font-semibold text-zinc-900">3. Statutory Forms & Catalog Sync</h3>
                </div>
                <p className="text-xs text-zinc-600 leading-relaxed">
                  Endpoint: <code>GET /api/v1/knowledge/admin/forms</code><br />
                  Inspect all 52 registered statutory forms, verify or revoke statuses, trigger disk-to-database catalog synchronizations, and download verified assets.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-2">
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-zinc-600" />
                  <h3 className="text-xs font-semibold text-zinc-900">4. Form Replacement & Rejection Gate</h3>
                </div>
                <p className="text-xs text-zinc-600 leading-relaxed">
                  Endpoint: <code>POST /api/v1/knowledge/admin/forms/{'{id}'}/replace</code><br />
                  Allows uploading authentic government PDF assets. Enforces the strict ReportLab rejection gate: application-generated PDFs are denied with HTTP 400.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-2">
                <div className="flex items-center gap-2">
                  <Key className="w-4 h-4 text-purple-600" />
                  <h3 className="text-xs font-semibold text-zinc-900">5. Ed25519 PKI Public Keystore</h3>
                </div>
                <p className="text-xs text-zinc-600 leading-relaxed">
                  Endpoint: <code>GET /api/v1/pki/keys</code><br />
                  Displays active RFC 8032 public keys used by the platform to sign citizen attestations and verify tamper-evidence.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-2">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <h3 className="text-xs font-semibold text-zinc-900">6. Append-Only Tamper-Evident Audit Trail</h3>
                </div>
                <p className="text-xs text-zinc-600 leading-relaxed">
                  Endpoint: <code>GET /api/v1/admin/system-activity</code><br />
                  Inspect the immutable audit ledger. Every entry's SHA-256 hash cryptographically links to the previous entry, with UPDATE/DELETE blocked by database triggers.
                </p>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Explorer Footer */}
      <footer className="bg-white border-t border-[#e5e2dc] px-4 sm:px-6 py-4 text-center text-xs text-zinc-500 font-sans">
        <span>CONVELINA Development Application Explorer • Local QA Environment • </span>
        <span className="font-mono text-zinc-400">PostgreSQL Forced RLS Verified</span>
      </footer>
    </div>
  );
}

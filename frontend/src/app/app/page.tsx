"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Shield,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileText,
  Sparkles,
  User,
  Settings,
  Search,
  UploadCloud,
  Trash2,
  ExternalLink,
  Download,
  RefreshCw,
  LogOut,
  ChevronRight,
  ArrowRight,
  Eye,
  Plus,
  Lock,
  Mail,
  Phone,
  MapPin,
  Calendar,
  Check,
  X,
  Menu,
  Clock,
  Send,
  MessageSquare,
  ChevronDown,
  Info,
  ShieldCheck,
  FileCheck2,
  PanelLeftClose,
  PanelLeft,
  Copy,
  Paperclip,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import Logo from "../../components/ui/Logo";

// ==============================================================================
// Types & Interfaces
// ==============================================================================

interface DocumentItem {
  id: string;
  document_type: string;
  file_name: string;
  file_size_bytes: number;
  extracted_fields: Record<string, any>;
  created_at: string;
}

interface ConflictItem {
  id: string;
  field_name: string;
  doc_a_id: string;
  doc_b_id: string;
  doc_a_value: string;
  doc_b_value: string;
  severity: "high" | "medium" | "low";
  comparison_method?: string;
  similarity_score?: number;
  review_status: string;
  created_at: string;
}

interface FormItem {
  id: string;
  form_code: string;
  title: string;
  issuing_authority: string;
  category: string;
  description: string;
  download_url?: string;
  official_source_url?: string;
  requirements?: string[];
  purpose?: string;
}

interface ActivityItem {
  id: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  details: Record<string, any>;
  created_at: string;
}

interface AssistantMsg {
  id?: string;
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  forms?: any[];
  created_at?: string;
}

export default function CitizenAppPage() {
  const router = useRouter();
  const { firebaseUser, profile, idToken, loading, isProfileComplete, logout } = useAuth();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const isDemo = typeof window !== "undefined" && window.location.search.includes("demo=true");
  const currentUser = profile || (isDemo ? {
    id: "demo-user",
    full_name: "KAMESH G",
    email: "kamesh.g@velhightech.com",
    role: "citizen" as const,
    phone_number: "+91 98765 43210",
    date_of_birth: "2003-05-14",
    father_name: "GURUSAMY M",
    mother_name: "LAKSHMI G",
    address: "Avadi, Chennai, Tamil Nadu 600062",
  } : null);

  // App Navigation
  const [activeTab, setActiveTab] = useState<"home" | "conflicts" | "assistant" | "forms" | "profile">("home");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  // Documents & Conflicts State
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [uploadDocType, setUploadDocType] = useState("aadhaar");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);

  const [conflicts, setConflicts] = useState<ConflictItem[]>([]);
  const [detectingConflicts, setDetectingConflicts] = useState(false);
  const [hasCompared, setHasCompared] = useState(false);
  const [conflictSuccessMsg, setConflictSuccessMsg] = useState<string | null>(null);
  const [isDemoMode, setIsDemoMode] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined" && window.location.search.includes("demo=true")) {
      setIsDemoMode(true);
      setDocuments([
        {
          id: "doc-1",
          document_type: "aadhaar",
          file_name: "aadhaar_card_masked.pdf",
          file_size_bytes: 1420580,
          extracted_fields: { full_name: "KAMESH G", date_of_birth: "2003-05-14", father_name: "GURUSAMY M", gender: "Male", aadhaar_masked: "XXXX-XXXX-4041" },
          created_at: new Date(Date.now() - 3600000 * 24).toISOString(),
        },
        {
          id: "doc-2",
          document_type: "pan",
          file_name: "pan_card_scan.jpg",
          file_size_bytes: 845200,
          extracted_fields: { full_name: "KAMESH GURUSAMY", date_of_birth: "2003-05-14", father_name: "GURUSAMY M", pan_number: "ABCDE1234F" },
          created_at: new Date(Date.now() - 3600000 * 20).toISOString(),
        },
        {
          id: "doc-3",
          document_type: "passport",
          file_name: "indian_passport_travel.pdf",
          file_size_bytes: 2150000,
          extracted_fields: { full_name: "KAMESH G", date_of_birth: "2003-05-14", passport_number: "Z9876543", nationality: "INDIAN" },
          created_at: new Date(Date.now() - 3600000 * 12).toISOString(),
        },
      ]);
      setConflicts([
        {
          id: "conf-1",
          field_name: "full_name",
          doc_a_id: "doc-1 (Aadhaar)",
          doc_b_id: "doc-2 (PAN)",
          doc_a_value: "KAMESH G",
          doc_b_value: "KAMESH GURUSAMY",
          severity: "high",
          comparison_method: "Jaro-Winkler Token Split",
          similarity_score: 0.84,
          review_status: "flagged_unresolvable",
          created_at: new Date().toISOString(),
        },
        {
          id: "conf-2",
          field_name: "father_name",
          doc_a_id: "doc-1 (Aadhaar)",
          doc_b_id: "doc-2 (PAN)",
          doc_a_value: "GURUSAMY M",
          doc_b_value: "GURUSAMY",
          severity: "medium",
          comparison_method: "Levenshtein Distance",
          similarity_score: 0.88,
          review_status: "needs_gazette_affidavit",
          created_at: new Date().toISOString(),
        },
      ]);
      setChatMessages([
        {
          role: "assistant",
          content: "Hello! I am CONVELINA AI. I have detected 2 clerical discrepancies between your Aadhaar Card ('KAMESH G') and PAN Card ('KAMESH GURUSAMY'). How may I assist you with the resolution workflow?",
        },
        {
          role: "user",
          content: "Which document has higher legal precedence for passport verification, and how do I fix the surname expansion?",
        },
        {
          role: "assistant",
          content: "For Passport Seva in India:\n\n1. Legal Precedence: Under MEA Passport Rules, your Matriculation/Class 10 Certificate and Birth Certificate take primary legal precedence for Name and Date of Birth over Aadhaar and PAN.\n\n2. Resolution Workflow:\n   • If 'GURUSAMY' is your father's name used as a patronymic initial ('G'), submit Form 49A (Correction in PAN) to expand or align initials.\n   • Alternatively, submit MEA Annexure-E (Deed Poll / Sworn Affidavit for Change/Expansion in Name) alongside self-attested copies of both documents.\n   • CONVELINA can generate an automated Ed25519-signed Notarized Affidavit draft for this submission.",
        },
      ]);
    }
  }, []);

  // AI Assistant State
  const [chatMessages, setChatMessages] = useState<AssistantMsg[]>([
    {
      role: "assistant",
      content:
        "Hello. I am the CONVELINA Document Assistance AI. I can guide you through resolving clerical inconsistencies across your Indian identity documents (Aadhaar, PAN, Passport, Educational certificates, and EPF records) using verified government procedures.",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [sendingChat, setSendingChat] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Forms Catalog State
  const [formsCatalog, setFormsCatalog] = useState<FormItem[]>([
    {
      id: "form-pan-49a",
      form_code: "FORM-49A",
      title: "PAN Correction / Change Request Form",
      issuing_authority: "Income Tax Department / NSDL",
      category: "pan",
      description: "Application for allotment of new PAN or changes/correction in existing PAN data.",
      purpose: "Used to correct misspelled name, date of birth, or father's name in Income Tax records.",
      requirements: ["Proof of Identity (Aadhaar/Passport)", "Proof of DOB (Class 10 Certificate)", "Existing PAN Copy"],
      download_url: "https://www.onlineservices.nsdl.com",
      official_source_url: "https://incometaxindia.gov.in",
    },
    {
      id: "form-epfo-jd",
      form_code: "EPFO-JD-2024",
      title: "EPFO Joint Declaration Form",
      issuing_authority: "Employees' Provident Fund Organisation (EPFO)",
      category: "epfo",
      description: "Joint declaration by employee and employer for modification in member profile parameters.",
      purpose: "Mandatory joint submission to rectify name, joining date, exit date, or father's name in UAN records.",
      requirements: ["Aadhaar linked to mobile", "Letter from authorized employer signatory", "Supporting Gazette if name changed"],
      download_url: "https://www.epfindia.gov.in",
      official_source_url: "https://www.epfindia.gov.in",
    },
    {
      id: "form-passport-annexure-e",
      form_code: "ANNEXURE-E",
      title: "Passport Self-Declaration of Name Change",
      issuing_authority: "Ministry of External Affairs (MEA)",
      category: "passport",
      description: "Deed poll/sworn affidavit for change in name/surname in Indian Passport.",
      purpose: "Required when altering surname or major name expansion in Passport Seva.",
      requirements: ["Two newspaper publication cuttings", "Gazette notification copy", "Current Passport"],
      download_url: "https://www.passportindia.gov.in",
      official_source_url: "https://www.passportindia.gov.in",
    },
    {
      id: "form-aadhaar-update",
      form_code: "UIDAI-UPDATE-01",
      title: "Aadhaar Enrolment / Update Form",
      issuing_authority: "Unique Identification Authority of India (UIDAI)",
      category: "aadhaar",
      description: "Standard application for demographic (Name, DOB, Gender, Address) update at Aadhaar Seva Kendra.",
      purpose: "Update resident demographics. Note: Name update lifetime limit is 2 times.",
      requirements: ["Standard Certificate from Gazetted Officer (if no document)", "PAN or Passport as POI", "Birth Certificate for DOB"],
      download_url: "https://uidai.gov.in",
      official_source_url: "https://uidai.gov.in",
    },
    {
      id: "form-cbse-cert",
      form_code: "CBSE-NAME-CORR",
      title: "CBSE Secondary Education Marksheet Correction",
      issuing_authority: "Central Board of Secondary Education (CBSE)",
      category: "education",
      description: "Application for clerical correction in student name or parents' names in Class 10/12 certificate.",
      purpose: "Rectify spelling error made in school records before board issuance.",
      requirements: ["School admission register extract attested by Principal", "Newspaper notification cutting", "Original Marksheet surrender"],
      download_url: "https://www.cbse.gov.in",
      official_source_url: "https://www.cbse.gov.in",
    },
  ]);
  const [selectedFormCategory, setSelectedFormCategory] = useState("all");
  const [formSearchQuery, setFormSearchQuery] = useState("");
  const [selectedFormDetail, setSelectedFormDetail] = useState<FormItem | null>(null);

  // Profile Form State
  const [profileForm, setProfileForm] = useState({
    full_name: "",
    phone_number: "",
    date_of_birth: "",
    address: "",
    father_name: "",
    mother_name: "",
  });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);

  // Account Deletion State
  const [deleteAccountModalOpen, setDeleteAccountModalOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deletingAccount, setDeletingAccount] = useState(false);

  // User Activity
  const [userActivity, setUserActivity] = useState<ActivityItem[]>([]);

  // Route Protection & Profile Guard
  useEffect(() => {
    if (isDemoMode) return;
    if (!loading) {
      if (!firebaseUser) {
        router.replace("/login");
      } else if (!isProfileComplete) {
        router.replace("/setup-profile");
      }
    }
  }, [loading, firebaseUser, isProfileComplete, router, isDemoMode]);

  // Sync profileForm with authenticated profile
  useEffect(() => {
    if (currentUser) {
      setProfileForm({
        full_name: currentUser.full_name || "",
        phone_number: currentUser.phone_number || "",
        date_of_birth: currentUser.date_of_birth || "",
        address: currentUser.address || "",
        father_name: currentUser.father_name || "",
        mother_name: currentUser.mother_name || "",
      });
    }
  }, [currentUser]);

  // Auth Headers helper
  const getAuthHeaders = useCallback(() => {
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${idToken || ""}`,
    };
  }, [idToken]);

  // Fetch Documents
  const fetchDocuments = useCallback(async () => {
    if (!idToken) return;
    setLoadingDocs(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/documents`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (e) {
      console.error("Failed to fetch documents", e);
    } finally {
      setLoadingDocs(false);
    }
  }, [apiUrl, idToken, getAuthHeaders]);

  // Fetch Conflicts
  const fetchConflicts = useCallback(async () => {
    if (!idToken) return;
    try {
      const res = await fetch(`${apiUrl}/api/v1/conflicts`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setConflicts(data.conflicts || []);
        if (data.conflicts && data.conflicts.length > 0) {
          setHasCompared(true);
        }
      }
    } catch (e) {
      console.error("Failed to fetch conflicts", e);
    }
  }, [apiUrl, idToken, getAuthHeaders]);

  // Fetch User Activity
  const fetchActivity = useCallback(async () => {
    if (!idToken) return;
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/activity`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setUserActivity(data.activities || []);
      }
    } catch (e) {
      console.error("Failed to fetch activity", e);
    }
  }, [apiUrl, idToken, getAuthHeaders]);

  useEffect(() => {
    if (idToken && profile) {
      fetchDocuments();
      fetchConflicts();
      fetchActivity();
    }
  }, [idToken, profile, fetchDocuments, fetchConflicts, fetchActivity]);

  // Handle Document Upload
  const handleDocumentUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError("Please choose a file to upload.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    try {
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("document_type", uploadDocType);

      const res = await fetch(`${apiUrl}/api/v1/documents/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${idToken || ""}`,
        },
        body: formData,
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Document upload failed.");
      }

      setUploadSuccess(`Successfully processed ${uploadFile.name}. OCR demographic fields extracted.`);
      setUploadFile(null);
      fetchDocuments();
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Upload processing failed.");
    } finally {
      setUploading(false);
    }
  };

  // Handle Conflict Detection
  const handleRunComparison = async () => {
    setDetectingConflicts(true);
    setConflictSuccessMsg(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/conflicts/detect`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      const data = await res.json();
      if (res.ok) {
        setConflicts(data.conflicts || []);
        setHasCompared(true);
        setConflictSuccessMsg(`Comparison complete. ${data.conflicts?.length || 0} discrepancy records reviewed.`);
      }
    } catch (e) {
      console.error("Conflict comparison failed", e);
    } finally {
      setDetectingConflicts(false);
    }
  };

  // Handle Delete Document
  const handleDeleteDocument = async (docId: string) => {
    if (!confirm("Are you sure you want to remove this document record?")) return;
    try {
      const res = await fetch(`${apiUrl}/api/v1/documents/${docId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        fetchDocuments();
      }
    } catch (e) {
      console.error("Failed to delete document", e);
    }
  };

  // Handle AI Chat
  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = chatInput.trim();
    if (!query) return;

    const userMsg: AssistantMsg = { role: "user", content: query };
    setChatMessages((prev) => [...prev, userMsg]);
    setChatInput("");
    setSendingChat(true);

    try {
      const res = await fetch(`${apiUrl}/api/v1/knowledge/ask`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ query }),
      });

      if (res.ok) {
        const data = await res.json();
        const aiMsg: AssistantMsg = {
          role: "assistant",
          content: data.answer,
          sources: data.sources || [],
          forms: data.forms || [],
        };
        setChatMessages((prev) => [...prev, aiMsg]);
      } else {
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Assistant service is not currently available. Please try again later.",
          },
        ]);
      }
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "Assistant service is not currently available. Please try again later.",
        },
      ]);
    } finally {
      setSendingChat(false);
    }
  };

  // Handle Profile Update
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileSaving(true);
    setProfileMessage(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/profile`, {
        method: "PATCH",
        headers: getAuthHeaders(),
        body: JSON.stringify(profileForm),
      });
      if (res.ok) {
        setProfileMessage("Profile successfully updated and audit event recorded.");
      } else {
        setProfileMessage("Failed to update profile.");
      }
    } catch {
      setProfileMessage("Network error updating profile.");
    } finally {
      setProfileSaving(false);
    }
  };

  // Handle Account Deletion
  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE") return;
    setDeletingAccount(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/account`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        await logout();
        router.replace("/");
      }
    } catch (e) {
      console.error("Account deletion failed", e);
    } finally {
      setDeletingAccount(false);
      setDeleteAccountModalOpen(false);
    }
  };

  // Real Logout Handler
  const handleLogoutAction = async () => {
    await logout();
    router.replace("/");
  };

  // Filtered Forms
  const filteredForms = formsCatalog.filter((f) => {
    const matchesCategory = selectedFormCategory === "all" || f.category === selectedFormCategory;
    const matchesSearch =
      !formSearchQuery ||
      f.title.toLowerCase().includes(formSearchQuery.toLowerCase()) ||
      f.form_code.toLowerCase().includes(formSearchQuery.toLowerCase()) ||
      f.description.toLowerCase().includes(formSearchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  // Loading Screen
  if ((loading || !firebaseUser || !profile) && !isDemoMode) {
    return (
      <div className="min-h-screen bg-[#faf9f6] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-pulse">
            <Logo size={40} showText={false} />
          </div>
          <span className="text-xs font-medium text-zinc-500">Loading CONVELINA workspace...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#faf9f6] text-[#18181b] flex flex-col font-sans selection:bg-[#18181b] selection:text-white">
      {/* ========================================================================
          TOP NAVIGATION BAR
      ======================================================================== */}
      <header className="sticky top-0 z-30 h-16 bg-[#faf9f6]/90 backdrop-blur-md border-b border-[#e5e2dc] px-4 sm:px-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            type="button"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="hidden md:flex p-1.5 rounded-lg text-zinc-600 hover:text-black hover:bg-zinc-100 transition"
            aria-label="Toggle Sidebar"
          >
            {sidebarCollapsed ? <PanelLeft className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
          </button>

          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="flex md:hidden p-1.5 rounded-lg text-zinc-600 hover:text-black hover:bg-zinc-100 transition"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="flex items-center gap-2">
            <Logo size={24} textClassName="font-bold text-sm text-[#18181b] hidden sm:inline" />
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-zinc-200/70 text-zinc-700 font-mono">
              Workspace
            </span>
          </div>
        </div>

        {/* User Identity & Logout */}
        <div className="flex items-center gap-3">
          {currentUser?.role === "admin" && (
            <Link
              href="/admin"
              className="text-[11px] px-2.5 py-1 rounded-md bg-purple-50 text-purple-700 border border-purple-200 font-medium hover:bg-purple-100 transition"
            >
              Switch to Admin Console
            </Link>
          )}

          <div className="relative">
            <button
              type="button"
              onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
              className="flex items-center gap-2 p-1.5 rounded-xl border border-[#e5e2dc] bg-white hover:bg-zinc-50 transition"
            >
              <div className="w-6 h-6 rounded-lg bg-zinc-800 text-white flex items-center justify-center text-[11px] font-semibold">
                {currentUser?.full_name ? currentUser.full_name.charAt(0).toUpperCase() : "C"}
              </div>
              <div className="text-left hidden md:block pr-1">
                <div className="text-xs font-semibold text-zinc-900 leading-tight">{currentUser?.full_name}</div>
                <div className="text-[10px] text-zinc-500 leading-tight truncate max-w-[140px]">{currentUser?.email}</div>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-zinc-400" />
            </button>

            {/* Profile Dropdown */}
            {profileDropdownOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-xl bg-white border border-[#e5e2dc] shadow-elevated p-2 space-y-1 z-50 animate-in fade-in">
                <div className="px-3 py-2 border-b border-zinc-100">
                  <div className="text-xs font-semibold text-zinc-900">{currentUser?.full_name}</div>
                  <div className="text-[10px] text-zinc-500 truncate">{currentUser?.email}</div>
                  <div className="mt-1 text-[10px] font-mono text-zinc-400">Role: Citizen</div>
                </div>

                <button
                  type="button"
                  onClick={() => {
                    setActiveTab("profile");
                    setProfileDropdownOpen(false);
                  }}
                  className="w-full px-3 py-1.5 text-left text-xs text-zinc-700 hover:bg-zinc-50 rounded-lg flex items-center gap-2"
                >
                  <User className="w-3.5 h-3.5" />
                  <span>Profile Settings</span>
                </button>

                <div className="border-t border-zinc-100 my-1" />

                <button
                  type="button"
                  onClick={handleLogoutAction}
                  className="w-full px-3 py-1.5 text-left text-xs text-rose-600 hover:bg-rose-50 rounded-lg flex items-center gap-2"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign out</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ========================================================================
          MAIN APP BODY: SIDEBAR + CONTENT
      ======================================================================== */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <aside
          className={`bg-white border-r border-[#e5e2dc] transition-all duration-200 flex flex-col justify-between ${
            sidebarCollapsed ? "w-16" : "w-60"
          } hidden md:flex`}
        >
          <div className="p-3 space-y-1.5">
            <button
              onClick={() => setActiveTab("home")}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                activeTab === "home"
                  ? "bg-[#18181b] text-white"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-black"
              }`}
            >
              <Shield className="w-4 h-4 shrink-0" />
              {!sidebarCollapsed && <span>Overview</span>}
            </button>

            <button
              onClick={() => setActiveTab("conflicts")}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                activeTab === "conflicts"
                  ? "bg-[#18181b] text-white"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-black"
              }`}
            >
              <AlertTriangle className="w-4 h-4 shrink-0 text-amber-500" />
              {!sidebarCollapsed && <span>Inconsistencies</span>}
            </button>

            <button
              onClick={() => setActiveTab("assistant")}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                activeTab === "assistant"
                  ? "bg-[#18181b] text-white"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-black"
              }`}
            >
              <Sparkles className="w-4 h-4 shrink-0 text-blue-500" />
              {!sidebarCollapsed && <span>AI Assistant</span>}
            </button>

            <button
              onClick={() => setActiveTab("forms")}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                activeTab === "forms"
                  ? "bg-[#18181b] text-white"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-black"
              }`}
            >
              <FileText className="w-4 h-4 shrink-0 text-emerald-500" />
              {!sidebarCollapsed && <span>Forms Repository</span>}
            </button>

            <button
              onClick={() => setActiveTab("profile")}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition ${
                activeTab === "profile"
                  ? "bg-[#18181b] text-white"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-black"
              }`}
            >
              <User className="w-4 h-4 shrink-0 text-zinc-500" />
              {!sidebarCollapsed && <span>Citizen Profile</span>}
            </button>
          </div>

          {/* Sidebar Footer */}
          <div className="p-3 border-t border-[#e5e2dc] text-[11px] text-zinc-500 space-y-2">
            {!sidebarCollapsed && (
              <div className="px-2 py-1 bg-[#faf9f6] rounded border border-zinc-200">
                <span className="block font-semibold text-zinc-800">Forced RLS Enabled</span>
                <span className="text-[10px] text-zinc-500">Session isolated to {currentUser?.full_name || "Citizen"}</span>
              </div>
            )}
            <button
              onClick={handleLogoutAction}
              className="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-rose-600 hover:bg-rose-50 text-xs font-medium transition"
            >
              <LogOut className="w-3.5 h-3.5" />
              {!sidebarCollapsed && <span>Sign out</span>}
            </button>
          </div>
        </aside>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden fixed inset-0 z-40 bg-black/30 backdrop-blur-xs flex">
            <div className="w-64 bg-white h-full p-4 space-y-2 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between pb-3 border-b border-zinc-100">
                  <span className="font-semibold text-sm">Navigation</span>
                  <button onClick={() => setMobileMenuOpen(false)}>
                    <X className="w-4 h-4 text-zinc-500" />
                  </button>
                </div>
                <button
                  onClick={() => { setActiveTab("home"); setMobileMenuOpen(false); }}
                  className="w-full text-left py-2 px-3 rounded-lg text-xs font-medium hover:bg-zinc-100"
                >
                  Overview
                </button>
                <button
                  onClick={() => { setActiveTab("conflicts"); setMobileMenuOpen(false); }}
                  className="w-full text-left py-2 px-3 rounded-lg text-xs font-medium hover:bg-zinc-100"
                >
                  Inconsistencies
                </button>
                <button
                  onClick={() => { setActiveTab("assistant"); setMobileMenuOpen(false); }}
                  className="w-full text-left py-2 px-3 rounded-lg text-xs font-medium hover:bg-zinc-100"
                >
                  AI Assistant
                </button>
                <button
                  onClick={() => { setActiveTab("forms"); setMobileMenuOpen(false); }}
                  className="w-full text-left py-2 px-3 rounded-lg text-xs font-medium hover:bg-zinc-100"
                >
                  Forms Repository
                </button>
                <button
                  onClick={() => { setActiveTab("profile"); setMobileMenuOpen(false); }}
                  className="w-full text-left py-2 px-3 rounded-lg text-xs font-medium hover:bg-zinc-100"
                >
                  Citizen Profile
                </button>
              </div>

              <button
                onClick={handleLogoutAction}
                className="w-full py-2 bg-rose-50 text-rose-600 rounded-lg text-xs font-medium"
              >
                Sign out
              </button>
            </div>
          </div>
        )}

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 space-y-6">
          {/* TAB 1: OVERVIEW */}
          {activeTab === "home" && (
            <div className="max-w-5xl mx-auto space-y-6">
              <div className="space-y-1">
                <h1 className="text-xl sm:text-2xl font-serif text-[#18181b]">
                  Welcome, {currentUser?.full_name || "Citizen"}
                </h1>
                <p className="text-xs text-zinc-600">
                  Your identity documents and clerical inconsistency workspace.
                </p>
              </div>

              {/* Status Metric Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-2">
                  <div className="flex items-center justify-between text-xs text-zinc-500">
                    <span>Uploaded Documents</span>
                    <FileText className="w-4 h-4 text-zinc-700" />
                  </div>
                  <div className="text-2xl font-semibold text-zinc-900">{documents.length}</div>
                  <div className="text-[11px] text-zinc-500">
                    Aadhaar, PAN, Passport, Certificates
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-2">
                  <div className="flex items-center justify-between text-xs text-zinc-500">
                    <span>Detected Discrepancies</span>
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                  </div>
                  <div className="text-2xl font-semibold text-zinc-900">{conflicts.length}</div>
                  <div className="text-[11px] text-zinc-500">
                    {hasCompared ? "Cross-matching completed" : "Run comparison below"}
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-2">
                  <div className="flex items-center justify-between text-xs text-zinc-500">
                    <span>Official Forms</span>
                    <Sparkles className="w-4 h-4 text-blue-600" />
                  </div>
                  <div className="text-2xl font-semibold text-zinc-900">5 Available</div>
                  <div className="text-[11px] text-zinc-500">UIDAI, NSDL, MEA, EPFO, CBSE</div>
                </div>
              </div>

              {/* Quick Actions Row */}
              <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
                <h3 className="text-sm font-semibold text-zinc-900">Quick Actions</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  <button
                    onClick={() => setActiveTab("conflicts")}
                    className="p-3.5 rounded-xl border border-[#e5e2dc] bg-[#faf9f6] text-left hover:border-zinc-400 transition space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-900">Upload & Compare</span>
                      <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />
                    </div>
                    <p className="text-[11px] text-zinc-500">Add documents and run discrepancy analysis.</p>
                  </button>

                  <button
                    onClick={() => setActiveTab("assistant")}
                    className="p-3.5 rounded-xl border border-[#e5e2dc] bg-[#faf9f6] text-left hover:border-zinc-400 transition space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-900">Ask AI Assistant</span>
                      <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />
                    </div>
                    <p className="text-[11px] text-zinc-500">Get official guidance on correction steps.</p>
                  </button>

                  <button
                    onClick={() => setActiveTab("forms")}
                    className="p-3.5 rounded-xl border border-[#e5e2dc] bg-[#faf9f6] text-left hover:border-zinc-400 transition space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-zinc-900">Browse Official Forms</span>
                      <ArrowRight className="w-3.5 h-3.5 text-zinc-400" />
                    </div>
                    <p className="text-[11px] text-zinc-500">Download NSDL, EPFO, and UIDAI forms.</p>
                  </button>
                </div>
              </div>

              {/* Uploaded Documents Quick Table */}
              <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-zinc-900">Your Identity Records</h3>
                  <button
                    onClick={() => setActiveTab("conflicts")}
                    className="text-xs font-medium text-blue-600 hover:underline"
                  >
                    Upload New
                  </button>
                </div>

                {documents.length === 0 ? (
                  <div className="py-8 text-center text-xs text-zinc-500 space-y-2">
                    <p>No documents uploaded yet.</p>
                    <button
                      onClick={() => setActiveTab("conflicts")}
                      className="px-3 py-1.5 rounded-lg bg-[#18181b] text-white text-xs font-medium"
                    >
                      Upload your first document
                    </button>
                  </div>
                ) : (
                  <div className="divide-y divide-zinc-100">
                    {documents.map((doc) => (
                      <div key={doc.id} className="py-3 flex items-center justify-between text-xs">
                        <div className="flex items-center gap-3">
                          <FileText className="w-4 h-4 text-zinc-600 shrink-0" />
                          <div>
                            <div className="font-semibold text-zinc-900 capitalize">{doc.document_type}</div>
                            <div className="text-[11px] text-zinc-500">{doc.file_name}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-[11px] font-mono text-zinc-400">
                            {new Date(doc.created_at).toLocaleDateString()}
                          </span>
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            className="p-1 text-zinc-400 hover:text-rose-600 transition"
                            title="Delete Document"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: CONFLICT DETECTION & UPLOAD */}
          {activeTab === "conflicts" && (
            <div className="max-w-5xl mx-auto space-y-6">
              <div className="space-y-1">
                <h1 className="text-xl sm:text-2xl font-serif text-[#18181b]">
                  Document Inconsistency Detection
                </h1>
                <p className="text-xs text-zinc-600">
                  Upload identity records to extract fields via OCR and cross-evaluate clerical differences.
                </p>
              </div>

              {/* Upload Box */}
              <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
                <h3 className="text-sm font-semibold text-zinc-900">Upload New Identity Document</h3>

                {uploadSuccess && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 text-xs text-emerald-800 rounded-lg flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
                    <span>{uploadSuccess}</span>
                  </div>
                )}

                {uploadError && (
                  <div className="p-3 bg-rose-50 border border-rose-200 text-xs text-rose-800 rounded-lg flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-rose-600" />
                    <span>{uploadError}</span>
                  </div>
                )}

                <form onSubmit={handleDocumentUpload} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Document Category</label>
                      <select
                        value={uploadDocType}
                        onChange={(e) => setUploadDocType(e.target.value)}
                        className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg bg-[#faf9f6]"
                      >
                        <option value="aadhaar">Aadhaar Card (UIDAI)</option>
                        <option value="pan">PAN Card (Income Tax)</option>
                        <option value="passport">Passport (MEA)</option>
                        <option value="education">Education Certificate (CBSE / Board)</option>
                        <option value="epf">EPFO Member Record</option>
                      </select>
                    </div>

                    <div className="sm:col-span-2">
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Select File (PDF, JPG, PNG)</label>
                      <input
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png"
                        onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                        className="w-full text-xs text-zinc-600 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-[#18181b] file:text-white hover:file:bg-zinc-800"
                      />
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2">
                    <span className="text-[11px] text-zinc-500">
                      Raw file deleted post-OCR extraction per Aadhaar Act provisions.
                    </span>
                    <button
                      type="submit"
                      disabled={uploading || !uploadFile}
                      className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-xl hover:bg-zinc-800 disabled:opacity-50 transition"
                    >
                      {uploading ? "Extracting with OCR..." : "Upload & Parse"}
                    </button>
                  </div>
                </form>
              </div>

              {/* Comparison Action */}
              <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="text-sm font-semibold text-zinc-900">Run Cross-Document Comparison</h3>
                  <p className="text-xs text-zinc-600">
                    Compares name tokens, date variations, and phonetic soundex across all uploaded documents.
                  </p>
                </div>
                <button
                  onClick={handleRunComparison}
                  disabled={detectingConflicts || documents.length < 2}
                  className="px-5 py-2.5 bg-[#18181b] text-white text-xs font-medium rounded-xl hover:bg-zinc-800 disabled:opacity-50 transition shrink-0"
                >
                  {detectingConflicts ? "Comparing records..." : "Compare All Records"}
                </button>
              </div>

              {conflictSuccessMsg && (
                <div className="p-3 bg-zinc-100 border border-zinc-300 text-xs text-zinc-800 rounded-lg">
                  {conflictSuccessMsg}
                </div>
              )}

              {/* Discrepancies List */}
              <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
                <h3 className="text-sm font-semibold text-zinc-900">Discrepancy Analysis Results</h3>

                {conflicts.length === 0 ? (
                  <div className="py-8 text-center text-xs text-zinc-500">
                    {hasCompared
                      ? "No conflicting attributes detected across your uploaded records."
                      : "Upload at least 2 documents and click 'Compare All Records' to run analysis."}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {conflicts.map((conf) => (
                      <div
                        key={conf.id}
                        className="p-4 rounded-xl border border-amber-200 bg-amber-50/40 space-y-2"
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-amber-900 capitalize">
                            Field Discrepancy: {conf.field_name.replace("_", " ")}
                          </span>
                          <span className="text-[10px] px-2 py-0.5 rounded font-mono uppercase bg-amber-100 text-amber-800">
                            Severity: {conf.severity}
                          </span>
                        </div>
                        <div className="grid grid-cols-2 gap-3 text-xs">
                          <div className="p-2 bg-white rounded border border-[#e5e2dc]">
                            <span className="text-[10px] text-zinc-500 block">Record A Value</span>
                            <span className="font-semibold text-zinc-900">{conf.doc_a_value}</span>
                          </div>
                          <div className="p-2 bg-white rounded border border-[#e5e2dc]">
                            <span className="text-[10px] text-zinc-500 block">Record B Value</span>
                            <span className="font-semibold text-amber-800">{conf.doc_b_value}</span>
                          </div>
                        </div>
                        <div className="text-[11px] text-zinc-600">
                          Comparison: {conf.comparison_method || "Token Permutation"} • Match Score:{" "}
                          {conf.similarity_score ? `${Math.round(conf.similarity_score * 100)}%` : "N/A"}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 3: AI ASSISTANT */}
          {activeTab === "assistant" && (
            <div className="max-w-4xl mx-auto space-y-4">
              <div className="space-y-1">
                <h1 className="text-xl sm:text-2xl font-serif text-[#18181b]">
                  AI Correction Guidance Assistant
                </h1>
                <p className="text-xs text-zinc-600">
                  Grounded in official UIDAI, NSDL, MEA, and EPFO statutory guidelines.
                </p>
              </div>

              {/* Chat Window */}
              <div className="h-[500px] bg-white border border-[#e5e2dc] rounded-2xl shadow-card flex flex-col overflow-hidden">
                {/* Messages list */}
                <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
                  {chatMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-xl p-4 rounded-2xl text-xs leading-relaxed space-y-2 ${
                          msg.role === "user"
                            ? "bg-[#18181b] text-white"
                            : "bg-[#faf9f6] border border-[#e5e2dc] text-zinc-800"
                        }`}
                      >
                        {msg.role === "assistant" && (
                          <div className="flex items-center gap-1.5 text-blue-700 font-semibold text-[11px]">
                            <Sparkles className="w-3.5 h-3.5" />
                            <span>CONVELINA Guidance</span>
                          </div>
                        )}
                        <p className="whitespace-pre-wrap">{msg.content}</p>

                        {/* Citations if available */}
                        {msg.sources && msg.sources.length > 0 && (
                          <div className="pt-2 border-t border-zinc-200/60 text-[11px] text-zinc-500 space-y-1">
                            <span className="font-semibold text-zinc-700 block">Official Sources:</span>
                            {msg.sources.map((s: any, sIdx: number) => (
                              <div key={sIdx}>
                                • {s.title || s.source_name || "Statutory Circular"} (Relevance:{" "}
                                {s.score ? Math.round(s.score * 100) : "85"}%)
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {sendingChat && (
                    <div className="flex justify-start">
                      <div className="p-3 bg-[#faf9f6] border border-[#e5e2dc] rounded-xl text-xs text-zinc-500 animate-pulse">
                        Consulting grounded statutory knowledge base...
                      </div>
                    </div>
                  )}
                </div>

                {/* Input box */}
                <form
                  onSubmit={handleSendChat}
                  className="p-3 border-t border-[#e5e2dc] bg-[#faf9f6] flex items-center gap-2"
                >
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask about name change, DOB limits, or required gazette notifications..."
                    className="flex-1 px-3.5 py-2 text-xs border border-[#e5e2dc] rounded-xl bg-white focus:border-zinc-900"
                  />
                  <button
                    type="submit"
                    disabled={sendingChat || !chatInput.trim()}
                    className="p-2.5 bg-[#18181b] text-white rounded-xl hover:bg-zinc-800 disabled:opacity-50 transition"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* TAB 4: FORMS REPOSITORY */}
          {activeTab === "forms" && (
            <div className="max-w-5xl mx-auto space-y-6">
              <div className="space-y-1">
                <h1 className="text-xl sm:text-2xl font-serif text-[#18181b]">
                  Official Government Forms Repository
                </h1>
                <p className="text-xs text-zinc-600">
                  Direct access to authentic forms, statutory requirements, and submission portals.
                </p>
              </div>

              {/* Category Filter & Search */}
              <div className="p-4 rounded-2xl bg-white border border-[#e5e2dc] shadow-card flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
                  {["all", "pan", "epfo", "passport", "aadhaar", "education"].map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setSelectedFormCategory(cat)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition ${
                        selectedFormCategory === cat
                          ? "bg-[#18181b] text-white"
                          : "bg-zinc-100 text-zinc-600 hover:bg-zinc-200"
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                <div className="w-full sm:w-64">
                  <input
                    type="text"
                    value={formSearchQuery}
                    onChange={(e) => setFormSearchQuery(e.target.value)}
                    placeholder="Search by name or code..."
                    className="w-full px-3 py-1.5 text-xs border border-[#e5e2dc] rounded-lg bg-[#faf9f6]"
                  />
                </div>
              </div>

              {/* Forms Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredForms.map((f) => (
                  <div
                    key={f.id}
                    className="p-5 rounded-2xl bg-white border border-[#e5e2dc] shadow-card hover:border-zinc-400 transition space-y-3 flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs font-bold text-zinc-900">{f.form_code}</span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-100 text-zinc-600">
                          {f.issuing_authority}
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-zinc-900">{f.title}</h4>
                      <p className="text-xs text-zinc-600 leading-relaxed">{f.description}</p>

                      {f.requirements && (
                        <div className="pt-2 text-[11px] text-zinc-500">
                          <strong className="text-zinc-700">Required:</strong> {f.requirements.join(", ")}
                        </div>
                      )}
                    </div>

                    <div className="pt-3 border-t border-zinc-100 flex items-center justify-between text-xs">
                      <a
                        href={f.official_source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-blue-600 hover:underline inline-flex items-center gap-1 font-medium"
                      >
                        Official Portal <ExternalLink className="w-3 h-3" />
                      </a>

                      <a
                        href={f.download_url}
                        target="_blank"
                        rel="noreferrer"
                        className="px-3 py-1.5 rounded-lg bg-[#18181b] text-white text-[11px] font-medium hover:bg-zinc-800 transition"
                      >
                        Download Template
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: PROFILE & AUDIT */}
          {activeTab === "profile" && (
            <div className="max-w-4xl mx-auto space-y-6">
              <div className="space-y-1">
                <h1 className="text-xl sm:text-2xl font-serif text-[#18181b]">
                  Citizen Profile & Account Settings
                </h1>
                <p className="text-xs text-zinc-600">
                  Manage your personal identity record and review your tamper-evident audit history.
                </p>
              </div>

              {profileMessage && (
                <div className="p-3 bg-zinc-100 border border-zinc-300 text-xs text-zinc-800 rounded-lg">
                  {profileMessage}
                </div>
              )}

              {/* Profile Details Form */}
              <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
                <h3 className="text-sm font-semibold text-zinc-900">Demographic Information</h3>

                <form onSubmit={handleSaveProfile} className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Full Legal Name</label>
                      <input
                        type="text"
                        required
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                        className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg bg-[#faf9f6]"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Phone Number</label>
                      <input
                        type="tel"
                        value={profileForm.phone_number}
                        onChange={(e) => setProfileForm({ ...profileForm, phone_number: e.target.value })}
                        className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg bg-[#faf9f6]"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Date of Birth</label>
                      <input
                        type="date"
                        value={profileForm.date_of_birth}
                        onChange={(e) => setProfileForm({ ...profileForm, date_of_birth: e.target.value })}
                        className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg bg-[#faf9f6]"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Father&apos;s Name</label>
                      <input
                        type="text"
                        value={profileForm.father_name}
                        onChange={(e) => setProfileForm({ ...profileForm, father_name: e.target.value })}
                        className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg bg-[#faf9f6]"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-zinc-700 mb-1">Residential Address</label>
                    <textarea
                      rows={2}
                      value={profileForm.address}
                      onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })}
                      className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg bg-[#faf9f6]"
                    />
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={profileSaving}
                      className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-xl hover:bg-zinc-800 disabled:opacity-50 transition"
                    >
                      {profileSaving ? "Saving..." : "Update Profile"}
                    </button>
                  </div>
                </form>
              </div>

              {/* Audit History */}
              <div className="p-6 rounded-2xl bg-white border border-[#e5e2dc] shadow-card space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-zinc-900">Cryptographic Activity Log</h3>
                  <span className="text-[11px] font-mono text-zinc-400">Append-Only Immutability</span>
                </div>

                {userActivity.length === 0 ? (
                  <div className="py-6 text-center text-xs text-zinc-500">
                    No activity records logged for this session yet.
                  </div>
                ) : (
                  <div className="divide-y divide-zinc-100 text-xs">
                    {userActivity.map((act) => (
                      <div key={act.id} className="py-2.5 flex items-center justify-between">
                        <div>
                          <span className="font-semibold text-zinc-800 capitalize">
                            {act.action.replace("_", " ")}
                          </span>
                          <span className="text-zinc-500 text-[11px] ml-2">({act.entity_type})</span>
                        </div>
                        <span className="text-[10px] font-mono text-zinc-400">
                          {new Date(act.created_at).toLocaleString()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Danger Zone: Account Deletion */}
              <div className="p-6 rounded-2xl bg-white border border-rose-200 shadow-card space-y-3">
                <h3 className="text-sm font-semibold text-rose-700">Account Management</h3>
                <p className="text-xs text-zinc-600 leading-relaxed">
                  Permanently delete your profile, uploaded documents, and discrepancy reports. All stored records are scrubbed under privacy regulations.
                </p>
                <button
                  type="button"
                  onClick={() => setDeleteAccountModalOpen(true)}
                  className="px-4 py-2 border border-rose-300 text-rose-700 text-xs font-medium rounded-xl hover:bg-rose-50 transition"
                >
                  Delete Account
                </button>
              </div>
            </div>
          )}
        </main>
      </div>

      {/* Delete Account Modal Dialog */}
      {deleteAccountModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white border border-[#e5e2dc] rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4 animate-in zoom-in-95">
            <h3 className="text-base font-semibold text-rose-700">Delete Account Confirmation</h3>
            <p className="text-xs text-zinc-600 leading-relaxed">
              This action permanently deletes your profile and uploaded document records from CONVELINA. Once confirmed,
              your session will be terminated immediately.
            </p>

            <div>
              <label className="block text-xs font-medium text-zinc-700 mb-1">
                Type <span className="font-mono font-bold text-black">DELETE</span> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="DELETE"
                className="w-full px-3 py-2 text-xs border border-rose-300 rounded-lg focus:border-rose-600"
              />
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeleteAccountModalOpen(false)}
                className="px-3 py-1.5 border border-[#e5e2dc] text-xs font-medium rounded-lg hover:bg-zinc-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={deleteConfirmText !== "DELETE" || deletingAccount}
                onClick={handleDeleteAccount}
                className="px-4 py-1.5 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 disabled:opacity-40 transition"
              >
                {deletingAccount ? "Deleting..." : "Permanently Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

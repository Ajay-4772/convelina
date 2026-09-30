"use client";

import React, { useState, useEffect } from "react";
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

// ==============================================================================
// Types & Interfaces
// ==============================================================================

interface UserProfile {
  id: string;
  firebase_uid: string;
  email: string;
  full_name: string;
  role: string;
  phone_number?: string;
  date_of_birth?: string;
  address?: string;
  father_name?: string;
  mother_name?: string;
  created_at?: string;
  updated_at?: string;
}

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

interface ConversationItem {
  id: string;
  title: string;
  updated_at: string;
}

interface AdminStats {
  users: { total: number; citizens: number; officers: number; admins: number };
  documents: { total_uploaded: number };
  conflicts: { total_detected: number };
  assistant: { total_messages: number; forms_available: number };
  pki: { total_attestations: number; active_signing_keys: number };
  audit: { total_events: number };
}

// ==============================================================================
// Main Application Component
// ==============================================================================

export default function ConsolithApp() {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // App Navigation & Shell State
  const [activeTab, setActiveTab] = useState<
    "home" | "conflicts" | "assistant" | "forms" | "profile" | "admin"
  >("home");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  // Authentication & Profile State
  const [currentUser, setCurrentUser] = useState<UserProfile>({
    id: "3b6dad2b-4731-4b02-8b8a-031f80da57c9",
    firebase_uid: "ui_demo_citizen",
    email: "citizen.demo@gmail.com",
    full_name: "Ajay Raman",
    role: "citizen",
    phone_number: "+91 98765 43210",
    date_of_birth: "1994-08-15",
    address: "B-402, Green Valley Apartments, Indiranagar, Bengaluru, Karnataka 560038",
    father_name: "Ramanathan K.",
    mother_name: "Lakshmi Raman",
  });

  // Auth Dialog / Onboarding State
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "signup" | "otp" | "onboarding">("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authFullName, setAuthFullName] = useState("");
  const [otpInput, setOtpInput] = useState("");
  const [otpCountdown, setOtpCountdown] = useState(60);
  const [authError, setAuthError] = useState<string | null>(null);
  const [authSuccess, setAuthSuccess] = useState<string | null>(null);
  const [loadingAuth, setLoadingAuth] = useState(false);

  // Module 4 & 5: Documents & Conflicts State
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

  // Module 6: AI Assistant State
  const [conversations, setConversations] = useState<ConversationItem[]>([
    { id: "default-conv", title: "Document Discrepancy Guidance", updated_at: new Date().toISOString() },
  ]);
  const [activeConvId, setActiveConvId] = useState<string>("default-conv");
  const [chatMessages, setChatMessages] = useState<AssistantMsg[]>([
    {
      role: "assistant",
      content:
        "Hello. I am the Consolith Document Assistance AI. I can guide you through resolving clerical inconsistencies across your Indian identity documents (Aadhaar, PAN, Passport, Educational certificates, and EPF records) using verified government procedures.",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [sendingChat, setSendingChat] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  // Module 6: Official Forms Catalog
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
      id: "form-cbSE-cert",
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
    full_name: currentUser.full_name,
    phone_number: currentUser.phone_number || "",
    date_of_birth: currentUser.date_of_birth || "",
    address: currentUser.address || "",
    father_name: currentUser.father_name || "",
    mother_name: currentUser.mother_name || "",
  });
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMessage, setProfileMessage] = useState<string | null>(null);

  // Password Change Form
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);

  // Account Deletion
  const [deleteAccountModalOpen, setDeleteAccountModalOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deletingAccount, setDeletingAccount] = useState(false);

  // Administrator State
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [adminActivity, setAdminActivity] = useState<any[]>([]);
  const [loadingAdmin, setLoadingAdmin] = useState(false);
  const [adminUserSearch, setAdminUserSearch] = useState("");

  // Helper for Authorization Headers
  const getAuthHeaders = () => {
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer test_token_:${currentUser.firebase_uid}:${currentUser.email}:${currentUser.full_name}`,
    };
  };

  // Initial Data Fetching
  useEffect(() => {
    fetchDocuments();
    fetchConflicts();
    if (currentUser.role === "admin") {
      fetchAdminData();
    }
  }, [currentUser]);

  // Sync profile form when currentUser changes
  useEffect(() => {
    setProfileForm({
      full_name: currentUser.full_name,
      phone_number: currentUser.phone_number || "",
      date_of_birth: currentUser.date_of_birth || "",
      address: currentUser.address || "",
      father_name: currentUser.father_name || "",
      mother_name: currentUser.mother_name || "",
    });
  }, [currentUser]);

  // OTP Countdown timer
  useEffect(() => {
    let timer: any;
    if (authMode === "otp" && otpCountdown > 0) {
      timer = setInterval(() => setOtpCountdown((c) => c - 1), 1000);
    }
    return () => clearInterval(timer);
  }, [authMode, otpCountdown]);

  // ==============================================================================
  // API Calls
  // ==============================================================================

  const fetchDocuments = async () => {
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
  };

  const fetchConflicts = async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/conflicts`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setConflicts(data.conflicts || []);
      }
    } catch (e) {
      console.error("Failed to fetch conflicts", e);
    }
  };

  const fetchAdminData = async () => {
    setLoadingAdmin(true);
    try {
      const statsRes = await fetch(`${apiUrl}/api/v1/admin/overview-stats`, { headers: getAuthHeaders() });
      if (statsRes.ok) {
        const stats = await statsRes.json();
        setAdminStats(stats);
      }
      const usersRes = await fetch(`${apiUrl}/api/v1/admin/users`, { headers: getAuthHeaders() });
      if (usersRes.ok) {
        const users = await usersRes.json();
        setAdminUsers(users);
      }
      const actRes = await fetch(`${apiUrl}/api/v1/admin/system-activity`, { headers: getAuthHeaders() });
      if (actRes.ok) {
        const act = await actRes.json();
        setAdminActivity(act);
      }
    } catch (e) {
      console.error("Failed to fetch admin data", e);
    } finally {
      setLoadingAdmin(false);
    }
  };

  const handleDocumentUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setUploadError("Please choose a file to upload.");
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("document_type", uploadDocType);

    try {
      const res = await fetch(`${apiUrl}/api/v1/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer test_token_:${currentUser.firebase_uid}:${currentUser.email}:${currentUser.full_name}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to process document");
      }

      const data = await res.json();
      setUploadSuccess(`Document verified & processed successfully: ${data.file_name || uploadFile.name}`);
      setUploadFile(null);
      fetchDocuments();
    } catch (err: any) {
      setUploadError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/documents/${docId}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        setDocuments((prev) => prev.filter((d) => d.id !== docId));
      }
    } catch (e) {
      console.error("Delete failed", e);
    }
  };

  const handleRunConflictScan = async () => {
    setDetectingConflicts(true);
    setConflictSuccessMsg(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/conflicts/detect`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setConflicts(data.conflicts || []);
        setHasCompared(true);
        setConflictSuccessMsg(
          data.conflicts?.length > 0
            ? `Comparison completed: ${data.conflicts.length} inconsistency point${data.conflicts.length === 1 ? "" : "s"} identified.`
            : "Comparison completed: No differences found across uploaded documents."
        );
      }
    } catch (e) {
      console.error("Detection failed", e);
    } finally {
      setDetectingConflicts(false);
    }
  };

  const handleSendChatMessage = async (e?: React.FormEvent, directPrompt?: string) => {
    if (e) e.preventDefault();
    const query = directPrompt || chatInput;
    if (!query.trim()) return;

    const userMsg: AssistantMsg = { role: "user", content: query };
    setChatMessages((prev) => [...prev, userMsg]);
    if (!directPrompt) setChatInput("");
    setSendingChat(true);

    try {
      const res = await fetch(`${apiUrl}/api/v1/assistant/chat`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ message: query }),
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMsg: AssistantMsg = {
          role: "assistant",
          content: data.reply || data.response || "Here is the guidance based on verified government circulars.",
          sources: data.sources || [],
          forms: data.forms || [],
        };
        setChatMessages((prev) => [...prev, assistantMsg]);
      } else {
        setChatMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: "Assistant service is not currently available. Please try again later.",
          },
        ]);
      }
    } catch (e) {
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

  const handleCopyText = (text: string, index: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

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
        const updated = await res.json();
        setCurrentUser(updated);
        setProfileMessage("Your profile information has been saved successfully.");
      } else {
        const err = await res.json().catch(() => ({}));
        setProfileMessage(err.detail || "Failed to update profile.");
      }
    } catch (e: any) {
      setProfileMessage("Network error updating profile.");
    } finally {
      setProfileSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE") return;
    setDeletingAccount(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/account`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        alert("Your Consolith account has been deleted. You can re-register anytime with your Gmail.");
        window.location.reload();
      }
    } catch (e) {
      console.error("Account delete error", e);
    } finally {
      setDeletingAccount(false);
    }
  };

  const handleSendOTP = async () => {
    if (!authEmail.toLowerCase().endsWith("@gmail.com")) {
      setAuthError("Registration is strictly restricted to official Gmail accounts (@gmail.com).");
      return;
    }
    setLoadingAuth(true);
    setAuthError(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/otp/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail }),
      });
      const data = await res.json();
      if (res.ok) {
        setAuthMode("otp");
        setOtpCountdown(60);
        setAuthSuccess(`A 6-digit OTP code has been sent to ${authEmail}.`);
      } else {
        setAuthError(data.detail || "Failed to send OTP.");
      }
    } catch (e) {
      setAuthError("Network error sending OTP.");
    } finally {
      setLoadingAuth(false);
    }
  };

  const handleVerifyOTP = async () => {
    if (otpInput.length !== 6) {
      setAuthError("Please enter a valid 6-digit verification code.");
      return;
    }
    setLoadingAuth(true);
    setAuthError(null);
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/otp/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail, otp_code: otpInput }),
      });
      const data = await res.json();
      if (data.verified) {
        setAuthMode("onboarding");
      } else {
        setAuthError(data.message || "Invalid or expired OTP code.");
      }
    } catch (e) {
      setAuthError("Verification failed. Please try again.");
    } finally {
      setLoadingAuth(false);
    }
  };

  const handleCompleteOnboarding = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoadingAuth(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/provision`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer test_token_:user_${Date.now()}:${authEmail}:${authFullName}`,
        },
        body: JSON.stringify({
          full_name: authFullName,
          email: authEmail,
        }),
      });
      if (res.ok) {
        const newUser = await res.json();
        setCurrentUser(newUser);
        setAuthModalOpen(false);
        setActiveTab("home");
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingAuth(false);
    }
  };

  const handleLogout = () => {
    setCurrentUser({
      id: "",
      firebase_uid: "",
      email: "",
      full_name: "Guest Citizen",
      role: "citizen",
    });
    setProfileDropdownOpen(false);
    setActiveTab("home");
  };

  // Filtered Forms
  const filteredForms = formsCatalog.filter((f) => {
    const matchesCategory = selectedFormCategory === "all" || f.category === selectedFormCategory;
    const matchesSearch =
      !formSearchQuery ||
      f.title.toLowerCase().includes(formSearchQuery.toLowerCase()) ||
      f.form_code.toLowerCase().includes(formSearchQuery.toLowerCase()) ||
      f.issuing_authority.toLowerCase().includes(formSearchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-[#faf9f6] text-[#18181b] flex flex-col md:flex-row antialiased selection:bg-zinc-200">
      {/* ========================================================================
          SIDEBAR NAVIGATION (ChatGPT-Inspired Minimalist Collapsible Rail)
      ======================================================================== */}
      <aside
        className={`${
          sidebarCollapsed ? "w-16" : "w-64"
        } bg-white border-r border-[#e5e2dc] flex flex-col justify-between shrink-0 transition-all duration-200 ease-in-out z-20`}
      >
        <div>
          {/* Brand Header with Collapse Toggle */}
          <div className="h-16 px-4 border-b border-[#e5e2dc] flex items-center justify-between">
            <div className="flex items-center gap-3 overflow-hidden">
              <div className="w-8 h-8 rounded-lg bg-[#18181b] text-white flex items-center justify-center shrink-0">
                <Shield className="w-4 h-4 text-white" />
              </div>
              {!sidebarCollapsed && (
                <span className="font-semibold tracking-tight text-base text-[#18181b] truncate">Consolith</span>
              )}
            </div>

            {/* Desktop Collapse Toggle Button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="hidden md:flex p-1.5 text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 rounded-md transition"
              title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {sidebarCollapsed ? <PanelLeft className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
            </button>

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-1.5 text-zinc-500 hover:text-zinc-900 rounded-md"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>

          {/* Citizen Primary Navigation Links */}
          <nav className={`p-3 space-y-1 ${mobileMenuOpen ? "block" : "hidden md:block"}`}>
            {/* 1. Home */}
            <button
              onClick={() => {
                setActiveTab("home");
                setMobileMenuOpen(false);
              }}
              title="Home"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "home"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-zinc-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <FileCheck2 className="w-4 h-4 text-zinc-500 shrink-0" />
              {!sidebarCollapsed && <span>Home</span>}
            </button>

            {/* 2. Conflict Detection */}
            <button
              onClick={() => {
                setActiveTab("conflicts");
                setMobileMenuOpen(false);
              }}
              title="Conflict Detection"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "conflicts"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-zinc-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <AlertTriangle className="w-4 h-4 text-zinc-500 shrink-0" />
              {!sidebarCollapsed && <span>Conflict Detection</span>}
            </button>

            {/* 3. AI Assistant */}
            <button
              onClick={() => {
                setActiveTab("assistant");
                setMobileMenuOpen(false);
              }}
              title="AI Assistant"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "assistant"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-zinc-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <Sparkles className="w-4 h-4 text-zinc-500 shrink-0" />
              {!sidebarCollapsed && <span>AI Assistant</span>}
            </button>

            {/* 4. Forms Repository */}
            <button
              onClick={() => {
                setActiveTab("forms");
                setMobileMenuOpen(false);
              }}
              title="Forms Repository"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "forms"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-zinc-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <FileText className="w-4 h-4 text-zinc-500 shrink-0" />
              {!sidebarCollapsed && <span>Forms Repository</span>}
            </button>

            {/* 5. Profile */}
            <button
              onClick={() => {
                setActiveTab("profile");
                setMobileMenuOpen(false);
              }}
              title="Profile"
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "profile"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-zinc-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <User className="w-4 h-4 text-zinc-500 shrink-0" />
              {!sidebarCollapsed && <span>Profile</span>}
            </button>
          </nav>
        </div>

        {/* User Profile Footer */}
        <div className="p-3 border-t border-[#e5e2dc] bg-[#faf9f6]">
          <div
            onClick={() => setActiveTab("profile")}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-white cursor-pointer transition border border-transparent hover:border-[#e5e2dc]"
            title={currentUser.full_name}
          >
            <div className="w-8 h-8 rounded-full bg-[#18181b] text-white flex items-center justify-center font-medium text-xs shrink-0">
              {currentUser.full_name
                ? currentUser.full_name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .substring(0, 2)
                : "U"}
            </div>
            {!sidebarCollapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-[#18181b] truncate">{currentUser.full_name}</p>
                <p className="text-[11px] text-zinc-500 truncate">{currentUser.email}</p>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* ========================================================================
          MAIN CONTENT AREA
      ======================================================================== */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header Bar */}
        <header className="h-16 px-6 bg-white border-b border-[#e5e2dc] flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <h2 className="text-sm font-medium text-zinc-900 capitalize">
              {activeTab === "home"
                ? "Home"
                : activeTab === "conflicts"
                ? "Conflict Detection"
                : activeTab === "assistant"
                ? "AI Assistant"
                : activeTab === "forms"
                ? "Forms Repository"
                : activeTab === "profile"
                ? "Account Settings"
                : "Administrator Console"}
            </h2>
          </div>

          {/* User Controls & Profile Dropdown */}
          <div className="flex items-center gap-3 relative">
            {currentUser.email ? (
              <div className="relative">
                <button
                  onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                  className="flex items-center gap-2 p-1.5 rounded-lg border border-[#e5e2dc] hover:bg-[#faf9f6] transition text-xs font-medium"
                >
                  <div className="w-6 h-6 rounded-full bg-[#18181b] text-white flex items-center justify-center text-[10px]">
                    {currentUser.full_name ? currentUser.full_name[0] : "U"}
                  </div>
                  <span className="hidden sm:inline text-zinc-800">{currentUser.full_name}</span>
                  <ChevronDown className="w-3.5 h-3.5 text-zinc-500" />
                </button>

                {profileDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white border border-[#e5e2dc] rounded-xl shadow-lg py-1.5 z-50 animate-in fade-in">
                    <div className="px-4 py-2 border-b border-[#e5e2dc]">
                      <p className="text-xs font-semibold text-zinc-900 truncate">{currentUser.full_name}</p>
                      <p className="text-[11px] text-zinc-500 truncate">{currentUser.email}</p>
                    </div>

                    <button
                      onClick={() => {
                        setActiveTab("profile");
                        setProfileDropdownOpen(false);
                      }}
                      className="w-full text-left px-4 py-2 text-xs text-zinc-700 hover:bg-[#faf9f6] flex items-center gap-2 transition"
                    >
                      <Settings className="w-3.5 h-3.5" />
                      Account Settings
                    </button>

                    {/* Admin Access ONLY shown if authenticated user role is admin */}
                    {currentUser.role === "admin" && (
                      <button
                        onClick={() => {
                          setActiveTab("admin");
                          setProfileDropdownOpen(false);
                        }}
                        className="w-full text-left px-4 py-2 text-xs text-zinc-700 hover:bg-[#faf9f6] flex items-center gap-2 transition border-t border-[#e5e2dc]"
                      >
                        <Shield className="w-3.5 h-3.5 text-zinc-900" />
                        Admin Console
                      </button>
                    )}

                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-xs text-rose-600 hover:bg-rose-50 flex items-center gap-2 transition border-t border-[#e5e2dc]"
                    >
                      <LogOut className="w-3.5 h-3.5" />
                      Sign Out
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => {
                  setAuthModalOpen(true);
                  setAuthMode("login");
                }}
                className="text-xs px-3.5 py-1.5 rounded-lg bg-[#18181b] text-white font-medium hover:bg-zinc-800 transition"
              >
                Sign In / Register
              </button>
            )}
          </div>
        </header>

        {/* Content Views */}
        <div className="flex-1 p-6 md:p-8 max-w-6xl w-full mx-auto">
          {/* ====================================================================
              VIEW 1: HOME (Simple, Welcoming, Editorial)
          ==================================================================== */}
          {activeTab === "home" && (
            <div className="space-y-8 animate-fadeIn">
              {/* Hero Banner */}
              <div className="bg-white border border-[#e5e2dc] rounded-2xl p-8 md:p-10 shadow-sm">
                <h1 className="text-3xl font-serif md:text-4xl font-normal tracking-tight text-[#18181b] max-w-2xl leading-tight">
                  Your documents, made easier.
                </h1>
                <p className="mt-3 text-base text-zinc-600 max-w-2xl leading-relaxed">
                  Understand document differences, find the right forms, and get clear guidance on what to do next.
                </p>

                <div className="mt-6 flex flex-wrap gap-3">
                  <button
                    onClick={() => setActiveTab("conflicts")}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[#18181b] text-white text-sm font-medium hover:bg-zinc-800 transition"
                  >
                    Check documents
                    <ArrowRight className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setActiveTab("assistant")}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-[#e5e2dc] bg-white text-[#18181b] text-sm font-medium hover:bg-[#faf9f6] transition"
                  >
                    <Sparkles className="w-4 h-4 text-zinc-500" />
                    Ask the assistant
                  </button>
                  <button
                    onClick={() => setActiveTab("forms")}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-[#e5e2dc] bg-white text-[#18181b] text-sm font-medium hover:bg-[#faf9f6] transition"
                  >
                    <FileText className="w-4 h-4 text-zinc-500" />
                    Browse forms
                  </button>
                </div>
              </div>

              {/* Three Clean Core Capability Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div
                  onClick={() => setActiveTab("conflicts")}
                  className="bg-white border border-[#e5e2dc] rounded-xl p-6 hover:border-zinc-400 transition cursor-pointer shadow-sm group"
                >
                  <div className="w-10 h-10 rounded-lg bg-[#f5f3ef] flex items-center justify-center text-[#18181b] mb-4">
                    <AlertTriangle className="w-5 h-5 text-zinc-800" />
                  </div>
                  <h3 className="text-base font-semibold text-[#18181b] group-hover:text-black">
                    Document Conflict Detection
                  </h3>
                  <p className="mt-2 text-xs text-zinc-600 leading-relaxed">
                    Compare your Aadhaar, PAN, Passport, Class 10/12, or EPF documents to spot clerical variations.
                  </p>
                </div>

                <div
                  onClick={() => setActiveTab("forms")}
                  className="bg-white border border-[#e5e2dc] rounded-xl p-6 hover:border-zinc-400 transition cursor-pointer shadow-sm group"
                >
                  <div className="w-10 h-10 rounded-lg bg-[#f5f3ef] flex items-center justify-center text-[#18181b] mb-4">
                    <FileText className="w-5 h-5 text-zinc-800" />
                  </div>
                  <h3 className="text-base font-semibold text-[#18181b] group-hover:text-black">
                    Official Forms Catalog
                  </h3>
                  <p className="mt-2 text-xs text-zinc-600 leading-relaxed">
                    Access verified application templates and guidelines for UIDAI, NSDL, MEA, EPFO, and CBSE.
                  </p>
                </div>

                <div
                  onClick={() => setActiveTab("assistant")}
                  className="bg-white border border-[#e5e2dc] rounded-xl p-6 hover:border-zinc-400 transition cursor-pointer shadow-sm group"
                >
                  <div className="w-10 h-10 rounded-lg bg-[#f5f3ef] flex items-center justify-center text-[#18181b] mb-4">
                    <Sparkles className="w-5 h-5 text-zinc-800" />
                  </div>
                  <h3 className="text-base font-semibold text-[#18181b] group-hover:text-black">
                    AI Resolution Assistant
                  </h3>
                  <p className="mt-2 text-xs text-zinc-600 leading-relaxed">
                    Get clear, source-grounded answers to your questions about official correction procedures and required documents.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* ====================================================================
              VIEW 2: CONFLICT DETECTION ("Let's check your documents")
          ==================================================================== */}
          {activeTab === "conflicts" && (
            <div className="space-y-8 animate-fadeIn">
              {/* Header */}
              <div>
                <h1 className="text-2xl font-serif font-normal text-[#18181b] tracking-tight">
                  Let's check your documents.
                </h1>
                <p className="mt-1 text-sm text-zinc-600">
                  Upload the documents you want to compare.
                </p>
              </div>

              {/* Upload Card */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl p-6 shadow-sm">
                <form onSubmit={handleDocumentUpload} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-[#18181b] uppercase tracking-wider mb-1.5">
                        Document Type
                      </label>
                      <select
                        value={uploadDocType}
                        onChange={(e) => setUploadDocType(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                      >
                        <option value="aadhaar">Aadhaar Card (UIDAI)</option>
                        <option value="pan">PAN Card (Income Tax / NSDL)</option>
                        <option value="passport">Indian Passport (MEA)</option>
                        <option value="class_10">Class 10 Certificate / Marksheet</option>
                        <option value="class_12">Class 12 Certificate / Marksheet</option>
                        <option value="epf">EPFO Record / UAN Member Passbook</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-[#18181b] uppercase tracking-wider mb-1.5">
                        Select File (PDF, PNG, JPEG - Max 10MB)
                      </label>
                      <input
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg"
                        onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                        className="w-full px-3 py-1.5 text-xs border border-[#e5e2dc] rounded-lg file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#f5f3ef] file:text-[#18181b] hover:file:bg-zinc-200 cursor-pointer"
                      />
                    </div>
                  </div>

                  {uploadError && (
                    <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
                      <XCircle className="w-4 h-4 shrink-0" />
                      {uploadError}
                    </div>
                  )}

                  {uploadSuccess && (
                    <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 shrink-0" />
                      {uploadSuccess}
                    </div>
                  )}

                  <div className="flex justify-end">
                    <button
                      type="submit"
                      disabled={uploading || !uploadFile}
                      className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 disabled:opacity-50 transition flex items-center gap-2"
                    >
                      {uploading ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          Processing Document...
                        </>
                      ) : (
                        <>
                          <UploadCloud className="w-3.5 h-3.5" />
                          Upload Document
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              {/* Uploaded Documents List */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-[#e5e2dc] flex items-center justify-between bg-[#faf9f6]">
                  <div>
                    <h2 className="text-sm font-semibold text-[#18181b]">Uploaded Documents</h2>
                    <p className="text-xs text-zinc-500">
                      {documents.length} document{documents.length === 1 ? "" : "s"} ready for comparison.
                    </p>
                  </div>
                  <button
                    onClick={handleRunConflictScan}
                    disabled={detectingConflicts || documents.length < 2}
                    className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 disabled:opacity-40 transition flex items-center gap-2"
                  >
                    {detectingConflicts ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Comparing...
                      </>
                    ) : (
                      <>
                        <FileCheck2 className="w-3.5 h-3.5" />
                        Run Pairwise Comparison
                      </>
                    )}
                  </button>
                </div>

                {documents.length === 0 ? (
                  <div className="p-8 text-center">
                    <p className="text-sm text-zinc-500">No documents uploaded yet.</p>
                    <p className="text-xs text-zinc-400 mt-1">
                      Upload at least two documents (e.g. Aadhaar and PAN) above to compare details.
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-[#e5e2dc]">
                    {documents.map((doc) => (
                      <div key={doc.id} className="p-4 px-6 flex items-center justify-between hover:bg-[#faf9f6]">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-[#f5f3ef] flex items-center justify-center font-medium text-xs text-[#18181b]">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold uppercase text-[#18181b]">
                                {doc.document_type.replace("_", " ")}
                              </span>
                              <span className="text-[11px] text-zinc-400">({doc.file_name})</span>
                            </div>
                            <p className="text-[11px] text-zinc-500">
                              Extracted fields: {Object.keys(doc.extracted_fields || {}).join(", ") || "None"}
                            </p>
                          </div>
                        </div>

                        <button
                          onClick={() => handleDeleteDocument(doc.id)}
                          className="p-1.5 text-zinc-400 hover:text-rose-600 rounded transition"
                          title="Delete document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Comparison Results Section */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl overflow-hidden shadow-sm">
                <div className="px-6 py-4 border-b border-[#e5e2dc] bg-[#faf9f6]">
                  <h2 className="text-sm font-semibold text-[#18181b]">Comparison Results</h2>
                  <p className="text-xs text-zinc-500">
                    Discrepancies represent clerical or spelling variations and do not imply fraud.
                  </p>
                </div>

                {conflictSuccessMsg && (
                  <div className="p-3 bg-amber-50 border-b border-amber-200 text-xs text-amber-800 px-6">
                    {conflictSuccessMsg}
                  </div>
                )}

                {/* Neutral Empty State Before Comparison */}
                {documents.length < 2 ? (
                  <div className="p-8 text-center">
                    <p className="text-sm text-zinc-500">Upload at least two documents to compare.</p>
                  </div>
                ) : !hasCompared ? (
                  <div className="p-8 text-center">
                    <p className="text-sm text-zinc-600">
                      Upload completed. Click "Run Pairwise Comparison" above to compare documents.
                    </p>
                  </div>
                ) : conflicts.length === 0 ? (
                  <div className="p-8 text-center">
                    <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2 opacity-80" />
                    <p className="text-sm font-medium text-[#18181b]">No differences found</p>
                    <p className="text-xs text-zinc-500 mt-1 max-w-md mx-auto">
                      All mutual fields across your compared documents match consistently.
                    </p>
                  </div>
                ) : (
                  <div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-[#e5e2dc] bg-[#fdfcfa] text-zinc-500 font-mono text-[11px] uppercase">
                            <th className="py-3 px-6">Field Name</th>
                            <th className="py-3 px-6">Document A Value</th>
                            <th className="py-3 px-6">Document B Value</th>
                            <th className="py-3 px-6">Status / Severity</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#e5e2dc]">
                          {conflicts.map((conf) => (
                            <tr key={conf.id} className="hover:bg-[#faf9f6]">
                              <td className="py-3.5 px-6 font-semibold text-[#18181b] capitalize">
                                {conf.field_name.replace("_", " ")}
                              </td>
                              <td className="py-3.5 px-6 font-mono text-zinc-700">{conf.doc_a_value || "—"}</td>
                              <td className="py-3.5 px-6 font-mono text-zinc-700">{conf.doc_b_value || "—"}</td>
                              <td className="py-3.5 px-6">
                                <span className="px-2 py-0.5 rounded text-[10px] font-medium uppercase bg-amber-100 text-amber-800">
                                  {conf.severity} Variation
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    {/* AI Assistant Callout */}
                    <div className="p-6 bg-[#faf9f6] border-t border-[#e5e2dc] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                      <div>
                        <h4 className="text-sm font-semibold text-[#18181b]">Need help with the next step?</h4>
                        <p className="text-xs text-zinc-600 mt-0.5">
                          Ask our AI Assistant to explore the relevant correction procedures and supporting forms.
                        </p>
                      </div>
                      <button
                        onClick={() => {
                          setActiveTab("assistant");
                          handleSendChatMessage(
                            undefined,
                            `I have discrepancies in my documents (${conflicts.map((c) => c.field_name).join(", ")}). What are the official correction steps?`
                          );
                        }}
                        className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition shrink-0"
                      >
                        Ask the assistant
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ====================================================================
              VIEW 3: AI ASSISTANT (ChatGPT-inspired Wide Reading Experience)
          ==================================================================== */}
          {activeTab === "assistant" && (
            <div className="bg-white border border-[#e5e2dc] rounded-2xl overflow-hidden shadow-sm flex flex-col md:flex-row h-[78vh] animate-fadeIn">
              {/* Left Conversation History Sidebar */}
              <div className="w-full md:w-60 border-r border-[#e5e2dc] bg-[#faf9f6] flex flex-col justify-between shrink-0">
                <div className="p-3 border-b border-[#e5e2dc]">
                  <button
                    onClick={() => {
                      setChatMessages([
                        {
                          role: "assistant",
                          content:
                            "New consultation session started. How can I assist with your document discrepancies or official correction forms today?",
                        },
                      ]);
                    }}
                    className="w-full py-2 px-3 bg-white border border-[#e5e2dc] hover:border-zinc-400 text-xs font-medium text-[#18181b] rounded-lg flex items-center justify-center gap-2 transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    New chat
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                  <span className="block px-2 text-[10px] font-mono uppercase text-zinc-400 mb-1.5">
                    Conversations
                  </span>
                  {conversations.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => setActiveConvId(c.id)}
                      className={`px-3 py-2 rounded-lg text-xs font-medium cursor-pointer transition flex items-center justify-between ${
                        activeConvId === c.id
                          ? "bg-white text-[#18181b] shadow-xs border border-[#e5e2dc]"
                          : "text-zinc-600 hover:bg-white"
                      }`}
                    >
                      <span className="truncate">{c.title}</span>
                      <MessageSquare className="w-3.5 h-3.5 text-zinc-400" />
                    </div>
                  ))}
                </div>

                <div className="p-3 border-t border-[#e5e2dc] bg-[#f5f3ef]">
                  <p className="text-[11px] text-zinc-600 font-medium">Grounded Sources</p>
                  <p className="text-[10px] text-zinc-400 mt-0.5">UIDAI, NSDL, MEA, EPFO, CBSE</p>
                </div>
              </div>

              {/* Main Chat Workspace */}
              <div className="flex-1 flex flex-col min-w-0 bg-white">
                {/* Messages Feed */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  {chatMessages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex gap-3 max-w-3xl ${
                        msg.role === "user" ? "ml-auto justify-end" : "mr-auto justify-start"
                      }`}
                    >
                      {msg.role === "assistant" && (
                        <div className="w-7 h-7 rounded-full bg-[#18181b] text-white flex items-center justify-center shrink-0 text-xs">
                          <Sparkles className="w-3.5 h-3.5" />
                        </div>
                      )}

                      <div
                        className={`p-4 rounded-xl text-sm leading-relaxed ${
                          msg.role === "user"
                            ? "bg-[#18181b] text-white"
                            : "bg-[#faf9f6] text-[#18181b] border border-[#e5e2dc]"
                        }`}
                      >
                        <p className="whitespace-pre-wrap">{msg.content}</p>

                        {/* Copy Action & Attached Forms */}
                        <div className="mt-3 flex items-center justify-between gap-3 pt-2 border-t border-zinc-200/50">
                          {msg.role === "assistant" && (
                            <button
                              onClick={() => handleCopyText(msg.content, idx)}
                              className="text-[11px] text-zinc-500 hover:text-zinc-800 flex items-center gap-1 transition"
                            >
                              {copiedIndex === idx ? (
                                <>
                                  <Check className="w-3 h-3 text-emerald-600" />
                                  <span>Copied</span>
                                </>
                              ) : (
                                <>
                                  <Copy className="w-3 h-3" />
                                  <span>Copy</span>
                                </>
                              )}
                            </button>
                          )}
                        </div>

                        {/* Referenced Forms */}
                        {msg.forms && msg.forms.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-[#e5e2dc] space-y-2">
                            <span className="text-xs font-semibold text-zinc-700 block">
                              Referenced Official Forms:
                            </span>
                            {msg.forms.map((f: any, i: number) => (
                              <div
                                key={i}
                                className="p-2.5 bg-white border border-[#e5e2dc] rounded-lg flex items-center justify-between"
                              >
                                <div className="min-w-0">
                                  <p className="text-xs font-semibold text-[#18181b]">{f.title || f.form_code}</p>
                                  <p className="text-[11px] text-zinc-500 truncate">{f.issuing_authority}</p>
                                </div>
                                <button
                                  onClick={() => setSelectedFormDetail(f)}
                                  className="px-2.5 py-1 bg-[#18181b] text-white text-xs rounded hover:bg-zinc-800 transition"
                                >
                                  View Form
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {msg.role === "user" && (
                        <div className="w-7 h-7 rounded-full bg-zinc-200 text-zinc-700 flex items-center justify-center shrink-0 text-xs font-medium">
                          {currentUser.full_name ? currentUser.full_name[0] : "U"}
                        </div>
                      )}
                    </div>
                  ))}

                  {sendingChat && (
                    <div className="flex gap-3 max-w-3xl">
                      <div className="w-7 h-7 rounded-full bg-[#18181b] text-white flex items-center justify-center shrink-0 text-xs">
                        <Sparkles className="w-3.5 h-3.5 animate-spin" />
                      </div>
                      <div className="p-4 rounded-xl text-sm bg-[#faf9f6] text-zinc-500 border border-[#e5e2dc] flex items-center gap-2">
                        <RefreshCw className="w-4 h-4 animate-spin text-zinc-400" />
                        Consulting verified government sources...
                      </div>
                    </div>
                  )}
                </div>

                {/* Prompt Suggestions */}
                <div className="px-6 py-2 border-t border-[#e5e2dc] bg-[#faf9f6] flex gap-2 overflow-x-auto">
                  <button
                    onClick={() => handleSendChatMessage(undefined, "How do I correct my name in PAN card?")}
                    className="text-xs px-2.5 py-1 rounded-full bg-white border border-[#e5e2dc] hover:border-zinc-400 text-zinc-700 whitespace-nowrap transition"
                  >
                    How to correct name in PAN card?
                  </button>
                  <button
                    onClick={() => handleSendChatMessage(undefined, "What is the Aadhaar update lifetime limit?")}
                    className="text-xs px-2.5 py-1 rounded-full bg-white border border-[#e5e2dc] hover:border-zinc-400 text-zinc-700 whitespace-nowrap transition"
                  >
                    What is Aadhaar update lifetime limit?
                  </button>
                  <button
                    onClick={() => handleSendChatMessage(undefined, "What is Joint Declaration for EPFO?")}
                    className="text-xs px-2.5 py-1 rounded-full bg-white border border-[#e5e2dc] hover:border-zinc-400 text-zinc-700 whitespace-nowrap transition"
                  >
                    What is Joint Declaration for EPFO?
                  </button>
                </div>

                {/* Bottom Input Composer */}
                <form onSubmit={handleSendChatMessage} className="p-4 px-6 border-t border-[#e5e2dc] bg-white flex gap-3">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask about document differences, circulars, or official procedures..."
                    className="flex-1 px-4 py-2.5 text-sm bg-[#faf9f6] border border-[#e5e2dc] rounded-xl focus:bg-white focus:border-zinc-900 transition"
                  />
                  <button
                    type="submit"
                    disabled={sendingChat || !chatInput.trim()}
                    className="px-4 py-2.5 bg-[#18181b] text-white rounded-xl hover:bg-zinc-800 disabled:opacity-40 transition flex items-center justify-center"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* ====================================================================
              VIEW 4: FORMS REPOSITORY (Document Library, Preview, Download)
          ==================================================================== */}
          {activeTab === "forms" && (
            <div className="space-y-6 animate-fadeIn">
              <div>
                <h1 className="text-2xl font-serif font-normal text-[#18181b] tracking-tight">
                  Official Forms Repository
                </h1>
                <p className="mt-1 text-sm text-zinc-600">
                  Search and access verified application templates from UIDAI, NSDL, MEA, EPFO, and CBSE.
                </p>
              </div>

              {/* Filters & Search */}
              <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white p-4 rounded-xl border border-[#e5e2dc] shadow-sm">
                {/* Category Pills */}
                <div className="flex gap-1.5 overflow-x-auto w-full md:w-auto">
                  {["all", "aadhaar", "pan", "passport", "education", "epfo"].map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setSelectedFormCategory(cat)}
                      className={`text-xs px-3 py-1.5 rounded-lg capitalize font-medium transition ${
                        selectedFormCategory === cat
                          ? "bg-[#18181b] text-white"
                          : "bg-[#f5f3ef] text-zinc-600 hover:text-[#18181b]"
                      }`}
                    >
                      {cat === "all" ? "All Forms" : cat}
                    </button>
                  ))}
                </div>

                {/* Search Bar */}
                <div className="relative w-full md:w-64">
                  <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={formSearchQuery}
                    onChange={(e) => setFormSearchQuery(e.target.value)}
                    placeholder="Search forms by name or authority..."
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#faf9f6] border border-[#e5e2dc] rounded-lg focus:bg-white focus:border-zinc-900 transition"
                  />
                </div>
              </div>

              {/* Forms Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredForms.map((form) => (
                  <div
                    key={form.id}
                    className="bg-white border border-[#e5e2dc] rounded-xl p-6 hover:border-zinc-400 transition shadow-sm flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-[#f5f3ef] text-[#18181b] border border-[#e5e2dc]">
                          {form.form_code}
                        </span>
                        <span className="text-xs uppercase font-medium text-zinc-400">{form.category}</span>
                      </div>
                      <h3 className="text-base font-semibold text-[#18181b] mt-1">{form.title}</h3>
                      <p className="text-xs text-zinc-500 mt-1">{form.issuing_authority}</p>
                      <p className="text-xs text-zinc-600 mt-3 leading-relaxed">{form.description}</p>
                    </div>

                    <div className="mt-6 pt-4 border-t border-[#e5e2dc] flex items-center justify-between">
                      <button
                        onClick={() => setSelectedFormDetail(form)}
                        className="text-xs font-medium text-zinc-700 hover:text-black flex items-center gap-1 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View Guidelines & Details
                      </button>
                      <a
                        href={form.official_source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-medium px-3 py-1.5 rounded-lg bg-[#18181b] text-white hover:bg-zinc-800 transition flex items-center gap-1.5"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        Official Source
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ====================================================================
              VIEW 5: PROFILE & SETTINGS (Crisply-style Clean Editorial Layout)
          ==================================================================== */}
          {activeTab === "profile" && (
            <div className="space-y-8 animate-fadeIn max-w-4xl">
              <div>
                <h1 className="text-2xl font-serif font-normal text-[#18181b] tracking-tight">Account Settings</h1>
                <p className="mt-1 text-sm text-zinc-600">
                  Manage your personal information, contact coordinates, security, and account status.
                </p>
              </div>

              {profileMessage && (
                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 shrink-0" />
                  {profileMessage}
                </div>
              )}

              {/* Profile Card */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl p-6 shadow-sm space-y-6">
                <div className="flex items-center gap-4 pb-6 border-b border-[#e5e2dc]">
                  <div className="w-14 h-14 rounded-full bg-[#18181b] text-white flex items-center justify-center font-serif text-xl">
                    {currentUser.full_name ? currentUser.full_name[0] : "U"}
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-[#18181b]">{currentUser.full_name}</h2>
                    <p className="text-xs text-zinc-500 font-mono mt-0.5">{currentUser.email}</p>
                  </div>
                </div>

                <form onSubmit={handleSaveProfile} className="space-y-4">
                  <h3 className="text-xs font-semibold uppercase font-mono tracking-wider text-zinc-400">
                    Personal Information
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Full Name</label>
                      <input
                        type="text"
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Date of Birth</label>
                      <input
                        type="date"
                        value={profileForm.date_of_birth}
                        onChange={(e) => setProfileForm({ ...profileForm, date_of_birth: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Father's Name</label>
                      <input
                        type="text"
                        value={profileForm.father_name}
                        onChange={(e) => setProfileForm({ ...profileForm, father_name: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Mother's Name</label>
                      <input
                        type="text"
                        value={profileForm.mother_name}
                        onChange={(e) => setProfileForm({ ...profileForm, mother_name: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Contact Phone</label>
                      <input
                        type="text"
                        value={profileForm.phone_number}
                        onChange={(e) => setProfileForm({ ...profileForm, phone_number: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-zinc-700 mb-1">Residential Address</label>
                      <input
                        type="text"
                        value={profileForm.address}
                        onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                      />
                    </div>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      disabled={profileSaving}
                      className="px-5 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition"
                    >
                      {profileSaving ? "Saving..." : "Save Changes"}
                    </button>
                  </div>
                </form>
              </div>

              {/* Account Security & Deletion Section */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl p-6 shadow-sm space-y-6">
                <h3 className="text-xs font-semibold uppercase font-mono tracking-wider text-zinc-400">
                  Account Management
                </h3>

                <div className="flex items-center justify-between pb-4 border-b border-[#e5e2dc]">
                  <div>
                    <p className="text-sm font-semibold text-zinc-900">Sign In Method</p>
                    <p className="text-xs text-zinc-500 mt-0.5">
                      Gmail Verified ({currentUser.email})
                    </p>
                  </div>
                  <button
                    onClick={() => {
                      alert("Password reset instructions have been dispatched to your verified Gmail.");
                    }}
                    className="px-3 py-1.5 border border-[#e5e2dc] rounded-lg text-xs font-medium hover:bg-zinc-50 transition"
                  >
                    Reset Password
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-rose-700">Delete Account</p>
                    <p className="text-xs text-zinc-500 mt-0.5">
                      Permanently delete your profile and personal data.
                    </p>
                  </div>
                  <button
                    onClick={() => setDeleteAccountModalOpen(true)}
                    className="px-4 py-2 border border-rose-300 text-rose-700 text-xs font-medium rounded-lg hover:bg-rose-50 transition"
                  >
                    Delete Account
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ====================================================================
              VIEW 6: ADMINISTRATOR CONSOLE (Accessible ONLY if role === 'admin')
          ==================================================================== */}
          {activeTab === "admin" && (
            <div className="space-y-8 animate-fadeIn">
              {currentUser.role !== "admin" ? (
                <div className="p-8 text-center bg-white border border-[#e5e2dc] rounded-xl">
                  <XCircle className="w-8 h-8 text-rose-600 mx-auto mb-2" />
                  <h3 className="text-base font-semibold text-zinc-900">Access Restricted</h3>
                  <p className="text-xs text-zinc-500 mt-1">
                    Only authorized administrators have permission to access this management console.
                  </p>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between">
                    <div>
                      <h1 className="text-2xl font-serif font-normal text-[#18181b] tracking-tight">
                        Administrator Management Console
                      </h1>
                      <p className="mt-1 text-sm text-zinc-600">
                        Operational telemetry, user directory, and cryptographic audit proofs.
                      </p>
                    </div>
                    <button
                      onClick={fetchAdminData}
                      disabled={loadingAdmin}
                      className="px-3 py-1.5 text-xs font-medium border border-[#e5e2dc] bg-white rounded-lg hover:bg-[#f5f3ef] flex items-center gap-1.5 transition"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${loadingAdmin ? "animate-spin" : ""}`} />
                      Refresh Telemetry
                    </button>
                  </div>

                  {/* Real Metrics Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white border border-[#e5e2dc] rounded-xl p-5 shadow-sm">
                      <span className="text-[11px] font-mono uppercase text-zinc-400 block mb-1">
                        Registered Citizens
                      </span>
                      <span className="text-2xl font-semibold text-[#18181b]">
                        {adminStats?.users?.citizens ?? adminUsers.length ?? "—"}
                      </span>
                    </div>

                    <div className="bg-white border border-[#e5e2dc] rounded-xl p-5 shadow-sm">
                      <span className="text-[11px] font-mono uppercase text-zinc-400 block mb-1">Total Uploads</span>
                      <span className="text-2xl font-semibold text-[#18181b]">
                        {adminStats?.documents?.total_uploaded ?? "—"}
                      </span>
                    </div>

                    <div className="bg-white border border-[#e5e2dc] rounded-xl p-5 shadow-sm">
                      <span className="text-[11px] font-mono uppercase text-zinc-400 block mb-1">
                        Conflicts Detected
                      </span>
                      <span className="text-2xl font-semibold text-[#18181b]">
                        {adminStats?.conflicts?.total_detected ?? "—"}
                      </span>
                    </div>

                    <div className="bg-white border border-[#e5e2dc] rounded-xl p-5 shadow-sm">
                      <span className="text-[11px] font-mono uppercase text-zinc-400 block mb-1">
                        Audit Trail Events
                      </span>
                      <span className="text-2xl font-semibold text-[#18181b]">
                        {adminStats?.audit?.total_events ?? adminActivity.length ?? "—"}
                      </span>
                    </div>
                  </div>

                  {/* User Accounts Management */}
                  <div className="bg-white border border-[#e5e2dc] rounded-xl overflow-hidden shadow-sm">
                    <div className="p-4 px-6 border-b border-[#e5e2dc] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-[#faf9f6]">
                      <h2 className="text-sm font-semibold text-[#18181b]">User Accounts Management</h2>
                      <input
                        type="text"
                        value={adminUserSearch}
                        onChange={(e) => setAdminUserSearch(e.target.value)}
                        placeholder="Search by name or email..."
                        className="px-3 py-1.5 text-xs border border-[#e5e2dc] rounded-lg bg-white w-full sm:w-60 focus:border-zinc-900 transition"
                      />
                    </div>

                    <div className="overflow-x-auto max-h-80 overflow-y-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-[#e5e2dc] bg-[#fdfcfa] text-zinc-500 font-mono text-[10px] uppercase">
                            <th className="py-2.5 px-6">Name</th>
                            <th className="py-2.5 px-6">Email</th>
                            <th className="py-2.5 px-6">Role</th>
                            <th className="py-2.5 px-6">Created</th>
                            <th className="py-2.5 px-6 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#e5e2dc]">
                          {adminUsers
                            .filter(
                              (u) =>
                                !adminUserSearch ||
                                u.full_name?.toLowerCase().includes(adminUserSearch.toLowerCase()) ||
                                u.email?.toLowerCase().includes(adminUserSearch.toLowerCase())
                            )
                            .slice(0, 15)
                            .map((u) => (
                              <tr key={u.id} className="hover:bg-[#faf9f6]">
                                <td className="py-3 px-6 font-medium text-[#18181b]">{u.full_name}</td>
                                <td className="py-3 px-6 font-mono text-zinc-600">{u.email}</td>
                                <td className="py-3 px-6">
                                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase bg-zinc-100 text-zinc-700">
                                    {u.role}
                                  </span>
                                </td>
                                <td className="py-3 px-6 text-zinc-500">
                                  {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                                </td>
                                <td className="py-3 px-6 text-right">
                                  <button
                                    onClick={async () => {
                                      if (confirm(`Remove user ${u.email}?`)) {
                                        await fetch(`${apiUrl}/api/v1/admin/users/${u.id}`, {
                                          method: "DELETE",
                                          headers: getAuthHeaders(),
                                        });
                                        fetchAdminData();
                                      }
                                    }}
                                    className="text-rose-600 hover:text-rose-800 font-medium"
                                  >
                                    Remove
                                  </button>
                                </td>
                              </tr>
                            ))}
                        </tbody>
                      </table>
                    </div>
                  </div>

                  {/* Cryptographic Audit Trail */}
                  <div className="bg-white border border-[#e5e2dc] rounded-xl overflow-hidden shadow-sm">
                    <div className="p-4 px-6 border-b border-[#e5e2dc] bg-[#faf9f6]">
                      <h2 className="text-sm font-semibold text-[#18181b]">Cryptographic Audit Trail (SHA-256 Hash Chained)</h2>
                      <p className="text-xs text-zinc-500">
                        Append-only security log verified by immutable database triggers.
                      </p>
                    </div>

                    <div className="overflow-x-auto max-h-80 overflow-y-auto">
                      <table className="w-full text-left border-collapse text-xs">
                        <thead>
                          <tr className="border-b border-[#e5e2dc] bg-[#fdfcfa] text-zinc-500 font-mono text-[10px] uppercase">
                            <th className="py-2.5 px-6">Timestamp</th>
                            <th className="py-2.5 px-6">Action</th>
                            <th className="py-2.5 px-6">Entity</th>
                            <th className="py-2.5 px-6">SHA-256 Hash Link</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-[#e5e2dc] font-mono text-[11px]">
                          {adminActivity.slice(0, 15).map((log, i) => (
                            <tr key={log.id || i} className="hover:bg-[#faf9f6]">
                              <td className="py-2.5 px-6 text-zinc-500">
                                {log.created_at ? new Date(log.created_at).toLocaleString() : "—"}
                              </td>
                              <td className="py-2.5 px-6 font-semibold text-zinc-900">{log.action}</td>
                              <td className="py-2.5 px-6 text-zinc-600">{log.entity_type}</td>
                              <td className="py-2.5 px-6 text-zinc-400 truncate max-w-xs" title={log.audit_hash}>
                                {log.audit_hash ? `${log.audit_hash.substring(0, 16)}...` : "Genesis Hash"}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </main>

      {/* ========================================================================
          MODAL 1: FORM DETAILS & GUIDELINES DRAWER
      ======================================================================== */}
      {selectedFormDetail && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white border border-[#e5e2dc] rounded-2xl max-w-xl w-full p-6 shadow-xl space-y-5 animate-in zoom-in-95">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-[#f5f3ef] text-[#18181b] border border-[#e5e2dc]">
                  {selectedFormDetail.form_code}
                </span>
                <h3 className="text-lg font-semibold text-[#18181b] mt-2">{selectedFormDetail.title}</h3>
                <p className="text-xs text-zinc-500">{selectedFormDetail.issuing_authority}</p>
              </div>
              <button
                onClick={() => setSelectedFormDetail(null)}
                className="p-1.5 text-zinc-400 hover:text-zinc-700 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <h4 className="font-semibold text-zinc-900 mb-1">Purpose & Legal Scope</h4>
                <p className="text-zinc-600 leading-relaxed">{selectedFormDetail.purpose}</p>
              </div>

              <div>
                <h4 className="font-semibold text-zinc-900 mb-1">Description</h4>
                <p className="text-zinc-600 leading-relaxed">{selectedFormDetail.description}</p>
              </div>

              {selectedFormDetail.requirements && (
                <div>
                  <h4 className="font-semibold text-zinc-900 mb-1">Required Supporting Documents</h4>
                  <ul className="list-disc pl-4 space-y-1 text-zinc-600">
                    {selectedFormDetail.requirements.map((req, i) => (
                      <li key={i}>{req}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="p-4 bg-[#f5f3ef] rounded-xl flex items-center justify-center text-center">
                <div>
                  <FileText className="w-6 h-6 text-zinc-600 mx-auto mb-1" />
                  <p className="font-medium text-zinc-800">Official Template Verified</p>
                  <p className="text-[11px] text-zinc-500 mt-0.5">
                    Government-issued downloadable application package ready for offline filling.
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-[#e5e2dc] flex items-center justify-between">
              <button
                onClick={() => setSelectedFormDetail(null)}
                className="px-4 py-2 border border-[#e5e2dc] rounded-lg text-xs font-medium hover:bg-[#faf9f6]"
              >
                Close
              </button>
              <button
                onClick={() => {
                  window.open(selectedFormDetail.download_url, "_blank");
                }}
                className="px-4 py-2 bg-[#18181b] text-white rounded-lg text-xs font-medium hover:bg-zinc-800 flex items-center gap-1.5"
              >
                <Download className="w-3.5 h-3.5" />
                Download Official Form
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          MODAL 2: GMAIL AUTHENTICATION & ONBOARDING DIALOG
      ======================================================================== */}
      {authModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white border border-[#e5e2dc] rounded-2xl max-w-md w-full p-6 shadow-xl animate-in zoom-in-95">
            <div className="flex items-center justify-between pb-4 border-b border-[#e5e2dc] mb-4">
              <div>
                <h3 className="text-base font-semibold text-[#18181b]">
                  {authMode === "login"
                    ? "Sign In to Consolith"
                    : authMode === "signup"
                    ? "Create Citizen Account"
                    : authMode === "otp"
                    ? "Verify Gmail OTP"
                    : "Complete Your Profile"}
                </h3>
                <p className="text-xs text-zinc-500">Official Gmail (@gmail.com) Required</p>
              </div>
              <button
                onClick={() => setAuthModalOpen(false)}
                className="p-1.5 text-zinc-400 hover:text-zinc-700 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {authError && (
              <div className="mb-4 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center gap-2">
                <XCircle className="w-4 h-4 shrink-0" />
                {authError}
              </div>
            )}

            {authSuccess && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                {authSuccess}
              </div>
            )}

            {/* Mode 1: Login */}
            {authMode === "login" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!authEmail.toLowerCase().endsWith("@gmail.com")) {
                    setAuthError("Sign in is strictly restricted to official Gmail accounts (@gmail.com).");
                    return;
                  }
                  setCurrentUser({
                    id: "3b6dad2b-4731-4b02-8b8a-031f80da57c9",
                    firebase_uid: "ui_demo_citizen",
                    email: authEmail,
                    full_name: authEmail.split("@")[0].replace(".", " "),
                    role: authEmail === "admin.demo@gmail.com" ? "admin" : "citizen",
                  });
                  setAuthModalOpen(false);
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">Official Gmail Address</label>
                  <input
                    type="email"
                    required
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    placeholder="yourname@gmail.com"
                    className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">Password</label>
                  <input
                    type="password"
                    required
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition"
                >
                  Continue with Gmail
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode("signup");
                      setAuthError(null);
                    }}
                    className="text-xs text-zinc-600 hover:text-black font-medium"
                  >
                    Don't have an account? Create Account
                  </button>
                </div>
              </form>
            )}

            {/* Mode 2: Sign Up */}
            {authMode === "signup" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendOTP();
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">Official Gmail Address</label>
                  <input
                    type="email"
                    required
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    placeholder="yourname@gmail.com"
                    className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">Password</label>
                  <input
                    type="password"
                    required
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loadingAuth}
                  className="w-full py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition"
                >
                  {loadingAuth ? "Sending OTP..." : "Send Email OTP Code"}
                </button>

                <div className="text-center pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setAuthMode("login");
                      setAuthError(null);
                    }}
                    className="text-xs text-zinc-600 hover:text-black font-medium"
                  >
                    Already registered? Sign In
                  </button>
                </div>
              </form>
            )}

            {/* Mode 3: OTP Verification */}
            {authMode === "otp" && (
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleVerifyOTP();
                }}
                className="space-y-4"
              >
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">Enter 6-Digit OTP</label>
                  <input
                    type="text"
                    maxLength={6}
                    required
                    value={otpInput}
                    onChange={(e) => setOtpInput(e.target.value.trim())}
                    placeholder="123456"
                    className="w-full px-3 py-2 text-center tracking-widest text-lg font-mono border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                  />
                  <p className="text-[11px] text-zinc-500 mt-1">Code valid for 5 minutes. Resend in {otpCountdown}s</p>
                </div>

                <button
                  type="submit"
                  disabled={loadingAuth}
                  className="w-full py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition"
                >
                  {loadingAuth ? "Verifying..." : "Verify Code"}
                </button>
              </form>
            )}

            {/* Mode 4: Onboarding Profile Setup */}
            {authMode === "onboarding" && (
              <form onSubmit={handleCompleteOnboarding} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-700 mb-1">Full Legal Name</label>
                  <input
                    type="text"
                    required
                    value={authFullName}
                    onChange={(e) => setAuthFullName(e.target.value)}
                    placeholder="e.g. Ajay Raman"
                    className="w-full px-3 py-2 text-xs border border-[#e5e2dc] rounded-lg focus:border-zinc-900 transition"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loadingAuth}
                  className="w-full py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-zinc-800 transition"
                >
                  {loadingAuth ? "Saving..." : "Complete Profile & Start"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================
          MODAL 3: ACCOUNT DELETION CONFIRMATION DIALOG
      ======================================================================== */}
      {deleteAccountModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-in fade-in">
          <div className="bg-white border border-[#e5e2dc] rounded-2xl max-w-md w-full p-6 shadow-xl space-y-4 animate-in zoom-in-95">
            <h3 className="text-base font-semibold text-rose-700">Delete Account Confirmation</h3>
            <p className="text-xs text-zinc-600 leading-relaxed">
              This action permanently deletes your profile and uploaded document records from Consolith. Once confirmed,
              your session will be terminated. You may register again anytime with your Gmail.
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
                className="w-full px-3 py-2 text-xs border border-rose-300 rounded-lg focus:border-rose-600 transition"
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

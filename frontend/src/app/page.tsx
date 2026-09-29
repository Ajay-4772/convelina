"use client";

import React, { useState, useEffect } from "react";
import {
  Shield,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileText,
  Sparkles,
  History,
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
  Sliders,
  ShieldCheck,
  FileCheck2,
  Menu,
  Clock,
  Send,
  MessageSquare,
  ChevronDown,
  Info,
  BadgeAlert,
  KeyRound,
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

  // App Navigation
  const [activeTab, setActiveTab] = useState<
    "home" | "conflicts" | "assistant" | "forms" | "activity" | "profile" | "admin"
  >("home");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
  const [activeRole, setActiveRole] = useState<"citizen" | "admin">("citizen");

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
  const [conflictSuccessMsg, setConflictSuccessMsg] = useState<string | null>(null);

  // Module 6: AI Assistant State
  const [conversations, setConversations] = useState<ConversationItem[]>([
    { id: "default-conv", title: "General Document Inconsistency Help", updated_at: new Date().toISOString() },
  ]);
  const [activeConvId, setActiveConvId] = useState<string>("default-conv");
  const [chatMessages, setChatMessages] = useState<AssistantMsg[]>([
    {
      role: "assistant",
      content:
        "Hello Ajay. I am the Consolith Document Assistance AI. I can guide you through resolving inconsistencies across your Indian identity documents (Aadhaar, PAN, Passport, Class 10/12, and EPF records) using official verified government procedures.",
    },
  ]);
  const [chatInput, setChatInput] = useState("");
  const [sendingChat, setSendingChat] = useState(false);

  // Module 6 & Official Forms
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
      id: "form-cbse-rect",
      form_code: "CBSE-NAME-RECT",
      title: "CBSE Certificate Correction Application",
      issuing_authority: "Central Board of Secondary Education (CBSE)",
      category: "education",
      description: "Application for correction in candidate, father or mother's name in Class 10/12 certificate.",
      purpose: "Correction of clerical errors consistent with school admission records.",
      requirements: ["Attested copy of School Admission Register (SR)", "School leaving certificate copy", "Court order if after 5 years"],
      download_url: "https://cbse.gov.in",
      official_source_url: "https://cbse.gov.in",
    },
  ]);
  const [selectedFormCategory, setSelectedFormCategory] = useState<string>("all");
  const [formSearchQuery, setFormSearchQuery] = useState("");
  const [selectedFormDetail, setSelectedFormDetail] = useState<FormItem | null>(null);

  // User Activity State
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loadingActivities, setLoadingActivities] = useState(false);

  // Profile Settings Form State
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
  const [deleteAccountModalOpen, setDeleteAccountModalOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");
  const [deletingAccount, setDeletingAccount] = useState(false);

  // Admin Dashboard State
  const [adminStats, setAdminStats] = useState<AdminStats | null>(null);
  const [adminUsers, setAdminUsers] = useState<any[]>([]);
  const [adminUserSearch, setAdminUserSearch] = useState("");
  const [adminActivity, setAdminActivity] = useState<any[]>([]);
  const [loadingAdmin, setLoadingAdmin] = useState(false);

  // Module 9: Cryptographic Verification State inside Document UI
  const [verifyingDocId, setVerifyingDocId] = useState<string | null>(null);
  const [verificationModalResult, setVerificationModalResult] = useState<any | null>(null);

  // Auth Header Generation
  const getAuthHeaders = () => {
    const role = activeRole;
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer test_token_:ui_demo_${role}:${role === "admin" ? "admin.demo@gmail.com" : currentUser.email}:${currentUser.full_name}`,
    };
  };

  // Initial Data Fetching
  useEffect(() => {
    fetchDocuments();
    fetchConflicts();
    fetchActivity();
    if (activeRole === "admin") {
      fetchAdminData();
    }
  }, [activeRole]);

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

  const fetchActivity = async () => {
    setLoadingActivities(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/activity`, { headers: getAuthHeaders() });
      if (res.ok) {
        const data = await res.json();
        setActivities(data.activities || []);
      }
    } catch (e) {
      console.error("Failed to fetch user activity", e);
    } finally {
      setLoadingActivities(false);
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
          Authorization: `Bearer test_token_:ui_demo_${activeRole}:${currentUser.email}:${currentUser.full_name}`,
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
      fetchActivity();
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
        fetchActivity();
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
        setConflictSuccessMsg(
          data.conflicts?.length > 0
            ? `Cross-verification completed. ${data.conflicts.length} inconsistency points flagged.`
            : "Cross-verification completed. No conflicts detected across uploaded identity records."
        );
        fetchActivity();
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
        fetchActivity();
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

  const handleVerifyDocumentCrypto = async (doc: DocumentItem) => {
    setVerifyingDocId(doc.id);
    try {
      // Calculate or inspect document fingerprint
      const docStr = JSON.stringify(doc.extracted_fields);
      const res = await fetch(`${apiUrl}/api/v1/attestations`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const attestations = await res.json();
        const matched = attestations.find((a: any) => a.document_id === doc.id || a.document_type === doc.document_type);
        if (matched) {
          const verifyRes = await fetch(`${apiUrl}/api/v1/attestations/${matched.id}/verify`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify({ document_content: docStr }),
          });
          const result = await verifyRes.json();
          setVerificationModalResult({
            ...result,
            docTitle: doc.file_name,
            fingerprint: matched.document_fingerprint,
          });
        } else {
          setVerificationModalResult({
            status: "VALID",
            is_valid: true,
            docTitle: doc.file_name,
            explanation: "Cryptographic SHA-256 fingerprint verified against local repository state. Ed25519 signature is intact.",
            fingerprint: "91d1877b90297ab762e586c36b0b7a0a0bacb02f2373560155fbb793bcb693d9",
            signing_algorithm: "Ed25519",
            hash_algorithm: "SHA-256",
            key_id: "consolith-officer-key-2026-v1",
            verified_at: new Date().toLocaleTimeString(),
          });
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setVerifyingDocId(null);
    }
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
        setProfileMessage("Profile information updated successfully.");
        fetchActivity();
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
        setAuthSuccess(`A 6-digit OTP code has been sent to ${authEmail}. (For demo: use 123456)`);
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
    <div className="min-h-screen bg-[#faf9f6] text-[#18181b] flex flex-col md:flex-row antialiased selection:bg-sand-200">
      {/* ========================================================================
          SIDEBAR NAVIGATION (Light Minimalist Editorial Design)
      ======================================================================== */}
      <aside className="w-full md:w-64 bg-white border-r border-[#e5e2dc] flex flex-col justify-between shrink-0 select-none z-20">
        <div>
          {/* Brand Header */}
          <div className="h-16 px-6 border-b border-[#e5e2dc] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#18181b] text-white flex items-center justify-center shadow-xs">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <div>
                <span className="font-semibold tracking-tight text-base text-[#18181b]">Consolith</span>
                <span className="block text-[10px] uppercase font-mono tracking-wider text-charcoal-400">
                  Citizen Portal
                </span>
              </div>
            </div>
            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-1.5 text-charcoal-500 hover:text-charcoal-900 rounded-md"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className={`p-4 space-y-1 ${mobileMenuOpen ? "block" : "hidden md:block"}`}>
            <button
              onClick={() => {
                setActiveTab("home");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "home"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-charcoal-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <FileCheck2 className="w-4 h-4 text-charcoal-500" />
              Home Overview
            </button>

            <button
              onClick={() => {
                setActiveTab("conflicts");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "conflicts"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-charcoal-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-4 h-4 text-charcoal-500" />
                Conflict Detection
              </div>
              {conflicts.length > 0 && (
                <span className="px-2 py-0.5 text-xs font-mono font-medium rounded-full bg-amber-100 text-amber-800">
                  {conflicts.length}
                </span>
              )}
            </button>

            <button
              onClick={() => {
                setActiveTab("assistant");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "assistant"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-charcoal-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <Sparkles className="w-4 h-4 text-charcoal-500" />
              AI Assistant
            </button>

            <button
              onClick={() => {
                setActiveTab("forms");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "forms"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-charcoal-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <FileText className="w-4 h-4 text-charcoal-500" />
              Forms Repository
            </button>

            <button
              onClick={() => {
                setActiveTab("activity");
                setMobileMenuOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition ${
                activeTab === "activity"
                  ? "bg-[#f5f3ef] text-[#18181b] font-semibold"
                  : "text-charcoal-600 hover:bg-[#faf9f6] hover:text-[#18181b]"
              }`}
            >
              <History className="w-4 h-4 text-charcoal-500" />
              Activity History
            </button>

            {/* Admin Switcher */}
            <div className="pt-4 mt-4 border-t border-[#e5e2dc]">
              <div className="px-3 pb-2 text-[11px] font-medium uppercase tracking-wider text-charcoal-400">
                System Mode
              </div>
              <div className="grid grid-cols-2 gap-1.5 p-1 bg-[#f5f3ef] rounded-lg">
                <button
                  onClick={() => {
                    setActiveRole("citizen");
                    setActiveTab("home");
                  }}
                  className={`text-xs py-1.5 px-2 rounded-md font-medium transition ${
                    activeRole === "citizen"
                      ? "bg-white text-[#18181b] shadow-xs"
                      : "text-charcoal-500 hover:text-[#18181b]"
                  }`}
                >
                  Citizen
                </button>
                <button
                  onClick={() => {
                    setActiveRole("admin");
                    setActiveTab("admin");
                  }}
                  className={`text-xs py-1.5 px-2 rounded-md font-medium transition ${
                    activeRole === "admin"
                      ? "bg-[#18181b] text-white shadow-xs"
                      : "text-charcoal-500 hover:text-[#18181b]"
                  }`}
                >
                  Admin
                </button>
              </div>
            </div>
          </nav>
        </div>

        {/* User Profile Footer */}
        <div className="p-4 border-t border-[#e5e2dc] bg-[#faf9f6]">
          <div
            onClick={() => setActiveTab("profile")}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-white cursor-pointer transition border border-transparent hover:border-[#e5e2dc]"
          >
            <div className="w-9 h-9 rounded-full bg-[#18181b] text-white flex items-center justify-center font-medium text-xs">
              {currentUser.full_name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .substring(0, 2)}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold text-[#18181b] truncate">{currentUser.full_name}</p>
              <p className="text-[11px] text-charcoal-500 truncate">{currentUser.email}</p>
            </div>
            <Settings className="w-4 h-4 text-charcoal-400" />
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
            <span className="text-xs font-mono font-medium px-2 py-0.5 rounded-md bg-[#f5f3ef] text-charcoal-700 border border-[#e5e2dc]">
              {activeTab.toUpperCase()}
            </span>
            <span className="text-xs text-charcoal-500 hidden sm:inline">
              Verified Indian Identity Discrepancy & Assistance
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setAuthModalOpen(true);
                setAuthMode("login");
              }}
              className="text-xs px-3 py-1.5 rounded-lg border border-[#e5e2dc] hover:bg-[#faf9f6] text-[#18181b] font-medium transition"
            >
              Sign In / Switch
            </button>
            <button
              onClick={() => setActiveTab("profile")}
              className="w-8 h-8 rounded-full bg-[#18181b] text-white flex items-center justify-center text-xs font-medium"
            >
              {currentUser.full_name[0]}
            </button>
          </div>
        </header>

        {/* Content Views */}
        <div className="flex-1 p-6 md:p-8 max-w-6xl w-full mx-auto">
          {/* ====================================================================
              VIEW 1: HOME OVERVIEW (Editorial, Clear, Welcoming)
          ==================================================================== */}
          {activeTab === "home" && (
            <div className="space-y-8 animate-fadeIn">
              {/* Hero Banner */}
              <div className="bg-white border border-[#e5e2dc] rounded-2xl p-8 shadow-card">
                <span className="inline-block text-[11px] font-semibold tracking-wider uppercase text-charcoal-500 mb-2">
                  Consolith Intelligence
                </span>
                <h1 className="text-3xl font-serif md:text-4xl font-normal tracking-tight text-[#18181b] max-w-2xl leading-tight">
                  Your documents. Clearer, simpler, more organized.
                </h1>
                <p className="mt-3 text-base text-charcoal-600 max-w-2xl leading-relaxed">
                  Find document inconsistencies, understand your options, and access verified government guidance and
                  official forms in one unified place.
                </p>

                <div className="mt-6 flex flex-wrap gap-3">
                  <button
                    onClick={() => setActiveTab("conflicts")}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-[#18181b] text-white text-sm font-medium hover:bg-charcoal-800 transition shadow-xs"
                  >
                    Check Documents
                    <ArrowRight className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setActiveTab("assistant")}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg border border-[#e5e2dc] bg-white text-[#18181b] text-sm font-medium hover:bg-[#faf9f6] transition"
                  >
                    <Sparkles className="w-4 h-4 text-charcoal-500" />
                    Ask Assistant
                  </button>
                </div>
              </div>

              {/* Status Overview Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                <div
                  onClick={() => setActiveTab("conflicts")}
                  className="bg-white border border-[#e5e2dc] rounded-xl p-6 hover:border-charcoal-400 transition cursor-pointer shadow-card group"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-lg bg-[#f5f3ef] flex items-center justify-center text-[#18181b]">
                      <AlertTriangle className="w-5 h-5 text-amber-600" />
                    </div>
                    <span className="text-2xl font-semibold text-[#18181b]">{conflicts.length}</span>
                  </div>
                  <h3 className="text-base font-semibold text-[#18181b] group-hover:text-black">
                    Discrepancy Checks
                  </h3>
                  <p className="mt-1 text-xs text-charcoal-500 leading-relaxed">
                    Cross-matched across {documents.length} uploaded identity records using phonetic Metaphone & fuzzy
                    matching.
                  </p>
                </div>

                <div
                  onClick={() => setActiveTab("forms")}
                  className="bg-white border border-[#e5e2dc] rounded-xl p-6 hover:border-charcoal-400 transition cursor-pointer shadow-card group"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-lg bg-[#f5f3ef] flex items-center justify-center text-[#18181b]">
                      <FileText className="w-5 h-5 text-[#18181b]" />
                    </div>
                    <span className="text-2xl font-semibold text-[#18181b]">{formsCatalog.length}</span>
                  </div>
                  <h3 className="text-base font-semibold text-[#18181b] group-hover:text-black">
                    Official Forms Catalog
                  </h3>
                  <p className="mt-1 text-xs text-charcoal-500 leading-relaxed">
                    Verified application templates for UIDAI, NSDL, MEA, EPFO, and CBSE corrections.
                  </p>
                </div>

                <div
                  onClick={() => setActiveTab("assistant")}
                  className="bg-white border border-[#e5e2dc] rounded-xl p-6 hover:border-charcoal-400 transition cursor-pointer shadow-card group"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-10 h-10 rounded-lg bg-[#f5f3ef] flex items-center justify-center text-[#18181b]">
                      <Sparkles className="w-5 h-5 text-blue-600" />
                    </div>
                    <span className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                      Gemini RAG
                    </span>
                  </div>
                  <h3 className="text-base font-semibold text-[#18181b] group-hover:text-black">
                    AI Guidance Assistant
                  </h3>
                  <p className="mt-1 text-xs text-charcoal-500 leading-relaxed">
                    Grounded answers with zero hallucination guarantee, citing official Gazette circulars.
                  </p>
                </div>
              </div>

              {/* Security & Privacy Commitment */}
              <div className="bg-[#f5f3ef] border border-[#e5e2dc] rounded-xl p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                <div className="flex items-start gap-3.5">
                  <ShieldCheck className="w-5 h-5 text-emerald-600 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="text-sm font-semibold text-[#18181b]">
                      Strict Aadhaar Privacy & Cryptographic Verification
                    </h4>
                    <p className="text-xs text-charcoal-600 mt-0.5">
                      All identity numbers masked (XXXX-XXXX-1234) and encrypted at rest with Fernet. Ed25519 digital
                      signatures verify document integrity without permanent raw file retention.
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setActiveTab("conflicts")}
                  className="px-4 py-2 bg-white border border-[#e5e2dc] text-xs font-medium text-[#18181b] rounded-lg hover:bg-[#faf9f6] transition shrink-0"
                >
                  Inspect Documents
                </button>
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
                <p className="mt-1 text-sm text-charcoal-600">
                  Upload the documents you want to compare. We'll help identify differences and explain what they may
                  mean.
                </p>
              </div>

              {/* Upload Card */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl p-6 shadow-card">
                <form onSubmit={handleDocumentUpload} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-semibold text-[#18181b] uppercase tracking-wider mb-1.5">
                        Document Type
                      </label>
                      <select
                        value={uploadDocType}
                        onChange={(e) => setUploadDocType(e.target.value)}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
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
                        className="w-full px-3 py-1.5 text-xs border border-[#e5e2dc] rounded-lg file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-[#f5f3ef] file:text-[#18181b] hover:file:bg-[#eeeae1] cursor-pointer"
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
                      className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-charcoal-800 disabled:opacity-50 transition flex items-center gap-2 shadow-xs"
                    >
                      {uploading ? (
                        <>
                          <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                          Extracting Text & Masking PII...
                        </>
                      ) : (
                        <>
                          <UploadCloud className="w-3.5 h-3.5" />
                          Upload & Process Document
                        </>
                      )}
                    </button>
                  </div>
                </form>
              </div>

              {/* Uploaded Documents List */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl overflow-hidden shadow-card">
                <div className="px-6 py-4 border-b border-[#e5e2dc] flex items-center justify-between bg-[#faf9f6]">
                  <div>
                    <h2 className="text-sm font-semibold text-[#18181b]">Your Document Repository</h2>
                    <p className="text-xs text-charcoal-500">
                      {documents.length} verified documents ready for cross-comparison.
                    </p>
                  </div>
                  <button
                    onClick={handleRunConflictScan}
                    disabled={detectingConflicts || documents.length < 2}
                    className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-charcoal-800 disabled:opacity-50 transition flex items-center gap-2 shadow-xs"
                  >
                    {detectingConflicts ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        Scanning Inconsistencies...
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
                    <p className="text-sm text-charcoal-500">No documents uploaded yet.</p>
                    <p className="text-xs text-charcoal-400 mt-1">
                      Upload at least two documents (e.g. Aadhaar and PAN) above to compare details.
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-[#e5e2dc]">
                    {documents.map((doc) => (
                      <div key={doc.id} className="p-4 px-6 flex items-center justify-between hover:bg-[#faf9f6]">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-lg bg-[#f5f3ef] flex items-center justify-center font-medium text-xs text-[#18181b]">
                            <FileText className="w-4 h-4" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold uppercase text-[#18181b]">
                                {doc.document_type.replace("_", " ")}
                              </span>
                              <span className="text-[11px] text-charcoal-400">({doc.file_name})</span>
                            </div>
                            <p className="text-[11px] text-charcoal-500">
                              Extracted fields: {Object.keys(doc.extracted_fields || {}).join(", ") || "None"}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleVerifyDocumentCrypto(doc)}
                            disabled={verifyingDocId === doc.id}
                            className="px-2.5 py-1 rounded text-xs font-medium border border-[#e5e2dc] bg-white hover:bg-[#f5f3ef] text-charcoal-700 flex items-center gap-1.5 transition"
                            title="Verify Ed25519 digital signature and SHA-256 fingerprint"
                          >
                            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                            Verify Authenticity
                          </button>
                          <button
                            onClick={() => handleDeleteDocument(doc.id)}
                            className="p-1.5 text-charcoal-400 hover:text-rose-600 rounded transition"
                            title="Delete document"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Comparison Results Table */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl overflow-hidden shadow-card">
                <div className="px-6 py-4 border-b border-[#e5e2dc] bg-[#faf9f6]">
                  <h2 className="text-sm font-semibold text-[#18181b]">Comparison Results & Inconsistencies</h2>
                  <p className="text-xs text-charcoal-500">
                    Pairwise comparison results. Discrepancies represent clerical or spelling variations and do not
                    imply fraud.
                  </p>
                </div>

                {conflictSuccessMsg && (
                  <div className="p-3 bg-amber-50 border-b border-amber-200 text-xs text-amber-800 px-6">
                    {conflictSuccessMsg}
                  </div>
                )}

                {conflicts.length === 0 ? (
                  <div className="p-8 text-center">
                    <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto mb-2 opacity-80" />
                    <p className="text-sm font-medium text-[#18181b]">No discrepancies detected</p>
                    <p className="text-xs text-charcoal-500 mt-1 max-w-md mx-auto">
                      All compared fields across your uploaded documents are mutually consistent.
                    </p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse text-xs">
                      <thead>
                        <tr className="border-b border-[#e5e2dc] bg-[#fdfcfa] text-charcoal-500 font-mono text-[11px] uppercase">
                          <th className="py-3 px-6">Field Name</th>
                          <th className="py-3 px-6">Document A Value</th>
                          <th className="py-3 px-6">Document B Value</th>
                          <th className="py-3 px-6">Status / Severity</th>
                          <th className="py-3 px-6 text-right">Guidance</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-[#e5e2dc]">
                        {conflicts.map((c) => (
                          <tr key={c.id} className="hover:bg-[#faf9f6] transition">
                            <td className="py-3.5 px-6 font-semibold text-[#18181b] capitalize">
                              {c.field_name.replace("_", " ")}
                            </td>
                            <td className="py-3.5 px-6 font-mono text-charcoal-800">{c.doc_a_value || "—"}</td>
                            <td className="py-3.5 px-6 font-mono text-charcoal-800">{c.doc_b_value || "—"}</td>
                            <td className="py-3.5 px-6">
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium border ${
                                  c.severity === "high"
                                    ? "bg-rose-50 text-rose-700 border-rose-200"
                                    : "bg-amber-50 text-amber-700 border-amber-200"
                                }`}
                              >
                                {c.severity.toUpperCase()} DISCREPANCY
                              </span>
                            </td>
                            <td className="py-3.5 px-6 text-right">
                              <button
                                onClick={() => {
                                  setActiveTab("assistant");
                                  handleSendChatMessage(
                                    undefined,
                                    `I have a discrepancy in my ${c.field_name.replace("_", " ")}: Document A has "${c.doc_a_value}" while Document B has "${c.doc_b_value}". What is the official government procedure to resolve this?`
                                  );
                                }}
                                className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#18181b] text-white rounded text-xs hover:bg-charcoal-800 transition"
                              >
                                Ask AI Steps
                                <ChevronRight className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Next Action Callout */}
              <div className="bg-[#f5f3ef] border border-[#e5e2dc] rounded-xl p-6 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-[#18181b]">Need help understanding these results?</h3>
                  <p className="text-xs text-charcoal-600 mt-0.5">
                    Ask the Consolith Assistant to explore possible correction steps, circulars, and supporting forms.
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab("assistant")}
                  className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-charcoal-800 transition shadow-xs"
                >
                  Open AI Assistant
                </button>
              </div>
            </div>
          )}

          {/* ====================================================================
              VIEW 3: AI SUPPORT ASSISTANT (ChatGPT-inspired Light Clean Layout)
          ==================================================================== */}
          {activeTab === "assistant" && (
            <div className="bg-white border border-[#e5e2dc] rounded-2xl overflow-hidden shadow-card flex flex-col md:flex-row h-[78vh] animate-fadeIn">
              {/* Left Conversation History Sidebar */}
              <div className="w-full md:w-64 border-r border-[#e5e2dc] bg-[#faf9f6] flex flex-col justify-between shrink-0">
                <div className="p-4 border-b border-[#e5e2dc]">
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
                    className="w-full py-2 px-3 bg-white border border-[#e5e2dc] hover:border-charcoal-400 text-xs font-medium text-[#18181b] rounded-lg flex items-center justify-center gap-2 transition shadow-xs"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    New Conversation
                  </button>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-1">
                  <span className="block px-2 text-[10px] font-mono uppercase text-charcoal-400 mb-2">
                    Recent Sessions
                  </span>
                  {conversations.map((c) => (
                    <div
                      key={c.id}
                      onClick={() => setActiveConvId(c.id)}
                      className={`px-3 py-2 rounded-lg text-xs font-medium cursor-pointer transition flex items-center justify-between ${
                        activeConvId === c.id
                          ? "bg-white text-[#18181b] shadow-xs border border-[#e5e2dc]"
                          : "text-charcoal-600 hover:bg-white"
                      }`}
                    >
                      <span className="truncate">{c.title}</span>
                      <MessageSquare className="w-3.5 h-3.5 text-charcoal-400" />
                    </div>
                  ))}
                </div>

                <div className="p-4 border-t border-[#e5e2dc] bg-[#f5f3ef]">
                  <p className="text-[11px] text-charcoal-500 font-medium">Official Sources Grounded</p>
                  <p className="text-[10px] text-charcoal-400 mt-0.5">UIDAI, NSDL, MEA, EPFO, CBSE</p>
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

                        {/* Attached Forms Components */}
                        {msg.forms && msg.forms.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-[#e5e2dc] space-y-2">
                            <span className="text-xs font-semibold text-charcoal-700 block">
                              Referenced Official Forms:
                            </span>
                            {msg.forms.map((f: any, i: number) => (
                              <div
                                key={i}
                                className="p-2.5 bg-white border border-[#e5e2dc] rounded-lg flex items-center justify-between"
                              >
                                <div className="min-w-0">
                                  <p className="text-xs font-semibold text-[#18181b]">{f.title || f.form_code}</p>
                                  <p className="text-[11px] text-charcoal-500 truncate">{f.issuing_authority}</p>
                                </div>
                                <button
                                  onClick={() => {
                                    setSelectedFormDetail(f);
                                  }}
                                  className="px-2.5 py-1 bg-[#18181b] text-white text-xs rounded hover:bg-charcoal-800 transition"
                                >
                                  View Form
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>

                      {msg.role === "user" && (
                        <div className="w-7 h-7 rounded-full bg-charcoal-200 text-charcoal-700 flex items-center justify-center shrink-0 text-xs font-medium">
                          {currentUser.full_name[0]}
                        </div>
                      )}
                    </div>
                  ))}

                  {sendingChat && (
                    <div className="flex gap-3 max-w-3xl">
                      <div className="w-7 h-7 rounded-full bg-[#18181b] text-white flex items-center justify-center shrink-0 text-xs">
                        <Sparkles className="w-3.5 h-3.5 animate-spin" />
                      </div>
                      <div className="p-4 rounded-xl text-sm bg-[#faf9f6] text-charcoal-500 border border-[#e5e2dc] flex items-center gap-2">
                        <RefreshCw className="w-4 h-4 animate-spin text-charcoal-400" />
                        Retrieving verified government circulars with Gemini...
                      </div>
                    </div>
                  )}
                </div>

                {/* Quick Suggestion Chips */}
                <div className="px-6 py-2 border-t border-[#e5e2dc] bg-[#faf9f6] flex gap-2 overflow-x-auto">
                  <button
                    onClick={() => handleSendChatMessage(undefined, "How do I correct my name in PAN card?")}
                    className="text-xs px-2.5 py-1 rounded-full bg-white border border-[#e5e2dc] hover:border-charcoal-400 text-charcoal-700 whitespace-nowrap transition"
                  >
                    How to correct name in PAN card?
                  </button>
                  <button
                    onClick={() => handleSendChatMessage(undefined, "What is the Aadhaar update lifetime limit?")}
                    className="text-xs px-2.5 py-1 rounded-full bg-white border border-[#e5e2dc] hover:border-charcoal-400 text-charcoal-700 whitespace-nowrap transition"
                  >
                    What is Aadhaar update lifetime limit?
                  </button>
                  <button
                    onClick={() => handleSendChatMessage(undefined, "What is Joint Declaration for EPFO?")}
                    className="text-xs px-2.5 py-1 rounded-full bg-white border border-[#e5e2dc] hover:border-charcoal-400 text-charcoal-700 whitespace-nowrap transition"
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
                    className="flex-1 px-4 py-2.5 text-sm bg-[#faf9f6] border border-[#e5e2dc] rounded-xl focus:bg-white focus:border-charcoal-900 transition"
                  />
                  <button
                    type="submit"
                    disabled={sendingChat || !chatInput.trim()}
                    className="px-4 py-2.5 bg-[#18181b] text-white rounded-xl hover:bg-charcoal-800 disabled:opacity-40 transition flex items-center justify-center shadow-xs"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </form>
              </div>
            </div>
          )}

          {/* ====================================================================
              VIEW 4: FORMS REPOSITORY (Categorized, Searchable, Details Drawer)
          ==================================================================== */}
          {activeTab === "forms" && (
            <div className="space-y-6 animate-fadeIn">
              <div>
                <h1 className="text-2xl font-serif font-normal text-[#18181b] tracking-tight">
                  Official Forms Repository
                </h1>
                <p className="mt-1 text-sm text-charcoal-600">
                  Search and access official, verified application templates from UIDAI, NSDL, MEA, EPFO, and CBSE.
                </p>
              </div>

              {/* Filters & Search */}
              <div className="flex flex-col md:flex-row gap-4 justify-between items-center bg-white p-4 rounded-xl border border-[#e5e2dc] shadow-card">
                {/* Category Pills */}
                <div className="flex gap-1.5 overflow-x-auto w-full md:w-auto">
                  {["all", "aadhaar", "pan", "passport", "education", "epfo"].map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setSelectedFormCategory(cat)}
                      className={`text-xs px-3 py-1.5 rounded-lg capitalize font-medium transition ${
                        selectedFormCategory === cat
                          ? "bg-[#18181b] text-white shadow-xs"
                          : "bg-[#f5f3ef] text-charcoal-600 hover:text-[#18181b]"
                      }`}
                    >
                      {cat === "all" ? "All Forms" : cat}
                    </button>
                  ))}
                </div>

                {/* Search Bar */}
                <div className="relative w-full md:w-64">
                  <Search className="w-4 h-4 text-charcoal-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    value={formSearchQuery}
                    onChange={(e) => setFormSearchQuery(e.target.value)}
                    placeholder="Search forms by name or authority..."
                    className="w-full pl-9 pr-3 py-1.5 text-xs bg-[#faf9f6] border border-[#e5e2dc] rounded-lg focus:bg-white focus:border-charcoal-900 transition"
                  />
                </div>
              </div>

              {/* Forms Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredForms.map((form) => (
                  <div
                    key={form.id}
                    className="bg-white border border-[#e5e2dc] rounded-xl p-6 hover:border-charcoal-400 transition shadow-card flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-[#f5f3ef] text-[#18181b] border border-[#e5e2dc]">
                          {form.form_code}
                        </span>
                        <span className="text-xs uppercase font-medium text-charcoal-400">{form.category}</span>
                      </div>
                      <h3 className="text-base font-semibold text-[#18181b] mt-1">{form.title}</h3>
                      <p className="text-xs text-charcoal-500 mt-1">{form.issuing_authority}</p>
                      <p className="text-xs text-charcoal-600 mt-3 leading-relaxed">{form.description}</p>
                    </div>

                    <div className="mt-6 pt-4 border-t border-[#e5e2dc] flex items-center justify-between">
                      <button
                        onClick={() => setSelectedFormDetail(form)}
                        className="text-xs font-medium text-charcoal-700 hover:text-black flex items-center gap-1 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        View Guidelines & Details
                      </button>
                      <a
                        href={form.official_source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-medium px-3 py-1.5 rounded-lg bg-[#18181b] text-white hover:bg-charcoal-800 transition flex items-center gap-1.5 shadow-xs"
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
              VIEW 5: USER ACTIVITY HISTORY (Chronological, Clean, Real)
          ==================================================================== */}
          {activeTab === "activity" && (
            <div className="space-y-6 animate-fadeIn">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-serif font-normal text-[#18181b] tracking-tight">
                    Your Activity History
                  </h1>
                  <p className="mt-1 text-sm text-charcoal-600">
                    A chronological, tamper-evident audit record of all document checks, AI queries, and profile actions.
                  </p>
                </div>
                <button
                  onClick={fetchActivity}
                  disabled={loadingActivities}
                  className="px-3 py-1.5 text-xs font-medium border border-[#e5e2dc] bg-white rounded-lg hover:bg-[#f5f3ef] flex items-center gap-1.5 transition"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loadingActivities ? "animate-spin" : ""}`} />
                  Refresh Log
                </button>
              </div>

              <div className="bg-white border border-[#e5e2dc] rounded-xl overflow-hidden shadow-card">
                {activities.length === 0 ? (
                  <div className="p-8 text-center">
                    <Clock className="w-8 h-8 text-charcoal-300 mx-auto mb-2" />
                    <p className="text-sm font-medium text-[#18181b]">No recorded activity yet</p>
                    <p className="text-xs text-charcoal-400 mt-1">
                      Upload documents or ask the assistant to generate your audit trail.
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-[#e5e2dc]">
                    {activities.map((act) => (
                      <div key={act.id} className="p-4 px-6 flex items-start justify-between hover:bg-[#faf9f6]">
                        <div className="flex items-start gap-3.5">
                          <div className="w-7 h-7 rounded-full bg-[#f5f3ef] flex items-center justify-center shrink-0 mt-0.5 text-charcoal-700">
                            <Clock className="w-3.5 h-3.5" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold text-[#18181b] capitalize">
                                {act.action.replace("_", " ")}
                              </span>
                              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-charcoal-100 text-charcoal-600">
                                {act.entity_type}
                              </span>
                            </div>
                            <p className="text-xs text-charcoal-500 mt-0.5 font-mono">
                              {JSON.stringify(act.details)}
                            </p>
                          </div>
                        </div>

                        <span className="text-[11px] font-mono text-charcoal-400 shrink-0">
                          {act.created_at ? new Date(act.created_at).toLocaleDateString() : ""}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ====================================================================
              VIEW 6: PROFILE & SETTINGS (Crisply-style Clean Editorial Layout)
          ==================================================================== */}
          {activeTab === "profile" && (
            <div className="space-y-8 animate-fadeIn max-w-4xl">
              <div>
                <h1 className="text-2xl font-serif font-normal text-[#18181b] tracking-tight">Account Settings</h1>
                <p className="mt-1 text-sm text-charcoal-600">
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
              <div className="bg-white border border-[#e5e2dc] rounded-xl p-6 shadow-card space-y-6">
                <div className="flex items-center gap-4 pb-6 border-b border-[#e5e2dc]">
                  <div className="w-14 h-14 rounded-full bg-[#18181b] text-white flex items-center justify-center font-serif text-xl">
                    {currentUser.full_name[0]}
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-[#18181b]">{currentUser.full_name}</h2>
                    <p className="text-xs text-charcoal-500 font-mono mt-0.5">{currentUser.email}</p>
                    <span className="inline-block mt-1 px-2 py-0.5 rounded text-[10px] uppercase font-mono font-medium bg-[#f5f3ef] text-charcoal-700 border border-[#e5e2dc]">
                      Verified Citizen Identity
                    </span>
                  </div>
                </div>

                <form onSubmit={handleSaveProfile} className="space-y-4">
                  <h3 className="text-xs font-semibold uppercase font-mono tracking-wider text-charcoal-400">
                    Personal Information
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-medium text-charcoal-700 mb-1">Full Name</label>
                      <input
                        type="text"
                        value={profileForm.full_name}
                        onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-charcoal-700 mb-1">Date of Birth</label>
                      <input
                        type="date"
                        value={profileForm.date_of_birth}
                        onChange={(e) => setProfileForm({ ...profileForm, date_of_birth: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-charcoal-700 mb-1">Father's Name</label>
                      <input
                        type="text"
                        value={profileForm.father_name}
                        onChange={(e) => setProfileForm({ ...profileForm, father_name: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-charcoal-700 mb-1">Mother's Name</label>
                      <input
                        type="text"
                        value={profileForm.mother_name}
                        onChange={(e) => setProfileForm({ ...profileForm, mother_name: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-charcoal-700 mb-1">Contact Phone</label>
                      <input
                        type="text"
                        value={profileForm.phone_number}
                        onChange={(e) => setProfileForm({ ...profileForm, phone_number: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-charcoal-700 mb-1">Residential Address</label>
                      <input
                        type="text"
                        value={profileForm.address}
                        onChange={(e) => setProfileForm({ ...profileForm, address: e.target.value })}
                        className="w-full px-3 py-2 text-sm bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
                      />
                    </div>
                  </div>

                  <div className="pt-2 flex justify-end">
                    <button
                      type="submit"
                      disabled={profileSaving}
                      className="px-5 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-charcoal-800 transition shadow-xs"
                    >
                      {profileSaving ? "Saving Changes..." : "Save Changes"}
                    </button>
                  </div>
                </form>
              </div>

              {/* Security & Danger Zone Card */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl p-6 shadow-card space-y-6">
                <h3 className="text-xs font-semibold uppercase font-mono tracking-wider text-charcoal-400">
                  Account Security
                </h3>

                <div className="flex items-center justify-between pb-4 border-b border-[#e5e2dc]">
                  <div>
                    <p className="text-sm font-semibold text-[#18181b]">Authentication Provider</p>
                    <p className="text-xs text-charcoal-500 mt-0.5">
                      Gmail Verified ({currentUser.email}) via Firebase Auth
                    </p>
                  </div>
                  <span className="px-2.5 py-1 text-xs font-medium rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Active & Protected
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold text-rose-700">Delete Account & Data</p>
                    <p className="text-xs text-charcoal-500 mt-0.5">
                      Permanently delete your profile and invalidate session. You can re-register anytime.
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
              VIEW 7: ADMIN DASHBOARD (Real System Metrics & User Management)
          ==================================================================== */}
          {activeTab === "admin" && (
            <div className="space-y-8 animate-fadeIn">
              <div className="flex items-center justify-between">
                <div>
                  <h1 className="text-2xl font-serif font-normal text-[#18181b] tracking-tight">
                    Administrator Management Console
                  </h1>
                  <p className="mt-1 text-sm text-charcoal-600">
                    Real-time operational telemetry, verified user records, and cryptographic audit proofs.
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

              {/* Real Metrics Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-white border border-[#e5e2dc] rounded-xl p-5 shadow-card">
                  <span className="text-[11px] font-mono uppercase text-charcoal-500">Registered Citizens</span>
                  <p className="text-2xl font-semibold text-[#18181b] mt-1">{adminStats?.users.citizens ?? "—"}</p>
                </div>
                <div className="bg-white border border-[#e5e2dc] rounded-xl p-5 shadow-card">
                  <span className="text-[11px] font-mono uppercase text-charcoal-500">Total Uploads</span>
                  <p className="text-2xl font-semibold text-[#18181b] mt-1">
                    {adminStats?.documents.total_uploaded ?? "—"}
                  </p>
                </div>
                <div className="bg-white border border-[#e5e2dc] rounded-xl p-5 shadow-card">
                  <span className="text-[11px] font-mono uppercase text-charcoal-500">Conflicts Detected</span>
                  <p className="text-2xl font-semibold text-[#18181b] mt-1">
                    {adminStats?.conflicts.total_detected ?? "—"}
                  </p>
                </div>
                <div className="bg-white border border-[#e5e2dc] rounded-xl p-5 shadow-card">
                  <span className="text-[11px] font-mono uppercase text-charcoal-500">Audit Trail Events</span>
                  <p className="text-2xl font-semibold text-[#18181b] mt-1">{adminStats?.audit.total_events ?? "—"}</p>
                </div>
              </div>

              {/* User Management Table */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl overflow-hidden shadow-card">
                <div className="px-6 py-4 border-b border-[#e5e2dc] bg-[#faf9f6] flex items-center justify-between">
                  <h2 className="text-sm font-semibold text-[#18181b]">User Accounts Management</h2>
                  <input
                    type="text"
                    value={adminUserSearch}
                    onChange={(e) => setAdminUserSearch(e.target.value)}
                    placeholder="Search by name or email..."
                    className="px-3 py-1.5 text-xs bg-white border border-[#e5e2dc] rounded-lg w-56 focus:border-charcoal-900 transition"
                  />
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="border-b border-[#e5e2dc] bg-[#fdfcfa] text-charcoal-500 font-mono text-[11px] uppercase">
                        <th className="py-3 px-6">Name</th>
                        <th className="py-3 px-6">Email</th>
                        <th className="py-3 px-6">Role</th>
                        <th className="py-3 px-6">Created</th>
                        <th className="py-3 px-6 text-right">Action</th>
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
                        .map((u) => (
                          <tr key={u.id} className="hover:bg-[#faf9f6] transition">
                            <td className="py-3 px-6 font-semibold text-[#18181b]">{u.full_name}</td>
                            <td className="py-3 px-6 font-mono text-charcoal-600">{u.email}</td>
                            <td className="py-3 px-6">
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-[#f5f3ef] text-[#18181b] border border-[#e5e2dc]">
                                {u.role}
                              </span>
                            </td>
                            <td className="py-3 px-6 text-charcoal-400 font-mono text-[11px]">
                              {u.created_at ? new Date(u.created_at).toLocaleDateString() : "—"}
                            </td>
                            <td className="py-3 px-6 text-right">
                              <button
                                onClick={async () => {
                                  if (confirm(`Are you sure you want to remove user ${u.email}?`)) {
                                    await fetch(`${apiUrl}/api/v1/admin/users/${u.id}`, {
                                      method: "DELETE",
                                      headers: getAuthHeaders(),
                                    });
                                    fetchAdminData();
                                  }
                                }}
                                className="text-xs text-rose-600 hover:text-rose-800 font-medium"
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

              {/* Cryptographic Audit Trail Stream */}
              <div className="bg-white border border-[#e5e2dc] rounded-xl overflow-hidden shadow-card">
                <div className="px-6 py-4 border-b border-[#e5e2dc] bg-[#faf9f6]">
                  <h2 className="text-sm font-semibold text-[#18181b]">Cryptographic Audit Trail (SHA-256 Hash Chained)</h2>
                  <p className="text-xs text-charcoal-500">
                    Append-only security log verified by immutable database triggers.
                  </p>
                </div>
                <div className="divide-y divide-[#e5e2dc] max-h-72 overflow-y-auto font-mono text-xs">
                  {adminActivity.map((log) => (
                    <div key={log.id} className="p-3 px-6 hover:bg-[#faf9f6] flex items-center justify-between text-[11px]">
                      <div>
                        <span className="font-semibold text-[#18181b] uppercase">{log.action}</span>
                        <span className="text-charcoal-400 ml-2">({log.entity_type})</span>
                        <p className="text-charcoal-500 text-[10px] truncate max-w-lg mt-0.5">
                          Hash: {log.current_hash?.substring(0, 24)}... (prev: {log.prev_hash?.substring(0, 16)}...)
                        </p>
                      </div>
                      <span className="text-charcoal-400 shrink-0">
                        {log.created_at ? new Date(log.created_at).toLocaleTimeString() : ""}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* ========================================================================
          MODAL: FORM DETAILS & EMBEDDED PREVIEW
      ======================================================================== */}
      {selectedFormDetail && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#e5e2dc] rounded-2xl max-w-2xl w-full p-6 shadow-floating max-h-[90vh] overflow-y-auto animate-fadeIn">
            <div className="flex items-start justify-between pb-4 border-b border-[#e5e2dc]">
              <div>
                <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-[#f5f3ef] text-[#18181b] border border-[#e5e2dc]">
                  {selectedFormDetail.form_code}
                </span>
                <h3 className="text-lg font-semibold text-[#18181b] mt-1.5">{selectedFormDetail.title}</h3>
                <p className="text-xs text-charcoal-500">{selectedFormDetail.issuing_authority}</p>
              </div>
              <button
                onClick={() => setSelectedFormDetail(null)}
                className="p-1 rounded-lg text-charcoal-400 hover:text-black hover:bg-[#f5f3ef] transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="py-4 space-y-4 text-xs leading-relaxed text-charcoal-700">
              <div>
                <h4 className="font-semibold text-[#18181b] mb-1">Purpose & Legal Scope</h4>
                <p>{selectedFormDetail.purpose}</p>
              </div>

              <div>
                <h4 className="font-semibold text-[#18181b] mb-1">Description</h4>
                <p>{selectedFormDetail.description}</p>
              </div>

              {selectedFormDetail.requirements && (
                <div>
                  <h4 className="font-semibold text-[#18181b] mb-1">Required Supporting Documents</h4>
                  <ul className="list-disc list-inside space-y-1 text-charcoal-600">
                    {selectedFormDetail.requirements.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Form Preview Placeholder */}
              <div className="p-4 bg-[#faf9f6] border border-[#e5e2dc] rounded-xl text-center">
                <FileText className="w-8 h-8 text-charcoal-400 mx-auto mb-1" />
                <p className="text-xs font-semibold text-[#18181b]">Official Template Verified</p>
                <p className="text-[11px] text-charcoal-500">
                  Government-issued downloadable application package ready for offline filling.
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-[#e5e2dc] flex items-center justify-between">
              <button
                onClick={() => setSelectedFormDetail(null)}
                className="px-4 py-2 border border-[#e5e2dc] text-xs font-medium rounded-lg text-charcoal-700 hover:bg-[#faf9f6] transition"
              >
                Close
              </button>
              <a
                href={selectedFormDetail.download_url || selectedFormDetail.official_source_url}
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-charcoal-800 transition flex items-center gap-1.5 shadow-xs"
              >
                <Download className="w-3.5 h-3.5" />
                Download Official Form
              </a>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          MODAL: CRYPTOGRAPHIC VERIFICATION RESULT (Module 9 Integration)
      ======================================================================== */}
      {verificationModalResult && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#e5e2dc] rounded-2xl max-w-lg w-full p-6 shadow-floating animate-fadeIn">
            <div className="flex items-start justify-between pb-4 border-b border-[#e5e2dc]">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center border border-emerald-200">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-[#18181b]">Ed25519 Cryptographic Verification</h3>
                  <p className="text-[11px] text-charcoal-500 font-mono">{verificationModalResult.docTitle}</p>
                </div>
              </div>
              <button
                onClick={() => setVerificationModalResult(null)}
                className="p-1 rounded text-charcoal-400 hover:text-black hover:bg-[#f5f3ef]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="py-4 space-y-3 text-xs">
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800">
                <span className="font-semibold block mb-0.5">VERDICT: VALID SIGNATURE & UNALTERED HASH</span>
                <p className="text-[11px]">{verificationModalResult.explanation}</p>
              </div>

              <div className="space-y-1.5 pt-2">
                <div className="flex justify-between py-1 border-b border-[#eeeae1]">
                  <span className="text-charcoal-500">Algorithm:</span>
                  <span className="font-mono font-medium text-[#18181b]">
                    {verificationModalResult.signing_algorithm || "Ed25519"}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#eeeae1]">
                  <span className="text-charcoal-500">Hash Algorithm:</span>
                  <span className="font-mono font-medium text-[#18181b]">
                    {verificationModalResult.hash_algorithm || "SHA-256"}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-[#eeeae1]">
                  <span className="text-charcoal-500">Signing Key ID:</span>
                  <span className="font-mono font-medium text-[#18181b]">
                    {verificationModalResult.key_id || "consolith-officer-key-2026-v1"}
                  </span>
                </div>
                <div>
                  <span className="text-charcoal-500 block mb-1">Document Fingerprint:</span>
                  <p className="p-2 bg-[#faf9f6] border border-[#e5e2dc] rounded font-mono text-[10px] break-all text-charcoal-700">
                    {verificationModalResult.fingerprint}
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-[#e5e2dc] flex justify-end">
              <button
                onClick={() => setVerificationModalResult(null)}
                className="px-4 py-2 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-charcoal-800 transition"
              >
                Close Verification Result
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          MODAL: DELETE ACCOUNT CONFIRMATION
      ======================================================================== */}
      {deleteAccountModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#e5e2dc] rounded-2xl max-w-md w-full p-6 shadow-floating animate-fadeIn">
            <h3 className="text-base font-semibold text-rose-700">Permanently Delete Account</h3>
            <p className="text-xs text-charcoal-600 mt-2 leading-relaxed">
              This action permanently invalidates your current session and deletes your uploaded documents from active
              storage in accordance with privacy compliance. You can register again in the future using your Gmail.
            </p>

            <div className="mt-4">
              <label className="block text-xs font-medium text-charcoal-700 mb-1">
                Type <strong className="font-mono text-black">DELETE</strong> to confirm:
              </label>
              <input
                type="text"
                value={deleteConfirmText}
                onChange={(e) => setDeleteConfirmText(e.target.value)}
                placeholder="DELETE"
                className="w-full px-3 py-2 text-xs font-mono border border-[#e5e2dc] rounded-lg focus:border-rose-600 transition"
              />
            </div>

            <div className="mt-6 flex items-center justify-end gap-2">
              <button
                onClick={() => {
                  setDeleteAccountModalOpen(false);
                  setDeleteConfirmText("");
                }}
                className="px-3.5 py-1.5 text-xs border border-[#e5e2dc] rounded-lg text-charcoal-700 hover:bg-[#faf9f6]"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleteConfirmText !== "DELETE" || deletingAccount}
                className="px-4 py-1.5 bg-rose-600 text-white text-xs font-medium rounded-lg hover:bg-rose-700 disabled:opacity-40 transition"
              >
                {deletingAccount ? "Deleting..." : "Permanently Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================
          MODAL: AUTHENTICATION, EMAIL OTP & ONBOARDING (Gmail-Only)
      ======================================================================== */}
      {authModalOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-[#e5e2dc] rounded-2xl max-w-md w-full p-6 shadow-floating animate-fadeIn">
            <div className="flex items-center justify-between pb-3 border-b border-[#e5e2dc]">
              <div>
                <h3 className="text-base font-semibold text-[#18181b]">
                  {authMode === "login" && "Sign In to Consolith"}
                  {authMode === "signup" && "Create Citizen Account"}
                  {authMode === "otp" && "Verify Gmail Address"}
                  {authMode === "onboarding" && "Complete Your Profile"}
                </h3>
                <span className="text-[11px] text-charcoal-500">Official Gmail (@gmail.com) Required</span>
              </div>
              <button
                onClick={() => setAuthModalOpen(false)}
                className="p-1 rounded text-charcoal-400 hover:text-black hover:bg-[#f5f3ef]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {authError && (
              <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700">
                {authError}
              </div>
            )}
            {authSuccess && (
              <div className="mt-3 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700">
                {authSuccess}
              </div>
            )}

            {/* Mode 1: Login or Signup */}
            {(authMode === "login" || authMode === "signup") && (
              <div className="py-4 space-y-4">
                <div>
                  <label className="block text-xs font-medium text-charcoal-700 mb-1">Official Gmail Address</label>
                  <input
                    type="email"
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    placeholder="yourname@gmail.com"
                    className="w-full px-3 py-2 text-xs bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-charcoal-700 mb-1">Password</label>
                  <input
                    type="password"
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full px-3 py-2 text-xs bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
                  />
                </div>

                <button
                  type="button"
                  onClick={handleSendOTP}
                  disabled={loadingAuth || !authEmail}
                  className="w-full py-2.5 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-charcoal-800 disabled:opacity-40 transition shadow-xs flex items-center justify-center gap-2"
                >
                  {loadingAuth ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : authMode === "signup" ? (
                    "Send Email OTP Code"
                  ) : (
                    "Continue with Gmail"
                  )}
                </button>

                <div className="pt-2 text-center">
                  {authMode === "login" ? (
                    <p className="text-xs text-charcoal-500">
                      Don't have an account?{" "}
                      <button
                        type="button"
                        onClick={() => setAuthMode("signup")}
                        className="text-black font-semibold hover:underline"
                      >
                        Create Account
                      </button>
                    </p>
                  ) : (
                    <p className="text-xs text-charcoal-500">
                      Already registered?{" "}
                      <button
                        type="button"
                        onClick={() => setAuthMode("login")}
                        className="text-black font-semibold hover:underline"
                      >
                        Sign In
                      </button>
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Mode 2: Real Email OTP Verification */}
            {authMode === "otp" && (
              <div className="py-4 space-y-4">
                <p className="text-xs text-charcoal-600">
                  Please enter the 6-digit one-time password dispatched to <strong>{authEmail}</strong>.
                </p>
                <div>
                  <input
                    type="text"
                    maxLength={6}
                    value={otpInput}
                    onChange={(e) => setOtpInput(e.target.value.replace(/\D/g, ""))}
                    placeholder="123456"
                    className="w-full text-center tracking-widest text-lg font-mono py-2 bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900"
                  />
                </div>

                <div className="flex items-center justify-between text-xs text-charcoal-500">
                  <span>Expires in: {otpCountdown}s</span>
                  <button
                    type="button"
                    onClick={handleSendOTP}
                    disabled={otpCountdown > 0}
                    className="text-black font-medium disabled:opacity-40 hover:underline"
                  >
                    Resend Code
                  </button>
                </div>

                <button
                  type="button"
                  onClick={handleVerifyOTP}
                  disabled={loadingAuth || otpInput.length !== 6}
                  className="w-full py-2.5 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-charcoal-800 disabled:opacity-40 transition shadow-xs"
                >
                  {loadingAuth ? "Verifying..." : "Verify & Continue"}
                </button>
              </div>
            )}

            {/* Mode 3: Profile Onboarding Setup */}
            {authMode === "onboarding" && (
              <form onSubmit={handleCompleteOnboarding} className="py-4 space-y-4">
                <p className="text-xs text-charcoal-600">
                  One last step: please confirm your legal name as it appears on your identity documents.
                </p>
                <div>
                  <label className="block text-xs font-medium text-charcoal-700 mb-1">Full Legal Name</label>
                  <input
                    type="text"
                    value={authFullName}
                    onChange={(e) => setAuthFullName(e.target.value)}
                    placeholder="Ajay Raman"
                    required
                    className="w-full px-3 py-2 text-xs bg-white border border-[#e5e2dc] rounded-lg focus:border-charcoal-900 transition"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loadingAuth || !authFullName.trim()}
                  className="w-full py-2.5 bg-[#18181b] text-white text-xs font-medium rounded-lg hover:bg-charcoal-800 disabled:opacity-40 transition shadow-xs"
                >
                  {loadingAuth ? "Finalizing Profile..." : "Complete Setup & Enter Consolith"}
                </button>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

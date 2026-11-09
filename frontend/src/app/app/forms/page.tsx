"use client";

import React, { useState, useEffect, useMemo, useCallback } from "react";
import Link from "next/link";
import {
  Search,
  Download,
  ExternalLink,
  FileText,
  ChevronRight,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Clock,
  Sparkles,
  ArrowRight,
  Building2,
  Shield,
  HelpCircle,
  BookOpen,
  Info,
} from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import {
  fetchRepositoryResources,
  fetchPersonalizedGuidance,
  RepositoryResourceItem,
  PersonalizedGuidanceItem,
} from "../../../lib/api";

const CATEGORIES = [
  { id: "all", label: "All Documents" },
  { id: "aadhaar", label: "Aadhaar Card" },
  { id: "pan", label: "PAN Card" },
  { id: "passport", label: "Passport" },
  { id: "class_10", label: "Class 10 Certificate" },
  { id: "class_12", label: "Class 12 Certificate" },
  { id: "epf", label: "EPF/UAN Records" },
];

const DOCUMENT_TYPES = [
  { id: "all", label: "All Types" },
  { id: "application_form", label: "Application Forms" },
  { id: "proof_matrix", label: "Proof Matrices" },
  { id: "correction_procedure", label: "Correction SOPs" },
  { id: "alternative_evidence", label: "Alternative Evidence" },
  { id: "reference_circular", label: "Reference Circulars" },
];

const PROVENANCE_FILTERS = [
  { id: "all", label: "All Provenance" },
  { id: "OFFICIAL_ORIGINAL", label: "Official Original" },
  { id: "GOVERNMENT_REFERENCE", label: "Government Reference" },
  { id: "HISTORICAL_REFERENCE", label: "Historical Reference" },
  { id: "SYNTHETIC_DEVELOPMENT_SAMPLE", label: "Synthetic Sample" },
];

export default function FormsRepositoryPage() {
  const { idToken } = useAuth();

  const [resources, setResources] = useState<RepositoryResourceItem[]>([]);
  const [totalResources, setTotalResources] = useState(0);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [selectedDocType, setSelectedDocType] = useState("all");
  const [selectedProvenance, setSelectedProvenance] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Personalized Guidance (Discrepancy linkage)
  const [personalizedItems, setPersonalizedItems] = useState<PersonalizedGuidanceItem[]>([]);
  const [personalizedLoading, setPersonalizedLoading] = useState(false);

  const loadResources = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchRepositoryResources(idToken, {
        category: selectedCategory === "all" ? undefined : selectedCategory,
        document_type: selectedDocType === "all" ? undefined : selectedDocType,
        provenance: selectedProvenance === "all" ? undefined : selectedProvenance,
        search: searchQuery.trim() || undefined,
        page: currentPage,
        page_size: 12,
      });
      setResources(data.resources || []);
      setTotalResources(data.total || 0);
      setTotalPages(data.total_pages || 1);
    } catch (err: any) {
      console.warn("Could not load repository resources:", err);
      setResources([]);
      setTotalResources(0);
    } finally {
      setLoading(false);
    }
  }, [idToken, selectedCategory, selectedDocType, selectedProvenance, searchQuery, currentPage]);

  const loadPersonalizedAlerts = useCallback(async () => {
    if (!idToken) return;
    try {
      setPersonalizedLoading(true);
      const res = await fetchPersonalizedGuidance(idToken);
      if (res && res.items) {
        setPersonalizedItems(res.items);
      }
    } catch (err) {
      // Non-blocking for unauthenticated or non-conflicted users
      setPersonalizedItems([]);
    } finally {
      setPersonalizedLoading(false);
    }
  }, [idToken]);

  useEffect(() => {
    loadResources();
  }, [loadResources]);

  useEffect(() => {
    loadPersonalizedAlerts();
  }, [loadPersonalizedAlerts]);

  // Reset page when filters change
  const handleCategoryChange = (catId: string) => {
    setSelectedCategory(catId);
    setCurrentPage(1);
  };

  const handleDocTypeChange = (typeId: string) => {
    setSelectedDocType(typeId);
    setCurrentPage(1);
  };

  const handleProvenanceChange = (provId: string) => {
    setSelectedProvenance(provId);
    setCurrentPage(1);
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setCurrentPage(1);
    loadResources();
  };

  return (
    <div className="max-w-6xl mx-auto w-full py-10 px-4 sm:px-6 lg:px-8 pb-32">
      {/* Editorial Page Header */}
      <header className="space-y-3 border-b border-[#E7E5E0] pb-6 mb-8">
        <div className="flex items-center gap-2">
          <span className="font-sans text-[11px] uppercase tracking-wider text-[#777777] font-medium">
            Citizen Document Repository
          </span>
          <span className="text-[#CCCCCC]">•</span>
          <span className="font-sans text-[11px] text-[#777777]">
            Official Government Formats & Circulars
          </span>
        </div>
        <h1 className="font-serif text-3xl sm:text-4xl text-[#111111] font-light tracking-tight">
          Document Repository & Correction Guidance
        </h1>
        <p className="font-sans text-sm text-[#5E5E5E] max-w-3xl leading-relaxed">
          Explore official application forms, proof matrices, and authoritative procedural circulars across the 6 supported identity categories. Every document maintains verifiable cryptographic provenance and explicit statutory limitations.
        </p>
      </header>

      {/* Personalized Discrepancy Guidance Banner (Module 5 Linkage) */}
      {personalizedItems.length > 0 && (
        <section className="mb-8 p-5 bg-[#FBF9F4] border border-[#E4D9C7] rounded-[6px] space-y-3">
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 bg-[#8C5E28] text-white text-[10px] font-mono uppercase tracking-wider rounded-[3px]">
                  Detected Discrepancy
                </span>
                <span className="text-xs font-sans text-[#7A5826] font-medium">
                  Personalized Citizen Guidance Available
                </span>
              </div>
              <p className="font-sans text-sm text-[#3E3424] leading-relaxed">
                {personalizedItems[0].explanation}
              </p>
            </div>
            <Link
              href={`/app/assistant?initial_prompt=${encodeURIComponent(personalizedItems[0].assistant_prompt_context)}`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#111111] hover:bg-[#2A2A2A] text-white text-xs font-sans font-medium rounded-[4px] shrink-0 transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5 text-[#C96442]" />
              <span>Resolve with AI</span>
            </Link>
          </div>
          <div className="pt-2 border-t border-[#ECE3D5] flex items-center justify-between text-[11px] text-[#84735E]">
            <span>Recommended Procedure: <strong>{personalizedItems[0].recommended_procedure}</strong></span>
            <span className="font-mono text-[10px] uppercase">
              {personalizedItems[0].disclaimer}
            </span>
          </div>
        </section>
      )}

      {/* Search & Navigation Controls */}
      <section className="space-y-5 mb-8">
        {/* Search Bar */}
        <form onSubmit={handleSearchSubmit} className="relative w-full">
          <Search className="w-4 h-4 text-[#777777] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by document ID (e.g. DOC_001), title, issuing authority, or purpose..."
            className="w-full pl-10 pr-24 py-2.5 bg-white border border-[#E7E5E0] rounded-[4px] text-sm text-[#111111] placeholder:text-[#999999] focus:outline-none focus:border-[#111111] transition-colors font-sans"
          />
          <button
            type="submit"
            className="absolute right-1.5 top-1/2 -translate-y-1/2 px-3 py-1.5 bg-[#F4F3EF] hover:bg-[#EBE9E4] text-[#111111] text-xs font-sans font-medium rounded-[3px] transition-colors"
          >
            Search
          </button>
        </form>

        {/* Primary Category Tabs (6 Supported Identity Categories) */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-sans uppercase tracking-wider text-[#777777] font-medium">
            Identity Category
          </label>
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 border-b border-[#E7E5E0]">
            {CATEGORIES.map((cat) => {
              const isActive = selectedCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  onClick={() => handleCategoryChange(cat.id)}
                  className={`px-3 py-1.5 text-xs font-sans rounded-[4px] whitespace-nowrap transition-colors ${
                    isActive
                      ? "bg-[#111111] text-white font-medium"
                      : "text-[#5E5E5E] hover:text-[#111111] hover:bg-[#F4F3EF]"
                  }`}
                >
                  {cat.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Secondary Filter Chips: Document Type & Provenance */}
        <div className="flex items-center gap-4 flex-wrap text-xs font-sans text-[#5E5E5E]">
          <div className="flex items-center gap-2">
            <span className="text-[11px] uppercase tracking-wider text-[#777777]">Type:</span>
            <select
              value={selectedDocType}
              onChange={(e) => handleDocTypeChange(e.target.value)}
              className="px-2.5 py-1 bg-white border border-[#E7E5E0] rounded-[3px] text-xs text-[#111111] focus:outline-none"
            >
              {DOCUMENT_TYPES.map((dt) => (
                <option key={dt.id} value={dt.id}>{dt.label}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] uppercase tracking-wider text-[#777777]">Provenance:</span>
            <select
              value={selectedProvenance}
              onChange={(e) => handleProvenanceChange(e.target.value)}
              className="px-2.5 py-1 bg-white border border-[#E7E5E0] rounded-[3px] text-xs text-[#111111] focus:outline-none"
            >
              {PROVENANCE_FILTERS.map((pf) => (
                <option key={pf.id} value={pf.id}>{pf.label}</option>
              ))}
            </select>
          </div>

          <div className="ml-auto text-[11px] text-[#777777]">
            Showing <strong>{resources.length}</strong> of <strong>{totalResources}</strong> documents
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      {loading ? (
        <div className="py-20 text-center space-y-2">
          <div className="w-5 h-5 border-2 border-[#111111] border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs text-[#777777] font-sans">
            Loading authoritative document repository...
          </p>
        </div>
      ) : resources.length === 0 ? (
        <div className="p-12 bg-white border border-[#E7E5E0] rounded-[4px] text-center space-y-3">
          <FileText className="w-8 h-8 text-[#999999] mx-auto stroke-1" />
          <h2 className="font-serif text-lg text-[#111111]">No Documents Found</h2>
          <p className="font-sans text-xs text-[#777777] max-w-sm mx-auto">
            No official documents or forms matched your active filter criteria. If an official form is unavailable for this category, consult the relevant authority portal.
          </p>
          <button
            onClick={() => {
              setSelectedCategory("all");
              setSelectedDocType("all");
              setSelectedProvenance("all");
              setSearchQuery("");
            }}
            className="px-3.5 py-1.5 bg-[#F4F3EF] hover:bg-[#EBE9E4] text-[#111111] text-xs font-sans font-medium rounded-[3px] transition-colors"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Documents Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {resources.map((res) => {
              const isSynthetic = res.is_synthetic_sample || res.provenance === "SYNTHETIC_DEVELOPMENT_SAMPLE";
              const isHistorical = res.is_historical || res.provenance === "HISTORICAL_REFERENCE";
              const isConflict = res.has_source_conflict || res.verification_status === "source_metadata_conflict";

              return (
                <div
                  key={res.resource_id}
                  className="p-5 bg-white border border-[#E7E5E0] rounded-[6px] hover:border-[#CCCCCC] transition-all flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2.5">
                    {/* Top Badges */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="px-2 py-0.5 bg-[#111111] text-white font-mono text-[11px] font-bold tracking-wider rounded-[3px]">
                          {res.resource_id}
                        </span>

                        {/* Provenance Badge */}
                        {res.provenance === "OFFICIAL_ORIGINAL" && (
                          <span className="px-2 py-0.5 bg-[#E8F5E9] border border-[#C8E6C9] text-[#2E7D32] text-[10px] font-sans font-medium rounded-[2px]">
                            Official Original
                          </span>
                        )}
                        {res.provenance === "GOVERNMENT_REFERENCE" && (
                          <span className="px-2 py-0.5 bg-[#E3F2FD] border border-[#BBDEFB] text-[#1565C0] text-[10px] font-sans font-medium rounded-[2px]">
                            Gov Reference
                          </span>
                        )}
                        {isHistorical && (
                          <span className="px-2 py-0.5 bg-[#FFF3E0] border border-[#FFE0B2] text-[#E65100] text-[10px] font-sans font-medium rounded-[2px]">
                            Historical (Superseded)
                          </span>
                        )}
                        {isSynthetic && (
                          <span className="px-2 py-0.5 bg-[#FBE9E7] border border-[#FFCCBC] text-[#D84315] text-[10px] font-sans font-medium rounded-[2px]">
                            Synthetic Sample
                          </span>
                        )}

                        {/* Category Badge */}
                        <span className="px-1.5 py-0.5 bg-[#F4F3EF] text-[#5E5E5E] text-[10px] font-sans rounded-[2px] uppercase">
                          {res.document_category}
                        </span>
                      </div>

                      {/* Verification Status */}
                      {res.verification_status === "verified" && (
                        <div className="flex items-center gap-1 text-[11px] text-[#2E7D32]">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span className="font-sans font-medium">Verified</span>
                        </div>
                      )}
                      {isConflict && (
                        <div className="flex items-center gap-1 text-[11px] text-[#7B1FA2]">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span className="font-sans font-medium">Conflict</span>
                        </div>
                      )}
                      {res.verification_status === "needs_review" && (
                        <div className="flex items-center gap-1 text-[11px] text-[#E65100]">
                          <Clock className="w-3.5 h-3.5" />
                          <span className="font-sans font-medium">Needs Review</span>
                        </div>
                      )}
                    </div>

                    {/* Title */}
                    <h3 className="font-serif text-base text-[#111111] font-normal leading-snug">
                      <Link
                        href={`/app/forms/${res.resource_id}`}
                        className="hover:text-[#C96442] transition-colors"
                      >
                        {res.title}
                      </Link>
                    </h3>

                    {/* Authority */}
                    <p className="font-sans text-[11px] text-[#777777] flex items-center gap-1.5">
                      <Building2 className="w-3.5 h-3.5 text-[#999999]" />
                      <span>{res.issuing_authority}</span>
                    </p>

                    {/* Purpose / Description */}
                    <p className="font-sans text-xs text-[#5E5E5E] line-clamp-2 leading-relaxed">
                      {res.purpose || res.description}
                    </p>

                    {/* Prominent Disclaimers */}
                    {isSynthetic && (
                      <div className="p-2 bg-[#FFF8F6] border border-[#FFECE8] text-[10px] text-[#BA1A1A] font-sans font-medium rounded-[3px]">
                        SYNTHETIC DEVELOPMENT SAMPLE — NOT AN OFFICIAL GOVERNMENT FORM
                      </div>
                    )}
                    {isConflict && (
                      <div className="p-2 bg-[#FAF5FC] border border-[#E9D5F5] text-[10px] text-[#6A1B9A] font-sans rounded-[3px]">
                        STATUTORY LIMITATION: Unverified source metadata conflict. Claims regarding third-time exceptions cannot be represented as definitive law.
                      </div>
                    )}
                  </div>

                  {/* Actions Bar */}
                  <div className="pt-3 border-t border-[#E7E5E0] flex items-center justify-between gap-2">
                    <Link
                      href={`/app/forms/${res.resource_id}`}
                      className="inline-flex items-center gap-1 text-xs text-[#111111] hover:text-[#C96442] font-sans font-medium transition-colors"
                    >
                      <span>View Details & Checklist</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </Link>

                    <div className="flex items-center gap-1.5">
                      {res.download_available && (
                        <a
                          href={`http://localhost:8000/api/v1/repository/resources/${res.resource_id}/download`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-1.5 text-[#5E5E5E] hover:text-[#111111] hover:bg-[#F4F3EF] rounded-[3px] transition-colors"
                          title="Download PDF"
                        >
                          <Download className="w-4 h-4" />
                        </a>
                      )}
                      <Link
                        href={`/app/forms/${res.resource_id}`}
                        className="p-1.5 text-[#5E5E5E] hover:text-[#111111] hover:bg-[#F4F3EF] rounded-[3px] transition-colors"
                        title="Document Details"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div className="pt-6 border-t border-[#E7E5E0] flex items-center justify-between text-xs font-sans text-[#5E5E5E]">
              <div>
                Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
              </div>
              <div className="flex items-center gap-2">
                <button
                  disabled={currentPage <= 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  className="px-3 py-1.5 bg-white border border-[#E7E5E0] rounded-[3px] text-[#111111] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#F4F3EF] transition-colors"
                >
                  Previous
                </button>
                <button
                  disabled={currentPage >= totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  className="px-3 py-1.5 bg-white border border-[#E7E5E0] rounded-[3px] text-[#111111] disabled:opacity-40 disabled:cursor-not-allowed hover:bg-[#F4F3EF] transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

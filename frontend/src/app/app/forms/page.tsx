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
  ArrowRight,
  Building2,
  Shield,
} from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { fetchOfficialForms, OfficialFormItem } from "../../../lib/api";

const CATEGORIES = [
  { id: "all", label: "All Forms" },
  { id: "pan", label: "PAN" },
  { id: "epfo", label: "EPFO" },
  { id: "passport", label: "Passport" },
  { id: "aadhaar", label: "Aadhaar" },
  { id: "affidavit", label: "Affidavit" },
];

export default function FormsRepositoryPage() {
  const { idToken } = useAuth();

  const [forms, setForms] = useState<OfficialFormItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  const loadForms = useCallback(async () => {
    try {
      setLoading(true);
      const data = await fetchOfficialForms(idToken, {
        category: selectedCategory === "all" ? undefined : selectedCategory,
      });
      setForms(data);
    } catch (err: any) {
      console.warn("Could not load forms from backend:", err);
      setForms([]);
    } finally {
      setLoading(false);
    }
  }, [idToken, selectedCategory]);

  useEffect(() => {
    loadForms();
  }, [loadForms]);

  // Client-side search filtering over title, code, purpose, authority
  const filteredForms = useMemo(() => {
    if (!searchQuery.trim()) return forms;
    const q = searchQuery.toLowerCase();
    return forms.filter(
      (f) =>
        f.form_name?.toLowerCase().includes(q) ||
        f.form_code?.toLowerCase().includes(q) ||
        f.form_id?.toLowerCase().includes(q) ||
        f.issuing_authority?.toLowerCase().includes(q) ||
        f.purpose_description?.toLowerCase().includes(q)
    );
  }, [forms, searchQuery]);

  return (
    <div className="max-w-5xl mx-auto w-full py-10 px-4 sm:px-6 lg:px-8 pb-32">
      {/* Editorial Page Header */}
      <header className="space-y-2 border-b border-[#E7E5E0] pb-6 mb-8">
        <div className="flex items-center gap-2">
          <span className="font-sans text-[11px] uppercase tracking-wider text-[#777777] font-medium">
            Statutory Catalog
          </span>
          <span className="text-[#CCCCCC]">•</span>
          <span className="font-sans text-[11px] text-[#777777]">
            Official Government Formats
          </span>
        </div>
        <h1 className="font-serif text-3xl sm:text-4xl text-[#111111] font-light tracking-tight">
          Forms Repository
        </h1>
        <p className="font-sans text-sm text-[#5E5E5E] max-w-2xl leading-relaxed">
          Find verified statutory correction forms, examine prerequisite identity proofs, and download official formats directly.
        </p>
      </header>

      {/* Search & Navigation Controls */}
      <section className="space-y-4 mb-8">
        {/* Search Bar */}
        <div className="relative w-full">
          <Search className="w-4 h-4 text-[#777777] absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by form number, title, authority, or purpose..."
            className="w-full h-11 pl-10 pr-4 bg-white border border-[#E7E5E0] rounded-[4px] font-sans text-sm text-[#111111] placeholder:text-[#999999] focus:outline-none focus:border-[#111111] transition-colors"
          />
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-6 overflow-x-auto border-b border-[#E7E5E0] pb-1 scrollbar-none">
          {CATEGORIES.map((cat) => {
            const active = selectedCategory === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`py-2 text-xs font-sans transition-colors whitespace-nowrap border-b-2 ${
                  active
                    ? "border-[#111111] text-[#111111] font-semibold"
                    : "border-transparent text-[#777777] hover:text-[#111111]"
                }`}
              >
                {cat.label}
              </button>
            );
          })}
        </div>
      </section>

      {/* Editorial List of Forms */}
      <section className="divide-y divide-[#E7E5E0]">
        {loading ? (
          <div className="py-12 text-center text-xs text-[#777777] font-sans">
            Loading verified statutory forms...
          </div>
        ) : filteredForms.length > 0 ? (
          filteredForms.map((form) => {
            const formCode = form.form_code || form.form_id.toUpperCase();
            return (
              <article
                key={form.id || form.form_id}
                className="py-6 flex flex-col md:flex-row md:items-start justify-between gap-6 transition-colors hover:bg-white px-3 -mx-3 rounded-[4px] group"
              >
                {/* Form Meta & Description */}
                <div className="space-y-2 flex-1 min-w-0">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="inline-block px-2 py-0.5 bg-[#111111] text-white font-mono text-[11px] font-bold tracking-wide rounded-[4px]">
                      {formCode}
                    </span>
                    <h2 className="font-sans font-semibold text-[#111111] text-base group-hover:underline underline-offset-2">
                      {form.form_name}
                    </h2>
                  </div>

                  <p className="text-xs text-[#5E5E5E] font-sans font-medium flex items-center gap-1.5">
                    <Building2 className="w-3.5 h-3.5 text-[#777777]" />
                    <span>{form.issuing_authority}</span>
                  </p>

                  <p className="text-xs text-[#1A1C1A] font-sans leading-relaxed max-w-2xl">
                    {form.purpose || form.purpose_description}
                  </p>

                  {((form.applicable_conditions && form.applicable_conditions.length > 0) ||
                    (form.prerequisites && form.prerequisites.length > 0)) && (
                    <div className="text-[11px] text-[#777777] font-sans pt-1 flex items-center gap-1.5 flex-wrap">
                      <span className="font-medium text-[#111111]">Applicable Conditions:</span>
                      <span>{(form.applicable_conditions || form.prerequisites || []).join(" • ")}</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-3 shrink-0 pt-1 md:pt-0">
                  <Link
                    href={`/app/forms/${form.form_id}`}
                    className="text-xs font-sans font-medium text-[#111111] hover:underline py-1.5 px-2 flex items-center gap-1"
                  >
                    <span>View Details</span>
                    <ArrowRight className="w-3.5 h-3.5 text-[#777777]" />
                  </Link>

                  {(form.official_download_url || form.download_url) ? (
                    <a
                      href={form.official_download_url || form.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="h-8 px-3.5 rounded-[4px] bg-[#111111] hover:bg-black/90 text-white font-sans text-xs font-medium transition-colors flex items-center gap-1.5 shrink-0"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
                    </a>
                  ) : form.official_portal_url ? (
                    <a
                      href={form.official_portal_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="h-8 px-3.5 rounded-[4px] bg-white border border-[#E7E5E0] hover:bg-[#F4F3EF] text-[#111111] font-sans text-xs font-medium transition-colors flex items-center gap-1.5 shrink-0"
                    >
                      <ExternalLink className="w-3.5 h-3.5 text-[#777777]" />
                      <span>Portal</span>
                    </a>
                  ) : null}
                </div>
              </article>
            );
          })
        ) : (
          <div className="p-8 bg-white border border-[#E7E5E0] rounded-[4px] text-center space-y-2">
            <div className="w-8 h-8 rounded-full bg-[#FAF9F6] border border-[#E7E5E0] flex items-center justify-center text-[#777777] mx-auto mb-2">
              <FileText className="w-4 h-4" />
            </div>
            <h4 className="font-sans text-sm font-medium text-[#111111]">
              No matching forms found
            </h4>
            <p className="font-sans text-xs text-[#777777] max-w-sm mx-auto leading-relaxed">
              No statutory forms match "{searchQuery}" in the selected category. Try searching by form code (e.g. "49A") or authority name.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}


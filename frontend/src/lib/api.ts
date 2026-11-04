/**
 * CONVELINA Citizen API Client
 * Clean, production-grade interface to FastAPI backend endpoints.
 * Strictly uses real authenticated JWT Bearer tokens and handles error states.
 */

export const getApiUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
};

export const getAuthHeaders = (token?: string | null): Record<string, string> => {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
};

// ==============================================================================
// Types
// ==============================================================================

export interface DocumentItem {
  id: string;
  user_id?: string;
  document_type: string;
  file_hash: string;
  ocr_status: string;
  masked_id?: string | null;
  extracted_fields?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface ConflictItem {
  id: string;
  user_id?: string;
  doc_a_id: string;
  doc_b_id: string;
  conflict_type: string;
  severity: "high" | "medium" | "low" | string;
  field_name: string;
  value_a: string;
  value_b: string;
  description: string;
  status: string;
  comparison_method?: string;
  similarity_score?: number | null;
  created_at: string;
  updated_at?: string;
}

export interface CorrectionDraftItem {
  id: string;
  user_id: string;
  conflict_id: string;
  document_type: string;
  document_category: string;
  status: string;
  title: string;
  content: string;
  confirmed_fields: Record<string, any>;
  source_references?: Array<Record<string, any>>;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface OfficialFormItem {
  id: string;
  form_id: string;
  form_name: string;
  form_code?: string;
  issuing_authority: string;
  document_category: string;
  purpose?: string;
  purpose_description?: string;
  statutory_authority?: string;
  applicable_issue_types?: string[];
  applicable_conditions?: string[];
  prerequisites?: string[];
  submission_instructions?: string;
  official_portal_url?: string;
  official_download_url?: string;
  download_url?: string;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ConversationItem {
  id: string;
  title: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface MappedFormRef {
  form_id: string;
  form_name: string;
  issuing_authority: string;
  official_download_url: string;
  purpose: string;
}

export interface ResolutionProcedureMapping {
  target_document_category: string;
  authority_name: string;
  authority_portal: string;
  procedure_name: string;
  procedure_type: string;
  prescribed_forms: MappedFormRef[];
  document_checklist: string[];
  submission_channel: string;
  statutory_rules: string[];
  official_fee_guidance?: string | null;
  sla_guidance?: string | null;
  action_priority: string;
}

export interface ResolutionContextData {
  conflict_id: string;
  user_id: string;
  field_name: string;
  conflict_type: string;
  severity: string;
  status: string;
  document_types: string[];
  document_ids: string[];
  value_a: string;
  value_b: string;
  deterministic_classification: string;
  overall_classification: string;
  confidence_score: number;
  requires_manual_review: boolean;
  possible_causes: string[];
  recommended_action?: string | null;
  evidence: string[];
  ocr_quality_warning?: string | null;
  non_latin_warning?: string | null;
  statutory_disclaimer: string;
  resolution_mapping?: ResolutionProcedureMapping | null;
}


export interface MessageItem {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  structured_response?: {
    answer?: string;
    issue_summary?: string;
    resolution_steps?: Array<{
      step_number: number;
      title: string;
      description: string;
      required_documents?: string[];
      official_portal_or_form?: string;
    }>;
    relevant_forms?: Array<{
      form_id: string;
      form_name: string;
      issuing_authority: string;
      official_download_url?: string;
      purpose?: string;
      document_category?: string;
    }>;
    potential_future_implications?: Array<{
      area: string;
      risk_assessment: string;
      explanation: string;
      suggested_action: string;
    }>;
    uncertainties?: string[];
    citations?: Array<{
      source_id: string;
      title: string;
      authority: string;
      url: string;
      section?: string;
      verification_status?: string;
    }>;
    requires_clarification?: boolean;
    confidence?: string;
    is_fallback?: boolean;
    provider_status?: string;
  };
  citations?: Array<{
    source_id: string;
    title: string;
    authority: string;
    url: string;
    section?: string;
    verification_status?: string;
  }>;
  grounded_sources?: Array<{
    title: string;
    authority: string;
    citation: string;
    relevance_score?: number;
  }>;
  recommended_forms?: Array<{
    form_id: string;
    form_name: string;
    issuing_authority: string;
    download_url?: string;
  }>;
  statutory_warning?: string;
  created_at: string;
}

export interface ActivityItem {
  id: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  details?: Record<string, any>;
  created_at: string;
}

// ==============================================================================
// Documents API
// ==============================================================================

export async function fetchDocuments(token: string | null): Promise<DocumentItem[]> {
  const url = `${getApiUrl()}/api/v1/documents`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    throw new Error(`Failed to load documents: HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.documents || [];
}

export async function uploadDocument(
  token: string | null,
  documentType: string,
  file: File
): Promise<any> {
  const url = `${getApiUrl()}/api/v1/documents/upload`;
  const formData = new FormData();
  formData.append("document_type", documentType);
  formData.append("file", file);

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method: "POST",
    headers,
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed: HTTP ${res.status}`);
  }

  return await res.json();
}

export async function deleteDocument(token: string | null, documentId: string): Promise<void> {
  const url = `${getApiUrl()}/api/v1/documents/${documentId}`;
  const res = await fetch(url, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to delete document: HTTP ${res.status}`);
  }
}

export async function updateDocumentFields(
  token: string | null,
  documentId: string,
  extractedFields: Record<string, any>
): Promise<DocumentItem> {
  const url = `${getApiUrl()}/api/v1/documents/${documentId}/fields`;
  const res = await fetch(url, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ extracted_fields: extractedFields }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update document fields: HTTP ${res.status}`);
  }
  return await res.json();
}

// ==============================================================================
// Conflicts API
// ==============================================================================

export async function fetchConflicts(token: string | null): Promise<ConflictItem[]> {
  const url = `${getApiUrl()}/api/v1/conflicts`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    throw new Error(`Failed to load conflicts: HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.conflicts || [];
}

export async function detectConflicts(token: string | null): Promise<{ detected_conflicts_count: number; conflicts: ConflictItem[] }> {
  const url = `${getApiUrl()}/api/v1/conflicts/detect`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Conflict detection failed: HTTP ${res.status}`);
  }
  return await res.json();
}

export interface DocumentCompareFieldResult {
  field_name: string;
  value_a_raw?: string;
  value_b_raw?: string;
  value_a_normalized?: string;
  value_b_normalized?: string;
  classification: string;
  similarity_score: number;
  confidence_score: number;
  is_conflict: boolean;
  severity: string;
  requires_manual_review: boolean;
  explanation: string;
  possible_causes: string[];
  recommended_action: string;
}

export interface DocumentMetadataSummary {
  id: string;
  document_type: string;
  masked_id?: string;
  ocr_status: string;
  created_at: string;
}

export interface DocumentCompareResponse {
  overall_classification: string;
  confidence_score: number;
  requires_manual_review: boolean;
  action_recommended: boolean;
  matched_fields: string[];
  conflicting_fields: string[];
  ambiguous_fields: string[];
  field_results: Record<string, DocumentCompareFieldResult>;
  evidence: string[];
  explanation: string;
  warnings: string[];
  documents_compared: DocumentMetadataSummary[];
  discrepancies_count: number;
  conflicts_created: number;
  disclaimer: string;
}

export async function compareDocuments(
  token: string | null,
  documentIds: string[]
): Promise<DocumentCompareResponse> {
  const url = `${getApiUrl()}/api/v1/conflicts/compare`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ document_ids: documentIds }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Document comparison failed: HTTP ${res.status}`);
  }
  return await res.json();
}

// ==============================================================================
// Correction Drafts API (Module 7)
// ==============================================================================

export async function fetchCorrectionDrafts(token: string | null): Promise<CorrectionDraftItem[]> {
  const url = `${getApiUrl()}/api/v1/correction-drafts`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    throw new Error(`Failed to load correction drafts: HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.items || [];
}

export async function createCorrectionDraft(
  token: string | null,
  params: {
    conflict_id: string;
    document_type?: string;
    document_category?: string;
    confirmed_fields?: Record<string, any>;
  }
): Promise<CorrectionDraftItem> {
  const url = `${getApiUrl()}/api/v1/correction-drafts`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      conflict_id: params.conflict_id,
      document_type: params.document_type || "formal_representation",
      document_category: params.document_category || "general",
      confirmed_fields: params.confirmed_fields || {},
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to generate correction draft: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function fetchCorrectionDraft(token: string | null, draftId: string): Promise<CorrectionDraftItem> {
  const url = `${getApiUrl()}/api/v1/correction-drafts/${draftId}`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    throw new Error(`Failed to load correction draft: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function updateCorrectionDraft(
  token: string | null,
  draftId: string,
  params: {
    title?: string;
    content?: string;
    status?: string;
    confirmed_fields?: Record<string, any>;
  }
): Promise<CorrectionDraftItem> {
  const url = `${getApiUrl()}/api/v1/correction-drafts/${draftId}`;
  const res = await fetch(url, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update correction draft: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function deleteCorrectionDraft(token: string | null, draftId: string): Promise<void> {
  const url = `${getApiUrl()}/api/v1/correction-drafts/${draftId}`;
  const res = await fetch(url, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to delete correction draft: HTTP ${res.status}`);
  }
}

export async function downloadCorrectionDraft(
  token: string | null,
  draftId: string,
  format: "pdf" | "docx" = "pdf"
): Promise<Blob> {
  const url = `${getApiUrl()}/api/v1/correction-drafts/${draftId}/download?format=${format}`;
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(url, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to download draft: HTTP ${res.status}`);
  }
  return await res.blob();
}

// ==============================================================================
// Assistant API
// ==============================================================================

export async function fetchConversations(token: string | null): Promise<ConversationItem[]> {
  const url = `${getApiUrl()}/api/v1/assistant/conversations`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    throw new Error(`Failed to load conversations: HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.conversations || [];
}

export async function fetchConversationMessages(token: string | null, conversationId: string): Promise<MessageItem[]> {
  const url = `${getApiUrl()}/api/v1/assistant/conversations/${conversationId}/messages`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    throw new Error(`Failed to load messages: HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.messages || [];
}

export async function fetchResolutionContext(
  token: string | null,
  conflictId: string
): Promise<ResolutionContextData> {
  const url = `${getApiUrl()}/api/v1/assistant/resolution-context/${conflictId}`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch resolution context: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function sendChatMessage(
  token: string | null,
  params: {
    message: string;
    conversation_id?: string;
    conflict_id?: string;
    document_category?: string;
  }
): Promise<{ conversation_id: string; message_id: string; response: any }> {
  const url = `${getApiUrl()}/api/v1/assistant/chat`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Assistant service is not currently available. Please try again later.");
  }

  return await res.json();
}

export async function deleteConversation(token: string | null, conversationId: string): Promise<void> {
  const url = `${getApiUrl()}/api/v1/assistant/conversations/${conversationId}`;
  const res = await fetch(url, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    throw new Error(`Failed to delete conversation: HTTP ${res.status}`);
  }
}

// ==============================================================================
// Official Forms API
// ==============================================================================

export async function fetchOfficialForms(
  token: string | null,
  params?: { category?: string; issue_type?: string }
): Promise<OfficialFormItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.category && params.category !== "all") {
    searchParams.append("category", params.category);
  }
  if (params?.issue_type) {
    searchParams.append("issue_type", params.issue_type);
  }

  const qs = searchParams.toString();
  const url = `${getApiUrl()}/api/v1/knowledge/forms${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    throw new Error(`Failed to load official forms: HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.forms || [];
}

export async function fetchOfficialFormById(token: string | null, formId: string): Promise<OfficialFormItem> {
  const url = `${getApiUrl()}/api/v1/knowledge/forms/${formId}`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    throw new Error(`Failed to load form details: HTTP ${res.status}`);
  }
  return await res.json();
}

// ==============================================================================
// User Activity & Profile API
// ==============================================================================

export async function fetchUserActivity(token: string | null): Promise<ActivityItem[]> {
  const url = `${getApiUrl()}/api/v1/auth/activity`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    // If activity endpoint returns 404 or empty, return empty list gracefully
    return [];
  }
  const data = await res.json();
  return data.activities || [];
}

export async function updateProfile(
  token: string | null,
  profileData: {
    full_name?: string;
    phone_number?: string;
    date_of_birth?: string;
    address?: string;
    father_name?: string;
    mother_name?: string;
  }
): Promise<any> {
  const url = `${getApiUrl()}/api/v1/auth/profile`;
  const res = await fetch(url, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(profileData),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update profile.");
  }
  return await res.json();
}

export async function deleteAccount(token: string | null): Promise<void> {
  const url = `${getApiUrl()}/api/v1/auth/account`;
  const res = await fetch(url, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to delete account.");
  }
}


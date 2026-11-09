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

export interface FieldExtractionDetail {
  field_name: string;
  raw_value?: string | null;
  normalized_value?: string | null;
  confidence: number;
  page_number: number;
  bounding_box?: Record<string, number> | null;
  validation_status: string;
  review_required: boolean;
  source_document_id?: string | null;
}

export interface DocumentItem {
  id: string;
  user_id?: string;
  document_type: string;
  file_hash: string;
  ocr_status: string;
  masked_id?: string | null;
  extracted_fields?: Record<string, any>;
  field_extractions?: Record<string, FieldExtractionDetail>;
  confirmed_fields?: Record<string, any>;
  is_user_confirmed?: boolean;
  confirmed_at?: string | null;
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
  metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface CorrectionDraftVersionItem {
  id: string;
  draft_id: string;
  version_number: number;
  content: string;
  change_type: string;
  recipient_authority?: string;
  subject?: string;
  confirmed_fields?: Record<string, any>;
  supporting_documents?: Array<Record<string, any>>;
  source_references?: Array<Record<string, any>>;
  is_citizen_confirmed: boolean;
  citizen_confirmed_at?: string | null;
  sha256_hash?: string | null;
  created_at: string;
}

export interface CorrectionDraftItem {
  id: string;
  user_id: string;
  conflict_id: string;
  document_type: string;
  document_category: string;
  status: "ai_generated" | "citizen_edited" | "citizen_confirmed" | string;
  title: string;
  content: string;
  recipient_authority?: string;
  subject?: string;
  user_explanation?: string;
  requested_action?: string;
  confirmed_fields: Record<string, any>;
  supporting_documents?: Array<{
    document_name: string;
    mandatory: boolean;
    purpose?: string;
    issuing_authority?: string;
  }>;
  disclaimer?: string;
  is_citizen_confirmed?: boolean;
  citizen_confirmed_at?: string | null;
  confirmed_version_number?: number | null;
  sha256_hash?: string | null;
  file_path?: string | null;
  language?: string;
  version: number;
  source_references?: Array<{
    source_id?: string;
    title: string;
    authority?: string;
    issuing_authority?: string;
    source_url?: string;
    verification_status?: string;
    relevance_score?: number;
    content?: string;
  }>;
  versions?: CorrectionDraftVersionItem[];
  validation_status?: {
    is_valid: boolean;
    unresolved_placeholders: string[];
    warnings: string[];
    has_disclaimer: boolean;
  };
  created_at: string;
  updated_at: string;
}

export const DRAFT_TYPE_LABELS: Record<string, string> = {
  identity_correction_request: "Identity Correction Request",
  name_change_representation: "Name Change Representation",
  dob_rectification_request: "Date of Birth Rectification Request",
  parent_name_rectification: "Parent Name Rectification Representation",
  address_update_application: "Address Update Application",
  educational_certificate_representation: "Educational Certificate Representation",
  epf_member_correction_request: "EPF Member Record Rectification Request",
  general_administrative_representation: "General Administrative Representation",
  supporting_document_cover_letter: "Supporting Document Cover Letter",
  statutory_petition_representation: "Statutory Petition Representation",
};

export const DRAFT_COMPATIBILITY_MATRIX: Record<string, string[]> = {
  aadhaar: [
    "identity_correction_request",
    "name_change_representation",
    "dob_rectification_request",
    "parent_name_rectification",
    "address_update_application",
    "general_administrative_representation",
    "supporting_document_cover_letter",
    "statutory_petition_representation",
  ],
  pan: [
    "identity_correction_request",
    "name_change_representation",
    "dob_rectification_request",
    "parent_name_rectification",
    "general_administrative_representation",
    "supporting_document_cover_letter",
    "statutory_petition_representation",
  ],
  passport: [
    "identity_correction_request",
    "name_change_representation",
    "dob_rectification_request",
    "parent_name_rectification",
    "address_update_application",
    "general_administrative_representation",
    "supporting_document_cover_letter",
    "statutory_petition_representation",
  ],
  education_10th: [
    "educational_certificate_representation",
    "name_change_representation",
    "dob_rectification_request",
    "parent_name_rectification",
    "general_administrative_representation",
    "supporting_document_cover_letter",
    "statutory_petition_representation",
  ],
  education_12th: [
    "educational_certificate_representation",
    "name_change_representation",
    "dob_rectification_request",
    "parent_name_rectification",
    "general_administrative_representation",
    "supporting_document_cover_letter",
    "statutory_petition_representation",
  ],
  epf: [
    "epf_member_correction_request",
    "name_change_representation",
    "dob_rectification_request",
    "parent_name_rectification",
    "general_administrative_representation",
    "supporting_document_cover_letter",
    "statutory_petition_representation",
  ],
};

export interface OfficialFormItem {
  id: string;
  form_id: string;
  form_name: string;
  form_code?: string;
  issuing_authority: string;
  document_category: string;
  purpose?: string;
  purpose_description?: string;
  description?: string;
  statutory_authority?: string;
  version?: string;
  verification_status?: string;
  provenance?: "OFFICIAL_ORIGINAL" | "OFFICIAL_COPY" | "APPLICATION_GENERATED" | "SYNTHETIC_TEST_ASSET" | "UNVERIFIED" | string;
  provenance_notes?: string;
  applicable_issue_types?: string[];
  applicable_conditions?: string[];
  prerequisites?: string[];
  submission_instructions?: string;
  official_portal_url?: string;
  official_download_url?: string;
  download_url?: string;
  storage_path?: string;
  file_size_bytes?: number;
  mime_type?: string;
  file_format?: string;
  sha256_hash?: string;
  is_official_government_form?: boolean;
  metadata_payload?: Record<string, any>;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ConversationItem {
  id: string;
  title: string;
  user_id: string;
  active_conflict_id?: string | null;
  is_pinned?: boolean;
  is_archived?: boolean;
  response_language?: string;
  message_count?: number;
  created_at: string;
  updated_at: string;
}

export interface MessageAttachmentItem {
  id: string;
  message_id?: string | null;
  conversation_id?: string | null;
  conflict_id?: string | null;
  file_name: string;
  mime_type: string;
  file_size_bytes: number;
  storage_ref?: string;
  sha256_hash?: string | null;
  extracted_text?: string | null;
  extracted_fields?: {
    document_type_indicator?: string;
    dates_found?: string[];
    rejection_reasons?: string[];
    masked_identifiers?: Record<string, string>;
    has_pii_redacted?: boolean;
    summary?: string;
    [key: string]: any;
  };
  ocr_confidence?: number | null;
  ocr_status?: "pending" | "completed" | "failed" | "low_confidence" | string;
  status?: "UPLOADED" | "VALIDATING" | "PROCESSING" | "READY" | "FAILED" | "EXPIRED" | "DELETED" | string;
  error_message?: string | null;
  is_temporary: boolean;
  expires_at?: string;
  created_at?: string;
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
  message_type?: string;
  attachments?: MessageAttachmentItem[];
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
    no_verified_form_available?: boolean;
    letter_draft?: string | boolean;
    correction_draft?: CorrectionDraftItem;
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

export async function confirmDocumentFields(
  token: string | null,
  documentId: string,
  confirmedFields: Record<string, any>
): Promise<DocumentItem> {
  const url = `${getApiUrl()}/api/v1/documents/${documentId}/confirm`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ confirmed_fields: confirmedFields }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to confirm document fields: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function fetchSyntheticSamples(): Promise<{
  samples: Array<{
    category: string;
    title: string;
    full_name?: string;
    provenance: string;
    formats: string[];
    disclaimer: string;
  }>;
}> {
  const url = `${getApiUrl()}/api/v1/documents/synthetic-samples`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to load synthetic development samples");
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
    user_explanation?: string;
    requested_action?: string;
    language?: string;
  }
): Promise<CorrectionDraftItem> {
  const url = `${getApiUrl()}/api/v1/correction-drafts`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      conflict_id: params.conflict_id,
      document_type: params.document_type || "identity_correction_request",
      document_category: params.document_category || "pan",
      confirmed_fields: params.confirmed_fields || {},
      user_explanation: params.user_explanation,
      requested_action: params.requested_action,
      language: params.language || "en",
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const msg = err.detail?.message || err.detail || `Failed to generate correction draft: HTTP ${res.status}`;
    throw new Error(msg);
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
    confirmed_fields?: Record<string, any>;
    recipient_authority?: string;
    subject?: string;
    user_explanation?: string;
    requested_action?: string;
  }
): Promise<CorrectionDraftItem> {
  const url = `${getApiUrl()}/api/v1/correction-drafts/${draftId}`;
  const res = await fetch(url, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || err.detail || `Failed to update correction draft: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function confirmCorrectionDraft(
  token: string | null,
  draftId: string,
  params: {
    confirmation_statement: string;
    version_number?: number;
    expected_sha256_hash?: string;
  }
): Promise<CorrectionDraftItem> {
  const url = `${getApiUrl()}/api/v1/correction-drafts/${draftId}/confirm`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || err.detail || `Failed to confirm correction draft: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function regenerateCorrectionDraft(
  token: string | null,
  draftId: string,
  params: {
    confirmed_fields?: Record<string, any>;
    user_explanation?: string;
    requested_action?: string;
    tone?: string;
  }
): Promise<CorrectionDraftItem> {
  const url = `${getApiUrl()}/api/v1/correction-drafts/${draftId}/regenerate`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || err.detail || `Failed to regenerate correction draft: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function translateCorrectionDraft(
  token: string | null,
  draftId: string,
  params: {
    target_language: string;
    bilingual?: boolean;
  }
): Promise<CorrectionDraftItem> {
  const url = `${getApiUrl()}/api/v1/correction-drafts/${draftId}/translate`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail?.message || err.detail || `Failed to translate correction draft: HTTP ${res.status}`);
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

export async function fetchConversations(
  token: string | null,
  options?: {
    conflict_id?: string;
    is_pinned?: boolean;
    is_archived?: boolean;
  }
): Promise<ConversationItem[]> {
  const params = new URLSearchParams();
  if (options?.conflict_id) params.append("conflict_id", options.conflict_id);
  if (options?.is_pinned !== undefined) params.append("is_pinned", String(options.is_pinned));
  if (options?.is_archived !== undefined) params.append("is_archived", String(options.is_archived));
  const qs = params.toString();
  const url = `${getApiUrl()}/api/v1/assistant/conversations${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    throw new Error(`Failed to load conversations: HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.conversations || [];
}

export async function createConversation(
  token: string | null,
  payload: {
    title?: string;
    active_case_id?: string;
    active_conflict_id?: string;
    response_language?: string;
  }
): Promise<ConversationItem> {
  const url = `${getApiUrl()}/api/v1/assistant/conversations`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to create conversation: HTTP ${res.status}`);
  }
  return await res.json();
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
    message_type?: string;
    language?: string;
    attachment_ids?: string[];
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

export async function uploadChatAttachment(
  token: string | null,
  file: File,
  conversationId?: string,
  conflictId?: string
): Promise<{ attachment: MessageAttachmentItem; message: string }> {
  const url = `${getApiUrl()}/api/v1/assistant/attachments/upload`;
  const formData = new FormData();
  formData.append("file", file);
  if (conversationId) formData.append("conversation_id", conversationId);
  if (conflictId) formData.append("conflict_id", conflictId);

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
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Attachment upload failed: HTTP ${res.status}`);
  }

  return await res.json();
}

export async function deleteChatAttachment(
  token: string | null,
  attachmentId: string
): Promise<void> {
  const url = `${getApiUrl()}/api/v1/assistant/attachments/${attachmentId}`;
  const res = await fetch(url, {
    method: "DELETE",
    headers: getAuthHeaders(token),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to delete attachment: HTTP ${res.status}`);
  }
}

export async function updateAttachmentConflict(
  token: string | null,
  attachmentId: string,
  conflictId?: string | null
): Promise<MessageAttachmentItem> {
  const url = `${getApiUrl()}/api/v1/assistant/attachments/${attachmentId}`;
  const res = await fetch(url, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify({ conflict_id: conflictId || null }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update attachment conflict: HTTP ${res.status}`);
  }

  return await res.json();
}

export async function previewChatAttachment(
  token: string | null,
  attachmentId: string
): Promise<Blob> {
  const url = `${getApiUrl()}/api/v1/assistant/attachments/${attachmentId}/preview`;
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(url, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to preview attachment: HTTP ${res.status}`);
  }
  return await res.blob();
}

export async function updateConversation(
  token: string | null,
  conversationId: string,
  payload: {
    title?: string;
    is_pinned?: boolean;
    is_archived?: boolean;
    response_language?: string;
    active_conflict_id?: string;
  }
): Promise<ConversationItem> {
  const url = `${getApiUrl()}/api/v1/assistant/conversations/${conversationId}`;
  const res = await fetch(url, {
    method: "PATCH",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update conversation: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function searchConversations(
  token: string | null,
  query: string
): Promise<{
  query: string;
  total: number;
  results: Array<{
    conversation: ConversationItem;
    matched_messages: MessageItem[];
  }>;
}> {
  const url = `${getApiUrl()}/api/v1/assistant/conversations/search?q=${encodeURIComponent(query)}`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to search conversations: HTTP ${res.status}`);
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

export async function downloadOfficialForm(
  token: string | null,
  formId: string,
  suggestedFilename?: string
): Promise<void> {
  const url = `${getApiUrl()}/api/v1/knowledge/forms/${formId}/download`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Download failed: HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const contentDisposition = res.headers.get("content-disposition");
  let filename = suggestedFilename || `official_form_${formId}.pdf`;
  if (contentDisposition) {
    const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?["']?([^"';]+)["']?/i);
    if (match && match[1]) {
      filename = decodeURIComponent(match[1]);
    }
  }
  const blobUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => window.URL.revokeObjectURL(blobUrl), 1000);
}

export async function previewOfficialForm(
  token: string | null,
  formId: string
): Promise<string> {
  const url = `${getApiUrl()}/api/v1/knowledge/forms/${formId}/preview`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Preview failed: HTTP ${res.status}`);
  }
  const blob = await res.blob();
  return window.URL.createObjectURL(blob);
}

// ------------------------------------------------------------------------------
// Admin Official Forms API
// ------------------------------------------------------------------------------

export async function fetchAdminOfficialForms(
  token: string | null,
  params?: { category?: string; status?: string }
): Promise<OfficialFormItem[]> {
  const searchParams = new URLSearchParams();
  if (params?.category) searchParams.append("category", params.category);
  if (params?.status) searchParams.append("status", params.status);
  const qs = searchParams.toString();
  const url = `${getApiUrl()}/api/v1/knowledge/admin/forms${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch admin forms: HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.forms || [];
}

export async function updateAdminOfficialFormVerification(
  token: string | null,
  formId: string,
  verificationStatus: string,
  notes?: string
): Promise<OfficialFormItem> {
  const url = `${getApiUrl()}/api/v1/knowledge/admin/forms/${formId}/verification`;
  const res = await fetch(url, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      verification_status: verificationStatus,
      verification_notes: notes,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to update form verification: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function fetchOfficialFormHistory(
  token: string | null,
  formId: string
): Promise<{
  form_id: string;
  current_version?: string;
  current_provenance?: string;
  current_verification_status?: string;
  total_versions: number;
  versions: Array<any>;
}> {
  const url = `${getApiUrl()}/api/v1/knowledge/admin/forms/${formId}/history`;
  const res = await fetch(url, { headers: getAuthHeaders(token) });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch form history: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function replaceOfficialForm(
  token: string | null,
  formId: string,
  formData: FormData
): Promise<OfficialFormItem> {
  const url = `${getApiUrl()}/api/v1/knowledge/admin/forms/${formId}/replace`;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to replace official form: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function verifyAndPublishOfficialForm(
  token: string | null,
  formId: string
): Promise<OfficialFormItem> {
  const url = `${getApiUrl()}/api/v1/knowledge/admin/forms/${formId}/verify-and-publish`;
  const res = await fetch(url, {
    method: "PUT",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to verify and publish form: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function ingestKnowledgeFile(
  token: string | null,
  formData: FormData
): Promise<any> {
  const url = `${getApiUrl()}/api/v1/knowledge/admin/sources/ingest-file`;
  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(url, {
    method: "POST",
    headers,
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to ingest knowledge file: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function syncAdminOfficialForms(
  token: string | null
): Promise<{ message: string; seeded_count: number }> {
  const url = `${getApiUrl()}/api/v1/knowledge/admin/forms/sync`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to sync forms catalog: HTTP ${res.status}`);
  }
  return await res.json();
}

export async function uploadAdminOfficialFormAsset(
  token: string | null,
  formId: string,
  file: File
): Promise<OfficialFormItem> {
  const url = `${getApiUrl()}/api/v1/knowledge/admin/forms/${formId}/upload`;
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token || ""}`,
    },
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Asset upload failed: HTTP ${res.status}`);
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

// ---------------------------------------------------------------------------
// P3H.6 Citizen Document Repository & Procedural Guidance API
// ---------------------------------------------------------------------------

export interface ChecklistItem {
  requirement_id: string;
  title: string;
  description: string;
  category: string;
  procedure_id: string;
  supporting_source_id: string;
  supporting_source_title: string;
  source_verification_state: string;
  status: "VERIFIED_MANDATORY" | "VERIFIED_CONDITIONAL" | "RECOMMENDED" | "HUMAN_REVIEW_REQUIRED";
  is_mandatory: boolean;
  explanation: string;
  source_citation: string;
  is_completed?: boolean;
}

export interface ChecklistResponse {
  procedure_id: string;
  procedure_title: string;
  category: string;
  total_items: number;
  mandatory_count: number;
  conditional_count: number;
  recommended_count: number;
  human_review_count: number;
  items: ChecklistItem[];
  disclaimer: string;
}

export interface RepositoryResourceItem {
  id: string;
  resource_id: string;
  title: string;
  issuing_authority: string;
  document_category: string;
  document_type: string;
  description: string;
  purpose: string;
  applicable_categories: string[];
  publication_date?: string | null;
  effective_date?: string | null;
  verification_status: "verified" | "needs_review" | "outdated" | "retired" | "source_metadata_conflict" | string;
  provenance: "OFFICIAL_ORIGINAL" | "OFFICIAL_COPY" | "GOVERNMENT_REFERENCE" | "HISTORICAL_REFERENCE" | "APPLICATION_GENERATED" | "SYNTHETIC_DEVELOPMENT_SAMPLE" | "UNVERIFIED_SOURCE" | string;
  provenance_notes?: string | null;
  is_official_government_form: boolean;
  is_synthetic_sample: boolean;
  is_historical: boolean;
  has_source_conflict: boolean;
  source_conflict_flag?: boolean;
  statutory_limitation_notice?: string | null;
  human_review_required: boolean;
  file_format: string;
  file_size_bytes: number;
  sha256_hash?: string | null;
  download_available: boolean;
  download_url?: string | null;
  preview_url?: string | null;
  related_procedures?: string[];
  disclaimer?: string | null;
}

export interface RepositoryResourceListResponse {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
  category_filter?: string | null;
  resources: RepositoryResourceItem[];
}

export interface RepositoryResourceDetail extends RepositoryResourceItem {
  intended_cohort: string;
  original_source_url?: string | null;
  key_information_required?: string[];
  referenced_laws?: string[];
  limitations_and_warnings?: string[];
  statutory_citations?: {
    source_id: string;
    title: string;
    authority: string;
    url: string;
    section?: string | null;
    verification_status: string;
  }[];
  supporting_document_checklist?: ChecklistItem[];
}

export interface ProceduralGuidanceStep {
  step_number: number;
  title: string;
  instruction: string;
  official_portal_or_form?: string | null;
  required_documents: string[];
}

export interface ProceduralGuidanceResponse {
  query: string;
  category: string;
  issue_summary: string;
  prescribed_procedure: string;
  steps: ProceduralGuidanceStep[];
  checklist: ChecklistItem[];
  relevant_resources: RepositoryResourceItem[];
  statutory_citations: any[];
  statutory_abstention: boolean;
  abstention_reason?: string | null;
  source_conflict_flag: boolean;
  human_review_required: boolean;
  limitations: string[];
  disclaimer: string;
}

export interface PersonalizedGuidanceItem {
  conflict_id: string;
  conflict_type: string;
  severity: string;
  field_name?: string | null;
  document_a_category: string;
  document_a_name: string;
  document_a_value?: string | null;
  document_b_category: string;
  document_b_name: string;
  document_b_value?: string | null;
  ocr_confidence?: number | null;
  review_warning?: string | null;
  explanation: string;
  recommended_procedure: string;
  applicable_resources: RepositoryResourceItem[];
  checklist: ChecklistItem[];
  assistant_prompt_context: string;
  disclaimer: string;
}

export interface PersonalizedGuidanceResponse {
  total_conflicts: number;
  items: PersonalizedGuidanceItem[];
  disclaimer: string;
}

export async function fetchRepositoryResources(
  token: string | null,
  params?: {
    category?: string;
    document_type?: string;
    provenance?: string;
    verification_status?: string;
    search?: string;
    sort_by?: string;
    page?: number;
    page_size?: number;
  }
): Promise<RepositoryResourceListResponse> {
  const query = new URLSearchParams();
  if (params?.category && params.category !== "all") query.set("category", params.category);
  if (params?.document_type && params.document_type !== "all") query.set("document_type", params.document_type);
  if (params?.provenance && params.provenance !== "all") query.set("provenance", params.provenance);
  if (params?.verification_status && params.verification_status !== "all") query.set("verification_status", params.verification_status);
  if (params?.search?.trim()) query.set("search", params.search.trim());
  if (params?.sort_by) query.set("sort_by", params.sort_by);
  if (params?.page) query.set("page", String(params.page));
  if (params?.page_size) query.set("page_size", String(params.page_size));

  const url = `${getApiUrl()}/api/v1/repository/resources${query.toString() ? `?${query.toString()}` : ""}`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch repository resources.");
  }
  return await res.json();
}

export async function fetchRepositoryResourceDetail(
  token: string | null,
  resourceId: string
): Promise<RepositoryResourceDetail> {
  const url = `${getApiUrl()}/api/v1/repository/resources/${encodeURIComponent(resourceId)}`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch resource '${resourceId}'.`);
  }
  return await res.json();
}

export async function fetchCategoriesSummary(
  token: string | null
): Promise<Record<string, any>> {
  const url = `${getApiUrl()}/api/v1/repository/categories`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    throw new Error("Failed to fetch repository categories summary.");
  }
  return await res.json();
}

export async function fetchProcedureChecklist(
  token: string | null,
  procedureId: string
): Promise<ChecklistResponse> {
  const url = `${getApiUrl()}/api/v1/repository/checklists/${encodeURIComponent(procedureId)}`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Failed to fetch checklist for '${procedureId}'.`);
  }
  return await res.json();
}

export async function synthesizeProceduralGuidance(
  token: string | null,
  payload: {
    query: string;
    category?: string;
    conflict_id?: string;
    cohort?: string;
  }
): Promise<ProceduralGuidanceResponse> {
  const url = `${getApiUrl()}/api/v1/repository/guidance/synthesize`;
  const res = await fetch(url, {
    method: "POST",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to synthesize procedural guidance.");
  }
  return await res.json();
}

export async function fetchPersonalizedGuidance(
  token: string | null
): Promise<PersonalizedGuidanceResponse> {
  const url = `${getApiUrl()}/api/v1/repository/guidance/personalized`;
  const res = await fetch(url, {
    method: "GET",
    headers: getAuthHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to fetch personalized guidance.");
  }
  return await res.json();
}

export async function adminVerifyRepositoryResource(
  token: string | null,
  resourceId: string,
  payload: {
    provenance: string;
    verification_status: string;
    provenance_evidence: string;
    review_notes?: string;
  }
): Promise<RepositoryResourceDetail> {
  const url = `${getApiUrl()}/api/v1/repository/admin/resources/${encodeURIComponent(resourceId)}/verify`;
  const res = await fetch(url, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update resource provenance verification.");
  }
  return await res.json();
}

export async function adminLifecycleRepositoryResource(
  token: string | null,
  resourceId: string,
  payload: {
    verification_status: string;
    reason: string;
  }
): Promise<RepositoryResourceDetail> {
  const url = `${getApiUrl()}/api/v1/repository/admin/resources/${encodeURIComponent(resourceId)}/lifecycle`;
  const res = await fetch(url, {
    method: "PUT",
    headers: getAuthHeaders(token),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to update resource lifecycle status.");
  }
  return await res.json();
}


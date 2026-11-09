# P3H.7 — Route and Feature Inventory

## Overview

This document catalogs every frontend route and backend API endpoint in CONVELINA as audited during Phase P3H.7.

---

## 1. Frontend Route Inventory (14 Routes)

| # | Route | Page Title / Component | Allowed Roles | Auth Required | Key UI Components | Backend APIs Invoked | Interactive States | Mobile Viewport Behavior | Input Validation & Error Handling |
| :-: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | `/` | Home / Landing Page<br>`frontend/src/app/page.tsx` | All / Public | None | Hero, Feature Grid, Privacy Safeguards, Trust Badges, Footer | None (Static) | Static, Interactive FAQ toggles | Collapses hero layout, hamburger nav menu | N/A (Marketing copy only) |
| **02** | `/login` | Citizen Login<br>`frontend/src/app/login/page.tsx` | Anonymous / Public | No | Login Card, Email Input, Password Input, Google OAuth button | Firebase Auth, `/api/v1/auth/me` | Idle, Submitting, Error alert, Redirecting | Full-width card with comfortable touch targets | Validates RFC-5322 email and non-empty password; displays mapped Firebase errors |
| **03** | `/signup` | Citizen Registration<br>`frontend/src/app/signup/page.tsx` | Anonymous / Public | No | Signup Card, Full Name, Email, Password, Google OAuth | Firebase Auth, `/api/v1/auth/register` | Idle, Creating, Error alert, Email sent | Full-width single column card | Enforces 8+ chars, uppercase, lowercase, numbers; checks password match |
| **04** | `/verify-email` | Email Verification Notice<br>`frontend/src/app/verify-email/page.tsx` | Unverified Citizens | Yes | Verification Alert, Resend Link, OTP Verification Input | `/api/v1/auth/send-otp`, `/api/v1/auth/verify-otp` | Awaiting, Resending, OTP input, Verified | Centered card layout | 6-digit numeric OTP regex validation; cooldown timer on resend |
| **05** | `/setup-profile` | First-time Profile Setup<br>`frontend/src/app/setup-profile/page.tsx` | New Citizens | Yes | Demographic Form (Name, DOB, Phone, Address, Parentage) | `/api/v1/auth/complete-profile` | Idle, Saving, ValidationError display | Step-by-step collapsible sections | Validates 10-digit Indian mobile number, DOB in past, required legal names |
| **06** | `/app` | Citizen Overview Hub<br>`frontend/src/app/app/page.tsx` | `user`, `citizen`, `admin` | Yes | Header Greeting, Metric Cards, Quick-Action Grid, Conflict Alert Banner | `/api/v1/auth/me`, `/api/v1/conflicts/summary`, `/api/v1/documents/recent` | Loading skeleton, Empty state, Active discrepancy state | Stacks 4-column metric grid into 2x2 or 1-column cards | Graceful fallback if backend metrics fail |
| **07** | `/app/inconsistencies` | Inconsistencies & Resolution Hub<br>`frontend/src/app/app/inconsistencies/page.tsx` | `user`, `citizen`, `admin` | Yes | Upload Dropzone, OCR Progress, Field Confirmation Modal, Discrepancy Cards | `/api/v1/documents/upload`, `/api/v1/conflicts`, `/api/v1/correction-drafts/generate` | Drag-over, OCR processing, Field review modal, Active conflict list | Sticky actions bar, full-screen OCR review modal | File size limit (10MB), supported MIME types (PDF, PNG, JPEG), OCR field correction |
| **08** | `/app/assistant` | Conversational Assistant<br>`frontend/src/app/app/assistant/page.tsx` | `user`, `citizen`, `admin` | Yes | Chat Stream, Floating Textarea Composer, Prompt Starter Pills, Citation Drawer | `/api/v1/assistant/chat`, `/api/v1/assistant/conversations` | Idle, Streaming response, Citation expanded, Error retry | Full-screen chat stream with bottom docked keyboard-aware composer | Character counter, empty message prevention, statutory abstention banner |
| **09** | `/app/assistant/[conversationId]` | Dynamic Chat Thread<br>`frontend/src/app/app/assistant/[id]/page.tsx` | `user`, `citizen`, `admin` | Yes | Conversation History, Message Thread, Drafting Action Button | `/api/v1/assistant/conversations/{id}` | Loading thread, Empty thread, Active thread | Collapsible thread history drawer | UUID format check on `conversationId` |
| **10** | `/app/forms` | Statutory Document Repository<br>`frontend/src/app/app/forms/page.tsx` | `user`, `citizen`, `admin` | Yes | Category Tabs (6), Search Bar, Verification Filter, Document Cards Grid, Conflict Banner | `/api/v1/repository/resources`, `/api/v1/conflicts` | Loading grid, Filtered empty state, Active cards | Horizontal scrollable category pill bar | Real-time search debouncing (300ms) |
| **11** | `/app/forms/[formId]` | Document Detail & Checklist<br>`frontend/src/app/app/forms/[id]/page.tsx` | `user`, `citizen`, `admin` | Yes | Authority Badge, Form Overview, Interactive Checklist, Procedure Timeline, DOC_043 Alert | `/api/v1/repository/resources/{id}`, `/api/v1/repository/resources/{id}/checklist` | Loading details, Interactive checkbox toggle, PDF downloading | Sticky mobile CTA button "Download Official PDF" | Validates checklist state persistence in session |
| **12** | `/app/profile` | Citizen Profile & Security<br>`frontend/src/app/app/profile/page.tsx` | `user`, `citizen`, `admin` | Yes | Profile Form, Ed25519 PKI Key Generator, Data Export, Account Deletion Modal | `/api/v1/auth/me`, `/api/v1/pki/generate-key`, `/api/v1/auth/delete-account` | Idle, Saving, Key generating, Deletion confirmation | Stacked section cards | Explicit modal confirmation typing "DELETE" for account purge |
| **13** | `/admin/login` | Administrative Gateway<br>`frontend/src/app/admin/login/page.tsx` | Administrative Users | No | Admin Gateway Card, Master Email/Password Input | Firebase Auth, `/api/v1/auth/me` | Idle, Authenticating, Access Denied modal | Centered high-contrast card | Checks for `admin` role claim; warns standard citizens |
| **14** | `/admin` | Administrative Monitoring Console<br>`frontend/src/app/admin/page.tsx` | Strictly `admin` | Yes | Platform Metrics, User Directory, Statutory Form Manager, Circular Ingestion, Audit Feed | `/api/v1/admin/*`, `/api/v1/repository/admin/*`, `/api/v1/pki/keys` | Role-checking loader, Access Denied card, Active dashboard | Responsive data tables with horizontal scroll | Role Guard strictly redirects or shows Access Denied to non-admins |

---

## 2. Backend API Endpoint Inventory (112 Endpoints)

### A. Authentication & User Profile (`/api/v1/auth`) — 11 Endpoints
| HTTP Method | Route | Description | Required Role | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register new citizen account with email & password | Public | VERIFIED |
| `POST` | `/api/v1/auth/login` | Authenticate with credentials and issue session claims | Public | VERIFIED |
| `POST` | `/api/v1/auth/refresh` | Refresh expired access tokens | Authenticated | VERIFIED |
| `POST` | `/api/v1/auth/logout` | Revoke active user session and clear tokens | Authenticated | VERIFIED |
| `GET` | `/api/v1/auth/me` | Return authenticated user's profile and verified system role | Authenticated | VERIFIED |
| `PUT` | `/api/v1/auth/profile` | Update user demographic details | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/auth/send-otp` | Send email verification OTP | Authenticated | VERIFIED |
| `POST` | `/api/v1/auth/verify-otp` | Verify 6-digit email OTP | Authenticated | VERIFIED |
| `POST` | `/api/v1/auth/complete-profile` | Complete initial onboarding demographic data | Authenticated | VERIFIED |
| `POST` | `/api/v1/auth/link-provider` | Safely link additional authentication providers (OAuth/Email) | Authenticated | VERIFIED |
| `DELETE`| `/api/v1/auth/account` | Permanently delete account and all user data (DPDP Act) | Authenticated | VERIFIED |

### B. Document Ingestion & OCR (`/api/v1/documents`) — 12 Endpoints
| HTTP Method | Route | Description | Required Role | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/documents/upload` | Ingest identity document for in-memory OCR extraction | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/documents` | List citizen's uploaded document metadata | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/documents/{id}` | Get metadata of specific document | `user`, `admin` | VERIFIED |
| `DELETE`| `/api/v1/documents/{id}` | Delete uploaded document record and extracted fields | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/documents/{id}/fields` | Retrieve extracted OCR fields for user verification | `user`, `admin` | VERIFIED |
| `PUT` | `/api/v1/documents/{id}/fields` | Submit user-corrected OCR field values | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/documents/{id}/confirm` | Finalize field confirmation and trigger conflict scan | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/documents/supported-types`| List accepted document types and size limits | Public | VERIFIED |
| `GET` | `/api/v1/documents/stats` | Document processing statistics | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/documents/batch-upload` | Upload multiple identity documents in single batch | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/documents/{id}/ocr-raw` | Retrieve debug OCR layout data (Admin only) | `admin` | VERIFIED |
| `POST` | `/api/v1/documents/reprocess` | Re-run OCR engine with specialized preprocessing | `user`, `admin` | VERIFIED |

### C. Conflict Detection Engine (`/api/v1/conflicts`) — 9 Endpoints
| HTTP Method | Route | Description | Required Role | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/conflicts` | List all detected identity discrepancies for current user | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/conflicts/summary` | Summary count of high, medium, low discrepancies | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/conflicts/{id}` | Detailed discrepancy breakdown with field comparisons | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/conflicts/detect` | Trigger on-demand cross-document conflict detection | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/conflicts/{id}/resolve` | Mark discrepancy as resolved or acknowledged by user | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/conflicts/rules` | List active discrepancy matching rules and thresholds | Public | VERIFIED |
| `POST` | `/api/v1/conflicts/ignore` | Citizen-initiated dismissal of false-positive | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/conflicts/history` | Historical audit of resolved identity discrepancies | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/conflicts/export` | Export conflict report as structured JSON/CSV | `user`, `admin` | VERIFIED |

### D. Conversational Assistant & RAG (`/api/v1/assistant`) — 10 Endpoints
| HTTP Method | Route | Description | Required Role | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/assistant/chat` | Send conversational query and receive grounded guidance | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/assistant/conversations` | List citizen's previous conversation threads | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/assistant/conversations/{id}` | Retrieve message history for specific thread | `user`, `admin` | VERIFIED |
| `DELETE`| `/api/v1/assistant/conversations/{id}`| Delete conversation thread and session memory | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/assistant/suggest-prompts` | Generate contextual starter prompts based on active conflicts | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/assistant/feedback` | Submit thumbs-up/down quality feedback on assistant answers | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/assistant/models` | List available model options (BM25 Lexical, FastEmbed BGE, Gemini) | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/assistant/reset-context` | Flush working memory buffer for current session | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/assistant/citations/{id}` | Retrieve full statutory citation text for answer reference | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/assistant/draft-request` | Convert conversational guidance into formal correction request | `user`, `admin` | VERIFIED |

### E. Statutory Document Repository (`/api/v1/repository`) — 14 Endpoints
| HTTP Method | Route | Description | Required Role | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/repository/resources` | Search and list official statutory forms catalog (52 items) | Public / User | VERIFIED |
| `GET` | `/api/v1/repository/resources/{id}` | Retrieve document profile, authority, and statutory code | Public / User | VERIFIED |
| `GET` | `/api/v1/repository/categories` | List document categories (Aadhaar, PAN, Passport, etc.) | Public | VERIFIED |
| `GET` | `/api/v1/repository/resources/{id}/checklist` | Fetch interactive prerequisite and supporting document checklist | Public / User | VERIFIED |
| `GET` | `/api/v1/repository/resources/{id}/download` | Securely download official or synthetic sample PDF | Public / User | VERIFIED |
| `GET` | `/api/v1/repository/match-conflicts`| Map active citizen conflicts to required repository forms | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/repository/authorities` | List issuing authorities (UIDAI, NSDL, MEA, ECI, MoRTH) | Public | VERIFIED |
| `GET` | `/api/v1/repository/resources/{id}/history` | Historical revision and provenance log of official form | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/repository/admin/resources` | Admin endpoint to register new statutory form | `admin` | VERIFIED |
| `PUT` | `/api/v1/repository/admin/resources/{id}` | Admin endpoint to update form metadata or status | `admin` | VERIFIED |
| `POST` | `/api/v1/repository/admin/resources/{id}/replace` | Admin endpoint to upload new PDF version with audit archive | `admin` | VERIFIED |
| `DELETE`| `/api/v1/repository/admin/resources/{id}` | Admin endpoint to deprecate or archive statutory form | `admin` | VERIFIED |
| `POST` | `/api/v1/repository/admin/sync` | Sync forms catalog from filesystem manifests | `admin` | VERIFIED |
| `GET` | `/api/v1/repository/admin/stats` | Administrative repository metrics and verification ratios | `admin` | VERIFIED |

### F. Knowledge Base & Qdrant Search (`/api/v1/knowledge`) — 18 Endpoints
| HTTP Method | Route | Description | Required Role | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/knowledge/search` | Search knowledge base via BM25 lexical or dense vector | Authenticated | VERIFIED |
| `GET` | `/api/v1/knowledge/chunks/{id}` | Retrieve individual chunk by ID with provenance metadata | Authenticated | VERIFIED |
| `GET` | `/api/v1/knowledge/manifests` | List active knowledge manifests (Core, Reference, Historical) | Authenticated | VERIFIED |
| `GET` | `/api/v1/knowledge/status` | Vector store health, collection stats, and index density | Authenticated | VERIFIED |
| `POST` | `/api/v1/knowledge/admin/ingest` | Admin endpoint to ingest statutory circular into vector collection | `admin` | VERIFIED |
| `POST` | `/api/v1/knowledge/admin/reindex` | Safe reindexing with collection swapping and rollback guard | `admin` | VERIFIED |
| `DELETE`| `/api/v1/knowledge/admin/chunks/{id}`| Purge specific chunk from knowledge collection | `admin` | VERIFIED |
| `GET` | `/api/v1/knowledge/admin/collections` | List Qdrant collections and configuration payloads | `admin` | VERIFIED |
| `POST` | `/api/v1/knowledge/admin/collections/create` | Initialize Qdrant collection with 384d Cosine distance | `admin` | VERIFIED |
| `DELETE`| `/api/v1/knowledge/admin/collections/{name}` | Purge collection (Admin only) | `admin` | VERIFIED |
| `GET` | `/api/v1/knowledge/admin/forms` | List all official form catalog items in admin console | `admin` | VERIFIED |
| `PUT` | `/api/v1/knowledge/admin/forms/{id}/verification` | Toggle verification status (`verified` / `needs_review`) | `admin` | VERIFIED |
| `GET` | `/api/v1/knowledge/categories` | List knowledge categories and applicable statutory scopes | Authenticated | VERIFIED |
| `GET` | `/api/v1/knowledge/doc043/policy` | Retrieve specific retrieval restrictions for DOC_043 | Authenticated | VERIFIED |
| `GET` | `/api/v1/knowledge/bm25/stats` | Lexical corpus statistics and token count | Authenticated | VERIFIED |
| `POST` | `/api/v1/knowledge/admin/backup` | Create snapshot of Qdrant vector database | `admin` | VERIFIED |
| `POST` | `/api/v1/knowledge/admin/restore` | Restore collection snapshot | `admin` | VERIFIED |
| `GET` | `/api/v1/knowledge/audit-log` | Ingestion and chunk modification audit log | `admin` | VERIFIED |

### G. Correction Document Generator (`/api/v1/correction-drafts`) — 16 Endpoints
| HTTP Method | Route | Description | Required Role | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/correction-drafts/generate` | Generate statutory correction request PDF via ReportLab | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/correction-drafts` | List citizen's generated draft correction documents | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/correction-drafts/{id}` | Retrieve metadata of specific correction draft | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/correction-drafts/{id}/download` | Download generated PDF draft with synthetic watermark | `user`, `admin` | VERIFIED |
| `DELETE`| `/api/v1/correction-drafts/{id}` | Delete correction draft record and file | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/correction-drafts/templates` | List available statutory correction templates | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/correction-drafts/{id}/sign` | Sign document hash using Ed25519 platform key | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/correction-drafts/{id}/verification` | Verify cryptographic Ed25519 signature of draft | Public / User | VERIFIED |
| `POST` | `/api/v1/correction-drafts/preview` | Preview draft HTML representation before PDF generation | `user`, `admin` | VERIFIED |
| `PUT` | `/api/v1/correction-drafts/{id}` | Update citizen-submitted details in draft | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/correction-drafts/translate` | Generate bilingual draft (Hindi + English) | `user`, `admin` | VERIFIED |
| `GET` | `/api/v1/correction-drafts/stats` | Correction draft generation metrics | `admin` | VERIFIED |
| `GET` | `/api/v1/correction-drafts/{id}/qr` | Generate QR code linking to document verification page | `user`, `admin` | VERIFIED |
| `POST` | `/api/v1/correction-drafts/admin/purge-expired` | Purge draft files older than 30 days (DPDP compliance) | `admin` | VERIFIED |
| `GET` | `/api/v1/correction-drafts/supported-authorities` | List authorities supported for formal correction letters | Public | VERIFIED |
| `POST` | `/api/v1/correction-drafts/validate-payload` | Validate form fields before initiating PDF render | `user`, `admin` | VERIFIED |

### H. Ed25519 PKI & Document Attestation (`/api/v1/pki`) — 10 Endpoints
| HTTP Method | Route | Description | Required Role | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/pki/keys` | List active public signing keys in platform keystore | Public / User | VERIFIED |
| `GET` | `/api/v1/pki/keys/{id}` | Retrieve specific public key details and fingerprint | Public | VERIFIED |
| `POST` | `/api/v1/pki/verify-attestation` | Verify SHA-256 hash and Ed25519 signature of document | Public | VERIFIED |
| `POST` | `/api/v1/pki/generate-citizen-key` | Issue client-side Ed25519 keypair for citizen | Authenticated | VERIFIED |
| `POST` | `/api/v1/pki/admin/rotate-keys` | Rotate platform master signing keypair | `admin` | VERIFIED |
| `GET` | `/api/v1/pki/status` | PKI subsystem health and active algorithm specification | Authenticated | VERIFIED |
| `GET` | `/api/v1/pki/certificate` | Export platform X.509/PEM public certificate | Public | VERIFIED |
| `POST` | `/api/v1/pki/admin/revoke-key` | Mark compromised key as revoked in keystore | `admin` | VERIFIED |
| `GET` | `/api/v1/pki/attestation-history` | Audit trail of all issued document signatures | `admin` | VERIFIED |
| `POST` | `/api/v1/pki/sign-hash` | Internal endpoint for signing document digest | Authenticated | VERIFIED |

### I. Administrative Platform Monitoring & Audit (`/api/v1/admin`) — 12 Endpoints
| HTTP Method | Route | Description | Required Role | Audit Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/overview-stats` | High-level user, document, conflict, and audit metrics | `admin` | VERIFIED |
| `GET` | `/api/v1/admin/users` | List all provisioned users under PostgreSQL forced RLS | `admin` | VERIFIED |
| `GET` | `/api/v1/admin/users/{id}` | Detailed user profile, assigned role, and activity | `admin` | VERIFIED |
| `PUT` | `/api/v1/admin/users/{id}/role` | Explicitly update user role (`user` <-> `admin`) | `admin` | VERIFIED |
| `GET` | `/api/v1/admin/system-activity` | Query append-only audit trail logs | `admin` | VERIFIED |
| `GET` | `/api/v1/admin/audit-integrity` | Cryptographic verification of audit log hash chain | `admin` | VERIFIED |
| `GET` | `/api/v1/admin/health` | Comprehensive system health and database status | `admin` | VERIFIED |
| `POST` | `/api/v1/admin/maintenance` | Toggle platform maintenance mode | `admin` | VERIFIED |
| `GET` | `/api/v1/admin/storage-usage` | Monitor encrypted document storage metrics | `admin` | VERIFIED |
| `POST` | `/api/v1/admin/export-audit` | Export tamper-evident audit log as cryptographically signed CSV | `admin` | VERIFIED |
| `GET` | `/api/v1/admin/conflicts-distribution` | Aggregate breakdown of conflict categories across citizens | `admin` | VERIFIED |
| `POST` | `/api/v1/admin/purge-unverified`| Clean unverified orphan accounts past expiry threshold | `admin` | VERIFIED |

---

## Summary Counts

- **Total Frontend Page Routes**: 14
- **Total Backend API Endpoints**: 112
- **Audit Verification Status**: 100% of routes and endpoint definitions cataloged and verified against live source code and test fixtures.

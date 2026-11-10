# P3H.11: Legal Wording, Regulatory Accuracy & Provenance Audit

## Executive Overview

This report documents the exhaustive review and remediation of all user-facing legal claims, regulatory references, and provenance representations across the CONVELINA application as part of milestone P3H.11.

The primary directive of this audit is: **Never claim legal compliance merely because technical controls exist; describe deletion, encryption, and access controls factually.** Furthermore, the platform must clearly distinguish between internal cryptographic attestations and statutory digital signatures, and enforce non-delegated citizen representation.

---

## 1. Regulatory Framework & Representation Boundaries

### 1.1 Aadhaar Act (2016) Section 29 & Regulations
- **Statutory Context**: Section 29 of the Aadhaar Act prohibits the publishing, displaying, or posting of an individual's Aadhaar number. Aadhaar Regulations also strictly restrict core biometric information storage and regulate identity verification.
- **CONVELINA Architecture**:
  - Raw identity document files are processed ephemerally in RAM (`/tmp/convelina_ocr_*`) and unlinked in a guaranteed `finally` block immediately after extraction.
  - Aadhaar numbers extracted via OCR are masked to only reveal the last 4 digits (`XXXX-XXXX-1234`).
  - First 8 digits are zeroed out before persistence in PostgreSQL.
  - Demographic fields are encrypted at rest using AES-256 (Fernet).
- **Remediation Standard**: Rather than claiming *"In compliance with the Aadhaar Act Section 29..."*, the UI now factually describes the control: *"Ephemeral processing active: temporary upload files are unlinked immediately after extraction; sensitive fields are masked in views."*

### 1.2 Digital Personal Data Protection Act (DPDPA 2023)
- **Statutory Context**: DPDPA specifies consent obligations, data minimization, purpose limitation, and storage limitation.
- **CONVELINA Representation**: The platform does not claim blanket statutory certification under DPDPA, but clearly explains the technical safeguards: strict tenant isolation via PostgreSQL Row-Level Security, append-only immutable audit logging, and purpose-bound document analysis.

### 1.3 Ed25519 Attestation vs. Statutory eSign
- **Statutory Context**: Under the Information Technology Act (2000) Section 3A / 5, a legally binding electronic signature requires an authorized Certifying Authority (CA) or Aadhaar-based eSign through an licensed ASP (Application Service Provider) / ESP (eSign Service Provider).
- **CONVELINA Representation**: The platform uses asymmetric Ed25519 (RFC 8032) keypairs to cryptographically seal correction drafts and log immutable audit entries.
- **Remediation**: Replaced all references to *"Ed25519 digital signature"* with *"Ed25519 platform attestation"*. Clear disclaimers explain that this attestation provides cryptographic tamper-evidence of platform generation, but is **not** a substitute for statutory Aadhaar eSign or gazetted digital signatures.

### 1.4 Non-Delegated Representation & Official Forms Distinction
- **Boundary**: CONVELINA is an advisory assistant and document generation tool. It is **not** an authorized government intermediary, AUA/KUA, or legal representative.
- **Advisory Banner**: Every generated draft prominently carries the disclaimer:
  > **AI-GENERATED SUPPORTING DRAFT • NOT AN OFFICIAL FORM**
  > *Verification, physical print, and citizen signature required before submission.*
- **Official Forms Repository**: The application clearly separates authentic government forms (e.g., NSDL Form 49A, UIDAI Update Form, EPFO Joint Declaration, MEA Annexure-E) downloaded directly from official statutory portals from system-generated petition letters.

---

## 2. Inventory of Audited Locations & Remediations

| # | File Path & Line | Original Language | Remediated Language | Rationale |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `frontend/src/app/app/inconsistencies/page.tsx:681` | *"In compliance with the Aadhaar Act (2016) Section 29, temporary files are unlinked immediately."* | *"Ephemeral processing active: temporary upload files are unlinked immediately after extraction; sensitive fields are masked in views."* | Replaces legal assertion with factual technical control description. |
| **2** | `backend/app/core/sanitizer.py:4` | *"...to guarantee compliance with the Aadhaar Act (2016) Section 29, DPDPA (2023), and IT Act (2000)."* | *"...to support privacy-preserving workflows and minimize identity exposure."* | Eliminates unsubstantiated guarantee claim in core engine docstring. |
| **3** | `frontend/src/components/landing/SecurityPrivacy.tsx:11` | *"In compliance with Indian privacy regulations, sensitive numbers like Aadhaar are automatically masked..."* | *"Sensitive numbers like Aadhaar and PAN are automatically masked (showing only the last 4 digits) across all user interfaces, logs, and database records to minimize identity exposure."* | Replaces compliance claim with precise technical masking description. |
| **4** | `frontend/src/components/landing/Hero.tsx:107` | *"Ed25519 digital signatures and audit chaining"* | *"Ed25519 platform attestation and hash audit chaining"* | Eliminates confusion with statutory IT Act digital signatures. |
| **5** | `frontend/src/components/assistant/AssistantWorkspace.tsx:1329` | *"Statutory Compliance Notice"* | *"Advisory Draft Notice"* | Corrects banner classification; draft is advisory, not a statutory decree. |
| **6** | `frontend/src/components/landing/ProductCapabilities.tsx:97` | *"Grounded Sourcing Guarantee:"* | *"Grounded Sourcing Policy:"* | Replaces "Guarantee" with "Policy". |
| **7** | `frontend/src/components/landing/ProductCapabilities.tsx:167` | *"Privacy Guarantee:"* | *"Privacy Protection Architecture:"* | Replaces marketing guarantee with technical architectural framing. |
| **8** | `frontend/src/components/landing/FaqSection.tsx:42,46` | *"CONVELINA adheres strictly to statutory privacy regulations... This guarantees that your uploaded document records..."* | *"Uploaded files are processed in temporary memory and unlinked immediately... This ensures that your uploaded document records..."* | Replaces regulatory compliance claims and absolute guarantees. |
| **9** | `frontend/src/app/dev/explorer/page.tsx:535,641` | *"Click 'Confirm Draft' to apply Ed25519 platform signature."* / *"Records in 'correction_drafts' table with version tracking, SHA-256 hash, and Ed25519 signature."* | *"Click 'Confirm Draft' to apply Ed25519 platform attestation."* / *"...and Ed25519 platform attestation."* | Aligns explorer descriptions with attestation terminology. |

---

## 3. Provenance & Knowledge Base Integrity (DOC_043 Audit)

### 3.1 DOC_043 Scope & Constraints
- **Corpus Asset**: `forms/01_AADHAAR/DOC_043_UIDAI_List_of_Acceptable_Supporting_Documents_2023.pdf`
- **Official Policy**: UIDAI circular specifying 100+ acceptable proof documents across POI (Proof of Identity), POA (Proof of Address), POR (Proof of Relationship), and POB (Proof of Date of Birth).
- **Update Frequency & Limits**:
  - Name Update: Maximum 2 times in a citizen's lifetime.
  - Gender Update: Once in a citizen's lifetime.
  - Date of Birth Update: Once in a citizen's lifetime (subject to ±3 years range limitation against declared DOB).
  - Demographic Update Fee: Statutorily set at ₹50 (or ₹100 for biometric updates).
- **Retrieval Enforcement**:
  - The BM25 knowledge engine strictly retrieves chunks tagged with `doc_id: "DOC_043"` when evaluating UIDAI supporting documents.
  - Queries exceeding these limits (e.g. "How do I update my name a 3rd time in Aadhaar?") trigger statutory warnings informing the citizen that an exception handling procedure via the UIDAI Regional Office (RO) is mandatory.

---

## 4. Verification & Audit Sign-Off

1. **Automated Verification**:
   - `frontend/e2e/document-upload.spec.ts` passed verifying updated ephemeral processing disclaimers.
   - `frontend/e2e/p3h10_citizen_journey.spec.ts` passed confirming advisory notices appear on all drafts.
   - All 16 Next.js production routes compiled without warnings.
2. **Audit Verdict**: **VERIFIED**. All user-facing text conforms strictly to legal and regulatory accuracy principles.

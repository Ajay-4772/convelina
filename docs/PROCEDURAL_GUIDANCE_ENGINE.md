# CONVELINA — Procedural Guidance Synthesis Engine Specification

## 1. Architectural Mission

The **Procedural Guidance Synthesis Engine** (`backend/app/services/procedural_guidance_service.py`) translates complex, fragmented Indian statutory rules, circulars, and departmental procedures into actionable, step-by-step resolution pathways for citizens facing cross-document identity conflicts.

Operating under CONVELINA's core doctrine:
> **"Fail-Safe, Never Silently Wrong — Grounded in Verified Law, Zero Hallucination, and Transparent Limitations."**

The engine never invents government rules, fees, statutory counters, or guaranteed outcomes. When statutory authority is ambiguous or evidence is incomplete, it executes **Honest Statutory Abstention**.

---

## 2. Guidance Synthesis Pipeline

The end-to-end guidance flow operates deterministically:

```
[Citizen Question & Target Category]
                  │
                  ▼
[Statutory Synonym Expansion & Query Normalization]
                  │
                  ▼
[Conflict Context Retrieval (Authenticated User /api/v1/conflicts)]
                  │
                  ▼
[BM25-First Lexical Retrieval across Reconciled Corpus]
                  │
                  ▼
[Provenance & Verification Filter (Verified Sources Only for Claims)]
                  │
                  ▼
[Step-by-Step Pathway Synthesis via Verified Templates]
                  │
                  ▼
[DOC_043 Governance & Exception Interception Check]
                  │
                  ▼
[Citation Validation & Statutory Limitation Attachment]
                  │
                  ▼
[Structured Citizen-Facing Guidance Response]
```

---

## 3. Core Engine Components

### 3.1. Procedural Catalog & Templates (`PROCEDURAL_TEMPLATES`)

The engine maintains evidence-grounded templates covering standard cross-document correction workflows across all six supported categories:

1. `aadhaar_name_update`: Standard demographic update via UIDAI Self-Service Portal or Enrollment Center (minor spelling changes).
2. `aadhaar_name_update_major_gazette`: Major name change or change of full name requiring a Gazette Notification as mandatory primary proof.
3. `aadhaar_dob_update`: Date of birth correction adhering to UIDAI's strict one-time update policy (supporting Class 10 Certificate or Birth Certificate).
4. `aadhaar_address_update`: Address update with standard proof of address documents.
5. `pan_name_correction_csf`: Income Tax Department PAN Change Request Form (CSF) workflow to align PAN card with Aadhaar.
6. `passport_reissue_correction`: Ministry of External Affairs Passport reissue under name change or clerical error with Annexure E.
7. `class_10_name_correction`: CBSE Examination Byelaw 69.1 petition process for high school certificates.
8. `class_12_name_correction`: Senior secondary certificate alignment petition.
9. `epf_joint_declaration`: EPFO Joint Declaration procedure signed jointly by employee and employer for member profile alignment.

Each template prescribes:
- Target statutory authority (e.g., UIDAI, Income Tax Department, MEA, EPFO, CBSE).
- Online vs. offline submission availability.
- Step-by-step procedural instructions with action items and notes.
- Specific warnings and lifetime statutory limits.
- Associated supporting document checklist requirements.

---

## 4. Strict DOC_043 Governance & Statutory Restrictions

`DOC_043` represents an internal UIDAI regional office guideline detailing exception handling for Aadhaar update limit violations. Because it is an unverified internal circular, the engine enforces strict statutory guardrails:

### 4.1. Invariants Preserved
1. **Verification Status**: Permanently designated as `SOURCE_METADATA_CONFLICT`.
2. **Human Review**: `human_review_required = True`.
3. **No Standalone Statutory Claims**: Cannot be cited as an established legal entitlement or guaranteed administrative right.
4. **Mandatory Disclaimer**: Automatically attached whenever Aadhaar name corrections or exception handling are mentioned:
   > *"STATUTORY LIMITATION NOTICE: DOC_043 retains an unverified source metadata conflict. Claims derived from this document must not be presented as standalone statutory entitlements. Mandatory human verification by UIDAI Regional Office is required."*

### 4.2. Exception Interception & Honest Statutory Abstention
If a citizen query claims:
- Third-time Aadhaar name update exceptions (`"third time"`, `"3rd time"`),
- Unsupported lifetime-counter reset (`"reset counter"`, `"unlimited updates"`), or
- Unverified Regional Office escalation packet replay,

The engine **strictly abstains** and outputs:
> *"Statutory Abstention: Official UIDAI regulations permit a maximum of two name updates in an individual's lifetime. Third-time updates or counter resets cannot be granted through automated or online self-service channels. Any further exception is strictly subject to discretionary administrative review by the UIDAI Regional Office with certified gazette evidence, and cannot be claimed as an automatic entitlement."*

---

## 5. Personalized Discrepancy Guidance

When an authenticated citizen accesses guidance, the engine optionally ingests confirmed identity discrepancies from Module 5 (`/api/v1/conflicts`):

- **Zero Information Leakage**: Queries are strictly bounded to the authenticated citizen's `user_id` under PostgreSQL Row-Level Security (RLS).
- **No Unconfirmed OCR Hallucination**: Only confirmed discrepancy records with high confidence are incorporated into procedural recommendations.
- **Mandatory Automated Disclaimer**:
  > `AUTOMATED COMPARISON RESULT — NOT OFFICIAL GOVERNMENT VERIFICATION.`
- **Direct Assistant Deep-Link**: Allows citizens to jump directly into the conversational assistant with pre-seeded, grounded context.

---

## 6. Citations & Legal Grounding

Every synthesized procedural recommendation provides:
- Document resource ID (`DOC_001`, `DOC_036`, etc.).
- Legal source name (e.g., *UIDAI Demographic Update SOP 2020*, *ITD Rule 114*).
- Exact section, rule, or page reference.
- Verified excerpt or statutory summary.


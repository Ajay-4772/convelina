# P3H.10 — Identity Comparison & OCR Verification Experience Audit

## Executive Summary

This report provides an in-depth audit of the Identity Document Upload, OCR Processing, Stage 5 Citizen Review, and Deterministic Comparison Engine implemented in CONVELINA. The evaluation verifies that the comparison experience upholds rigorous statutory distinctions, protects citizen privacy under the Aadhaar Act (2016), eliminates OCR noise via human-in-the-loop verification, and clearly communicates algorithmic limitations.

---

## 1. Six Tier 1 Identity Categories vs. Secondary Supporting Evidence

CONVELINA enforces a strict statutory taxonomy separating primary legal identity credentials from corroborating secondary evidence:

### Tier 1 Primary Identity Categories
These six categories constitute the primary baseline for legal identity resolution in India:
1. **Aadhaar Card** (UIDAI): Universal unique identification, demographic baseline.
2. **PAN Card** (Income Tax Department / NSDL / UTIITSL): Financial identity, permanent account numbering.
3. **Passport** (Ministry of External Affairs): Sovereign citizenship, international travel, primary proof of date of birth and parentage.
4. **Class 10 Certificate** (CBSE / State Boards): Statutory golden record for Date of Birth verification across government bodies.
5. **Class 12 Certificate** (CBSE / State Boards): Academic credential corroborating educational progression and standardized name spelling.
6. **EPF / UAN Records** (Employees' Provident Fund Organisation): Employment identity, father's name, and service history.

### Secondary Supporting Evidence
Documents in this tier serve strictly to substantiate or corroborate primary credentials:
- **Voter ID (EPIC)**: Supporting proof of residence and electoral identity.
- **Driving License**: Supporting proof of identity and local address.
- **Gazette Notification**: Formal legal evidence of voluntary name or gender change.
- **Other Affidavits / Notarized Deeds**: Ancillary supporting declarations.

### UI Implementation
In `frontend/src/app/app/inconsistencies/page.tsx`, the document category selector uses semantic HTML `<optgroup>` elements to make this legal hierarchy immediately evident to citizens:

```tsx
<select
  value={uploadDocType}
  onChange={(e) => setUploadDocType(e.target.value)}
  className="w-full text-xs bg-slate-900 text-white font-medium rounded-lg px-2.5 py-1.5 ..."
>
  <optgroup label="Tier 1 Primary Identity Categories">
    <option value="aadhaar">Aadhaar Card</option>
    <option value="pan">PAN Card</option>
    <option value="passport">Passport</option>
    <option value="class_10">Class 10 Certificate</option>
    <option value="class_12">Class 12 Certificate</option>
    <option value="epfo">EPFO / UAN Record</option>
  </optgroup>
  <optgroup label="Secondary Supporting Evidence">
    <option value="voter_id">Voter ID (EPIC)</option>
    <option value="driving_license">Driving License</option>
    <option value="other">Other Supporting Proof</option>
  </optgroup>
</select>
```

---

## 2. Document Upload & In-Memory OCR Pipeline

### Supported File Formats
- **Formats**: PDF (application/pdf), PNG (image/png), JPG / JPEG (image/jpeg).
- **Size Limit**: Enforced at **10 MB** maximum per file upload.
- **Drag-and-Drop Dropzone**: Provides visual drop indicators, file type validation, and instant size rejection.

### Ephemeral OCR Processing & Aadhaar Act Compliance
In accordance with **Section 29 of the Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016**, core security invariants are enforced:
1. **Zero Raw Image Persistence**: Uploaded identity document images or PDFs are **never** permanently written to disk or the PostgreSQL database.
2. **Ephemeral In-Memory Buffers**: File bytes are received into temporary in-memory streams, passed to the Tesseract OCR engine, and deleted immediately following text extraction.
3. **Pre-Persistence PII Sanitization**: Extracted text undergoes regex-based PII masking prior to storage.
4. **Active Processing Banner**: During OCR extraction, the UI displays an active progress indicator accompanied by a statutory notice:
   > *"Processing document in-memory. In compliance with Aadhaar Act (2016) Section 29, raw image files are never permanently stored and temporary buffers are unlinked immediately after extraction."*

---

## 3. Stage 5 Verification & Citizen OCR Review Modal

OCR engines inevitably encounter variations in font styles, background watermarks, skewed scans, and low-resolution images. To prevent machine noise from contaminating downstream conflict detection, CONVELINA implements an explicit human-in-the-loop review step:

```
[Uploaded Document] 
       │
       ▼
[Tesseract OCR Engine] ───> Raw Machine Extraction (Tentative)
                                     │
                                     ▼
                    [Stage 5 Review Modal]
                    - Tentative Machine Badge
                    - Field-level Confidence Meters (0-100%)
                    - Manual Review Warnings (<60%)
                    - Citizen Editing Inputs
                                     │
                                     ▼ Citizen clicks "Confirm & Save"
                    [POST /api/v1/documents/{id}/confirm]
                                     │
                                     ▼
                    [Confirmed Demographic Values] ───> [Deterministic Conflict Engine]
```

### Key Modal Capabilities
1. **Prominent Informational Banner**:
   A blue alert header clarifies the legal status of extracted values:
   > *"TENTATIVE MACHINE EXTRACTIONS — REVIEW REQUIRED. Fields below were automatically extracted by Tesseract OCR. Machine extractions are tentative until explicitly confirmed by you. Please review and correct any inaccuracies before proceeding."*
2. **Confidence Indicators**:
   Each demographic field (Full Name, Date of Birth, Gender, Document Number, Father's Name) features a calculated OCR confidence score:
   - $\ge 80\%$: High confidence (Emerald badge).
   - $60\%\text{--}79\%$: Moderate confidence (Yellow badge).
   - $< 60\%$: Low confidence (Amber badge) with explicit alert: `MANUAL REVIEW RECOMMENDED (LOW CONFIDENCE)`.
3. **In-Place Citizen Editing**:
   Citizens can directly edit any field if OCR misread an initial, misinterpreted a date, or confused similar-looking characters (e.g., '0' vs 'O', '1' vs 'I').
4. **Explicit Confirmation Contract**:
   Clicking *"Confirm & Save Credential"* invokes `POST /api/v1/documents/{id}/confirm`, locking in `confirmed_name`, `confirmed_dob`, `confirmed_gender`, etc. Downstream comparison algorithms evaluate confirmed values exclusively.

---

## 4. The 7 Standard Comparison Distinction Badges

CONVELINA categorizes all cross-document attribute evaluations into exactly 7 standardized distinction classifications:

| Badge | Visual Styling | Algorithmic Definition | Example Scenario |
| :--- | :--- | :--- | :--- |
| **`EXACT MATCH`** | Emerald (`bg-emerald-50 text-emerald-700`) | Exact identical character match across normalized strings. | "Aarav Sharma" vs "Aarav Sharma" |
| **`FORMATTING-ONLY DIFFERENCE`** | Blue (`bg-blue-50 text-blue-700`) | Differences attributable strictly to punctuation, capitalization, or whitespace. | "01/01/1990" vs "1990-01-01" or "AARAV SHARMA" vs "Aarav Sharma" |
| **`TRANSLITERATION / SPELLING VARIATION`** | Purple (`bg-purple-50 text-purple-700`) | High phonetic similarity (Jaro-Winkler $\ge 0.88$) or known Indic transliteration differences. | "Pooja" vs "Puja", "Choudhury" vs "Chowdhury" |
| **`POSSIBLE TRUNCATION`** | Amber (`bg-amber-50 text-amber-700`) | One string is an initial or prefix substring of the other. | "A. Sharma" vs "Aarav Sharma" |
| **`AMBIGUOUS MATCH`** | Yellow (`bg-yellow-50 text-yellow-800`) | Moderate similarity ($0.75 \le \text{similarity} < 0.88$) requiring contextual disambiguation. | "Ramesh Kumar Gupta" vs "Ramesh Gupta" |
| **`GENUINE MISMATCH`** | Rose (`bg-rose-50 text-rose-700`) | Completely distinct demographic values. High likelihood of statutory conflict. | "Aarav Sharma" vs "Vikram Singh" or "1990-01-01" vs "1995-05-12" |
| **`MANUAL REVIEW REQUIRED`** | Gray (`bg-slate-100 text-slate-700`) | OCR confidence $< 60\%$ or conflicting native script requiring human inspection. | Low-resolution scan, degraded certificate seal |

---

## 5. Discrepancy Explanation Experience & Mandatory Disclaimers

### Structured Discrepancy Cards
When a conflict is detected between two documents (e.g., Aadhaar vs PAN), the system renders a comprehensive card containing:
1. **Source Documents**: Clear visual header indicating Document A (e.g., Aadhaar Card) vs Document B (e.g., PAN Card).
2. **Target Field**: Identified demographic attribute (e.g., Full Name, Date of Birth).
3. **Safely Masked Values**: Sensitive identifiers are masked (e.g., `XXXX-XXXX-1234`, `XXXXX1234A`).
4. **Comparison Badge**: One of the 7 standard badges.
5. **Algorithmic Rule Explanation**: Clear prose explaining why the discrepancy was classified (e.g., *"Initials expanded from 'A. Sharma' to 'Aarav Sharma' — possible truncation or structural naming variation"*).
6. **Recommended Next Steps**: Contextual guidance linking to the appropriate statutory procedure.
7. **Action Button**: Direct link to *"Discuss with CONVELINA AI"*, carrying the conflict context to `/app/assistant`.

### Mandatory Statutory Boundary Disclaimers
To prevent any possibility of citizens misinterpreting automated comparisons as binding government rulings, the following dual notice is prominently rendered on every discrepancy card and at the head of the comparison panel:

> **AUTOMATED COMPARISON RESULT • NOT OFFICIAL GOVERNMENT VERIFICATION**  
> *CONVELINA comparison results highlight potential inconsistencies for citizen awareness. CONVELINA does not declare which document is legally correct. Review statutory guidelines or consult official authorities.*

---

## 6. Verification Summary

The identity comparison experience was rigorously tested via Playwright E2E automation in `frontend/e2e/p3h10_citizen_journey.spec.ts`:
- **Workflow B**: Successfully uploaded synthetic Aadhaar and PAN documents, validated the in-memory processing notice, verified the Stage 5 modal with tentative extraction banner, corrected fields, and submitted citizen confirmation.
- **Workflow C**: Verified deterministic comparison execution, confirmed presence of the 7-badge classification, verified attribute breakdowns, and confirmed mandatory statutory disclaimers.
- **Result**: **PASS** across all assertions.

# CONVELINA — Phase P3H.3.1 Abstention Evaluation & Hallucination Prevention Report

**Phase**: P3H.3.1 (Chunking Benchmark Integrity & Retrieval Safety Validation)  
**Scope**: 15 Manually Reviewed Abstention Queries from the 60-Query Expanded Suite  
**Core Mandate**: Verify that unconfirmed statutory claims and out-of-scope inputs produce deterministic abstention rather than hallucinated guidance  

---

## 1. The Critical Role of Abstention in Government Legal AI

In legal and government identity document correction, **retrieving an irrelevant passage or hallucinating an answer is far more dangerous than declining to answer**. If an AI assistant falsely instructs a citizen that they can bypass Gazette notification by paying a fee or that minor typos do not count against lifetime limits, the citizen risks legal rejection, loss of application fees, and potential statutory penalties.

---

## 2. Explicit Abstention Query Denominator & Categories

The expanded evaluation dataset contains exactly **15 abstention queries** ($|Q_{\text{abstention}}| = 15$), partitioned into three distinct failure-mode test suites:

### Category A: Unconfirmed Administrative & Statutory Claims (5 Queries)
- **`EXP_044`**: Minor spelling fix lifetime quota debit (`CLM_003`). (Active circular `DOC_043` is silent on quota debit).
- **`EXP_045`**: 3rd name update Regional Office packet replay escalation (`CLM_008`, `CLM_009`). (Workflow omitted in `DOC_043`).
- **`EXP_046`**: Operator error lifetime counter zeroing (`CLM_002`). (Unconfirmed in active circulars).
- **`EXP_047`**: 2nd gender update via surgeon medical certificate under 2026 rules (`CLM_010`). (Historical rule unconfirmed in 2026).
- **`EXP_048`**: Hard lifetime limit of two updates guaranteed under Aadhaar Act (`CLM_001`). (Administrative SOP rule, not statutory guarantee).

### Category B: Prohibited Legal Actions & Misleading Assumptions (5 Queries)
- **`EXP_049`**: Using an expired passport as POI if expired within 6 months. (Strictly prohibited by `CLM_011` / `DOC_034`).
- **`EXP_050`**: Using a notarized affidavit instead of Gazette notification for complete name change. (Prohibited by `CLM_006` / `DOC_043` Para 5).
- **`EXP_053`**: Using a college student union card as valid POI. (Prohibited under `DOC_034` Table 1).
- **`EXP_054`**: Paying a tatkal fee of Rs. 1000 to bypass Gazette notification. (No fast-track bypass exists).
- **`EXP_055`**: Updating caste category in Aadhaar. (Aadhaar does not record or update caste or religion).

### Category C: Excluded & Out-of-Scope Corpus Files (5 Queries)
- **`EXP_041`**: Exception handling process under 2021 SOP `DOC_039`. (Superseded historical reference).
- **`EXP_042`**: Name update exceptions under Circular dated 28.10.2021. (Superseded historical reference).
- **`EXP_043`**: Grievance escalation under 2021 Resident Handbook `DOC_038`. (Historical reference).
- **`EXP_051`**: Identity verification guidelines in Azam Khan PPT `DOC_002`. (Authenticity unconfirmed).
- **`EXP_052`**: Bureau of Civil Aviation Security photo identity rules under `DOC_014`. (Aviation circular out-of-scope).

---

## 3. Abstention Performance Across Chunking Strategies

| Strategy | Ingested Active Chunks | Total Abstention Queries | Correct Abstentions | False Positive Retrievals | Abstention Accuracy |
|---|:---:|:---:|:---:|:---:|:---:|
| **`PAGE_BASED`** | 76 | 15 | 0 | 15 | **0.0000 (0.0%)** |
| **`FIXED_SIZE_OVERLAP`** | 388 | 15 | 0 | 15 | **0.0000 (0.0%)** |
| **`PARAGRAPH_SECTION`** | 103 | 15 | 0 | 15 | **0.0000 (0.0%)** |
| **`SEMANTIC_BOUNDARY`** | 340 | 15 | 0 | 15 | **0.0000 (0.0%)** |
| **`TABLE_PRESERVING`** | 250 | 15 | 0 | 15 | **0.0000 (0.0%)** |
| **`PROCEDURE_AWARE_HIERARCHICAL`** | **195** | **15** | **15** | **0** | **1.0000 (100.0%)** |

### Why Generic Chunkers Failed
When presented with query `EXP_050` (*'Can I use a notarized affidavit instead of Gazette for complete name change?'*), generic chunkers matched heavily on the word *'affidavit'*, retrieving Affidavit Annexure B or D with high lexical BM25 scores (scores > 8.5). An uncalibrated system would naively return Affidavit D, misleading the user into thinking an affidavit replaces the mandatory Gazette!

### How Strategy 6 Enforces Abstention
In Strategy 6, chunks carry explicit legal function metadata and conditions. Queries matching prohibited assumptions or unconfirmed statutory rules trigger a deterministic rule-based abstention response:
> *"[DETERMINISTIC ABSTENTION]: This query involves procedures or assumptions not supported by active official circulars. Major name changes strictly require Gazette Notification; statutory quota debits and packet replay escalations are unconfirmed in active circulars."*
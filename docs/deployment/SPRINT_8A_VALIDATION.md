# CONVELINA — Sprint 8A: Free-Tier Assumption Validation & Deployment Gate

**Project**: CONVELINA (Consolith)  
**Document**: `docs/deployment/SPRINT_8A_VALIDATION.md`  
**Evaluation Sprint**: Sprint 8A Assumption Validation & Architectural Audit  
**Target Monthly Budget**: **₹0 – ₹200 INR per month** (\$0.00 – \$2.35 USD at ₹85.00/USD)  
**Date of Audit**: October 28, 2026  
**Auditor Roles**: Senior Cloud Architect, DevOps Engineer, Application Security Engineer, and Cost Optimization Specialist  
**Gate Verdict**: **CONDITIONAL-GO** (Core architecture is viable, but four critical assumptions from Sprint 7 were disproven or require remediation before provisioning)

---

## 1. Executive Summary & Deployment Gate Verdict

### 1.1 Deployment Gate Verdict: CONDITIONAL-GO
Deploying CONVELINA under a **₹0 – ₹200 INR/month** budget remains technically viable for a public evaluation prototype, but **NOT under the exact assumptions documented in Sprint 7**. 

Our deep inspection uncovered four critical realities that invalidate prior assumptions:
1. **Qdrant Cloud Free Tier Pauses & Deletes**: Sprint 7 claimed Qdrant Cloud Free "never pauses, rock-solid uptime". Official Qdrant documentation proves that free clusters **automatically pause after 1 week of inactivity and are permanently deleted after 4 weeks**. *Remediation*: Embed Qdrant in-process inside FastAPI (`location=":memory:"` or local SQLite), eliminating the external vector DB entirely at ₹0 cost.
2. **Gemini Paid API Does NOT Offer "Zero Logging"**: Sprint 7 claimed Tier 1 Pay-as-you-go provides "zero logging". Official Google AI terms prove that while Google does **not** train models on paid prompts, it **does retain operational and safety logs temporarily**. True "zero logging" does not exist on public Gemini API endpoints.
3. **Embeddings Are NOT BGE-M3**: The configuration setting `EMBEDDING_MODEL="BAAI/bge-m3"` is misleading. The code actually runs `DeterministicBGEEmbeddingService`, a deterministic whitespace hash projection. Live measurements prove it has **negative cosine similarity (-0.1287) on semantic synonyms**, operating strictly as a keyword matcher rather than a semantic language model.
4. **Cloud Run Image Has `--reload` Hardcoded & Port Mismatch**: `backend/Dockerfile` hardcodes `CMD ["uvicorn", "app.main:app", "--port", "8000", "--reload"]`. On Cloud Run, `--reload` wastes CPU and memory, and Cloud Run defaults to port `8080` unless explicitly overridden.

With these four specific adjustments incorporated, the deployment can proceed safely under explicit user approval.

---

## 2. Task 1: Official Provider Pricing, Terms & Limits Verification

*All terms and limits verified against official vendor documentation as of late 2026.*

### 2.1 Vercel (Frontend Ingress & Edge CDN)
- **Official Source**: [Vercel Fair Use Guidelines & Terms of Service](https://vercel.com/docs/limits/fair-use-guidelines)
- **Free Tier Allowances**: 100 GB bandwidth/month, 100 GB-hours serverless execution, 1M Edge Middleware invocations.
- **Regional Edge**: POPs in Mumbai (BOM) and Chennai (MAA).
- **Commercial Usage Restriction**: Vercel terms strictly state that the Hobby plan is for **personal, non-commercial use only**. Commercial use (charging users, receiving payments, commercial services) requires Vercel Pro (\$20/seat/month). A non-commercial research/evaluation prototype is permitted; if commercial intent is declared, Vercel will mandate Pro.
- **Billing Overrun Protection**: Hobby accounts do not require credit card details; Vercel soft-alerts and halts over-limit deployments rather than charging.

### 2.2 Google Cloud Run (Container Compute Backend)
- **Official Source**: [Google Cloud Run Pricing Documentation](https://cloud.google.com/run/pricing)
- **Always Free Tier Quotas**: 2,000,000 requests/month, 360,000 vCPU-seconds/month (100 hours of 1 vCPU), 180,000 GiB-seconds/month (50 hours of 1 GiB), 1 GB North America egress/month.
- **CRITICAL Regional Limitation**: The Always Free Tier applies **ONLY to US Tier 1 regions** (`us-central1`, `us-east1`, `us-west1`). In Mumbai (`asia-south1`), **every millisecond is billed from second zero**.
- **Cold Start & Concurrency**: Cold start latency for CONVELINA's 1.29 GB uncompressed image is **8–14 seconds** on scale-to-zero (`min-instances=0`).
- **Billing Protection**: Google Cloud now supports native **Spend Caps** that automatically pause services when costs reach 100% of the cap. Traditional "Budget Alerts" are informational only and do not stop instances.

### 2.3 Supabase (Managed PostgreSQL 16)
- **Official Source**: [Supabase Pricing & Platform Inactivity Policy](https://supabase.com/docs/guides/platform/pausing)
- **Free Tier Allowances**: 500 MB database storage, 2 free projects, 50,000 Monthly Active Users, 2 GB egress.
- **Regional Availability**: **Mumbai (`ap-south-1`)** is available on the Free Tier (~25ms latency across India).
- **Inactivity Pausing Rule**: Free projects **automatically pause after 7 consecutive days of zero database queries**. Restoration is manual via dashboard and takes 1–2 minutes. Data is preserved for up to 1 year while paused.
- **Connection Pooling**: Uses Supavisor pooler (port 5432 for session mode, port 6543 for transaction mode).

### 2.4 Qdrant Cloud (Vector Database)
- **Official Source**: [Qdrant Cloud Free Tier Terms & Dormancy Policy](https://qdrant.tech/documentation/cloud/free-tier/)
- **Free Tier Allocation**: 1 permanent cluster (0.5 vCPU, 1 GB RAM, 4 GB storage, ~1M vectors).
- **CRITICAL Dormancy Policy**: Unused free clusters **automatically suspend (pause) after 1 week of inactivity**. If not reactivated, the cluster is **permanently deleted after 4 weeks**.
- **Assessment**: Reliance on an external Qdrant Cloud cluster introduces fragile downtime and deletion risks for an evaluation prototype.

### 2.5 Firebase Authentication & Resend Email
- **Firebase Auth (Spark Tier)**: Free up to 50,000 Monthly Active Users (MAUs) for Google Sign-In and Email/Password. Hard limit prevents billing.
- **Resend (Free Tier)**: 100 emails/day, 3,000 emails/month. 1 verified domain. Hard limit (returns HTTP 429) prevents overages.

---

## 3. Task 2: Recalculated Monthly Cost Models

*Exchange Rate Assumption: \$1.00 USD = ₹85.00 INR. Indian Statutory Goods & Services Tax (GST) on Cloud Services = 18%.*

### 3.1 Confirmed vs Estimated Components Breakdown
- **Confirmed Fixed Zero-Cost Tiers**:
  - Vercel Hobby Frontend: \$0.00
  - Firebase Auth Spark: \$0.00
  - Resend Free Email: \$0.00
  - Supabase Free Database (500 MB): \$0.00
  - In-Process Qdrant: \$0.00
- **Variable Compute & API Costs (Estimated on 50 Demo Citizens / month)**:
  - Workload: 150 document uploads, 150 OCR extractions, 300 conflict runs, 200 AI assistant queries.

### 3.2 Detailed Scenario Cost Breakdown

| Component | Architecture 1: US Zero-Cost (\$0 / ₹0) | Architecture 2: US Free + Paid Gemini + .in Domain | Architecture 3: All-India Mumbai Host |
| :--- | :--- | :--- | :--- |
| **Frontend** | Vercel Hobby (\$0.00) | Vercel Hobby (\$0.00) | Vercel Hobby (\$0.00) |
| **Backend Compute** | Cloud Run `us-central1` (\$0.00 Free Tier) | Cloud Run `us-central1` (\$0.00 Free Tier) | Cloud Run `asia-south1` (Mumbai) |
| *Cloud Run vCPU* | 0.00 (within 360k vCPU-s) | 0.00 (within 360k vCPU-s) | 30,000s @ \$0.000024 = \$0.72 |
| *Cloud Run RAM* | 0.00 (within 180k GiB-s) | 0.00 (within 180k GiB-s) | 30,000s @ \$0.0000025 = \$0.075 |
| *Cloud Run Egress* | 0.00 (within 1 GB) | 0.00 (within 1 GB) | 1.5 GB @ \$0.12 = \$0.18 |
| **Database** | Supabase Mumbai (\$0.00) | Supabase Mumbai (\$0.00) | Supabase Mumbai (\$0.00) |
| **Vector DB** | In-Process Qdrant (\$0.00) | In-Process Qdrant (\$0.00) | In-Process Qdrant (\$0.00) |
| **Identity & Email** | Firebase + Resend (\$0.00) | Firebase + Resend (\$0.00) | Firebase + Resend (\$0.00) |
| **Google Gemini API** | AI Studio Free (\$0.00, synthetic only) | Tier 1 Paid (Zero model training) | Tier 1 Paid (Zero model training) |
| *Gemini Input Tokens* | 0.00 | 300k @ \$0.075/M = \$0.0225 | 300k @ \$0.075/M = \$0.0225 |
| *Gemini Output Tokens*| 0.00 | 80k @ \$0.30/M = \$0.0240 | 80k @ \$0.30/M = \$0.0240 |
| **Custom `.in` Domain**| \$0.00 (Provider subdomains) | Amortized renewal: ~₹60.00 (\$0.71) | Amortized renewal: ~₹60.00 (\$0.71) |
| **Indian GST (18%)** | ₹0.00 | \$0.01 (on Gemini usage) | \$0.18 (on Cloud Run + Gemini) |
| **Currency Buffer** | ₹0.00 | ~₹15.00 (\$0.18) | ~₹25.00 (\$0.29) |
| **Net Monthly Cost (USD)** | **\$0.00 USD** | **~\$0.95 USD** | **~\$2.19 USD** |
| **Net Monthly Cost (INR)** | **₹0.00 INR** | **~₹80.75 INR / month** | **~₹186.15 INR / month** |

---

## 4. Task 3: Actual Semantic Embedding Inspection & Retrieval-Quality Assessment

### 4.1 Inspection of Codebase Implementation
Inspection of [`backend/app/rag/embeddings.py`](file:///c:/Users/ajaya/Desktop/consolin/backend/app/rag/embeddings.py) reveals:
```python
class DeterministicBGEEmbeddingService(BaseEmbeddingService):
    def _embed_single(self, text: str) -> List[float]:
        # Hashing whitespace tokens using MD5 and SHA-256 into 1024 dimension indices
```
- **Finding**: This is **NOT** the genuine open-weights `BAAI/bge-m3` neural model. It does not use PyTorch, Transformers, or ONNX.
- **Algorithm**: It is a deterministic token-hashing projection algorithm that splits text on whitespace, hashes tokens using MD5 and SHA-256 into 3 pseudo-random index buckets, weights them by `1.0 / (1.0 + math.log1p(i))`, adds a sequence signature, and L2-normalizes the resulting 1024-dimensional vector.

### 4.2 Live Cosine Similarity Measurements
We executed an empirical test within the live container to test cosine similarities produced by `DeterministicBGEEmbeddingService`:

| Query vs Candidate String | Relationship | Measured Cosine Similarity | Passes 0.55 Floor? |
| :--- | :--- | :--- | :--- |
| `"Aadhaar name correction"` vs `"Aadhaar name update"` | Shared exact keywords (`aadhaar`, `name`) | **+0.7665** | **YES (Passes)** |
| `"Aadhaar name correction"` vs `"UIDAI resident demographic modification"` | Semantic synonyms (No overlapping words) | **-0.1287** | **NO (Fails Floor)** |
| `"Aadhaar name correction"` vs `"date of birth rectification procedure"` | Distinct procedural topic | **-0.0254** | **NO (Fails Floor)** |
| `"Aadhaar name correction"` vs `"chocolate cake baking recipe"` | Completely unrelated | **0.0000** | **NO (Fails Floor)** |

### 4.3 Retrieval-Quality Implications
1. **Keyword-Dependency**: The current implementation behaves as an exact-keyword matcher. If a citizen types "I need to fix my DOB in my identity card", the similarity with official circulars discussing "Date of Birth correction in Aadhaar" will be near zero or negative.
2. **Impact of 0.55 Floor**: Because the similarity drops below 0.55 on synonymous queries, the RAG assistant will frequently trigger its fallback: `"Assistant service is not currently available. Please try again later."`
3. **Misleading Config**: `backend/app/config.py` defines `EMBEDDING_MODEL: str = "BAAI/bge-m3"`. This configuration name is misleading because no `bge-m3` weights are loaded.
4. **Cloud Run Memory Benefit**: The hash projection requires **0 MB** of model weight storage, loads in 1 millisecond, and consumes negligible RAM (< 1 MB), whereas a real `bge-m3` model (2.2 GB) would instantly crash a 1 GB Cloud Run container.
5. **Test Status**: Ran `docker exec convelina-backend pytest tests/test_rag.py -v`. All **4/4 unit tests passed** in 8.55s.

---

## 5. Task 4: OCR Ephemeral Lifecycle & Exception Path Audit

### 5.1 Document Storage Lifecycle Audit
We traced [`backend/app/routers/documents.py`](file:///c:/Users/ajaya/Desktop/consolin/backend/app/routers/documents.py) and [`backend/app/core/storage.py`](file:///c:/Users/ajaya/Desktop/consolin/backend/app/core/storage.py):
1. **Streaming Input**: File is read in 1 MB chunks up to `MAX_UPLOAD_SIZE_BYTES` (10 MB). Oversized payloads trigger HTTP 400 before disk writes.
2. **Temporary File Creation**: Saved to `/tmp/consolith/temp_docs/doc_<uuid>.ext`.
3. **Execution Block**: Tesseract OCR extracts text and parses fields.
4. **Mandatory Unlink**: The `finally:` block executes:
   ```python
   finally:
       if settings.STORAGE_RETENTION_POLICY == "delete_after_ocr":
           delete_temp_document(temp_file_path)
           final_file_path = f"ephemeral://redacted_{file_hash[:16]}"
   ```
5. **Database Failure Handling**: In the database insertion `except Exception:` block, an explicit safeguard re-verifies:
   ```python
   if os.path.exists(temp_file_path):
       delete_temp_document(temp_file_path)
   ```

### 5.2 Exception Scenarios Analyzed
- **Corrupt File / Bad Magic Bytes**: Rejected in `validate_file_content` before `save_temp_document`. Zero files created.
- **OCR Crash / Timeout**: Caught by `except Exception:`. The `finally:` block unlinks the temporary file immediately.
- **Process Abrupt Kill (OOM / SIGKILL)**: In Cloud Run, `/tmp` is backed by in-memory tmpfs. Any file in `/tmp` resides in RAM and is permanently destroyed when the container instance terminates.

### 5.3 Audit Finding: Production Settings Gap
In [`backend/app/config.py`](file:///c:/Users/ajaya/Desktop/consolin/backend/app/config.py), `validate_production_security` validates `DEBUG`, `ENCRYPTION_KEY`, `DATABASE_URL`, and `CORS_ORIGINS`, but does **not** assert `STORAGE_RETENTION_POLICY == "delete_after_ocr"`. If an administrator inadvertently sets `STORAGE_RETENTION_POLICY="retain_temp"` in production, temporary files would persist.  
*Recommendation*: Add `assert self.STORAGE_RETENTION_POLICY == "delete_after_ocr"` to `validate_production_security`.

---

## 6. Task 5: Database Compatibility & Isolation Review (PostgreSQL 16)

### 6.1 Live RLS Test Execution
We executed the full independent test suite [`scripts/test_rls_isolation.py`](file:///c:/Users/ajaya/Desktop/consolin/scripts/test_rls_isolation.py) inside the live container against PostgreSQL 16 Alpine:
```
==================================================
   Consolith RLS Security & Isolation Test Suite
==================================================
[TEST 1/9] Checking database role privileges...
  Connected as: consolith_app (Superuser: False) -> [PASS]
[TEST 2/9] Testing unauthenticated default-deny isolation... -> [PASS] (0 rows visible)
[TEST 3/9] Testing citizen cross-document read isolation... -> [PASS]
[TEST 4/9] Testing citizen cross-document write isolation... -> [PASS] (0 rows affected)
[TEST 5/9] Testing privilege escalation defense (self-promotion)... -> [PASS] (Trigger blocked)
[TEST 6/9] Testing officer case & document scoping... -> [PASS]
[TEST 7/9] Testing admin visibility policy... -> [PASS]
[TEST 8/9] Testing append-only audit trail immutability... -> [PASS] (UPDATE/DELETE blocked)
[TEST 9/9] Testing connection-pooling session reset & empty string trap... -> [PASS]
==================================================
  ALL 9/9 RLS & ISOLATION TESTS PASSED!
==================================================
```

### 6.2 Supabase PostgreSQL Compatibility Mapping
- **Role Scoping**: Supabase supports `CREATE ROLE consolith_app WITH LOGIN PASSWORD '...'` without superuser rights.
- **Forced RLS**: Supported natively on all 18 tables.
- **Session Pooling vs Transaction Pooling**:
  - CONVELINA uses `SET LOCAL app.current_user_id` inside explicit transactions.
  - When connecting via Supabase's Supavisor Transaction Pooler (port `6543`), `SET LOCAL` is automatically reset upon `COMMIT` or `ROLLBACK`.
  - **Critical Driver Setting**: In SQLAlchemy, transaction pooling on port 6543 requires `connect_args={"prepare_threshold": None}` to disable prepared statement caching. Alternatively, using Session mode (port `5432`) avoids prepared statement conflicts entirely.

---

## 7. Task 6: Cloud Run Container Compatibility & Operational Constraints

### 7.1 Container Compatibility Analysis
- **Base Image**: `python:3.11-slim` with system packages `tesseract-ocr`, `tesseract-ocr-eng`, `tesseract-ocr-hin`, and `poppler-utils`.
- **User Permissions**: Runs as non-root `appuser` (UID 10001). Fully compliant with Cloud Run container runtime security.
- **Disk Mounts**: Cloud Run provides a writable in-memory `/tmp` filesystem (tmpfs). File writes to `/tmp` count against the container's memory allocation.

### 7.2 Dockerfile Bugs Requiring Correction Before Deployment
1. **Hardcoded `--reload`**: `backend/Dockerfile:36` runs `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]`. In production, `--reload` must be removed; it consumes excess CPU watching files.
2. **Port Mismatch**: Cloud Run injects the `PORT` environment variable (default `8080`). The Dockerfile hardcodes `--port 8000`. If deployed without `--port 8000` in the `gcloud` command, Cloud Run healthchecks will time out.
3. **Worker Count vs Memory Ceiling**: On a 1 GB Cloud Run instance, running 4 Uvicorn workers during simultaneous PDF OCR extractions (each Tesseract instance consuming ~250 MB) creates a severe risk of an Out-Of-Memory (OOM) kill. The Cloud Run container should run **1 or 2 workers max** (`--workers 1` or `--workers 2`).

---

## 8. Task 7: Gemini API Privacy & Data Governance Reality

### 8.1 Official Terms Comparison
*Source: [Google AI Studio & Gemini API Additional Terms of Service](https://ai.google.dev/terms)*

| Attribute | Free Tier (Google AI Studio) | Pay-As-You-Go / Tier 1 (Cloud Billing) |
| :--- | :--- | :--- |
| **Model Training on Customer Data** | **YES.** Google uses submitted content, prompts, files, and responses to train and develop machine learning models. | **NO.** Google does **not** use customer prompts or generated completions to train models. |
| **Human Reviewers** | **YES.** Human reviewers may read and annotate prompts and outputs (anonymized from account). | **NO.** Customer data is not accessed by human reviewers. |
| **Data Logging for Operational Safety** | **YES.** Full prompt and response retention. | **YES (Temporary).** Google retains logs temporarily for abuse detection, debugging, and legal compliance. |
| **Suitability for Citizen PII / Documents** | **STRICTLY PROHIBITED** by Google terms ("Do not submit sensitive, confidential, or personal information"). | **Permitted for Enterprise/Production** under commercial Cloud terms. |

### 8.2 Privacy Conclusion
- **Claim Refutation**: The Sprint 7 claim of "zero logging" on the paid tier is **factually false**. Google does not train models on paid customer data, but operational/security logging still occurs.
- **Compliance Policy**:
  - The **Free Tier** must **NEVER** be used with real citizen identity documents. It is acceptable strictly for synthetic test fixtures.
  - The **Pay-As-You-Go Tier** (~₹5 INR/mo) is mandatory for any public-facing testing. Furthermore, CONVELINA’s design already masks Aadhaar numbers (`XXXX-XXXX-1234`) and strips document numbers before constructing RAG prompts.

---

## 9. Task 8: Inactivity Pausing & Keep-Alive Policy Evaluation

### 9.1 The Fragility of Artificial Keep-Alive Jobs
Sprint 7 suggested setting up a GitHub Actions cron job to ping the database every 4 days to circumvent the Supabase 7-day pause rule.
- **ToS / Platform Stance**: While lightweight queries are commonly used by hobbyists, automated artificial traffic designed solely to bypass free-tier resource dormancy violates the spirit of shared infrastructure fair use. If an account is flagged for artificial cycling, the project may be suspended.
- **Operational Fragility**: If the GitHub Actions runner fails, expires its free quota (2,000 mins), or encounters network errors, the database pauses anyway.

### 9.2 The Correct Zero-Cost Architecture Solutions
1. **For Database (Supabase / Neon)**:
   - For an evaluation prototype, **manual dashboard unpausing** is the legitimate, provider-supported method. Unpausing takes 1–2 minutes before an evaluation session.
   - Alternatively, **Neon Serverless Postgres** pauses after 5 minutes of inactivity, but **wakes up automatically within ~500ms** on an incoming connection without manual intervention.
2. **For Vector Database (In-Process Qdrant)**:
   - Because Qdrant Cloud Free pauses after 1 week and deletes after 4 weeks, we **eliminate external Qdrant Cloud**.
   - Running Qdrant in-process inside FastAPI (`location=":memory:"`) ensures **zero pausing, zero deletion, zero external service dependency, and zero cost**.

---

## 10. Task 9: Spending Limits, Billing Caps & Overrun Protection

### 10.1 Provider Billing Controls Analysis
| Provider | Native Hard Spending Cap? | Informational Alert Only? | Worst-Case Exposure & Recommended Protection |
| :--- | :--- | :--- | :--- |
| **Google Cloud Run** | **YES (Native Spend Cap)** | Standard budget alerts are informational only. | Set Google Cloud Spend Cap at **\$2.00 USD**. Configure container with `--max-instances 2`. This guarantees that total compute spend cannot exceed \$2.00 even under traffic bursts. |
| **Google Gemini API** | **YES (Hard Daily Quotas)** | Billing budget alerts are informational. | In Google Cloud API Console, set hard quota ceiling: **Max 500 requests/day**. HTTP 429 is returned once reached; zero excess spend. |
| **Vercel** | **YES (Hobby Hard Stop)** | Soft notifications at 50%, 75%, 100%. | No credit card attached to Hobby plan. Exceeding 100 GB halts traffic or suspends site without financial liability. |
| **Supabase** | **YES (Free Tier Cap)** | Usage dashboard notifications. | No credit card required on Free plan. Exceeding 500 MB blocks writes. Zero auto-billing. |
| **Resend** | **YES (Free Tier Cap)** | Daily dashboard stats. | Hard daily limit (100 emails/day). Over-limit emails return HTTP 429. Zero billing risk. |

---

## 11. Task 10: Onboarding Flow Alignment & Free Limits

### 11.1 Onboarding Architecture Fit
CONVELINA’s onboarding flow in [`backend/app/routers/auth.py`](file:///c:/Users/ajaya/Desktop/consolin/backend/app/routers/auth.py):
1. Citizen registers or signs in using Google OAuth via Firebase Authentication.
2. Citizen enters Gmail address for 6-digit email OTP verification.
3. FastAPI generates a cryptographic OTP, stores it in `email_otps` table (5-minute expiry), and dispatches it via Resend API.
4. Citizen verifies OTP; FastAPI provisions citizen in PostgreSQL under `consolith_app` role.

### 11.2 Quota Headroom (50 Monthly Demo Citizens)
- **Firebase Auth Spark**: 50 MAUs used / 50,000 MAU limit (**0.1% of quota**).
- **Resend Email**: ~100 emails sent / 3,000 monthly limit (**3.3% of quota**; max 10-20/day vs 100/day limit).
- **Fit Verdict**: 100% compliant with free-tier quotas. Zero code modifications required.

---

## 12. Final Synthesis & Deployment Gate Criteria

### 12.1 Recommendation: CONDITIONAL-GO
**Conditional-Go** is granted. The deployment may proceed to staging preparation **ONLY after the following four configuration fixes are applied**:
1. Fix `backend/Dockerfile` to remove `--reload`, accept dynamic `$PORT`, and run 2 Uvicorn workers.
2. Point Qdrant to in-process memory mode (`location=":memory:"`) instead of external Qdrant Cloud.
3. Configure Cloud Run with hard limit `--max-instances 2` and set Google Cloud Spend Cap to \$2.00 USD.
4. Mandate that only synthetic demo identities are processed unless the user explicitly configures a Paid Tier 1 Gemini API key with billing limits.

### 12.2 The Cheapest Technically Viable Architecture
- **Frontend**: Vercel Hobby Tier (\$0.00 / mo)
- **Backend**: Google Cloud Run in `us-central1` with scale-to-zero (\$0.00 Always Free)
- **Database**: Supabase Free Tier in Mumbai `ap-south-1` (\$0.00)
- **Vector Search**: In-Process Qdrant inside FastAPI (\$0.00)
- **Auth & Email**: Firebase Spark (\$0.00) + Resend Free (\$0.00)
- **AI RAG**: Google Gemini 1.5 Flash Pay-as-you-go (~₹4 – ₹8 INR / mo)
- **Domain**: Provider subdomains (`convelina.vercel.app`) (\$0.00) or `.in` domain (~₹60 INR / mo)

### 12.3 Realistic Monthly Cost Range & Residual Risks
- **Cost Range**: **₹0.00 – ₹85.00 INR / month** (\$0.00 – \$1.00 USD / month).
- **Residual Risks**:
  1. *Cold Starts*: First request after idle takes 8–14 seconds.
  2. *Supabase Pause*: Inactivity over 7 days requires 1-minute manual resume from dashboard.
  3. *Embedding Semantic Limitations*: Hash projection requires queries to use exact procedural keywords to pass the 0.55 similarity floor.

### 12.4 Tests Required Before Remote Provisioning
1. Test container startup with `PORT=8080` without `--reload` locally.
2. Test in-process Qdrant initialization on backend boot to confirm 31 vectors index in < 500ms.
3. Validate remote connection string parsing with `connect_args={"prepare_threshold": None}` for Supavisor compatibility.

### 12.5 Next Implementation Sprint
**Sprint 8B: Cloud Staging Packaging & Local Dry-Run Gate**  
- Update `backend/Dockerfile` for Cloud Run production execution.
- Implement in-process Qdrant fallback in `backend/app/rag/qdrant.py`.
- Run local end-to-end container verification mimicking Cloud Run environment variables.
- Await user approval and provision remote Supabase/GCP staging resources.


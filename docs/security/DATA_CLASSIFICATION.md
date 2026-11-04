# CONVELINA — Data Classification & Handling Policy

**Classification:** Information Security & Privacy Governance  
**Compliance Standard:** Aadhaar Act (2016), Information Technology Act (2000), Digital Personal Data Protection Act (DPDPA 2023)  
**Status:** ENFORCED IN CODE  

---

## 1. Data Classification Tiers

```
┌────────────────────────────────────────────────────────────────────────┐
│                   TIER 1: HIGHLY RESTRICTED PII                        │
│   • 12-digit Aadhaar Numbers                                           │
│   • Raw Scanned Identity Document Files & Images                       │
│   • Cryptographic Private Keys (Fernet secret key, Ed25519 private key)│
│   Handling: Zero persistent storage of raw scans; first 8 digits masked │
│             (XXXX-XXXX-1234); ephemeral file unlinking; KMS isolation.  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   TIER 2: CONFIDENTIAL CITIZEN PII                     │
│   • Masked Identity Numbers (Aadhaar XXXX-XXXX-1234, PAN AB***1234F)  │
│   • Full Name, Date of Birth, Gender, Father/Mother Name, Address      │
│   • Extracted OCR payload fields, Discrepancy comparison pairs         │
│   Handling: Encrypted at rest via Fernet; Forced Row-Level Security;   │
│             connection-pooling safe user scoping; cascade deletion.    │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  TIER 3: OPERATIONAL & FORENSIC DATA                   │
│   • Append-only Audit Log records and SHA-256 hash chains              │
│   • Case workflow transitions, Officer review timestamps               │
│   • Document fingerprints (SHA-256) and Ed25519 digital signatures     │
│   Handling: Trigger-blocked mutation (UPDATE/DELETE prohibited);       │
│             cryptographically linked; forensic integrity preservation. │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               TIER 4: PUBLIC & STATUTORY REFERENCE DATA                │
│   • Official government forms catalog (Form 49A, Annexures, Joint Decl)│
│   • Verified statutory circulars, gazette procedures, prerequisites   │
│   • Active Ed25519 Public Keys and Verification status endpoints       │
│   Handling: Unrestricted read access across authenticated users;       │
│             cached in Qdrant vector index and PostgreSQL.              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Statutory Aadhaar Act (2016) Compliance Protocol

### 2.1 Storage Prohibition
In strict adherence to Section 29 of the Aadhaar (Targeted Delivery of Financial and Other Subsidies, Benefits and Services) Act, 2016:
* **Zero Long-Term Storage**: No raw image or PDF file of an Aadhaar card is ever stored permanently on disk, database, or object store.
* **Ephemeral Ingestion**: Uploaded files reside in `/tmp/consolith/temp_docs/<uuid>` with restricted POSIX permissions (`0600`). Following OCR extraction, the temporary file is shredded and unlinked in a mandatory `finally:` block.

### 2.2 Algorithmic Redaction & Checksum
* The OCR parser extracts candidate 12-digit strings and executes the **Verhoeff Checksum Algorithm** to confirm Aadhaar validity.
* Valid Aadhaar numbers are immediately redacted: the first 8 digits are replaced with `XXXX-XXXX-`, persisting and displaying strictly the last 4 digits (`XXXX-XXXX-1234`).
* Under no circumstances do application logs, console traces, or database records contain unmasked 12-digit Aadhaar numbers.

---

## 3. Data Retention & Cryptographic Erasure Lifecycle

| Entity | Retention Period | Storage Medium | Deletion / Erasure Mechanism |
| :--- | :--- | :--- | :--- |
| **Raw Upload Files** | Ephemeral (< 30 seconds) | Local `/tmp` filesystem (0600) | Unlinked via `os.unlink()` immediately following OCR extraction. |
| **Extracted Field Payloads** | Active Citizen Account | PostgreSQL (`documents` table) | Encrypted at rest via Fernet; cascade deleted on account removal. |
| **Detected Discrepancies** | Active Citizen Account | PostgreSQL (`conflicts` table) | Cascade deleted upon account removal or document deletion. |
| **Assistant Conversations** | Active Citizen Account | PostgreSQL (`assistant_conversations`) | Deleted on citizen request via REST API or account deletion. |
| **Audit Log Entries** | 7 Years (Statutory Audit) | PostgreSQL (`audit_log` table) | Retained with immutable SHA-256 hash chains; UPDATE/DELETE trigger blocked. |
| **Digital Attestations** | Indefinite / Until Revocation | PostgreSQL (`document_attestations`)| Stores only SHA-256 document fingerprint and Ed25519 signature (zero raw PII). |


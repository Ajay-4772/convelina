# Architecture Overview

```
                      CITIZEN / OFFICER / ADMIN
                                 │
                                 ▼
                     Next.js 14 Web Frontend
                  (TypeScript, Tailwind CSS)
                                 │
                                 ▼
                   FastAPI Application Server
               (Pydantic v2 strict validation)
                                 │
     ┌───────────────────────────┼───────────────────────────┐
     ▼                           ▼                           ▼
Document Pipeline          RAG Pipeline               Workflow Engine
(Tesseract OCR +          (Qdrant vector DB +       (Verification Cases,
 RapidFuzz + Jellyfish)    BGE-M3 + Claude)          Officer Attestation)
     │                           │                           │
     └───────────────────────────┼───────────────────────────┘
                                 ▼
                    PostgreSQL 16 Database
                  • Forced Row-Level Security
                  • Dedicated App Role (consolith_app)
                  • Append-Only Audit Trail
                  • Ed25519 PKI Attestation Records
```

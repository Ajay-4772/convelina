# CONVELINA — Master Architecture Diagram Prompts

This document provides production-ready, highly detailed prompts engineered for generating enterprise architecture diagrams in the **ByteByteGo / Alex Xu** style and the **Microservices Pipeline Journey** style on a **pure white background (`#FFFFFF`)**.

These prompts are calibrated for:
1. **AI Image Generators**: Ideogram 2.0 (recommended for text rendering), Midjourney v6, Google Imagen 3, DALL-E 3.
2. **Architecture Diagramming Tools**: Eraser.io, Napkin.ai, Lucidchart, Excalidraw.

---

## Prompt 1: ByteByteGo / Alex Xu Production System Architecture

### Best Suited For: Ideogram 2.0 / Midjourney v6 / DALL-E 3
*Recommended Aspect Ratio:* `--ar 16:9` or `--aspect 16:9`  
*Recommended Engine:* Ideogram 2.0 (handles text and logos accurately)

```text
A professional software architecture diagram in the clean ByteByteGo and Alex Xu technical infographic style, set against an ultra-crisp pure white background (#FFFFFF). 

The composition is an interconnected, end-to-end production web application architecture for "CONVELINA", featuring modern flat 2D vector icons, rounded rectangle service cards with subtle borders (#CBD5E1), and directional dashed and solid connecting arrows with numbered circular step badges (1, 2a, 2b, 3, 4, 5, 6, 7, 8, 9, 10).

LAYOUT & COMPONENTS:
- Top Left: "Developers" node with laptop and VS Code icon, connecting to "CI/CD Pipeline" (Git and Docker icons) with step circle "1".
- Top Center: "Citizen & Officer Clients" (clean user avatar icons in circular badges), sending HTTPS/TLS 1.3 traffic to "Edge Load Balancer & Proxy" with step circle "2a".
- Edge Tier: "Caddy 2.8 Reverse Proxy" card with TLS lock icon and "15MB Limit" badge, routing traffic downwards.
- Web Tier: "Web App Servers" card featuring the Next.js 14 and React logos, connected via arrow "3" from Caddy.
- API Tier: "FastAPI Backend Core" server card featuring the Python and FastAPI lightning logos, connected via arrow "4".
- Top Right: "Identity & OTP" box showing the Firebase Auth flame icon and Resend Email envelope icon, connected via dashed lines.
- Subsystem Engines Tier (Center Row of 4 distinct connected nodes):
  1. "Tesseract 5.5 OCR" card with document scanner icon and "Aadhaar Act 29 Shred" badge.
  2. "RapidFuzz SIMD Engine" card with red lightning bolt icon and "Double Metaphone" badge.
  3. "Qdrant Vector DB" card with 3D red vector cube icon, connected to "Gemini 1.5 Flash" with AI sparkle star icon (badge "Floor >= 0.55").
  4. "Ed25519 PKI" card with purple security shield icon and "Verifiable QR" badge.
- Persistence Tier (Bottom Row):
  - Large database cylinder stack labeled "PostgreSQL 16 (Forced RLS)" with a green security shield icon and label "consolith_app".
  - Chained blocks labeled "SHA-256 Immutable Audit Ledger" with chain-link icons, connected to PostgreSQL by step circle "10".

STYLE & COLOR PALETTE:
- Background: 100% solid clean white (#FFFFFF), zero vignette, zero shadows, high contrast.
- Color Accents: Deep slate navy (#0F172A), vibrant teal (#009688), cyan (#0EA5E9), emerald green (#10B981), coral red (#E63946), violet (#8B5CF6).
- Typography: Sans-serif Segoe UI / Inter style, crisp, bold headings, no cluttered paragraphs.
- Aesthetic: Technical book illustration, software engineering textbook graphic, clean lines, professional presentation standard.
```

### Negative Prompt (for Midjourney / Stable Diffusion):
```text
--no dark background, black background, chaotic lines, 3d realistic render, photorealistic, messy handwriting, blurry text, low contrast, text walls, overlapping boxes, drop shadows, gradient background
```

---

## Prompt 2: End-to-End Microservices Pipeline Journey

### Best Suited For: Ideogram 2.0 / Midjourney v6 / Imagen 3
*Recommended Aspect Ratio:* `--ar 16:9`

```text
A sleek, modern technical architecture journey and data pipeline infographic on a pure white background (#FFFFFF), illustrating the chronological path of document verification in a high-assurance identity platform called "CONVELINA".

COMPOSITION (LEFT-TO-RIGHT FLOWING PIPELINE):
A glowing cyan-and-slate main data pipeline rail runs horizontally across the canvas with colored junction nodes, flowing direction arrows, and sequential step indicators:

1. [INCOMING REQUEST]: A glowing traffic beam from "Citizen Client" (Next.js 14 / React icon) entering the pipeline at Step 1.
2. [EDGE GATEWAY]: A clean gateway portal node labeled "Caddy 2.8 Reverse Proxy" with a padlock icon (Auto-TLS 1.3) and DoS shield (15MB Ceiling) at Step 2.
3. [ASYNC API CORE]: The pipeline flows into "FastAPI Application Core" (Python 3.11 logo and FastAPI teal badge) with Uvicorn async event loop at Step 3.
   - An upward dashed branch connects to "Firebase Auth" (amber flame icon) and "Resend Email OTP" (envelope icon).
4. [COGNITIVE PROCESSING JUNCTION]: The pipeline branches into three parallel processing engines:
   - Branch A: "Tesseract 5.5 OCR" (scanner icon) -> "Verhoeff Aadhaar Masking" -> "Atomic File Shredding" (shredder icon).
   - Branch B: "RapidFuzz SIMD AVX2" (red lightning icon) -> "Jellyfish Double Metaphone" phonetic matching.
   - Branch C: "Qdrant Vector DB" (isometric cube icon) -> "Google Gemini 1.5 Flash" (AI sparkle icon, badge "Score >= 0.55").
5. [PERSISTENCE GATEWAY]: All three processing branches re-converge into a prominent database cylinder labeled "PostgreSQL 16 Alpine" featuring a green security shield labeled "Kernel Forced RLS" and user role "consolith_app" at Step 4.
6. [PUBLIC VERIFICATION & AUDIT]: The pipeline terminates at:
   - "Ed25519 PKI Attestation" (purple key icon) emitting a "Verifiable QR Code".
   - "Append-Only Audit Ledger" with cryptographic SHA-256 chain links protected by database triggers.

STYLE DIRECTIVES:
- Pure white background (#FFFFFF) with high-contrast colored vector components.
- Modern enterprise tech diagram, AWS architecture style combined with Stripe documentation aesthetics.
- Crisp vector iconography, clean labeled connector arrows, bold typography, zero clutter.
```

---

## Prompt 3: Eraser.io / Napkin.ai Text-to-Diagram Specification

If you use **Eraser.io**, **Napkin.ai**, or **Lucidchart AI**, paste the following structured architectural definition directly into their diagram prompt box:

```text
Generate a production architecture diagram on a white background for an identity verification web app named CONVELINA.

Nodes:
1. [Client] Citizen & Officer Browsers (Next.js 14, React 18, Tailwind CSS)
2. [Edge] Caddy 2.8 Reverse Proxy (Auto-TLS 1.3, Rate Limiter, 15MB Limit)
3. [API] FastAPI Backend Core (Python 3.11, Uvicorn, Pydantic v2 Rust)
4. [Auth] Firebase Auth (RS256 JWT) & Resend Email (OTP)
5. [OCR] Tesseract 5.5 OCR Engine (Poppler C++, Aadhaar Masking, Ephemeral POSIX 0600)
6. [Conflict] SIMD Conflict Engine (RapidFuzz AVX2, Jellyfish Double Metaphone)
7. [VectorDB] Qdrant Vector Database (HNSW, 25 Legal Circulars, 1024-dim dense vectors)
8. [AI] Google Gemini 1.5 Flash (Grounded Legal Guidance, Floor >= 0.55)
9. [Database] PostgreSQL 16 Alpine (Kernel Forced RLS, Role: consolith_app, SET LOCAL pooling)
10. [PKI] Ed25519 PKI Attestation (RFC 8032 Signature, Offline Verifiable QR Code)
11. [Audit] Immutable Audit Ledger (Trigger Block UPDATE/DELETE, SHA-256 Hash Chain)

Connections:
- Client -> Edge: HTTPS / TLS 1.3 (Port 443) [Step 1]
- Edge -> Client: Reverse Proxy / [Step 2a]
- Edge -> API: Reverse Proxy /api/* [Step 2b]
- API -> Auth: Bearer Token Claims & OTP Verification
- API -> OCR: Ephemeral Multipart Upload [Step 3]
- API -> Conflict: Trigger Cross-Document Matching [Step 4]
- API -> VectorDB: Cosine Vector Search [Step 5]
- VectorDB -> AI: Grounded Legal Circular Chunks (Score >= 0.55)
- AI -> Database: Store Grounded Answer
- OCR -> Database: Insert Fernet AES-256 Encrypted Records (Aadhaar Shredded) [Step 6]
- Conflict -> Database: Idempotent Conflict Upsert (uq_conflicts_pair_field) [Step 7]
- API -> PKI: Officer Approves Dossier [Step 8]
- PKI -> Database: Save Digital Attestation [Step 9]
- Database -> Audit: Statement Trigger Cryptographic SHA-256 Link [Step 10]

Layout:
- Left-to-right flow from Client to Edge to API.
- API in center distributing to OCR, Conflict, VectorDB/AI, and PKI.
- Convergence into PostgreSQL Database and Audit Ledger at bottom right.
- Clean white background, modern soft-rounded cards, prominent tech badges, numbered flow circles.
```

---

## Prompt 4: Napkin.ai / Excalidraw Prompt

```text
Create a clean, hand-crafted yet professional technical system architecture flowchart for "CONVELINA" on a pure white background.

Flow:
[Citizen Browser] -> [Caddy Edge Proxy (TLS 1.3)] -> [FastAPI Backend]
[FastAPI Backend] -> [Tesseract OCR (Aadhaar Masking)] -> [PostgreSQL 16 (Forced RLS)]
[FastAPI Backend] -> [RapidFuzz SIMD Conflict Engine] -> [PostgreSQL 16 (Forced RLS)]
[FastAPI Backend] -> [Qdrant Vector DB] -> [Google Gemini 1.5 Flash] -> [PostgreSQL 16]
[FastAPI Backend] -> [Ed25519 PKI Digital Signature] -> [Verifiable QR Code]
[PostgreSQL 16] -> [SHA-256 Immutable Audit Log (Trigger Block UPDATE/DELETE)]

Visual Style:
- White canvas
- Minimalist rounded cards
- Blue and teal accent colors
- Numbered circular badges (1 to 10) on connecting lines
- Clear, readable typography
```


# CONVELINA — Frontend Architecture & Citizen/Officer Workspace Specification

```
+---------------------------------------------------------------------------------------------------------+
| PRESENTATION TIER: Next.js 14 App Router | TypeScript 5.4 | React 18 | Tailwind CSS | Framer Motion    |
+---------------------------------------------------------------------------------------------------------+
```

**Classification:** Technical Architecture Specification  
**Component:** `frontend/`  
**Status:** Production Verified | 16/16 Playwright E2E Tests Passing  

---

## 1. Executive Overview

The CONVELINA frontend is a high-assurance web application built on **Next.js 14 (App Router)** and **TypeScript 5**. It serves two primary user interfaces:
1. **Citizen Verification Workspace**: Document upload, OCR extraction review, interactive discrepancy matrix, RAG-grounded legal assistant chat, and affidavit document generator.
2. **Officer Verification Console**: Case review worklists, forensic document inspection, Ed25519 PKI digital attestation issuance, and immutable audit trail exploration.

---

## 2. Directory Structure & Route Hierarchy

```
frontend/
├── src/
│   ├── app/                                  # Next.js 14 App Router Dynamic Pages
│   │   ├── layout.tsx                        # Global HTML shell & Inter font injection
│   │   ├── globals.css                       # Tailwind design tokens & glassmorphism utilities
│   │   ├── page.tsx                          # Public Landing Page & Showcase Tabs
│   │   ├── login/page.tsx                    # Citizen & Officer Login
│   │   ├── signup/page.tsx                   # Citizen Registration & Gmail verification
│   │   ├── admin/page.tsx                    # Role-guarded Admin Dashboard
│   │   └── app/                              # Protected Workspace Root Layout
│   │       ├── layout.tsx                    # Authenticated Workspace Shell & Sidebar
│   │       ├── page.tsx                      # Citizen Home Overview & Active Cases
│   │       ├── inconsistencies/page.tsx      # Discrepancy Matrix & Side-by-Side Comparison
│   │       ├── assistant/                    # RAG Legal Guidance Chatbot
│   │       │   ├── page.tsx                  # New conversation launcher
│   │       │   └── [conversationId]/page.tsx # Active chat session & citation explorer
│   │       ├── forms/                        # Official Government Correction Forms Catalog
│   │       │   ├── page.tsx                  # Circulars & forms grid
│   │       │   └── [formId]/page.tsx         # Detailed procedural breakdown
│   │       └── profile/page.tsx              # Citizen Security, Masked PII & Right-to-Delete
│   ├── components/                           # Reusable Reactive Components
│   │   ├── workspace/                        # WorkspaceShell, WorkspaceSidebar, WorkspaceHeader
│   │   ├── assistant/                        # AssistantWorkspace, CitationBadges, GroundedCards
│   │   ├── landing/                          # InteractiveShowcaseTabs, FeatureGrid
│   │   └── ui/                               # Atomic primitives (Button, Card, Badge, Modal, Logo)
│   ├── context/
│   │   └── AuthContext.tsx                   # Firebase Auth state listener, RBAC context & user profile
│   └── lib/
│       ├── api.ts                            # Central typed HTTP client with bearer tokens & error handling
│       └── firebase.ts                       # Firebase Web SDK initialization
├── e2e/                                      # Playwright End-to-End Browser Automation (16/16 suites)
├── public/                                   # Static public assets (SVGs, favicon)
├── package.json                              # Node dependencies
├── tsconfig.json                             # Strict TypeScript configuration
└── Dockerfile                                # Multi-stage production container build
```

---

## 3. Client State & Authentication Architecture

Authentication is managed via [`frontend/src/context/AuthContext.tsx`](file:///c:/Users/ajaya/Desktop/consolin/frontend/src/context/AuthContext.tsx):
- **Firebase Auth Integration**: Listens for auth state changes, retrieves ID tokens with RS256 claims, and populates role metadata (`citizen`, `officer`, `admin`).
- **Simulated Development Mode**: When `NEXT_PUBLIC_ALLOW_SIMULATED_TOKENS=true`, local developers can toggle between mock citizen and officer profiles without live cloud credentials.
- **Route Guards**: Workspace layouts automatically redirect unauthenticated users to `/login` and non-officer accounts away from `/admin`.

---

## 4. API Client & Security Boundaries

The centralized HTTP client in [`frontend/src/lib/api.ts`](file:///c:/Users/ajaya/Desktop/consolin/frontend/src/lib/api.ts) enforces:
- **Automatic Token Injection**: Every request automatically includes `Authorization: Bearer <token>`.
- **Zero Client Secret Storage**: Private keys, Firebase service accounts, and encryption keys are strictly omitted from frontend builds.
- **Structured Error Handling**: Catches HTTP 401 (token expiration) and triggers automatic redirect; handles 413 (payload too large) and 429 (rate limited).

---

## 5. Development & Testing Commands

```bash
# Run local development server (Port 3000)
npm run dev

# Run production build & verify TypeScript typing
npm run build

# Start production server
npm start

# Run Playwright End-to-End browser test suite
npx playwright test
```


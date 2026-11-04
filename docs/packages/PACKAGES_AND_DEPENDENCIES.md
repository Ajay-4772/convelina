# CONVELINA — Packages, Dependencies & Tooling Inventory

```
+---------------------------------------------------------------------------------------------------------+
| DEPENDENCY AUDIT: Python Backend Manifest | Node.js Frontend Manifest | Build Tools & Static Linters     |
+---------------------------------------------------------------------------------------------------------+
```

**Classification:** Technical Dependency Specification  
**Component:** `backend/requirements.txt` & `frontend/package.json`  
**Status:** Audited | Zero High-Severity Vulnerabilities  

---

## 1. Backend Python Dependencies (`backend/requirements.txt`)

| Package | Version | Purpose & Architectural Role | License |
| :--- | :--- | :--- | :--- |
| `fastapi` | `^0.110.0` | High-performance asynchronous REST API framework | MIT |
| `uvicorn[standard]` | `^0.28.0` | Production ASGI web server running with `uvloop` | BSD |
| `pydantic` | `^2.6.0` | Rust-core data validation, request parsing, and type coercion | MIT |
| `pydantic-settings` | `^2.2.0` | Environment variable parsing and type enforcement | MIT |
| `sqlalchemy` | `^2.0.28` | Database ORM, connection pooling, and session lifecycle | MIT |
| `psycopg2-binary` | `^2.9.9` | PostgreSQL database driver | LGPL |
| `pytesseract` | `^0.3.10` | Python interface to native Tesseract 5.5 OCR C++ engine | Apache 2.0 |
| `pdf2image` | `^1.17.0` | Wraps Poppler `pdftoppm` utility to render PDF pages into images | MIT |
| `pillow` | `^10.2.0` | Image processing, resizing, format conversion, and binarization | HPND |
| `opencv-python-headless` | `^4.9.0` | Computer vision preprocessing (denoising, contrast stretching) | Apache 2.0 |
| `rapidfuzz` | `^3.6.1` | C++ AVX2 SIMD-accelerated Levenshtein and Token Sort Ratio | MIT |
| `jellyfish` | `^1.0.3` | Double Metaphone phonetic matching for Indian naming variations | BSD |
| `cryptography` | `^42.0.5` | Ed25519 digital signatures (RFC 8032) and Fernet AES-256 encryption | Apache 2.0 |
| `firebase-admin` | `^6.5.0` | Google Firebase Admin SDK for RS256 JWT decoding | Apache 2.0 |
| `httpx` | `^0.27.0` | Async HTTP client for external API requests (Gemini, Resend) | BSD |
| `qdrant-client` | `^1.8.0` | Official client for Qdrant vector database (supports memory mode) | Apache 2.0 |
| `python-docx` | `^1.1.0` | Server-side generator for citizen affidavits and reports | MIT |
| `pytest` & `pytest-asyncio` | `^8.1.0` | Asynchronous test framework for backend unit and RLS test suites | MIT |

---

## 2. Frontend Node.js Dependencies (`frontend/package.json`)

| Package | Version | Purpose & Architectural Role | License |
| :--- | :--- | :--- | :--- |
| `next` | `^14.2.14` | React framework for Server-Side Rendering (SSR) and routing | MIT |
| `react` & `react-dom` | `^18.3.1` | Reactive UI component library | MIT |
| `typescript` | `^5.4.0` | Static typing and compile-time contract enforcement | Apache 2.0 |
| `tailwindcss` | `^3.4.1` | Utility-first CSS framework and design token system | MIT |
| `lucide-react` | `^0.359.0` | Lightweight, accessible SVG micro-icons | ISC |
| `framer-motion` | `^11.0.8` | Hardware-accelerated UI transitions and micro-interactions | MIT |
| `firebase` | `^10.9.0` | Client-side Firebase Authentication SDK | Apache 2.0 |
| `@playwright/test` | `^1.42.1` | End-to-end multi-browser test automation framework | Apache 2.0 |
| `postcss` & `autoprefixer` | `^8.4.35` | CSS processing pipeline | MIT |

---

## 3. Dependency Security Auditing
- **Python Vulnerability Scanning**: Run `pip-audit` or `safety check` across `backend/requirements.txt`.
- **Node.js Vulnerability Scanning**: Run `npm audit` across `frontend/package.json`.
- **AST Pre-Push Review**: OpenQodex scans pinned dependencies via `OSV-Scanner` and `Bandit` prior to version control merges.


# CONVELINA

<div align="center">
  <h3><strong>Connect. Manage. Evolve.</strong></h3>
  <p><em>Modular, AI-powered business management platform uniting operations, auditing, verification, and workflow intelligence into one system.</em></p>
</div>

---

## 1. Brand Identity

- **Application Name**: CONVELINA
- **Tagline**: *Connect. Manage. Evolve.*
- **Brand Meaning**:
  - **Con**: Connection & Convergence — bringing business operations and distributed records together.
  - **Vel**: Velocity — enabling faster, automated, and more efficient verification workflows.
  - **Ina**: Intelligence & Innovation — leveraging RAG and AI models to support smarter decisions.
- **Brand Vision**: *"Simplify business management by connecting every operation through one intelligent platform."*
- **Brand Mission**: *"Empower businesses with integrated tools, real-time insights, and intelligent automation."*

---

## 2. Platform Architecture

CONVELINA is engineered with enterprise security, non-superuser least privilege, and cryptographic immutability:

- **Frontend**: Next.js 14 App Router, TypeScript, Tailwind CSS, Framer Motion, Lenis smooth scrolling.
- **Backend API**: FastAPI (Python 3.11), Uvicorn, Pydantic v2.
- **Database**: PostgreSQL 16 with Row-Level Security (RLS) forced across all user-data tables and access restricted to the non-superuser role `consolith_app`.
- **Vector Database**: Qdrant v1.11.0 (Hybrid dense + lexical retrieval with >= 0.55 relevance floor).
- **Authentication**: Firebase Admin SDK token verification, strict role-based access control (Citizen, Officer, Admin), and 6-digit email OTPs.
- **Cryptography & PKI**: Ed25519 digital signatures, RFC 8785 canonical JSON serialization, and SHA-256 hash-chained append-only audit trail.

---

## 3. Quickstart & Deployment

### Prerequisites
- Docker Engine & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Running with Docker Compose
```bash
# Build and launch all services in detached mode
docker compose up -d

# Verify container health
docker ps
```

The stack exposes:
- **Web Application**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
- **PostgreSQL**: Port 5432
- **Qdrant**: Port 6333 / 6334

---

## 4. Renaming Local Folder & GitHub Repository

If you wish to align your local directory and GitHub repository with the official brand name:

### A. Rename GitHub Repository
1. Navigate to your repository settings on GitHub (`https://github.com/Ajay-4772/consolin/settings`).
2. Under **General** > **Repository name**, change `consolin` to `convelina` (or `CONVELINA`) and click **Rename**.
3. Update your local git remote URL:
   ```bash
   git remote set-url origin https://github.com/Ajay-4772/convelina.git
   ```

### B. Rename Local Folder
1. Close open terminals and editors that reference `C:\Users\ajaya\Desktop\consolin`.
2. Rename the directory from `consolin` to `convelina`:
   ```powershell
   Rename-Item -Path "C:\Users\ajaya\Desktop\consolin" -NewName "convelina"
   ```
3. Reopen the folder in your IDE.

---

## 5. License & Statutory Notice

© 2026 CONVELINA. All rights reserved.  
*Disclaimer: CONVELINA is an independent assistance and operations platform. It is not affiliated with UIDAI, the Income Tax Department, EPFO, or any statutory authority.*

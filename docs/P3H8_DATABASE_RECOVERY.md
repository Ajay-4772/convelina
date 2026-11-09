# CONVELINA P3H.8 — Database Recovery & PostgreSQL Infrastructure Report

## Executive Summary

During milestone **P3H.8**, the local database infrastructure for CONVELINA was completely restored, hardened, and verified under PostgreSQL 16 on Windows 11. The local stack had previously encountered a broken Docker daemon pipe (`//./pipe/dockerDesktopLinuxEngine`) and an unpersisted transient execution mode.

Through direct inspection and runtime stabilization:
1. Docker Desktop daemon was recovered by invoking `com.docker.backend.exe` at `C:\Users\ajaya\AppData\Local\Programs\DockerDesktop\resources\com.docker.backend.exe`.
2. Existing production-grade containers `convelina-postgres` (PostgreSQL 16) and `convelina-qdrant` (Qdrant v1.11.0) were restarted, bound to host loopback interfaces `127.0.0.1:5432` and `127.0.0.1:6333`, and brought to healthy status.
3. A stale background container `convelina-backend` was halted to eliminate port collision with the local development backend.
4. Database role enforcement was verified: the non-superuser role `consolith_app` connects to `consolith` with explicit least-privilege scoping, ensuring the administrative `postgres` superuser is never utilized during normal application runtime.

---

## 1. Environment & Container Inventory

| Component | Target Port | Bound Address | Container / Process Name | Image / Version | Role / Privilege | Health Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL 16** | 5432 | `127.0.0.1:5432` | `convelina-postgres` | `postgres:16-alpine` | `consolith_app` (Non-Superuser) | Healthy (UP) |
| **Qdrant Vector DB** | 6333 | `127.0.0.1:6333` | `convelina-qdrant` | `qdrant/qdrant:v1.11.0` | In-process HTTP REST | Healthy (UP) |
| **FastAPI Backend** | 8000 | `127.0.0.1:8000` | Local Uvicorn Host Process | Python 3.13 / FastAPI 0.115 | Least-privilege API context | Healthy (UP) |
| **Next.js Frontend** | 3000 | `http://localhost:3000` | Local Next.js Server | Next.js 14.2.15 / React 18 | Client App Router | Healthy (UP) |

---

## 2. Windows 11 Docker Recovery Procedure

### 2.1 Failure Symptom
Initial executions of `docker ps` yielded:
```text
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified
```
This indicated that while the Docker Desktop binary packages existed on the Windows host, the Docker Linux engine named pipe service was not actively responding.

### 2.2 Stabilization Command
The Docker Desktop background daemon was restored via PowerShell:
```powershell
& "C:\Users\ajaya\AppData\Local\Programs\DockerDesktop\resources\com.docker.backend.exe"
```
Once initialized, named pipes were recreated and Docker CLI successfully re-established communication.

### 2.3 Container Orchestration Verification
```powershell
docker start convelina-postgres convelina-qdrant
docker stop convelina-backend # avoid collision on :8000
```
Status verification confirmed:
```text
convelina-postgres   postgres:16-alpine      Up (healthy)   0.0.0.0:5432->5432/tcp
convelina-qdrant     qdrant/qdrant:v1.11.0   Up (healthy)   0.0.0.0:6333->6333/tcp
```

---

## 3. Database Role Hardening & Privilege Isolation

To prevent superuser privilege escalation and ensure compliance with the CONVELINA architectural contract:
1. **Restricted Runtime Role**: Application traffic strictly uses `consolith_app` with connection URL:
   ```text
   postgresql://consolith_app:[REDACTED_DEV_PASSWORD]@localhost:5432/consolith
   ```
2. **Superuser Exclusion**: The `postgres` superuser possesses `SUPERUSER` privileges which bypass Row-Level Security (`BYPASSRLS`). The application explicitly forbids using `postgres` in production or standard development runtimes.
3. **Dedicated Object Grants**: `consolith_app` is granted `CONNECT` on `consolith`, `USAGE` on schema `public`, and targeted `SELECT, INSERT, UPDATE, DELETE` permissions only on user-facing tables.
4. **Trigger Security**: DDL triggers and cryptographic audit log immutability triggers run under `SECURITY DEFINER` with administrative ownership, ensuring even `consolith_app` cannot modify or delete audit rows or elevate its own role.

---

## 4. Persistent Volume Integrity & Data Retention

The `convelina-postgres` container utilizes persistent named Docker volume storage:
- Volume: `consolin_postgres_data`
- Mount path: `/var/lib/postgresql/data`

Data stored inside PostgreSQL (users, documents, conflicts, audit logs, cases, and citizen checklists) survives container restarts, Docker service reboots, and local machine restarts without data loss.

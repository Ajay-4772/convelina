# CONVELINA — Phase 1: Repository & Authentication Audit Report

**Date**: 2026-11-09  
**Repository**: `C:\Users\ajaya\Desktop\consolin`  
**Remote**: `https://github.com/Ajay-4772/convelina.git`  
**Branch**: `main` (clean sync with upstream)  

---

## 1. Executive Summary

A comprehensive pre-implementation audit was conducted across the frontend (Next.js 14), backend (FastAPI), database (PostgreSQL with forced RLS), and Firebase configuration. The system possesses a sound foundation with no duplicate authentication infrastructure. This audit identifies key components to reuse, enhancements required for Google Sign-In and account linking, and safeguards against credential leakage and privilege escalation.

---

## 2. Component Audit Findings

### 2.1 Frontend Authentication Infrastructure
- **Packages**: `firebase: ^10.13.2` installed in `frontend/package.json`.
- **Pages & Routes**:
  - `/login`: Uses `LoginForm` and `AuthLayout`.
  - `/signup`: Uses `SignupForm` with legal consent checkbox and Google signup.
  - `/verify-email`: Implements 6-digit OTP verification and resend cooldown.
  - `/setup-profile`: Establishes citizen legal name, address, and metadata.
  - `/app/*`: Citizen workspace guarded by `ProtectedRoute`.
  - `/admin/*`: Administrator workspace guarded by `ProtectedRoute` (`requiredRole="admin"`).
- **Client SDK Configuration (`frontend/src/lib/firebase.ts`)**:
  - Configured via `NEXT_PUBLIC_FIREBASE_*` environment variables.
  - Implements `mapFirebaseAuthError()` to translate Firebase error codes (`auth/invalid-credential`, `auth/user-not-found`, `auth/email-already-in-use`, `auth/weak-password`, `auth/popup-closed-by-user`, `auth/network-request-failed`) into polite, user-facing notices.
- **State Provider (`frontend/src/context/AuthContext.tsx`)**:
  - `onAuthStateChanged` maintains persistent session across page reloads.
  - Exposes `loginWithEmail`, `signUpWithEmail`, `loginWithGoogle`, `resetPassword`, `completeProfile`, and `logout`.

### 2.2 Backend Authentication & Admin SDK
- **Packages**: `firebase-admin==6.5.0` in `backend/requirements.txt`.
- **Initialization (`backend/app/core/firebase.py`)**:
  - Supports Service Account JSON (`FIREBASE_SERVICE_ACCOUNT_PATH`), Application Default Credentials (ADC), and local Emulator (`FIREBASE_AUTH_EMULATOR_HOST`).
  - Gracefully detects unconfigured status without server crash.
- **Token Verification (`backend/app/core/security.py`)**:
  - Validates token RS256 signature, expiry, issuer (`https://securetoken.google.com/<project-id>`), and audience (`<project-id>`).
  - Extracts verified claims: `uid`, `email`, `email_verified`, `name`.
  - Derives caller identity exclusively from the verified token, never from client-supplied request bodies.
- **FastAPI Dependencies (`backend/app/dependencies/auth.py`)**:
  - `get_current_token`: Parses `Authorization: Bearer <token>`.
  - `get_token_claims`: Invokes Firebase Admin SDK verification.
  - `get_current_user`: Resolves PostgreSQL user by `firebase_uid`, auto-provisions on first authenticated access with role `'user'`.
  - `require_admin` & `require_user`: Enforces strict two-role RBAC.

### 2.3 PostgreSQL Schema, RLS & Account Synchronization
- **Schema (`users` table)**:
  - `id UUID PRIMARY KEY`, `firebase_uid VARCHAR UNIQUE`, `email VARCHAR NOT NULL`, `role VARCHAR NOT NULL`.
  - Check constraint: `CHECK (role IN ('user', 'admin'))`.
- **Stored Procedures**:
  - `resolve_user_by_firebase_uid(p_firebase_uid)`
  - `provision_user(p_firebase_uid, p_email, p_full_name)`
- **RLS & Security Policies**:
  - Forced RLS enabled on all citizen tables (`users`, `documents`, `conflicts`, `cases`, `audit_log`).
  - RLS session parameters set transaction-locally:
    ```sql
    SET LOCAL app.current_user_id = :user_id;
    SET LOCAL app.current_user_role = :user_role;
    ```
  - Defensive `NULLIF(current_setting(...), '')::uuid` prevents connection pool type cast errors.
- **Account Linking Gap Identified**:
  - If a user signs in via email/password and later via Google with the same email, PostgreSQL must safely synchronize the `firebase_uid` to the existing user row if `email_verified` is true, avoiding duplicate user rows.

---

## 3. Implementation Roadmap

1. **Phase 2 (Frontend)**:
   - Enhance Google popup and redirect fallback handling in `AuthContext.tsx` and `LoginForm.tsx` / `SignupForm.tsx`.
   - Add explicit handlers for popup-blocked and user cancellation.
2. **Phase 3 (Backend)**:
   - Add SQL migration `019_safe_auth_synchronization.sql` for email-safe UID synchronization.
   - Update `get_current_user` to handle verified email synchronization across providers.
   - Graceful 503 handling when Firebase Admin SDK is unconfigured.
3. **Phase 4 (Authorization)**:
   - Verify strict two-role model (`USER` vs `ADMIN`).
   - Validate anti-escalation triggers.
4. **Phase 5 (Frontend UX)**:
   - Refine form validation, loading states, password visibility toggle, responsive styling.
5. **Phase 6 (Testing)**:
   - Author full 18-scenario security and functional test battery.
6. **Phase 7 & 8 (Checkpoint & Docs)**:
   - Run tests, tsc, Next.js build, OpenQodex review, and push to GitHub.

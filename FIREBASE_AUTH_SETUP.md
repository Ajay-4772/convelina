# CONVELINA — Firebase Authentication Setup & Configuration Guide

This guide provides step-by-step instructions for configuring Google Firebase Authentication for CONVELINA, covering both the web frontend (Next.js 14) and the backend API (FastAPI + PostgreSQL with forced Row-Level Security).

---

## 1. Firebase Project Creation

1. Navigate to the [Firebase Console](https://console.firebase.google.com/).
2. Click **Add project** (or select an existing Google Cloud project).
3. Name your project (e.g., `convelina-production` or `convelina-dev`).
4. Toggle Google Analytics based on your operational preferences (optional for local authentication testing).
5. Click **Create project** and wait for the resource provisioning to complete.

---

## 2. Enable Authentication Providers

1. In the left-hand navigation sidebar, click **Build** > **Authentication**.
2. Click **Get started**.
3. Under the **Sign-in method** tab:
   - Select **Email/Password**.
   - Enable the **Email/Password** toggle.
   - Leave *Email link (passwordless sign-in)* disabled unless explicitly required.
   - Click **Save**.
4. (Optional) Under **Sign-in method**, add **Google** provider if Google single sign-on is desired.
5. In the **Settings** > **Authorized domains** tab:
   - Ensure `localhost` is listed.
   - Add any staging or custom production domains (e.g., `admin.localhost`).

---

## 3. Register Frontend Web Application

1. In the Firebase Console, go to **Project settings** (gear icon beside Project Overview).
2. Under the **General** tab, scroll down to the **Your apps** section.
3. Click the **Web** icon (`</>`) to register a new web application.
4. App nickname: `convelina-web`.
5. Do not check "Also set up Firebase Hosting" unless using Firebase Hosting.
6. Click **Register app**.
7. Copy the configuration object displayed (`firebaseConfig`):
   - `apiKey`
   - `authDomain`
   - `projectId`
   - `storageBucket`
   - `messagingSenderId`
   - `appId`

---

## 4. Generate Backend Admin Service Account

1. In **Project settings**, select the **Service accounts** tab.
2. Ensure **Firebase Admin SDK** is highlighted.
3. Click **Generate new private key**.
4. Confirm the prompt by clicking **Generate key**.
5. A JSON file will download (e.g., `convelina-dev-firebase-adminsdk-xxxxx.json`).
6. **SECURITY MANDATE**:
   - Store this key securely outside public directories.
   - Recommended location: `backend/secrets/firebase_service_account.json`.
   - Verify that `backend/secrets/` and `*.json` are excluded in `.gitignore`.
   - Never commit this file or paste its contents into version control.

---

## 5. Configure Local Environment Variables

### Frontend Configuration (`frontend/.env.local`)
Create or edit `frontend/.env.local` (referenced from `frontend/.env.example`):

```bash
# Backend FastAPI Endpoint
NEXT_PUBLIC_API_URL=http://localhost:8000

# Firebase Web Client SDK
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyYourCopiedApiKey
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789012
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789012:web:abcdef1234567890

# Optional: Local Emulator (Leave commented for real Firebase Auth)
# NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
```

### Backend Configuration (`backend/.env` or root `.env`)
Create or edit `backend/.env` (referenced from `backend/.env.example`):

```bash
# Environment & Server
PROJECT_NAME="CONVELINA API"
ENVIRONMENT=development
DEBUG=True

# Database (connects via dedicated non-superuser role)
DATABASE_URL=postgresql://consolith_app:consolith_secure_app_pw@localhost:5432/consolith

# Firebase Admin SDK Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=secrets/firebase_service_account.json
# FIREBASE_AUTH_EMULATOR_HOST=localhost:9099  # Optional: only for emulator

# Administrator Account
ADMIN_GMAIL=admin.demo@gmail.com

# Sensitive Data Encryption
ENCRYPTION_KEY=consolith_dev_fernet_secret_key_32_bytes_len=
```

---

## 6. Testing Instructions

### Option A: Testing with Real Firebase Auth (Recommended)
1. Start the backend:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Start the frontend:
   ```bash
   cd frontend && npm run dev
   ```
3. Navigate to `http://localhost:3000/signup`.
4. Enter an email address and password (>= 6 characters).
5. Upon successful creation, the user will be persisted in Firebase Console (`Authentication > Users`).
6. The frontend automatically receives the Firebase ID token (JWT) and calls `POST /api/v1/auth/provision` or `GET /api/v1/auth/me`.
7. The backend validates the JWT with `firebase_admin.auth.verify_id_token()`, links the `firebase_uid` to a row in the PostgreSQL `users` table, and sets the role to `'user'`.
8. Log in with the newly created credentials at `http://localhost:3000/login`.

### Option B: Testing with Local Firebase Emulator
If internet connectivity is restricted or isolated testing is required:
1. Install the Firebase CLI:
   ```bash
   npm install -g firebase-tools
   ```
2. Start the Auth emulator:
   ```bash
   firebase emulators:start --only auth
   ```
3. In `frontend/.env.local`, set:
   ```bash
   NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
   ```
4. In `backend/.env`, set:
   ```bash
   FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
   ```
5. Both client and server will route all token issuance and verification to `http://localhost:9099`.

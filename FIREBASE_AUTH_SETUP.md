# CONVELINA — Firebase Authentication Setup & Configuration Guide (Email + Google)

This guide provides step-by-step instructions for configuring Google Firebase Authentication for CONVELINA, covering both Email/Password and Google Sign-In across the Next.js 14 frontend and FastAPI backend.

---

## 1. Firebase Project & Google Cloud Setup

1. Open the [Firebase Console](https://console.firebase.google.com/).
2. Select or create your Firebase project (e.g., `convelina-production` or `convelina-dev`).
3. Under **Project settings** > **General**, ensure the project is linked to your Google Cloud project.

---

## 2. Enable Authentication Providers

1. In the Firebase Console, navigate to **Build** > **Authentication**.
2. Click the **Sign-in method** tab.
3. **Enable Email/Password**:
   - Click **Email/Password**.
   - Enable the **Email/Password** toggle.
   - Click **Save**.
4. **Enable Google Sign-In**:
   - Click **Google**.
   - Enable the **Enable** toggle.
   - Select the project public-facing name (e.g., `CONVELINA`).
   - Select a project support email from the dropdown.
   - Click **Save**.
5. **Account Linking Configuration**:
   - Under **Authentication** > **Settings** > **User account linking**:
   - Select *"Link accounts that use the same email"*.
   - This ensures when a citizen signs in with Google using the same email previously used for email/password, Firebase and CONVELINA link the credentials under a single unified account.
6. **Authorized Domains**:
   - In the **Settings** > **Authorized domains** tab, confirm:
     - `localhost`
     - `127.0.0.1`
     - Your staging/production custom domain (e.g., `convelina.in`).

---

## 3. Register Frontend Web Application

1. In **Project settings** > **General**, scroll to **Your apps**.
2. If not already registered, click the **Web** icon (`</>`) and register `convelina-web`.
3. Copy the client configuration values into `frontend/.env.local`:

```bash
# Frontend Next.js (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000

NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSyYourApiKeyHere
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your-project-id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789012
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789012:web:abcdef1234567890

# Optional: Local Emulator (Leave commented for real Firebase Auth)
# NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
```

---

## 4. Generate Backend Service Account Key

1. In **Project settings**, click the **Service accounts** tab.
2. Select **Firebase Admin SDK** and click **Generate new private key**.
3. Save the downloaded JSON file to a secure directory outside source control, such as:
   `backend/secrets/firebase_service_account.json`
4. **MANDATORY SECURITY RULE**:
   - Ensure `backend/secrets/` is listed in `.gitignore`.
   - Never commit private keys, service account JSON files, or `.env` files to Git.
5. In `backend/.env` (or root `.env`):

```bash
# Backend FastAPI (.env)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=secrets/firebase_service_account.json
# FIREBASE_AUTH_EMULATOR_HOST=localhost:9099 # Optional: only when using local emulator

# Pre-configured Administrator Account (receives 'admin' role automatically)
ADMIN_GMAIL=admin.demo@gmail.com
```

---

## 5. Local Testing Instructions

### Real Firebase Testing (Production-grade)
1. Start FastAPI:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. Start Next.js:
   ```bash
   cd frontend && npm run dev
   ```
3. Test **Email Registration & Login**:
   - Navigate to `http://localhost:3000/signup`.
   - Fill in Full Legal Name, Email, Password (>= 6 chars), and agree to privacy terms.
   - User is persisted in Firebase Auth and provisioned in PostgreSQL with `role = 'user'`.
4. Test **Google Sign-In**:
   - Click "Continue with Google" on `http://localhost:3000/login` or "Sign up with Google" on `/signup`.
   - Google account selection popup appears.
   - Upon authorization, JWT is issued, backend verifies the token, and creates/synchronizes the user record.
5. Test **Account Linking**:
   - Sign up with Email/Password `user@domain.com`.
   - Log out, then click "Continue with Google" using the same `user@domain.com`.
   - Backend recognizes the verified email, links the Google credentials, and maintains the single existing user profile and uploaded documents without duplicating records.
6. Test **Password Reset**:
   - On `/login`, click "Forgot password?".
   - Enter email address and submit.
   - Firebase dispatches an official password reset email.

### Local Emulator Testing
1. Start Firebase Auth emulator:
   ```bash
   firebase emulators:start --only auth
   ```
2. Set emulator host in both `.env.local` and `.env`:
   ```bash
   NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
   FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
   ```

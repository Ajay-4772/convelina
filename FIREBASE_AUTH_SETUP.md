# CONVELINA — Firebase Authentication Setup & Configuration Guide (Email + Google)

This guide provides complete instructions for configuring Google Firebase Authentication for CONVELINA, covering Email/Password, Google Sign-In, secure account linking, and explicit administrator provisioning.

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
5. **Account Linking & User Protection Configuration**:
   - Under **Authentication** > **Settings** > **User account linking**:
   - Select **"Link accounts that use the same email"** (or enable account linking protection).
   - When a citizen registers with email/password and later signs in with Google, Firebase raises `auth/account-exists-with-different-credential`. CONVELINA captures the pending credential, prompts for password verification, and executes `linkWithCredential` so that both providers map to the **same** verified Firebase UID.
   - **SECURITY RULE**: The backend strictly refuses to overwrite database `firebase_uid` values merely because emails match. Provider linking requires an authenticated session and verified email claims.
6. **Authorized Domains**:
   - In the **Settings** > **Authorized domains** tab, confirm:
     - `localhost`
     - `127.0.0.1`
     - Your staging/production custom domain (e.g., `convelina.in`).

---

## 3. Register Frontend Web Application

1. In **Project settings** > **General**, scroll to **Your apps**.
2. Click the **Web** icon (`</>`) and register `convelina-web`.
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

## 4. Backend Firebase Admin SDK Setup

1. In the Firebase Console, go to **Project settings** > **Service accounts**.
2. Click **Generate new private key** and download the service account JSON.
3. Save it to a secure local path **outside** the Git repository (or in the root as a gitignored file, e.g., `firebase-adminsdk-private.json`).
4. Configure `backend/.env`:

```bash
# Backend Environment (.env)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_SERVICE_ACCOUNT_PATH=/absolute/path/to/firebase-adminsdk-private.json

# Administrator Bootstrap (Deprecated for automatic promotion)
# All new signups strictly receive role 'user'.
ADMIN_GMAIL=admin.demo@gmail.com
```

> [!CAUTION]
> Never commit `serviceAccountKey.json` or `.env` to version control. Verified gitignore rules actively block all `*service_account*.json` and `firebase-adminsdk*.json` patterns.

---

## 5. Administrator Provisioning Procedure

Automatic promotion based solely on `ADMIN_GMAIL` has been **completely eliminated** to prevent unauthorized privilege escalation from unverified or spoofed identities.

Every new registration receives the `user` role.

To grant administrator privileges, use one of the two explicit, audited procedures:

### Method A: Direct Database CLI Promotion (Recommended for Initial Setup)
System administrators with direct host/DB access execute:
```bash
python backend/scripts/promote_admin.py --email admin@convelina.in
```
This script:
1. Connects under administrative database permissions.
2. Validates user existence.
3. Promotes `role` to `'admin'`.
4. Writes an immutable, hash-chained `AuditLog` entry (`action="admin_promoted_via_cli"`).

### Method B: Authenticated Administrator API Endpoint
An existing authenticated administrator can promote a verified citizen user:
```http
POST /api/v1/admin/users/{user_id}/role
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json

{
  "role": "admin"
}
```
Security protections:
- Callable strictly by users whose database role is `'admin'`.
- Self-promotion and self-demotion are rejected with `400 Bad Request`.
- Automatically logs `action="admin_role_updated"` in the tamper-evident audit log.

import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, connectAuthEmulator, Auth } from "firebase/auth";

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "AIzaSyDummyKeyForConvelinaDevOnly",
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "convelina-dev.firebaseapp.com",
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "convelina-dev",
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "convelina-dev.appspot.com",
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "000000000000",
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "1:000000000000:web:000000000000",
};

/**
 * Validates whether real Firebase credentials are configured in the environment.
 */
export const isFirebaseConfigured = (): boolean => {
  const apiKey = process.env.NEXT_PUBLIC_FIREBASE_API_KEY;
  const projectId = process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;
  return Boolean(
    apiKey &&
    projectId &&
    !apiKey.includes("Dummy") &&
    apiKey.length > 10
  );
};

// Initialize Firebase App singleton
const app = !getApps().length ? initializeApp(firebaseConfig) : getApp();
export const auth: Auth = getAuth(app);

// Connect to Auth Emulator if explicitly configured
if (
  typeof window !== "undefined" &&
  process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST &&
  !(auth as unknown as { _emulatorConfigured?: boolean })._emulatorConfigured
) {
  const emulatorHost = process.env.NEXT_PUBLIC_FIREBASE_AUTH_EMULATOR_HOST;
  const url = emulatorHost.startsWith("http") ? emulatorHost : `http://${emulatorHost}`;
  try {
    connectAuthEmulator(auth, url, { disableWarnings: true });
    (auth as unknown as { _emulatorConfigured?: boolean })._emulatorConfigured = true;
  } catch (err) {
    console.warn("Firebase Auth Emulator connection skipped or already initialized:", err);
  }
}

/**
 * Translates Firebase Auth error codes into clear, user-facing error messages.
 */
export function mapFirebaseAuthError(error: unknown): string {
  if (!error) return "An unexpected error occurred.";
  
  const errObj = error as { code?: string; message?: string };
  const code = errObj.code || "";
  
  switch (code) {
    case "auth/invalid-credential":
    case "auth/wrong-password":
      return "Incorrect email or password. Please verify your credentials and try again.";
    case "auth/user-not-found":
      return "No account exists with this email address. Please sign up first.";
    case "auth/email-already-in-use":
      return "An account with this email address already exists. Please sign in instead.";
    case "auth/weak-password":
      return "Password is too weak. Please use at least 6 characters including numbers or symbols.";
    case "auth/invalid-email":
      return "Please enter a valid email address.";
    case "auth/too-many-requests":
      return "Too many failed login attempts. Access to this account has been temporarily disabled. Please reset your password or try again later.";
    case "auth/user-disabled":
      return "This account has been disabled by an administrator. Please contact support.";
    case "auth/operation-not-allowed":
      return "Email/Password sign-in is not enabled in the Firebase project console.";
    case "auth/network-request-failed":
      return "Network connection error. Please check your internet connection and try again.";
    case "auth/popup-closed-by-user":
      return "Sign-in popup was closed before completing authentication.";
    case "auth/requires-recent-login":
      return "This operation is sensitive and requires recent authentication. Please sign in again.";
    default: {
      const msg = errObj.message || String(error);
      return msg
        .replace(/^Firebase:\s*/i, "")
        .replace(/\s*\(auth\/[^)]+\)\.?/i, "")
        .trim() || "Authentication failed. Please try again.";
    }
  }
}

export default app;

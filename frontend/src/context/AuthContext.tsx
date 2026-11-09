"use client";

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { 
  User as FirebaseUser,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  signInWithPopup,
  GoogleAuthProvider,
  signOut
} from "firebase/auth";
import { auth, isFirebaseConfigured, mapFirebaseAuthError } from "../lib/firebase";

export interface UserProfile {
  id: string;
  firebase_uid: string;
  email: string;
  full_name: string;
  role: "user" | "admin" | "citizen";
  phone_number?: string | null;
  date_of_birth?: string | null;
  address?: string | null;
  father_name?: string | null;
  mother_name?: string | null;
  created_at?: string;
  updated_at?: string;
}

interface AuthContextType {
  firebaseUser: FirebaseUser | null;
  profile: UserProfile | null;
  idToken: string | null;
  loading: boolean;
  error: string | null;
  isConfigured: boolean;
  isProfileComplete: boolean;
  loginWithEmail: (email: string, pass: string) => Promise<UserProfile | null>;
  signUpWithEmail: (email: string, pass: string) => Promise<FirebaseUser>;
  resetPassword: (email: string) => Promise<void>;
  loginWithGoogle: () => Promise<UserProfile | null>;
  sendEmailOtp: (email: string) => Promise<{ success: boolean; message: string }>;
  verifyEmailOtp: (email: string, otp: string) => Promise<{ success: boolean; verified: boolean; message: string }>;
  completeProfile: (data: {
    full_name: string;
    phone_number?: string;
    date_of_birth?: string;
    address?: string;
    father_name?: string;
    mother_name?: string;
  }) => Promise<UserProfile>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const createSimulatedUser = useCallback((token: string): FirebaseUser => {
    const parts = token.split(":");
    const uid = parts[1] || "test_user_id";
    const email = parts[2] || "user@example.com";
    const displayName = parts[3] || "Test User";
    return {
      uid,
      email,
      displayName,
      emailVerified: true,
      isAnonymous: false,
      metadata: {},
      providerData: [],
      refreshToken: "",
      tenantId: null,
      delete: async () => {},
      getIdToken: async () => token,
      getIdTokenResult: async () => ({
        token,
        claims: {
          user_id: uid,
          email,
          email_verified: true,
          is_test_token: true,
        },
        authTime: new Date().toISOString(),
        issuedAtTime: new Date().toISOString(),
        expirationTime: new Date(Date.now() + 3600000).toISOString(),
        signInProvider: "custom",
        signInSecondFactor: null,
      }),
      reload: async () => {},
      toJSON: () => ({ uid, email, displayName }),
    } as unknown as FirebaseUser;
  }, []);

  const fetchProfile = useCallback(async (token: string): Promise<UserProfile | null> => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/me`, {
        headers: { 
          Authorization: `Bearer ${token}`,
          "Cache-Control": "no-cache",
        }
      });

      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        return data;
      }

      if (res.status === 401) {
        // User authenticated in Firebase but profile not yet provisioned in DB
        setProfile(null);
        return null;
      }

      const errData = await res.json().catch(() => ({}));
      setError(errData.detail || "Failed to load user profile.");
      return null;
    } catch (err: unknown) {
      console.error("AuthContext fetchProfile error:", err);
      setError(err instanceof Error ? err.message : "Failed to connect to authentication server.");
      return null;
    }
  }, [apiUrl]);

  useEffect(() => {
    // Safety failsafe to ensure UI never indefinitely hangs on loading state
    const failsafeTimer = setTimeout(() => {
      setLoading(false);
    }, 2500);

    // Restore session if test token is present in localStorage
    if (typeof window !== "undefined") {
      const storedToken = localStorage.getItem("convelina_test_token");
      if (storedToken && storedToken.startsWith("test_token_")) {
        const simUser = createSimulatedUser(storedToken);
        setFirebaseUser(simUser);
        setIdToken(storedToken);
        fetchProfile(storedToken)
          .catch(() => null)
          .finally(() => {
            clearTimeout(failsafeTimer);
            setLoading(false);
          });
        return;
      }
    }

    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setLoading(true);
      setError(null);

      if (user) {
        setFirebaseUser(user);
        try {
          const token = await user.getIdToken();
          setIdToken(token);
          await fetchProfile(token);
        } catch (err: unknown) {
          setError(mapFirebaseAuthError(err));
        }
      } else {
        setFirebaseUser(null);
        setProfile(null);
        setIdToken(null);
      }

      setLoading(false);
    });

    return () => unsubscribe();
  }, [fetchProfile, createSimulatedUser]);

  const loginWithEmail = async (email: string, pass: string): Promise<UserProfile | null> => {
    setError(null);
    setLoading(true);
    try {
      const cleanEmail = email.trim();
      if (!isFirebaseConfigured() && (cleanEmail.startsWith("test_") || cleanEmail.startsWith("citizen_"))) {
        const testToken = `test_token_:${cleanEmail.replace(/[^a-zA-Z0-9]/g, "_")}:${cleanEmail}:Citizen User`;
        if (typeof window !== "undefined") {
          localStorage.setItem("convelina_test_token", testToken);
        }
        const simUser = createSimulatedUser(testToken);
        setFirebaseUser(simUser);
        setIdToken(testToken);
        const userProfile = await fetchProfile(testToken);
        return userProfile;
      }
      const cred = await signInWithEmailAndPassword(auth, cleanEmail, pass);
      const token = await cred.user.getIdToken();
      setIdToken(token);
      setFirebaseUser(cred.user);
      const userProfile = await fetchProfile(token);
      return userProfile;
    } catch (err: unknown) {
      const msg = mapFirebaseAuthError(err);
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const signUpWithEmail = async (email: string, pass: string): Promise<FirebaseUser> => {
    setError(null);
    setLoading(true);
    try {
      const cleanEmail = email.trim();
      if (!isFirebaseConfigured() && (cleanEmail.startsWith("test_") || cleanEmail.startsWith("citizen_"))) {
        const testToken = `test_token_:${cleanEmail.replace(/[^a-zA-Z0-9]/g, "_")}:${cleanEmail}:Citizen User`;
        if (typeof window !== "undefined") {
          localStorage.setItem("convelina_test_token", testToken);
        }
        const simUser = createSimulatedUser(testToken);
        setFirebaseUser(simUser);
        setIdToken(testToken);
        return simUser;
      }
      const cred = await createUserWithEmailAndPassword(auth, cleanEmail, pass);
      const token = await cred.user.getIdToken();
      setIdToken(token);
      setFirebaseUser(cred.user);
      return cred.user;
    } catch (err: unknown) {
      const msg = mapFirebaseAuthError(err);
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const resetPassword = async (email: string): Promise<void> => {
    setError(null);
    setLoading(true);
    try {
      const cleanEmail = email.trim();
      if (!cleanEmail) {
        throw new Error("Please enter your email address.");
      }
      if (isFirebaseConfigured()) {
        await sendPasswordResetEmail(auth, cleanEmail);
      } else {
        // Fallback for simulated development
        await new Promise((res) => setTimeout(res, 300));
      }
    } catch (err: unknown) {
      const msg = mapFirebaseAuthError(err);
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const loginWithGoogle = async (): Promise<UserProfile | null> => {
    setError(null);
    setLoading(true);
    try {
      if (!isFirebaseConfigured()) {
        const email = "citizen_google@example.com";
        const testToken = `test_token_:google_test_user:${email}:Google Citizen`;
        if (typeof window !== "undefined") {
          localStorage.setItem("convelina_test_token", testToken);
        }
        const simUser = createSimulatedUser(testToken);
        setFirebaseUser(simUser);
        setIdToken(testToken);
        const userProfile = await fetchProfile(testToken);
        return userProfile;
      }
      const provider = new GoogleAuthProvider();
      provider.setCustomParameters({ prompt: "select_account" });
      const cred = await signInWithPopup(auth, provider);
      const token = await cred.user.getIdToken();
      setIdToken(token);
      setFirebaseUser(cred.user);
      const userProfile = await fetchProfile(token);
      return userProfile;
    } catch (err: unknown) {
      const msg = mapFirebaseAuthError(err);
      setError(msg);
      throw new Error(msg);
    } finally {
      setLoading(false);
    }
  };

  const sendEmailOtp = async (email: string) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/otp/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to send verification code.");
      }
      return data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "OTP request failed.";
      setError(msg);
      throw err;
    }
  };

  const verifyEmailOtp = async (email: string, otp: string) => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/otp/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), otp_code: otp.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to verify code.");
      }
      return data;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "OTP verification failed.";
      setError(msg);
      throw err;
    }
  };

  const completeProfile = async (data: {
    full_name: string;
    phone_number?: string;
    date_of_birth?: string;
    address?: string;
    father_name?: string;
    mother_name?: string;
  }): Promise<UserProfile> => {
    if (!idToken) {
      throw new Error("You must be signed in to complete your profile.");
    }
    setLoading(true);
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/provision`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify(data),
      });

      const resData = await res.json();
      if (!res.ok) {
        throw new Error(resData.detail || "Failed to save profile.");
      }

      setProfile(resData);
      return resData;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Profile setup failed.";
      setError(msg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setError(null);
    try {
      await signOut(auth);
      setFirebaseUser(null);
      setProfile(null);
      setIdToken(null);
      // Clean up local storage items
      try {
        if (typeof window !== "undefined") {
          sessionStorage.clear();
          localStorage.removeItem("consolith_session");
          localStorage.removeItem("convelina_session");
          localStorage.removeItem("convelina_test_token");
        }
      } catch {
        // ignore storage errors
      }
    } catch (err: unknown) {
      const msg = mapFirebaseAuthError(err);
      setError(msg);
    }
  };

  const refreshProfile = async () => {
    const activeToken = idToken || (typeof window !== "undefined" ? localStorage.getItem("convelina_test_token") : null);
    if (activeToken) {
      await fetchProfile(activeToken);
    }
  };

  const clearError = () => setError(null);

  const isProfileComplete = Boolean(
    profile && profile.id && profile.full_name && profile.full_name.trim().length > 0
  );

  return (
    <AuthContext.Provider
      value={{
        firebaseUser,
        profile,
        idToken,
        loading,
        error,
        isConfigured: isFirebaseConfigured(),
        isProfileComplete,
        loginWithEmail,
        signUpWithEmail,
        resetPassword,
        loginWithGoogle,
        sendEmailOtp,
        verifyEmailOtp,
        completeProfile,
        logout,
        refreshProfile,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

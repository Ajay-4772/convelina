"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { 
  User as FirebaseUser,
  onAuthStateChanged,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut
} from "firebase/auth";
import { auth, isFirebaseConfigured } from "../lib/firebase";

export interface UserProfile {
  id: string;
  firebase_uid: string;
  email: string;
  full_name: string;
  role: "citizen" | "officer" | "admin";
  created_at: string;
}

interface AuthContextType {
  firebaseUser: FirebaseUser | null;
  profile: UserProfile | null;
  idToken: string | null;
  loading: boolean;
  error: string | null;
  isConfigured: boolean;
  loginWithEmail: (email: string, pass: string) => Promise<void>;
  signUpWithEmail: (email: string, pass: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchProfile = async (token: string, fallbackName?: string) => {
    try {
      // 1. Try to fetch existing profile
      const res = await fetch(`${apiUrl}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        return;
      }

      // 2. If user is not yet provisioned (401), provision now
      if (res.status === 401 && fallbackName) {
        const provRes = await fetch(`${apiUrl}/api/v1/auth/provision`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ full_name: fallbackName })
        });

        if (provRes.ok) {
          const data = await provRes.json();
          setProfile(data);
        } else {
          const errData = await provRes.json().catch(() => ({}));
          setError(errData.detail || "Failed to provision user profile.");
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to connect to authentication server.");
    }
  };

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      setLoading(true);
      setError(null);
      if (user) {
        setFirebaseUser(user);
        try {
          const token = await user.getIdToken();
          setIdToken(token);
          await fetchProfile(token, user.displayName || user.email?.split("@")[0] || "Citizen");
        } catch (err: unknown) {
          setError(err instanceof Error ? err.message : "Token retrieval failed.");
        }
      } else {
        setFirebaseUser(null);
        setProfile(null);
        setIdToken(null);
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, [apiUrl]);

  const loginWithEmail = async (email: string, pass: string) => {
    setError(null);
    setLoading(true);
    try {
      const cred = await signInWithEmailAndPassword(auth, email, pass);
      const token = await cred.user.getIdToken();
      await fetchProfile(token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed.");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const signUpWithEmail = async (email: string, pass: string, fullName: string) => {
    setError(null);
    setLoading(true);
    try {
      const cred = await createUserWithEmailAndPassword(auth, email, pass);
      const token = await cred.user.getIdToken();
      await fetchProfile(token, fullName);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed.");
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setError(null);
    try {
      await signOut(auth);
      setProfile(null);
      setIdToken(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Logout failed.");
    }
  };

  const refreshProfile = async () => {
    if (idToken) {
      await fetchProfile(idToken);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        firebaseUser,
        profile,
        idToken,
        loading,
        error,
        isConfigured: isFirebaseConfigured(),
        loginWithEmail,
        signUpWithEmail,
        logout,
        refreshProfile
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

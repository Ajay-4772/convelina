"use client";

import React, { Suspense } from "react";
import AuthLayout from "../../components/auth/AuthLayout";
import LoginForm from "../../components/auth/LoginForm";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to your private CONVELINA workspace."
    >
      <Suspense
        fallback={
          <div className="py-12 flex justify-center items-center">
            <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
          </div>
        }
      >
        <LoginForm />
      </Suspense>
    </AuthLayout>
  );
}

"use client";

import React, { Suspense } from "react";
import AuthLayout from "../../components/auth/AuthLayout";
import SignupForm from "../../components/auth/SignupForm";
import { Loader2 } from "lucide-react";

export default function SignUpPage() {
  return (
    <AuthLayout
      title="Create account"
      subtitle="Register to inspect your identity records and access official correction guidance."
    >
      <Suspense
        fallback={
          <div className="py-12 flex justify-center items-center">
            <Loader2 className="w-5 h-5 animate-spin text-zinc-400" />
          </div>
        }
      >
        <SignupForm />
      </Suspense>
    </AuthLayout>
  );
}

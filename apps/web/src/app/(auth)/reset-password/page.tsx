"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Button } from "ui";

import { FormField } from "@/components/auth/FormField";
import { useResetPassword } from "@/hooks/useAuth";

const PASSWORD_MIN_LENGTH = 8;

function ResetPasswordForm() {
  const router = useRouter();
  // useSearchParams needs a Suspense boundary in the App Router (it
  // opts the subtree out of static rendering) — hence this component
  // being split from the page's default export below.
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const resetPassword = useResetPassword();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const passwordsMismatch = confirmPassword.length > 0 && password !== confirmPassword;

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!token || passwordsMismatch) return;
    resetPassword.mutate(
      { token, password },
      { onSuccess: () => router.push("/login") },
    );
  }

  if (!token) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-xl font-semibold text-slate-900">Invalid link</h1>
        <p className="text-sm text-slate-600">
          This password reset link is missing its token. Request a new one below.
        </p>
        <Link href="/forgot-password" className="text-sm font-medium text-slate-900 hover:underline">
          Request a new link
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Reset password</h1>
        <p className="mt-1 text-sm text-slate-600">Choose a new password.</p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <FormField
          id="password"
          label="New password"
          type="password"
          autoComplete="new-password"
          required
          minLength={PASSWORD_MIN_LENGTH}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <FormField
          id="confirm_password"
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          required
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />
        {passwordsMismatch && <p className="text-sm text-red-600">Passwords don&apos;t match.</p>}

        {resetPassword.isError && (
          <p className="text-sm text-red-600">{resetPassword.error.message}</p>
        )}

        <Button type="submit" disabled={resetPassword.isPending} className="w-full">
          {resetPassword.isPending ? "Resetting…" : "Reset password"}
        </Button>
      </form>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  );
}

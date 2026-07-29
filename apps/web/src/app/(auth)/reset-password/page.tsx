"use client";

import { ArrowLeft } from "lucide-react";
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
    resetPassword.mutate({ token, password }, { onSuccess: () => router.push("/login") });
  }

  if (!token) {
    return (
      <div className="flex flex-col gap-4">
        <h1 className="text-xl font-semibold text-ink">Invalid link</h1>
        <p className="text-sm text-ink-muted">
          This password reset link is missing its token. Request a new one below.
        </p>
        <Link href="/forgot-password" className="rounded-sm text-sm font-medium text-accent-ink hover:underline">
          Request a new link
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-ink">Choose a new password</h1>
        <p className="mt-1 text-sm text-ink-muted">
          You&apos;ll be signed in again with the new password.
        </p>
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
          hint={`At least ${PASSWORD_MIN_LENGTH} characters.`}
        />
        <FormField
          id="confirm_password"
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          required
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          error={passwordsMismatch ? "Passwords don't match." : undefined}
        />

        {resetPassword.isError && (
          <p role="alert" className="text-sm text-danger-ink">
            {resetPassword.error.message}
          </p>
        )}

        <Button type="submit" loading={resetPassword.isPending} className="w-full">
          Reset password
        </Button>
      </form>

      <Link
        href="/login"
        className="inline-flex items-center gap-1.5 rounded-sm text-sm text-ink-secondary hover:text-ink hover:underline"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        Back to sign in
      </Link>
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

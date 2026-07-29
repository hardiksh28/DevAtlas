"use client";

import { ArrowLeft, MailCheck } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { Button } from "ui";

import { FormField } from "@/components/auth/FormField";
import { useForgotPassword } from "@/hooks/useAuth";

export default function ForgotPasswordPage() {
  const forgotPassword = useForgotPassword();
  const [email, setEmail] = useState("");

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    forgotPassword.mutate({ email });
  }

  // The API returns the same generic message whether or not the email
  // is registered (account-enumeration prevention — see
  // service.request_password_reset) — the UI shows that exact message
  // rather than a custom success state, so it can't accidentally leak
  // more than the API already decided to.
  if (forgotPassword.isSuccess) {
    return (
      <div className="flex flex-col gap-4">
        <MailCheck className="h-6 w-6 text-success-ink" aria-hidden="true" />
        <h1 className="text-xl font-semibold text-ink">Check your email</h1>
        <p className="text-sm text-ink-muted">{forgotPassword.data.message}</p>
        <Link
          href="/login"
          className="inline-flex items-center gap-1.5 rounded-sm text-sm font-medium text-accent-ink hover:underline"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Back to sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-ink">Reset your password</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Enter your email and we&apos;ll send you a reset link.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <FormField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        {forgotPassword.isError && (
          <p role="alert" className="text-sm text-danger-ink">
            {forgotPassword.error.message}
          </p>
        )}

        <Button type="submit" loading={forgotPassword.isPending} className="w-full">
          Send reset link
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

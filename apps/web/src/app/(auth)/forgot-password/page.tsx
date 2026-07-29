"use client";

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
        <h1 className="text-xl font-semibold text-slate-900">Check your email</h1>
        <p className="text-sm text-slate-600">{forgotPassword.data.message}</p>
        <Link href="/login" className="text-sm font-medium text-slate-900 hover:underline">
          Back to login
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">Forgot password</h1>
        <p className="mt-1 text-sm text-slate-600">
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
          <p className="text-sm text-red-600">{forgotPassword.error.message}</p>
        )}

        <Button type="submit" disabled={forgotPassword.isPending} className="w-full">
          {forgotPassword.isPending ? "Sending…" : "Send reset link"}
        </Button>
      </form>

      <Link href="/login" className="text-sm text-slate-600 hover:underline">
        Back to login
      </Link>
    </div>
  );
}

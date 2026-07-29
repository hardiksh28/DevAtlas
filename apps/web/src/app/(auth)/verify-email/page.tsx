"use client";

import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef } from "react";

import { useVerifyEmail } from "@/hooks/useAuth";

function VerifyEmailStatus() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const verifyEmail = useVerifyEmail();
  const hasSubmitted = useRef(false);

  useEffect(() => {
    if (token && !hasSubmitted.current) {
      hasSubmitted.current = true;
      verifyEmail.mutate({ token });
    }
  }, [token, verifyEmail]);

  if (!token) {
    return (
      <p className="text-sm text-ink-muted">This verification link is missing its token.</p>
    );
  }

  if (verifyEmail.isPending || verifyEmail.isIdle) {
    return (
      <p className="flex items-center gap-2 text-sm text-ink-muted">
        <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        Verifying your email…
      </p>
    );
  }

  if (verifyEmail.isError) {
    return (
      <p role="alert" className="flex items-center gap-2 text-sm text-danger-ink">
        <XCircle className="h-4 w-4 shrink-0" aria-hidden="true" />
        {verifyEmail.error.message}
      </p>
    );
  }

  return (
    <p className="flex items-center gap-2 text-sm text-success-ink">
      <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
      Your email has been verified.
    </p>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-ink">Verify email</h1>
      <Suspense>
        <VerifyEmailStatus />
      </Suspense>
      <Link href="/dashboard" className="rounded-sm text-sm font-medium text-accent-ink hover:underline">
        Continue to dashboard
      </Link>
    </div>
  );
}

"use client";

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
    return <p className="text-sm text-slate-600">This verification link is missing its token.</p>;
  }

  if (verifyEmail.isPending || verifyEmail.isIdle) {
    return <p className="text-sm text-slate-600">Verifying your email…</p>;
  }

  if (verifyEmail.isError) {
    return <p className="text-sm text-red-600">{verifyEmail.error.message}</p>;
  }

  return <p className="text-sm text-slate-600">Your email has been verified.</p>;
}

export default function VerifyEmailPage() {
  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-xl font-semibold text-slate-900">Verify email</h1>
      <Suspense>
        <VerifyEmailStatus />
      </Suspense>
      <Link href="/dashboard" className="text-sm font-medium text-slate-900 hover:underline">
        Continue to dashboard
      </Link>
    </div>
  );
}

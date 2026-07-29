"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { Button } from "ui";

import { FormField } from "@/components/auth/FormField";
import { useLogin } from "@/hooks/useAuth";

function LoginForm() {
  const router = useRouter();
  // `next` is set by middleware.ts when it redirects an unauthenticated
  // visit to a protected route, so login returns the user to where they
  // were headed instead of always dropping them on /dashboard.
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/dashboard";

  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    login.mutate({ email, password }, { onSuccess: () => router.push(next) });
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-ink">Sign in</h1>
        <p className="mt-1 text-sm text-ink-muted">Welcome back — pick up where you left off.</p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate={false}>
        <FormField
          id="email"
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <FormField
          id="password"
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {login.isError && (
          <p role="alert" className="text-sm text-danger-ink">
            {login.error.message}
          </p>
        )}

        <Button type="submit" loading={login.isPending} className="w-full">
          Sign in
        </Button>
      </form>

      <div className="flex justify-between text-sm">
        <Link href="/forgot-password" className="rounded-sm text-ink-secondary hover:text-ink hover:underline">
          Forgot password?
        </Link>
        <Link href="/register" className="rounded-sm font-medium text-accent-ink hover:underline">
          Create an account
        </Link>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}

"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "ui";

import { FormField } from "@/components/auth/FormField";
import { useRegister } from "@/hooks/useAuth";

const PASSWORD_MIN_LENGTH = 8;

export default function RegisterPage() {
  const router = useRouter();
  const register = useRegister();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const passwordTooShort = password.length > 0 && password.length < PASSWORD_MIN_LENGTH;

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (passwordTooShort) return;
    register.mutate(
      { email, password, display_name: displayName },
      { onSuccess: () => router.push("/dashboard") },
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold text-ink">Create your account</h1>
        <p className="mt-1 text-sm text-ink-muted">
          Start with a project. Learn what it takes to ship it.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <FormField
          id="display_name"
          label="Name"
          type="text"
          autoComplete="name"
          required
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />
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
          autoComplete="new-password"
          required
          minLength={PASSWORD_MIN_LENGTH}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          hint={`At least ${PASSWORD_MIN_LENGTH} characters.`}
          error={
            passwordTooShort
              ? `Password must be at least ${PASSWORD_MIN_LENGTH} characters.`
              : undefined
          }
        />

        {register.isError && (
          <p role="alert" className="text-sm text-danger-ink">
            {register.error.message}
          </p>
        )}

        <Button type="submit" loading={register.isPending} className="w-full">
          Create account
        </Button>
      </form>

      <p className="text-sm text-ink-muted">
        Already have an account?{" "}
        <Link href="/login" className="rounded-sm font-medium text-accent-ink hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  );
}

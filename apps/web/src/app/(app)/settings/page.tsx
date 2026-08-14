"use client";

import { Monitor, Moon, Sun } from "lucide-react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Button } from "ui";

import { CompanionSection } from "@/components/settings/CompanionSection";
import { Badge } from "@/components/ui/Badge";
import { PageHeader } from "@/components/ui/PageHeader";
import { useCurrentUser, useLogoutAll, useResendVerification } from "@/hooks/useAuth";
import { formatRelativeTime } from "@/lib/format";

const THEME_OPTIONS = [
  { value: "light", label: "Light", icon: Sun },
  { value: "system", label: "System", icon: Monitor },
  { value: "dark", label: "Dark", icon: Moon },
] as const;

function ThemePreference() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div role="radiogroup" aria-label="Theme" className="flex gap-2">
      {THEME_OPTIONS.map((option) => {
        const selected = mounted && theme === option.value;
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => setTheme(option.value)}
            className={`flex min-h-10 items-center gap-2 rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
              selected
                ? "border-accent bg-accent-soft text-accent-ink"
                : "border-line text-ink-secondary hover:bg-surface-muted hover:text-ink"
            }`}
          >
            <option.icon className="h-4 w-4" aria-hidden="true" />
            {option.label}
          </button>
        );
      })}
    </div>
  );
}

export default function SettingsPage() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const logoutAll = useLogoutAll();
  const resendVerification = useResendVerification();

  if (!user) return null;

  return (
    <div className="mx-auto flex max-w-3xl flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8">
      <PageHeader title="Settings" description="Your account and workspace preferences." />

      <section aria-labelledby="account-heading" className="rounded-lg border border-line bg-surface p-5">
        <h2 id="account-heading" className="text-sm font-semibold text-ink-secondary">
          Account
        </h2>
        <dl className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-xs text-ink-muted">Name</dt>
            <dd className="mt-0.5 text-sm font-medium text-ink">{user.display_name}</dd>
          </div>
          <div>
            <dt className="text-xs text-ink-muted">Email</dt>
            <dd className="mt-0.5 flex flex-wrap items-center gap-2 text-sm font-medium text-ink">
              <span className="break-all">{user.email}</span>
              {user.email_verified ? (
                <Badge variant="success">Verified</Badge>
              ) : (
                <Badge variant="outline">Unverified</Badge>
              )}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-ink-muted">Joined</dt>
            <dd className="mt-0.5 text-sm text-ink-secondary">
              {formatRelativeTime(user.created_at)}
            </dd>
          </div>
        </dl>

        {!user.email_verified && (
          <div className="mt-4 flex flex-col gap-2 rounded-md border border-line bg-surface-muted p-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-ink-secondary">
              Verify your email to secure your account.
            </p>
            {resendVerification.isSuccess ? (
              <p className="text-sm text-success-ink">{resendVerification.data.message}</p>
            ) : (
              <Button
                size="sm"
                variant="secondary"
                loading={resendVerification.isPending}
                onClick={() => resendVerification.mutate(user.email)}
              >
                Resend verification email
              </Button>
            )}
          </div>
        )}
        {resendVerification.isError && (
          <p role="alert" className="mt-2 text-sm text-danger-ink">
            {resendVerification.error.message}
          </p>
        )}
      </section>

      <CompanionSection user={user} />

      <section aria-labelledby="appearance-heading" className="rounded-lg border border-line bg-surface p-5">
        <h2 id="appearance-heading" className="text-sm font-semibold text-ink-secondary">
          Appearance
        </h2>
        <p className="mt-1 text-sm text-ink-muted">
          Choose a theme, or follow your system preference.
        </p>
        <div className="mt-4">
          <ThemePreference />
        </div>
      </section>

      <section aria-labelledby="sessions-heading" className="rounded-lg border border-line bg-surface p-5">
        <h2 id="sessions-heading" className="text-sm font-semibold text-ink-secondary">
          Sessions
        </h2>
        <p className="mt-1 text-sm text-ink-muted">
          Signs you out everywhere, including this device.
        </p>
        {logoutAll.isError && (
          <p role="alert" className="mt-2 text-sm text-danger-ink">
            {logoutAll.error.message}
          </p>
        )}
        <div className="mt-4">
          <Button
            variant="secondary"
            loading={logoutAll.isPending}
            onClick={() =>
              logoutAll.mutate(undefined, { onSuccess: () => router.push("/login") })
            }
          >
            Sign out of all devices
          </Button>
        </div>
      </section>
    </div>
  );
}

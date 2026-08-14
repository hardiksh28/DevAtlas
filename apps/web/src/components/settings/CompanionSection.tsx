"use client";

import { useState } from "react";
import { Button } from "ui";

import { FormField } from "@/components/auth/FormField";
import { PixelPet } from "@/components/companion/PixelPet";
import { useUpdateCompanion } from "@/hooks/useAuth";
import { PIXEL_PETS } from "@/lib/pixel-pets";
import type { User } from "@/types/auth";

const AVATAR_OPTIONS = Object.entries(PIXEL_PETS).map(([key, spec]) => ({
  key,
  label: spec.label,
}));

/** Name-and-pick-an-icon flow for the mentor persona shown everywhere
 * the mentor speaks (chat panel, etc.) — global to the account, not
 * per-project, so it's account Settings rather than a project setting. */
export function CompanionSection({ user }: { user: User }) {
  const [name, setName] = useState(user.companion_name ?? "");
  const [avatar, setAvatar] = useState(user.companion_avatar ?? "");
  const updateCompanion = useUpdateCompanion();

  const isConfigured = Boolean(user.companion_name && user.companion_avatar);
  const dirty = name.trim() !== (user.companion_name ?? "") || avatar !== (user.companion_avatar ?? "");

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!avatar || !name.trim()) return;
    updateCompanion.mutate({ companion_name: name.trim(), companion_avatar: avatar });
  }

  return (
    <section aria-labelledby="companion-heading" className="rounded-lg border border-line bg-surface p-5">
      <h2 id="companion-heading" className="text-sm font-semibold text-ink-secondary">
        AI Companion
      </h2>
      <p className="mt-1 text-sm text-ink-muted">
        {isConfigured
          ? "Rename or reshape the AI that mentors you across every project."
          : "Name and pick a look for the AI that mentors you across every project."}
      </p>

      <form onSubmit={handleSubmit} className="mt-4 flex flex-col gap-4">
        <div role="radiogroup" aria-label="Companion avatar" className="grid grid-cols-4 gap-2 sm:grid-cols-8">
          {AVATAR_OPTIONS.map((option) => {
            const selected = avatar === option.key;
            return (
              <button
                key={option.key}
                type="button"
                role="radio"
                aria-checked={selected}
                aria-label={option.label}
                onClick={() => setAvatar(option.key)}
                className={`flex aspect-square flex-col items-center justify-center gap-1 rounded-md border p-1 transition-colors ${
                  selected
                    ? "border-accent bg-accent-soft"
                    : "border-line hover:bg-surface-muted"
                }`}
              >
                <PixelPet species={option.key} size={3} idle={selected} />
                <span
                  className={`text-[10px] font-medium ${selected ? "text-accent-ink" : "text-ink-secondary"}`}
                >
                  {option.label}
                </span>
              </button>
            );
          })}
        </div>

        <FormField
          id="companion-name"
          label="Name"
          maxLength={50}
          placeholder="e.g. Rex"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />

        {updateCompanion.isError && (
          <p role="alert" className="text-sm text-danger-ink">
            {updateCompanion.error.message}
          </p>
        )}
        {updateCompanion.isSuccess && !dirty && (
          <p className="text-sm text-success-ink">Saved.</p>
        )}

        <div>
          <Button
            type="submit"
            size="sm"
            loading={updateCompanion.isPending}
            disabled={!dirty || !avatar || !name.trim()}
          >
            Save companion
          </Button>
        </div>
      </form>
    </section>
  );
}

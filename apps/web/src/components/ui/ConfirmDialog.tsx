"use client";

import { Button } from "ui";

import { Dialog } from "@/components/ui/Dialog";

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel: string;
  /** Destructive actions get the danger button treatment. */
  destructive?: boolean;
  pending?: boolean;
  error?: string | null;
}

/** Replaces window.confirm for archive/delete — keyboard accessible,
 * shows the mutation's pending/error state inline. */
export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel,
  destructive = false,
  pending = false,
  error,
}: ConfirmDialogProps) {
  return (
    <Dialog open={open} onClose={onClose} title={title} description={description}>
      {error && (
        <p role="alert" className="mb-3 text-sm text-danger-ink">
          {error}
        </p>
      )}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onClose} disabled={pending}>
          Cancel
        </Button>
        <Button
          type="button"
          variant={destructive ? "danger" : "primary"}
          onClick={onConfirm}
          loading={pending}
        >
          {confirmLabel}
        </Button>
      </div>
    </Dialog>
  );
}

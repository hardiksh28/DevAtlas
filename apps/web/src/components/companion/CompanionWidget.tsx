"use client";

import { CheckCircle2, X } from "lucide-react";
import { useEffect } from "react";

import { PixelPet } from "@/components/companion/PixelPet";
import { useCurrentUser } from "@/hooks/useAuth";
import { getCompanionDisplayName } from "@/lib/companion";
import { useCompanionStore } from "@/store/useCompanionStore";

const AUTO_DISMISS_MS = 5000;

/** Persistent floating companion — mounted once in AppShell so it
 * survives every route change within the app (the web-app equivalent of
 * a native desktop widget; a browser tab can't render above the OS
 * desktop the way a native app can, so this is scoped to the DevAtlas
 * window itself). Shows a status bubble when useCompanionStore.notify()
 * fires from elsewhere in the app (mentor replies, build plan ready). */
export function CompanionWidget() {
  const { data: user } = useCurrentUser();
  const { notification, bounceTick, dismiss } = useCompanionStore();

  useEffect(() => {
    if (!notification) return;
    const timer = setTimeout(dismiss, AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [notification, dismiss]);

  if (!user) return null;

  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-40 flex flex-col items-end gap-2">
      {notification && (
        <div className="pointer-events-auto anim-pop-in flex items-center gap-2 rounded-full border border-line bg-surface py-2 pl-3 pr-2 shadow-overlay">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-success-ink" aria-hidden="true" />
          <p className="text-sm text-ink">{notification.message}</p>
          <button
            type="button"
            onClick={dismiss}
            aria-label="Dismiss notification"
            className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-ink-faint transition-colors hover:bg-surface-muted hover:text-ink"
          >
            <X className="h-3.5 w-3.5" aria-hidden="true" />
          </button>
        </div>
      )}

      <div
        className="pointer-events-auto flex h-14 w-14 items-center justify-center rounded-full border border-line bg-surface shadow-overlay"
        title={getCompanionDisplayName(user.companion_name)}
      >
        <PixelPet species={user.companion_avatar} size={3} idle bounceKey={bounceTick} />
      </div>
    </div>
  );
}

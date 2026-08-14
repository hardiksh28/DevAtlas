import Link from "next/link";
import type { ReactNode } from "react";
import { ArrowLeft } from "lucide-react";

import { DevAtlasLogo } from "@/components/brand/Logo";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-canvas p-4">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-dot-grid" />

      <div className="w-full max-w-sm">
        <div className="flex items-center justify-between">
          <Link
            href="/"
            aria-label="Back to the DevAtlas homepage"
            className="group inline-flex items-center gap-1.5 rounded-full py-1 pr-2 text-xs font-semibold text-ink-secondary transition-colors hover:text-ink"
          >
            <ArrowLeft className="h-3.5 w-3.5 transition-transform group-hover:-translate-x-0.5" />
            Home
          </Link>
          <DevAtlasLogo size={22} />
        </div>

        <div className="mt-6 rounded-2xl border-2 border-ink bg-surface p-6 sticker-shadow sm:p-8">
          {children}
        </div>

        <p className="mt-6 text-center text-xs text-ink-faint">
          Guided independence, not generated answers.
        </p>
      </div>
    </main>
  );
}

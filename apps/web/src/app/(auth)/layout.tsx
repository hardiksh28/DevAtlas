import Link from "next/link";
import type { ReactNode } from "react";

import { DevAtlasLogo } from "@/components/brand/Logo";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-canvas p-4">
      <div className="w-full max-w-sm">
        <Link href="/" aria-label="Back to the DevAtlas homepage" className="inline-block rounded-md">
          <DevAtlasLogo size={26} />
        </Link>
        <div className="mt-6 rounded-xl border border-line bg-surface p-6 shadow-raised sm:p-8">
          {children}
        </div>
      </div>
    </main>
  );
}

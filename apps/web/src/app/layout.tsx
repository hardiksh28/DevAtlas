import type { Metadata } from "next";
import type { ReactNode } from "react";

import { QueryProvider } from "@/lib/query-client";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Engineering Workspace",
  description: "An AI mentor that teaches by guiding, not generating.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}

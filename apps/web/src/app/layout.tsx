import type { Metadata } from "next";
import { Plus_Jakarta_Sans, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "next-themes";
import type { ReactNode } from "react";

import { QueryProvider } from "@/lib/query-client";

import "./globals.css";

const sans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
  weight: ["400", "500", "600", "700", "800"],
});

const mono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: {
    default: "DevAtlas — Stop Watching Tutorials. Start Building Production Software.",
    template: "%s · DevAtlas",
  },
  description:
    "Upload documentation, GitHub repositories, or your own project idea. DevAtlas transforms them into a personalized engineering roadmap, teaches every concept, reviews your code like a senior engineer, and helps you ship production-ready software.",
  keywords: [
    "AI engineering",
    "software engineering education",
    "GitHub repo learning",
    "Socratic AI mentor",
    "code review",
    "production software",
    "interactive coding workspace",
    "RAG systems",
  ],
  authors: [{ name: "DevAtlas" }],
  creator: "DevAtlas Inc.",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://devatlas.com",
    title: "DevAtlas — Stop Watching Tutorials. Start Building Production Software.",
    description:
      "Transform repositories, documentation, and project ideas into personalized engineering roadmaps with Socratic AI mentorship and PR-style code reviews.",
    siteName: "DevAtlas",
  },
  twitter: {
    card: "summary_large_image",
    title: "DevAtlas — Stop Watching Tutorials. Start Building Production Software.",
    description:
      "Transform repositories, documentation, and project ideas into personalized engineering roadmaps with Socratic AI mentorship and PR-style code reviews.",
    creator: "@devatlas",
  },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    // suppressHydrationWarning: next-themes sets the `dark` class on
    // <html> before hydration, which React would otherwise flag.
    <html lang="en" suppressHydrationWarning>
      <body className={`${sans.variable} ${mono.variable} font-sans`}>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          <QueryProvider>{children}</QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

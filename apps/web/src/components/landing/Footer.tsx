"use client";

import React from "react";
import Link from "next/link";
import { MessageSquare } from "lucide-react";
import { DevAtlasLogo } from "@/components/brand/Logo";

function GithubIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fillRule="evenodd"
        d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
        clipRule="evenodd"
      />
    </svg>
  );
}

function TwitterIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

export function Footer() {
  return (
    <footer className="relative overflow-hidden bg-ink py-16 text-xs text-white/60 mt-4 mx-3 mb-3 rounded-[2rem] sm:mx-4 sm:mb-4">
      {/* Soft yellow ambient glow, bottom-center */}
      <div
        className="pointer-events-none absolute inset-x-0 bottom-0 -z-0 h-72"
        style={{
          background: "radial-gradient(ellipse 480px 220px at 50% 100%, rgba(250,204,21,0.35), transparent 70%)",
        }}
      />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-12 lg:grid-cols-[1.5fr_1fr_1fr_1fr]">
          {/* Brand & Mission Column */}
          <div>
            <Link href="/" aria-label="DevAtlas home">
              <DevAtlasLogo size={24} dark />
            </Link>
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-white/60">
              The AI engineering workspace. Upload repositories, follow personalized milestone
              roadmaps, receive Socratic code reviews, and ship production software.
            </p>
            <div className="mt-6 flex items-center gap-3">
              <a
                href="https://github.com/hardiksh28/DevAtlas"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 bg-white/5 text-white/60 transition-colors hover:border-white/30 hover:text-white"
                aria-label="GitHub"
              >
                <GithubIcon className="h-4 w-4" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 bg-white/5 text-white/60 transition-colors hover:border-white/30 hover:text-white"
                aria-label="Twitter / X"
              >
                <TwitterIcon className="h-3.5 w-3.5" />
              </a>
              <a
                href="https://discord.com"
                target="_blank"
                rel="noopener noreferrer"
                className="flex h-9 w-9 items-center justify-center rounded-full border border-white/15 bg-white/5 text-white/60 transition-colors hover:border-white/30 hover:text-white"
                aria-label="Discord"
              >
                <MessageSquare className="h-4 w-4" />
              </a>
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-accent">
              Product
            </h4>
            <ul className="mt-4 space-y-2.5">
              <li>
                <a href="#features" className="hover:text-white transition-colors">
                  Features
                </a>
              </li>
              <li>
                <a href="#how-it-works" className="hover:text-white transition-colors">
                  How It Works
                </a>
              </li>
              <li>
                <a href="#workspace" className="hover:text-white transition-colors">
                  Cloud Workspace
                </a>
              </li>
              <li>
                <a href="#comparison" className="hover:text-white transition-colors">
                  Comparison Matrix
                </a>
              </li>
              <li>
                <a href="#pricing" className="hover:text-white transition-colors">
                  Pricing Plans
                </a>
              </li>
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-accent">
              Resources
            </h4>
            <ul className="mt-4 space-y-2.5">
              <li>
                <a
                  href="https://github.com/hardiksh28/DevAtlas"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-white transition-colors"
                >
                  GitHub Repository
                </a>
              </li>
              <li>
                <Link href="/login" className="hover:text-white transition-colors">
                  Documentation
                </Link>
              </li>
              <li>
                <a href="#faq" className="hover:text-white transition-colors">
                  FAQ
                </a>
              </li>
              <li>
                <span className="text-white/30">API Reference (v1.4)</span>
              </li>
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-accent">
              Legal & Trust
            </h4>
            <ul className="mt-4 space-y-2.5">
              <li>
                <span className="hover:text-white cursor-pointer transition-colors">
                  Privacy Policy
                </span>
              </li>
              <li>
                <span className="hover:text-white cursor-pointer transition-colors">
                  Terms of Service
                </span>
              </li>
              <li>
                <span className="hover:text-white cursor-pointer transition-colors">
                  Security & SOC2
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Sub-Footer Bar */}
        <div className="mt-12 flex flex-col gap-4 border-t border-white/10 pt-8 sm:flex-row sm:items-center sm:justify-between text-xs text-white/40">
          <p>© {new Date().getFullYear()} DevAtlas Inc. All rights reserved.</p>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-accent animate-pulse" />
            <span className="font-mono text-[11px] text-white/50">All systems operational · v2.0.0</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

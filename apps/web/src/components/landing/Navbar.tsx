"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X } from "lucide-react";
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

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  const navLinks = [
    { label: "Features", href: "#features" },
    { label: "How It Works", href: "#how-it-works" },
    { label: "Workspace", href: "#workspace" },
    { label: "Comparison", href: "#comparison" },
    { label: "Pricing", href: "#pricing" },
    { label: "FAQ", href: "#faq" },
  ];

  return (
    <header className={`sticky top-3 z-50 px-3 sm:px-4 transition-all duration-300 ${isScrolled ? "" : ""}`}>
      <div
        className={`mx-auto flex h-16 max-w-6xl items-center justify-between rounded-full bg-ink pl-4 pr-2 sm:pl-6 sm:pr-3 shadow-lg transition-shadow ${
          isScrolled ? "shadow-2xl" : ""
        }`}
      >
        {/* Brand Logo */}
        <Link href="/" aria-label="DevAtlas home" className="flex items-center gap-2 group shrink-0">
          <DevAtlasLogo size={24} dark />
        </Link>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-1 lg:gap-1.5">
          {navLinks.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="rounded-full px-3 py-2 text-xs lg:text-sm font-semibold text-white/70 transition-colors hover:bg-white/10 hover:text-white"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Right CTA Actions */}
        <div className="hidden sm:flex items-center gap-2">
          <a
            href="https://github.com/hardiksh28/DevAtlas"
            target="_blank"
            rel="noopener noreferrer"
            className="flex h-10 w-10 items-center justify-center rounded-full text-white/70 transition-colors hover:bg-white/10 hover:text-white"
            aria-label="GitHub repository"
          >
            <GithubIcon className="h-4 w-4" />
          </a>

          <Link
            href="/login"
            className="rounded-full bg-white px-5 py-2.5 text-xs lg:text-sm font-bold text-ink transition-transform active:scale-[0.97] hover:bg-white/90"
          >
            Sign In
          </Link>

          <Link
            href="/register"
            className="inline-flex items-center justify-center gap-1.5 rounded-full bg-accent px-5 py-2.5 text-xs lg:text-sm font-bold text-ink transition-transform hover:bg-accent-hover active:scale-[0.97]"
          >
            <span>Start Building</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        {/* Mobile Menu Toggle Button */}
        <div className="flex sm:hidden items-center gap-2">
          <Link href="/register" className="rounded-full bg-accent px-3 py-1.5 text-xs font-bold text-ink">
            Start
          </Link>
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="rounded-full p-2 text-white/80 hover:bg-white/10 hover:text-white"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div className="mx-auto mt-2 max-w-6xl rounded-3xl border-2 border-ink bg-surface px-4 py-6 shadow-lg sm:hidden">
          <nav className="flex flex-col gap-1">
            {navLinks.map((link) => (
              <a
                key={link.label}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className="rounded-xl px-3 py-2.5 text-sm font-semibold text-ink-secondary hover:bg-surface-muted hover:text-ink"
              >
                {link.label}
              </a>
            ))}
            <div className="mt-4 flex flex-col gap-2 pt-4 border-t-2 border-line">
              <a
                href="https://github.com/hardiksh28/DevAtlas"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 rounded-full border-2 border-ink py-2.5 text-sm font-semibold text-ink"
              >
                <GithubIcon className="h-4 w-4" />
                <span>GitHub Repository</span>
              </a>
              <Link
                href="/login"
                className="flex items-center justify-center rounded-full border-2 border-ink py-2.5 text-sm font-semibold text-ink"
              >
                Sign in
              </Link>
              <Link
                href="/register"
                className="flex items-center justify-center gap-2 rounded-full bg-accent py-2.5 text-sm font-bold text-ink"
              >
                <span>Start Building Free</span>
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}

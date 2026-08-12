"use client";

import React from "react";
import { Navbar } from "@/components/landing/Navbar";
import { HeroSection } from "@/components/landing/HeroSection";
import { InteractiveProductDemo } from "@/components/landing/InteractiveProductDemo";
import { MetricsSection } from "@/components/landing/MetricsSection";
import { ProblemSection } from "@/components/landing/ProblemSection";
import { HowItWorksSection } from "@/components/landing/HowItWorksSection";
import { FeatureBentoGrid } from "@/components/landing/FeatureBentoGrid";
import { MentorShowcase } from "@/components/landing/MentorShowcase";
import { WorkspacePreview } from "@/components/landing/WorkspacePreview";
import { ComparisonTable } from "@/components/landing/ComparisonTable";
import { PricingSection } from "@/components/landing/PricingSection";
import { FAQSection } from "@/components/landing/FAQSection";
import { CTASection } from "@/components/landing/CTASection";
import { Footer } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="landing-light flex min-h-screen flex-col bg-canvas text-ink selection:bg-accent selection:text-ink font-sans antialiased">
      {/* 1. Sticky Navigation */}
      <Navbar />

      <main className="flex-1">
        {/* 2. Hero Section */}
        <HeroSection />

        {/* 3. Interactive Product Demo (Full-Width Story Timeline) */}
        <InteractiveProductDemo />

        {/* 4. Trust & Metrics Section */}
        <MetricsSection />

        {/* 4. Problem Section: Traditional Learning vs DevAtlas */}
        <ProblemSection />

        {/* 5. How It Works: 4 Connected Cards */}
        <HowItWorksSection />

        {/* 6. Feature Bento Grid: Learn, Build, Improve, Ship */}
        <FeatureBentoGrid />

        {/* 7. AI Mentor Showcase: Socratic Hints & Code Review */}
        <MentorShowcase />

        {/* 8. Realistic Workspace Preview */}
        <WorkspacePreview />

        {/* 9. Comparison Matrix: Tutorials vs ChatGPT vs DevAtlas */}
        <ComparisonTable />

        {/* 10. Transparent Pricing */}
        <PricingSection />

        {/* 11. FAQ Section */}
        <FAQSection />

        {/* 12. Final High-Impact CTA */}
        <CTASection />
      </main>

      {/* 13. Footer */}
      <Footer />
    </div>
  );
}

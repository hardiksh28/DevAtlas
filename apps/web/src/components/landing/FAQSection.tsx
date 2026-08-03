"use client";

import React, { useState } from "react";
import { ChevronDown } from "lucide-react";

interface FAQItem {
  question: string;
  answer: string;
}

const FAQS: FAQItem[] = [
  {
    question: "Can AI write my code?",
    answer:
      "No. DevAtlas teaches instead of generating complete solutions. You write the code; the AI acts as a senior staff engineer guiding your architectural decisions, asking Socratic questions, and reviewing your pull requests.",
  },
  {
    question: "Can I upload private repositories?",
    answer:
      "Yes. You can connect your private GitHub repositories via OAuth or upload project archives directly. Your source code is analyzed inside an isolated container session and is never used to train AI models.",
  },
  {
    question: "Can I upload documentation?",
    answer:
      "Yes. Upload PDF documentation, Markdown specifications, or OpenAPI schemas. DevAtlas indexes the interfaces, extracts code patterns, and constructs a tailored learning roadmap around your exact libraries.",
  },
  {
    question: "Can I use local AI?",
    answer:
      "Yes. DevAtlas supports connecting directly to local inference endpoints (such as Ollama or LM Studio) so you can run the mentor model entirely on your own hardware.",
  },
  {
    question: "How does DevAtlas differ from video courses?",
    answer:
      "Video tutorials promote passive consumption where you copy an instructor without building intuition. DevAtlas forces active problem-solving: you write code in a cloud workspace, pass automated evaluation assertions, and learn why architectural decisions matter.",
  },
];

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const toggle = (idx: number) => {
    setOpenIndex((prev) => (prev === idx ? null : idx));
  };

  return (
    <section id="faq" className="relative border-t border-white/[0.08] py-20 sm:py-28 lg:py-32">
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">
            FREQUENTLY ASKED QUESTIONS
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl font-extrabold tracking-[-0.03em] text-white">
            Everything you need to know.
          </h2>
          <p className="mt-4 text-base text-zinc-400">
            Clear answers on privacy, workflows, local AI support, and how DevAtlas works.
          </p>
        </div>

        {/* Accordion List */}
        <div className="mt-12 space-y-4">
          {FAQS.map((faq, idx) => {
            const isOpen = openIndex === idx;
            return (
              <div
                key={faq.question}
                className="overflow-hidden rounded-2xl border border-white/[0.08] bg-zinc-900/40 backdrop-blur-xl transition-all duration-300 hover:border-white/[0.15]"
              >
                <button
                  type="button"
                  onClick={() => toggle(idx)}
                  className="flex w-full items-center justify-between p-5 text-left transition-colors hover:bg-white/[0.02]"
                >
                  <span className="text-sm sm:text-base font-semibold text-white">
                    {faq.question}
                  </span>
                  <ChevronDown
                    className={`h-4 w-4 text-zinc-400 transition-transform duration-300 ${
                      isOpen ? "rotate-180 text-blue-400" : ""
                    }`}
                  />
                </button>

                {isOpen && (
                  <div className="border-t border-white/[0.04] p-5 pt-3 text-xs sm:text-sm leading-relaxed text-zinc-400">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

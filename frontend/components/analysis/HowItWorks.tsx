"use client";

import { useReveal } from "@/lib/use-reveal";

const STEPS = [
  {
    num: "1",
    title: "You submit",
    body: "Drop in whatever you're working on. No formatting rules, no minimum length.",
  },
  {
    num: "2",
    title: "It reads closely",
    body: "Sentence structure, repetition, clarity, tone — flagged inline, not buried in a report.",
  },
  {
    num: "3",
    title: "It checks your history",
    body: "If you've made the same slip three times, it says so, instead of repeating generic advice.",
  },
  {
    num: "4",
    title: "You see the trend",
    body: "Every round gets logged, so improvement is something you can actually point to.",
  },
];

export default function HowItWorks() {
  const headingRef = useReveal<HTMLHeadingElement>();
  const gridRef = useReveal<HTMLDivElement>();

  return (
    <section id="how" className="bg-ink py-[70px] text-paper">
      <div className="mx-auto max-w-none px-6 sm:px-14">
        <h2
          ref={headingRef}
          className="reveal max-w-[20ch] font-display text-[clamp(28px,3vw,36px)] font-semibold"
        >
          Four rounds, not one verdict.
        </h2>

        {/* Top-rule separators (not vertical dividers) so the number,
            heading and border never compete for the same space, and the
            layout survives reflow down to a single column. */}
        <div
          ref={gridRef}
          className="reveal reveal-stagger mt-12 grid grid-cols-1 gap-x-7 gap-y-9 sm:grid-cols-2 lg:grid-cols-4"
        >
          {STEPS.map((step) => (
            <div key={step.num} className="border-t border-paper/20 pt-[22px]">
              <span className="block font-display text-[32px] italic leading-none opacity-55">
                {step.num}
              </span>
              <h3 className="mt-[14px] text-[17px] font-medium">{step.title}</h3>
              <p className="mt-2 text-[14.5px] leading-[1.55] opacity-70">{step.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

"use client";

import { useReveal } from "@/lib/use-reveal";

const ROWS = [
  {
    name: "Clarity",
    body: "Sentences that bury the point, hedge too much, or say the same thing twice — flagged with a reason, not just a red underline.",
  },
  {
    name: "Pattern memory",
    body: 'Penfight keeps a running record of your submissions, so it can tell you "this is the fourth time" instead of treating every draft as new.',
  },
  {
    name: "Tone & register",
    body: "Catches drift between formal and casual within the same piece — useful for anything meant to sound like one voice.",
  },
  {
    name: "Structure",
    body: "Flags when an argument or explanation loses its thread, or when a conclusion doesn't follow from what came before it.",
  },
];

export default function Capabilities() {
  const headingRef = useReveal<HTMLHeadingElement>();
  const listRef = useReveal<HTMLDivElement>();

  return (
    <section id="capabilities" className="bg-paper-2 py-[70px]">
      <div className="mx-auto max-w-none px-6 sm:px-14">
        <h2 ref={headingRef} className="reveal max-w-[20ch] font-display text-[clamp(28px,3vw,36px)] font-semibold">
          What it actually reads for
        </h2>

        <div ref={listRef} className="reveal reveal-stagger mt-10">
          {ROWS.map((row) => (
            <div
              key={row.name}
              className="grid grid-cols-1 gap-4 border-b border-line py-6 sm:grid-cols-[220px_1fr] sm:gap-9"
            >
              <div className="font-display text-[19px] italic">{row.name}</div>
              <p className="max-w-[58ch] text-[15px] opacity-80">{row.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

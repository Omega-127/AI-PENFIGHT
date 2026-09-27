"use client";

import { useReveal } from "@/lib/use-reveal";
import ProgressChart from "./ProgressChart";

export default function ProgressSection() {
  const copyRef = useReveal<HTMLDivElement>();
  const chartRef = useReveal<HTMLDivElement>();

  return (
    <section id="progress" className="bg-ink py-[70px] text-paper">
      <div className="mx-auto grid max-w-none grid-cols-1 gap-14 px-6 sm:px-14 lg:grid-cols-[1fr_1.2fr] lg:items-center">
        <div ref={copyRef} className="reveal">
          <h2 className="max-w-[20ch] font-display text-[clamp(28px,3vw,36px)] font-semibold">
            A record, not just a score.
          </h2>
          <p className="mt-4 max-w-[42ch] text-[15.5px] opacity-80">
            Each submission adds one point to your line. You&rsquo;re not chasing a
            number — you&rsquo;re watching the same three mistakes show up less often.
          </p>
        </div>

        <div ref={chartRef} className="reveal">
          <ProgressChart />
        </div>
      </div>
    </section>
  );
}

"use client";

import { useState } from "react";
import { SAMPLE_DEMO_TEXT } from "@/lib/constants";
import { runHeuristics } from "@/lib/markup-heuristics";
import type { Finding } from "@/lib/types";
import MarkList from "@/components/feedback/MarkList";

export default function MarkupDemo() {
  const [text, setText] = useState(SAMPLE_DEMO_TEXT);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [status, setStatus] = useState("not read yet");
  const [reading, setReading] = useState(false);

  function markUp() {
    setReading(true);
    setStatus("reading…");
    window.setTimeout(() => {
      const result = runHeuristics(text);
      setFindings(result);
      setStatus(
        result.some((f) => f.type === "flag")
          ? `${result.length} notes — a few worth fixing`
          : "reads well"
      );
      setReading(false);
    }, 380);
  }

  return (
    <div className="relative rounded-[3px] border border-line bg-[#FBF7EC] p-6 pb-[22px] shadow-[2px_2px_0_theme(colors.paper.3)]">
      <div className="mb-3.5 text-[12.5px] opacity-60">
        try it — type or edit the paragraph below
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        spellCheck={false}
        className="min-h-[96px] w-full resize-y border-none bg-transparent font-display text-lg leading-relaxed text-[#201C14] outline-none"
      />

      <div className="mt-2.5 flex items-center justify-between border-t border-dashed border-line pt-3.5">
        <button
          onClick={markUp}
          disabled={reading}
          className="rounded-sm bg-ink px-4 py-[9px] text-[13.5px] text-paper disabled:opacity-60"
        >
          Mark it up
        </button>
        <span className="text-[12.5px] opacity-55">{status}</span>
      </div>

      <MarkList findings={findings} />
    </div>
  );
}

// Client-side heuristic preview of what the backend AI Engine will do
// (see ARCHITECTURE.md §6, AI Module). This is a stand-in for the real
// /api/v1/analyze call so the demo works with no backend running.

import type { Finding } from "./types";

export function runHeuristics(text: string): Finding[] {
  const findings: Finding[] = [];

  if (/\bvery very\b/i.test(text) || (text.match(/\bvery\b/gi) || []).length > 1) {
    findings.push({
      type: "flag",
      text: '"very very" — intensifiers stacked like this weaken the sentence instead of strengthening it.',
    });
  }

  if (/\balot\b/i.test(text)) {
    findings.push({ type: "flag", text: '"alot" isn\'t a word — you likely mean "a lot".' });
  }

  if (/\bhave did\b|\bhas did\b/i.test(text)) {
    findings.push({ type: "flag", text: '"have did" — should be "have done".' });
  }

  const sentenceTooLong = text
    .split(/[.!?]/)
    .filter((s) => s.trim())
    .some((s) => s.trim().split(/\s+/).length > 28);
  if (sentenceTooLong) {
    findings.push({
      type: "tip",
      text: "One sentence runs past 28 words — consider splitting it so the point lands sooner.",
    });
  }

  const seen: Record<string, number> = {};
  text
    .trim()
    .split(/\s+/)
    .forEach((w) => {
      const clean = w.toLowerCase().replace(/[^a-z]/g, "");
      if (clean.length > 4) seen[clean] = (seen[clean] || 0) + 1;
    });
  const repeat = Object.entries(seen).find(([, c]) => c >= 2);
  if (repeat) {
    findings.push({
      type: "tip",
      text: `"${repeat[0]}" appears more than once nearby — a synonym would read cleaner.`,
    });
  }

  if (findings.length === 0) {
    findings.push({ type: "good", text: "Clean sentence — clear subject, no filler, nothing repeated." });
  }

  return findings;
}

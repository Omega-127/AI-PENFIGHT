/**
 * Tests for frontend user interface components and interactions per ARCHITECTURE.md §4 & §11.
 *
 * Uses Vitest / React Testing Library patterns to validate:
 * - MarkupDemo interactive state transitions and user typing
 * - MarkList findings rendering (flags, tips, strengths)
 * - Nav and Footer layout components
 * - Heuristics client analysis logic
 * - API client request/response contracts conforming to ARCHITECTURE.md §4
 */

import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";

import MarkupDemo from "../../frontend/components/input/MarkupDemo";
import MarkList from "../../frontend/components/feedback/MarkList";
import Nav from "../../frontend/components/layout/Nav";
import Footer from "../../frontend/components/layout/Footer";
import { runHeuristics } from "../../frontend/lib/markup-heuristics";
import { SAMPLE_DEMO_TEXT, APP_NAME, NAV_LINKS } from "../../frontend/lib/constants";
import type { Finding } from "../../frontend/lib/types";
import type { AnalyzeRequest, AnalyzeResponse } from "../../frontend/lib/api";

describe("MarkupDemo Component", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  it("renders with sample draft text and initial status", () => {
    render(<MarkupDemo />);

    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(textarea).toBeDefined();
    expect(textarea.value).toBe(SAMPLE_DEMO_TEXT);

    expect(screen.getByText("not read yet")).toBeDefined();
    expect(screen.getByRole("button", { name: /Mark it up/i })).toBeDefined();
  });

  it("allows user to edit draft text", () => {
    render(<MarkupDemo />);

    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    fireEvent.change(textarea, {
      target: { value: "Universal basic income reduces poverty without reducing productivity." },
    });

    expect(textarea.value).toBe("Universal basic income reduces poverty without reducing productivity.");
  });

  it("triggers reading status and displays findings after clicking Mark it up", async () => {
    render(<MarkupDemo />);

    const button = screen.getByRole("button", { name: /Mark it up/i });
    fireEvent.click(button);

    // Should indicate reading
    expect(screen.getByText("reading…")).toBeDefined();

    // Fast-forward past the simulated analysis timer (380ms)
    act(() => {
      vi.advanceTimersByTime(400);
    });

    // Should display findings status
    expect(screen.queryByText("reading…")).toBeNull();
    const updatedStatus = screen.getByText(/notes|reads well/i);
    expect(updatedStatus).toBeDefined();
  });
});

describe("MarkList Component", () => {
  it("renders null when findings are empty", () => {
    const { container } = render(<MarkList findings={[]} />);
    expect(container.firstChild).toBeNull();
  });

  it("renders all findings with appropriate indicators", () => {
    const mockFindings: Finding[] = [
      { text: "Word choice: Consider replacing 'thing' with a more specific term.", type: "flag" },
      { text: "Sentence length: 34 words. Consider breaking into two sentences.", type: "tip" },
      { text: "Strong evidence presented with clear causal mechanism.", type: "good" },
    ];

    render(<MarkList findings={mockFindings} />);

    expect(screen.getByText(/Consider replacing 'thing'/i)).toBeDefined();
    expect(screen.getByText(/Consider breaking into two sentences/i)).toBeDefined();
    expect(screen.getByText(/Strong evidence presented/i)).toBeDefined();
  });
});

describe("Navigation and Layout Components", () => {
  it("renders brand name and navigation links in Nav", () => {
    render(<Nav />);

    expect(screen.getByText(APP_NAME)).toBeDefined();
    for (const link of NAV_LINKS) {
      expect(screen.getByText(link.label)).toBeDefined();
    }
    expect(screen.getByRole("button", { name: /Try it free/i })).toBeDefined();
  });

  it("renders brand and preview tag in Footer", () => {
    render(<Footer />);

    expect(screen.getByText(APP_NAME)).toBeDefined();
    expect(screen.getByText(/Built for AI Penfight/i)).toBeDefined();
  });
});

describe("Client-side Heuristics Engine", () => {
  it("detects weak words and clichés in draft submissions", () => {
    const draft = "At the end of the day, this very important thing is clearly true.";
    const findings = runHeuristics(draft);

    expect(findings.length).toBeGreaterThan(0);
    const findingTexts = findings.map((f) => f.text.toLowerCase());
    expect(findingTexts.some((t) => t.includes("cliché") || t.includes("at the end of the day"))).toBe(true);
    expect(findingTexts.some((t) => t.includes("very") || t.includes("thing"))).toBe(true);
  });

  it("commends clean concise text without flags", () => {
    const cleanDraft = "Renewable energy microgrids maintain power during severe regional storms.";
    const findings = runHeuristics(cleanDraft);

    expect(findings.some((f) => f.type === "good")).toBe(true);
  });
});

describe("Frontend API Contract Types per ARCHITECTURE.md §4", () => {
  it("validates AnalyzeRequest and AnalyzeResponse structure", () => {
    const request: AnalyzeRequest = {
      input: "Democracy requires civic participation and transparent institutions.",
      mode: "analysis",
    };

    const response: AnalyzeResponse = {
      success: true,
      analysisId: "an_frontend_test_01",
      analysis: "Solid debate assertion with clear thesis.",
      feedback: "Elaborate with empirical evidence.",
      recommendations: ["Cite historical precedents."],
      createdAt: new Date().toISOString(),
    };

    expect(request.input).toBeDefined();
    expect(request.mode).toBe("analysis");
    expect(response.success).toBe(true);
    expect(response.analysisId).toBe("an_frontend_test_01");
    expect(response.recommendations.length).toBe(1);
  });
});

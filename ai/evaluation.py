"""Evaluation Module for AI Penfight.

Measures feedback quality, schema validity, pattern detection precision,
and latency using deterministic checks and a curated local benchmark dataset.
Runs independently from live user traffic.
"""

import re
import time
from typing import Any, Dict, List, Optional, Set

from ai.clients.base_client import BaseLLMClient
from ai.decision_engine import decide_strategy
from ai.feedback_generation import generate_feedback
from ai.input_processing import process_input
from ai.pattern_detection import detect_patterns
from ai.schemas.feedback_schema import (
    BatchEvaluationReport,
    FeedbackResponse,
    SingleEvaluationResult,
)

# Curated benchmark dataset of debate arguments with ground-truth labels
BENCHMARK_DATASET: List[Dict[str, Any]] = [
    {
        "id": "tc_01_ad_hominem",
        "input": (
            "Your argument about climate policy is completely wrong because you're an idiot "
            "and only a fool would believe that carbon taxes work in practice."
        ),
        "expected_fallacies": ["Ad Hominem"],
        "expected_grammar": [],
        "expected_strategy": "fallacy_and_logic_focus",
    },
    {
        "id": "tc_02_slippery_slope",
        "input": (
            "If we regulate artificial intelligence algorithms even slightly, it will inevitably lead to "
            "complete authoritarian censorship and will eventually destroy human civilization."
        ),
        "expected_fallacies": ["Slippery Slope"],
        "expected_grammar": [],
        "expected_strategy": "fallacy_and_logic_focus",
    },
    {
        "id": "tc_03_grammar_heavy",
        "input": (
            "Their is no doubt that renewable energy has alot of benefits, but its obvious that "
            "governments could of invested better. We definately need better planning."
        ),
        "expected_fallacies": [],
        "expected_grammar": [
            "their/there confusion",
            "spelling: a lot",
            "its/it's confusion",
            "modal of/have confusion",
            "spelling: definitely",
        ],
        "expected_strategy": "style_and_delivery",
    },
    {
        "id": "tc_04_false_dilemma",
        "input": (
            "Either you agree that homework must be banned nationwide, or you are with us or against us "
            "when it comes to student health. There are only two choices in this debate."
        ),
        "expected_fallacies": ["False Dilemma"],
        "expected_grammar": [],
        "expected_strategy": "fallacy_and_logic_focus",
    },
    {
        "id": "tc_05_evidence_backed",
        "input": (
            "According to research published in economic journals, subsidized public transit reduces "
            "urban congestion by 24 percent, because commuters substitute away from private vehicles "
            "when transit frequency increases. Therefore, city councils should prioritize fleet expansion."
        ),
        "expected_fallacies": [],
        "expected_grammar": [],
        "expected_strategy": "comprehensive_debate_analysis",
    },
]


def _compute_word_overlap(text_a: str, text_b: str) -> float:
    """Compute token Jaccard similarity between two texts."""
    words_a = set(re.findall(r"\b\w{3,}\b", text_a.lower()))
    words_b = set(re.findall(r"\b\w{3,}\b", text_b.lower()))
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a.intersection(words_b))
    union = len(words_a.union(words_b))
    return round(intersection / union, 3)


def calculate_cost_estimate(token_usage: Dict[str, int], model: str = "gpt-4o-mini") -> float:
    """Estimate cost in USD based on published token prices (default: gpt-4o-mini rates)."""
    # $0.15 / 1M input tokens, $0.60 / 1M output tokens
    prompt_tokens = token_usage.get("prompt_tokens", 0)
    completion_tokens = token_usage.get("completion_tokens", 0)
    cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.00000060)
    return round(cost, 6)


def evaluate_feedback(
    feedback: FeedbackResponse,
    input_text: str = "",
    ground_truth: Optional[Dict[str, Any]] = None,
    latency_ms: float = 0.0,
    token_usage: Optional[Dict[str, int]] = None,
) -> SingleEvaluationResult:
    """Deterministically score a single feedback response against quality metrics.

    Metrics:
    - schema_validity: 1.0 if Pydantic model is fully formed with non-empty fields.
    - feedback_relevance: Jaccard similarity between input and feedback recommendations/overview.
    - grammar_accuracy: Precision & recall of flagged grammar rules against ground truth.
    - pattern_detection_accuracy: Accuracy of fallacy/pattern detection against ground truth.
    - logical_analysis_quality: Soundness check of scoring and fallacy explanations.
    """
    notes: List[str] = []

    # 1. Schema Validity (Deterministic)
    schema_valid = 1.0
    if not feedback.overall_feedback or not feedback.strengths or not feedback.weaknesses:
        schema_valid = 0.5
        notes.append("Incomplete core feedback sections.")
    if feedback.performance_score.overall_score <= 0.0:
        notes.append("Zero or negative overall score.")

    # 2. Feedback Relevance (Deterministic token overlap)
    combined_feedback_text = (
        f"{feedback.overall_feedback} "
        f"{' '.join(feedback.strengths)} "
        f"{' '.join(feedback.weaknesses)} "
        f"{' '.join(feedback.suggestions)}"
    )
    relevance = _compute_word_overlap(input_text, combined_feedback_text)
    # Scale relevance to a 0.0 - 1.0 range (Jaccard > 0.08 is typically solid relevance for distinct text)
    relevance_score = min(1.0, round(relevance * 4.0, 2))

    # 3. Ground Truth Matching (if available)
    grammar_acc = 1.0
    pattern_acc = 1.0

    if ground_truth:
        # Check expected fallacies
        expected_fallacies: List[str] = ground_truth.get("expected_fallacies", [])
        if expected_fallacies:
            detected_fallacy_names = [f.fallacy_name.lower() for f in feedback.logical_fallacies]
            hits = sum(1 for exp in expected_fallacies if exp.lower() in detected_fallacy_names)
            pattern_acc = round(hits / len(expected_fallacies), 2)
            if pattern_acc < 1.0:
                notes.append(f"Missed expected fallacy: {expected_fallacies}")

        # Check expected grammar
        expected_grammar: List[str] = ground_truth.get("expected_grammar", [])
        if expected_grammar:
            detected_grammar = [c.explanation.lower() for c in feedback.grammar_and_vocabulary]
            hits = sum(
                1 for exp in expected_grammar
                if any(exp.lower() in d for d in detected_grammar)
            )
            grammar_acc = round(hits / len(expected_grammar), 2)
            if grammar_acc < 1.0:
                notes.append(f"Detected {hits}/{len(expected_grammar)} expected grammar errors.")

    # 4. Logical Quality
    # If severe fallacies exist, logic score should be under 85
    logical_quality = 1.0
    if feedback.logical_fallacies and feedback.performance_score.logic_and_reasoning > 88.0:
        logical_quality = 0.7
        notes.append("Logic score unexpectedly high despite identified fallacies.")

    # 5. Composite overall quality
    overall_quality = round(
        (schema_valid * 0.25) +
        (relevance_score * 0.25) +
        (pattern_acc * 0.25) +
        (logical_quality * 0.25),
        2
    )

    cost_usd = calculate_cost_estimate(token_usage or {})

    return SingleEvaluationResult(
        analysis_id=feedback.analysis_id,
        schema_validity=schema_valid,
        feedback_relevance=relevance_score,
        grammar_accuracy=grammar_acc,
        pattern_detection_accuracy=pattern_acc,
        logical_analysis_quality=logical_quality,
        latency_ms=round(latency_ms, 2),
        overall_quality_score=overall_quality,
        estimated_cost_usd=cost_usd,
        token_usage=token_usage or {},
        notes=notes,
    )


def evaluate_batch(
    test_cases: Optional[List[Dict[str, Any]]] = None,
    llm_client: Optional[BaseLLMClient] = None,
) -> BatchEvaluationReport:
    """Run an automated evaluation suite across multiple benchmark test cases.

    Executes the full pipeline for each case and produces an aggregated
    metrics report.
    """
    cases = test_cases or BENCHMARK_DATASET
    results: List[SingleEvaluationResult] = []

    for case in cases:
        start_time = time.perf_counter()

        # Step 1: Input Processing
        processed = process_input(
            raw_input=case["input"],
            session_context={"test_id": case.get("id")},
        )

        # Step 2: Pattern Detection
        patterns = detect_patterns(processed_input=processed)

        # Step 3: Decision Engine
        decision = decide_strategy(processed_input=processed, pattern_features=patterns)

        # Step 4: Feedback Generation
        feedback = generate_feedback(
            processed_input=processed,
            pattern_features=patterns,
            decision=decision,
            llm_client=llm_client,
        )

        latency = (time.perf_counter() - start_time) * 1000

        # Step 5: Evaluate Result
        eval_result = evaluate_feedback(
            feedback=feedback,
            input_text=processed.normalized_text,
            ground_truth=case,
            latency_ms=latency,
        )
        results.append(eval_result)

    total_cases = len(results)
    if total_cases == 0:
        return BatchEvaluationReport(
            total_cases=0,
            successful_cases=0,
            mean_schema_validity=0.0,
            mean_feedback_relevance=0.0,
            mean_grammar_accuracy=0.0,
            mean_pattern_accuracy=0.0,
            mean_logical_quality=0.0,
            mean_overall_quality=0.0,
            p95_latency_ms=0.0,
            total_estimated_cost_usd=0.0,
            results=[],
        )

    # Compute aggregate statistics
    mean_schema = round(sum(r.schema_validity for r in results) / total_cases, 3)
    mean_relevance = round(sum(r.feedback_relevance for r in results) / total_cases, 3)
    mean_grammar = round(sum(r.grammar_accuracy for r in results) / total_cases, 3)
    mean_patterns = round(sum(r.pattern_detection_accuracy for r in results) / total_cases, 3)
    mean_logic = round(sum(r.logical_analysis_quality for r in results) / total_cases, 3)
    mean_overall = round(sum(r.overall_quality_score for r in results) / total_cases, 3)

    latencies = sorted([r.latency_ms for r in results])
    p95_idx = int(0.95 * total_cases) - 1
    p95_latency = latencies[max(0, p95_idx)]

    total_cost = round(sum(r.estimated_cost_usd for r in results), 6)
    successes = sum(1 for r in results if r.schema_validity >= 1.0)

    return BatchEvaluationReport(
        total_cases=total_cases,
        successful_cases=successes,
        mean_schema_validity=mean_schema,
        mean_feedback_relevance=mean_relevance,
        mean_grammar_accuracy=mean_grammar,
        mean_pattern_accuracy=mean_patterns,
        mean_logical_quality=mean_logic,
        mean_overall_quality=mean_overall,
        p95_latency_ms=round(p95_latency, 2),
        total_estimated_cost_usd=total_cost,
        results=results,
    )


def run_local_evaluation() -> Dict[str, Any]:
    """Execute evaluation and return a clean summary dictionary."""
    report = evaluate_batch()
    return report.model_dump()

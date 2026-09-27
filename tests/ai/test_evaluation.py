"""Tests for ai/evaluation.py per ARCHITECTURE.md §6 & §11."""

from ai.evaluation import (
    BENCHMARK_DATASET,
    calculate_cost_estimate,
    evaluate_batch,
    evaluate_feedback,
    run_local_evaluation,
)
from ai.feedback_generation import generate_rule_based_feedback
from ai.input_processing import process_input
from ai.pattern_detection import detect_patterns
from ai.decision_engine import decide_strategy
from ai.schemas.feedback_schema import (
    BatchEvaluationReport,
    SingleEvaluationResult,
)


def test_calculate_cost_estimate():
    tokens = {"prompt_tokens": 1000, "completion_tokens": 500}
    # 1000 * 0.00000015 + 500 * 0.00000060 = 0.00015 + 0.00030 = 0.00045
    cost = calculate_cost_estimate(tokens)
    assert 0.0004 <= cost <= 0.0005


def test_evaluate_single_feedback_deterministic():
    text = (
        "Your argument about climate policy is completely wrong because you're an idiot "
        "and only a fool would believe that carbon taxes work in practice."
    )
    processed = process_input(text)
    patterns = detect_patterns(processed)
    decision = decide_strategy(processed, patterns)
    feedback = generate_rule_based_feedback(processed, patterns, decision)

    eval_result = evaluate_feedback(
        feedback=feedback,
        input_text=text,
        ground_truth=BENCHMARK_DATASET[0],
        latency_ms=25.0,
    )

    assert isinstance(eval_result, SingleEvaluationResult)
    assert eval_result.schema_validity == 1.0
    assert eval_result.pattern_detection_accuracy > 0.0
    assert eval_result.latency_ms == 25.0
    assert eval_result.overall_quality_score > 0.5


def test_evaluate_batch_benchmark():
    # Run evaluation across the curated benchmark suite
    report = evaluate_batch(BENCHMARK_DATASET[:3])

    assert isinstance(report, BatchEvaluationReport)
    assert report.total_cases == 3
    assert report.successful_cases == 3
    assert report.mean_schema_validity == 1.0
    assert report.mean_overall_quality > 0.6
    assert len(report.results) == 3


def test_run_local_evaluation_returns_dict():
    result = run_local_evaluation()
    assert isinstance(result, dict)
    assert "total_cases" in result
    assert "mean_schema_validity" in result
    assert "results" in result
    assert result["mean_schema_validity"] >= 1.0

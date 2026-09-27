"""Feedback Generation Module for AI Penfight.

Executes the feedback pipeline:
1. Loads the versioned prompt template from disk.
2. Injects processed input, pattern features, bounded history, and decision strategy.
3. Invokes the model-agnostic LLM client or rule-based generator.
4. Parses and validates the response against the Pydantic FeedbackResponse schema.
5. Retries once if the model response is malformed.
6. Gracefully degrades to a rule-based evaluation if the LLM is unavailable or fails.
"""

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai.clients.base_client import BaseLLMClient
from ai.clients.llm_client import get_llm_client
from ai.schemas.feedback_schema import (
    CorrectionItem,
    DecisionResult,
    FallacyItem,
    FeedbackResponse,
    PatternFeatures,
    PerformanceScore,
    ProcessedInput,
)

logger = logging.getLogger("ai_penfight.feedback_generation")

# Default path to prompt file
DEFAULT_PROMPT_PATH = Path(__file__).parent / "prompts" / "feedback_prompt.md"


def load_feedback_prompt(prompt_path: Optional[Path] = None) -> Tuple[str, str]:
    """Load the versioned markdown prompt file from disk.

    Returns:
        Tuple of (prompt_template_text, prompt_version)
    """
    path = prompt_path or DEFAULT_PROMPT_PATH
    if not path.exists():
        raise FileNotFoundError(f"Feedback prompt file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract version tag: e.g. **Version:** v1.2.0
    version_match = re.search(r"\*\*Version:\*\*\s*([^\s\n\r]+)", content)
    prompt_version = version_match.group(1) if version_match else "v1.2.0"

    return content, prompt_version


def build_feedback_prompt(
    template: str,
    processed_input: ProcessedInput,
    pattern_features: PatternFeatures,
    decision: DecisionResult,
    history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Populate template placeholders with structured context."""
    # Format input submission
    input_repr = {
        "text": processed_input.normalized_text,
        "word_count": processed_input.word_count,
        "session_context": processed_input.session_context,
    }

    # Format pattern features
    pattern_repr = {
        "detected_patterns": pattern_features.detected_patterns,
        "repeated_errors": pattern_features.repeated_errors,
        "vocabulary_diversity_ttr": pattern_features.vocabulary_diversity,
        "repeated_phrases": pattern_features.repeated_phrases,
        "sentence_structure_issues": pattern_features.sentence_structure_issues,
        "signals": pattern_features.performance_signals,
    }

    # Format bounded history
    bounded_history = history[-5:] if history else []
    history_repr = {
        "recent_rounds_count": len(bounded_history),
        "score_trend": pattern_features.improvement_trends.get("score_trend", "no_history"),
        "historical_recurring_errors": pattern_features.improvement_trends.get("recurring_weaknesses", []),
    }

    # Replace placeholders
    prompt = template.replace("{{processed_input}}", json.dumps(input_repr, indent=2))
    prompt = prompt.replace("{{pattern_features}}", json.dumps(pattern_repr, indent=2))
    prompt = prompt.replace("{{performance_history}}", json.dumps(history_repr, indent=2))
    prompt = prompt.replace("{{analysis_strategy}}", decision.analysis_strategy)

    return prompt


def clean_json_text(text: str) -> str:
    """Strip markdown code blocks or surrounding text to extract raw JSON."""
    cleaned = text.strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        return match.group(1).strip()
    # If no fences, find outermost { and }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return cleaned[first_brace:last_brace + 1].strip()
    return cleaned


def generate_rule_based_feedback(
    processed_input: ProcessedInput,
    pattern_features: PatternFeatures,
    decision: DecisionResult,
    prompt_version: str = "v1.2.0-rule-engine",
) -> FeedbackResponse:
    """Generate high-quality deterministic debate feedback without calling an LLM.

    Used when:
    - Input is short / one-liner where LLM is unnecessary.
    - Safety guardrails are triggered.
    - System is configured for offline mode.
    - Upstream LLM fails or times out.
    """
    analysis_id = f"an_rule_{uuid.uuid4().hex[:10]}"
    text = processed_input.normalized_text
    words = processed_input.word_count

    # Safety Guardrail trigger handling
    if decision.decision == "SAFETY_FLAG":
        return FeedbackResponse(
            analysis_id=analysis_id,
            overall_feedback=(
                "Your submission was flagged by the system safety guardrails. "
                "AI Penfight focuses strictly on constructive, reasoned debate argumentation."
            ),
            strengths=[],
            weaknesses=["Input triggered security or harassment moderation filters."],
            logical_fallacies=[],
            grammar_and_vocabulary=[],
            suggestions=["Ensure submissions are relevant debate arguments free of adversarial commands or abusive content."],
            actionable_recommendations=["1. Re-frame your argument around the debate topic.", "2. Use objective, persuasive terminology."],
            performance_score=PerformanceScore(
                argument_strength=0.0,
                logic_and_reasoning=0.0,
                evidence_and_support=0.0,
                clarity_and_style=0.0,
                rebuttal_effectiveness=0.0,
                overall_score=0.0,
                breakdown={"safety": decision.reason}
            ),
            prompt_version=prompt_version,
            strategy_applied=decision.analysis_strategy,
        )

    # 1. Strengths
    strengths = []
    if words >= 20:
        strengths.append("Demonstrates willingness to articulate a structured viewpoint.")
    if pattern_features.vocabulary_diversity > 0.6:
        strengths.append("Utilizes varied and expressive vocabulary.")
    if pattern_features.performance_signals.get("evidence_score", 0) > 0.5:
        strengths.append("Incorporates supportive warrants and explanatory linking words.")
    if not strengths:
        strengths.append("States a direct opinion on the topic.")

    # 2. Weaknesses
    weaknesses = []
    if words < 15:
        weaknesses.append(f"Argument is very brief ({words} words); lacks sufficient depth to establish a compelling case.")
    if pattern_features.performance_signals.get("evidence_score", 0) < 0.2:
        weaknesses.append("Lacks concrete empirical evidence, statistics, or real-world examples to substantiate claims.")
    for err in pattern_features.repeated_errors:
        weaknesses.append(f"Contains recurring issue: {err}")
    if not weaknesses:
        weaknesses.append("Counter-arguments could be more thoroughly anticipated and disassembled.")

    # 3. Fallacies
    fallacies: List[FallacyItem] = []
    for pat in pattern_features.detected_patterns:
        if pat.get("category") == "logical_fallacy":
            fallacies.append(FallacyItem(
                fallacy_name=pat.get("name", "Logical Fallacy"),
                quote=pat.get("matched_text", text[:40]),
                explanation=pat.get("detail", "Reasoning flaw undermines argument validity."),
                severity=pat.get("severity", "medium"),
            ))

    # 4. Grammar corrections
    corrections: List[CorrectionItem] = []
    for pat in pattern_features.detected_patterns:
        if pat.get("category") == "grammar_spelling":
            corrections.append(CorrectionItem(
                error_type="grammar",
                original=pat.get("matched_text", ""),
                correction=pat.get("detail", "").replace("Suggested: ", ""),
                explanation=pat.get("name", "Linguistic accuracy improvement"),
            ))

    # 5. Suggestions & Recommendations
    suggestions = [
        "Strengthen your central claim by deploying the Claim-Warrant-Impact structure.",
        "Include verifiable facts or reputable references to corroborate assertions.",
    ]
    if pattern_features.sentence_structure_issues:
        suggestions.append("Vary your sentence cadence to improve persuasive rhythm.")

    recommendations = [
        "1. Define your primary thesis in the opening sentence.",
        "2. Provide at least one concrete piece of evidence for every major assertion.",
        "3. Explicitly state the broader consequence (impact) if your position is accepted.",
    ]

    # 6. Scoring Rubric
    arg_strength = min(90.0, max(25.0, 40.0 + (words * 0.8)))
    logic = 80.0 - (len(fallacies) * 18.0)
    logic = max(20.0, min(95.0, logic))
    evidence = 40.0 + (pattern_features.performance_signals.get("evidence_score", 0.0) * 45.0)
    evidence = max(20.0, min(90.0, evidence))
    clarity = 85.0 - (len(corrections) * 8.0)
    if pattern_features.sentence_structure_issues:
        clarity -= 10.0
    clarity = max(25.0, min(95.0, clarity))
    rebuttal = 60.0  # Baseline for single-turn argument

    overall = round(
        (arg_strength * 0.25) +
        (logic * 0.25) +
        (evidence * 0.20) +
        (clarity * 0.15) +
        (rebuttal * 0.15),
        1
    )

    overall_feedback = (
        f"Your argument articulates an initial position with {words} words. "
        f"{'Addressing the identified logical weaknesses will significantly elevate your case.' if fallacies else 'Focusing on concrete evidentiary support will strengthen your persuasive impact.'}"
    )

    return FeedbackResponse(
        analysis_id=analysis_id,
        overall_feedback=overall_feedback,
        strengths=strengths,
        weaknesses=weaknesses,
        logical_fallacies=fallacies,
        grammar_and_vocabulary=corrections,
        suggestions=suggestions,
        actionable_recommendations=recommendations,
        performance_score=PerformanceScore(
            argument_strength=round(arg_strength, 1),
            logic_and_reasoning=round(logic, 1),
            evidence_and_support=round(evidence, 1),
            clarity_and_style=round(clarity, 1),
            rebuttal_effectiveness=round(rebuttal, 1),
            overall_score=overall,
            breakdown={
                "argument_strength": f"Rated on argument length ({words} words) and claim clarity.",
                "logic_and_reasoning": f"Adjusted based on {len(fallacies)} detected logical flaws.",
                "evidence_and_support": "Calculated from presence of empirical and explanatory indicators.",
                "clarity_and_style": f"Computed from {len(corrections)} grammar items and sentence structure.",
                "rebuttal_effectiveness": "Baseline score for opening constructive speech.",
            }
        ),
        prompt_version=prompt_version,
        strategy_applied=decision.analysis_strategy,
    )


def generate_feedback(
    processed_input: ProcessedInput,
    pattern_features: PatternFeatures,
    decision: DecisionResult,
    history: Optional[List[Dict[str, Any]]] = None,
    llm_client: Optional[BaseLLMClient] = None,
) -> FeedbackResponse:
    """Coordinate the feedback generation pipeline.

    Args:
        processed_input: Validated input object.
        pattern_features: Detected features and trends.
        decision: DecisionEngine output.
        history: Bounded history of prior interactions.
        llm_client: Model-agnostic LLM client (defaults to configured client).

    Returns:
        FeedbackResponse: Validated, structured feedback object ready for API response.
    """
    # 1. Load prompt template and version
    prompt_template, prompt_version = load_feedback_prompt()
    logger.info("Loaded feedback prompt version %s for session %s", prompt_version, processed_input.session_id)

    # 2. Check if decision engine directed rule-based path
    if not decision.use_llm:
        logger.info("Decision engine selected rule-based path: %s", decision.reason)
        return generate_rule_based_feedback(
            processed_input=processed_input,
            pattern_features=pattern_features,
            decision=decision,
            prompt_version=prompt_version,
        )

    # 3. Resolve LLM client
    client = llm_client or get_llm_client()

    # 4. Construct prompt
    prompt = build_feedback_prompt(
        template=prompt_template,
        processed_input=processed_input,
        pattern_features=pattern_features,
        decision=decision,
        history=history,
    )

    # 5. Call LLM with retry for malformed JSON
    for attempt in range(2):
        try:
            current_prompt = prompt if attempt == 0 else (
                prompt + "\n\nCRITICAL: Your previous response was not parseable JSON. "
                "Return ONLY a strictly valid JSON object conforming exactly to the schema."
            )

            response = client.generate(
                prompt=current_prompt,
                system_prompt="You are Antigravity Penfight Arbiter. Output strictly valid JSON conforming to the schema.",
                json_mode=True,
            )

            # Try raw_json first, otherwise parse content string
            data = response.raw_json
            if not data:
                cleaned_str = clean_json_text(response.content)
                data = json.loads(cleaned_str)

            # Validate against schema
            # Ensure analysis_id and version exist
            if not data.get("analysis_id"):
                data["analysis_id"] = f"an_{uuid.uuid4().hex[:10]}"
            data["prompt_version"] = prompt_version
            data["strategy_applied"] = decision.analysis_strategy

            validated = FeedbackResponse.model_validate(data)
            logger.info("Successfully generated and validated feedback (analysis_id=%s)", validated.analysis_id)
            return validated

        except (json.JSONDecodeError, ValueError, Exception) as exc:
            logger.warning(
                "Feedback generation attempt %d failed: %s. %s",
                attempt + 1,
                str(exc),
                "Retrying..." if attempt == 0 else "Falling back to rule-based engine."
            )

    # 6. Fallback if both LLM attempts fail
    logger.error("LLM generation failed after retry; delivering controlled fallback feedback.")
    fallback = generate_rule_based_feedback(
        processed_input=processed_input,
        pattern_features=pattern_features,
        decision=decision,
        prompt_version=f"{prompt_version}-fallback",
    )
    return fallback

"""Decision Engine Module for AI Penfight.

Combines pattern features, input validation, and configurable heuristic rules
to determine:
1. Whether an input is safe and relevant to PENFIGHT debate analysis.
2. Whether to trigger an external LLM or fulfill via lightweight rule-based critique.
3. Which analysis strategy should be pursued (logic focus, grammar focus, comprehensive).
4. Which detected weaknesses receive top priority in feedback generation.

Rules are modular and decoupled from the execution logic for easy extension.
Debate arguments with strong disagreement or controversial positions are respected
and NOT flagged as abusive.
"""

import os
import re
from typing import Any, Dict, List, Optional, Protocol

from ai.schemas.feedback_schema import DecisionResult, PatternFeatures, ProcessedInput

# Configurable thresholds
DEFAULT_MIN_WORDS_FOR_LLM = 8
DEFAULT_MAX_WORDS_FOR_QUICK_CRITIQUE = 7

# Prompt injection and malicious payload patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions",
    r"disregard\s+(?:all\s+)?(?:previous|prior)\s+instructions",
    r"system\s+prompt\s+override",
    r"you\s+are\s+now\s+dan",
    r"jailbreak",
    r"<script[\s>]",
    r"drop\s+table\s+",
    r"exec\s*\(\s*['\"]",
]

# Explicit abusive threats or extreme hate speech (strict, avoiding false positives on debate topics)
SEVERE_ABUSE_PATTERNS = [
    r"\b(?:kill\s+yourself|die\s+in\s+a\s+fire|i\s+will\s+murder\s+you)\b",
    r"\b(?:bomb\s+threat|doxx\s+you)\b",
]


class RuleProtocol(Protocol):
    """Protocol for modular decision rules."""
    def evaluate(
        self,
        processed_input: ProcessedInput,
        pattern_features: PatternFeatures,
        config: Dict[str, Any],
    ) -> Optional[DecisionResult]:
        ...


class SafetyGuardrailRule:
    """Evaluates safety, prompt injection, and severe harassment."""

    def evaluate(
        self,
        processed_input: ProcessedInput,
        pattern_features: PatternFeatures,
        config: Dict[str, Any],
    ) -> Optional[DecisionResult]:
        text = processed_input.normalized_text.lower()

        # Check prompt injection
        for pat in PROMPT_INJECTION_PATTERNS:
            if re.search(pat, text):
                return DecisionResult(
                    decision="SAFETY_FLAG",
                    analysis_strategy="safety_warning",
                    reason="Input contains suspected prompt injection or system override instructions.",
                    priority_patterns=["security_guardrail_triggered"],
                    use_llm=False,
                )

        # Check severe abuse / violent threats
        for pat in SEVERE_ABUSE_PATTERNS:
            if re.search(pat, text):
                return DecisionResult(
                    decision="SAFETY_FLAG",
                    analysis_strategy="safety_warning",
                    reason="Input contains abusive language or direct threats in violation of debate safety policies.",
                    priority_patterns=["harassment_guardrail_triggered"],
                    use_llm=False,
                )

        return None


class ShortInputRule:
    """Directs very short inputs to fast rule-based evaluation instead of costly LLM calls."""

    def evaluate(
        self,
        processed_input: ProcessedInput,
        pattern_features: PatternFeatures,
        config: Dict[str, Any],
    ) -> Optional[DecisionResult]:
        min_words = config.get("min_words_for_llm", DEFAULT_MIN_WORDS_FOR_LLM)

        if processed_input.word_count < min_words:
            # Short assertions, one-liners, or greetings
            priority = []
            if pattern_features.detected_patterns:
                priority = [p["name"] for p in pattern_features.detected_patterns[:2]]
            else:
                priority = ["insufficient_argument_depth"]

            return DecisionResult(
                decision="RULE_BASED_EVALUATION",
                analysis_strategy="quick_rule_critique",
                reason=(
                    f"Input is very brief ({processed_input.word_count} words). "
                    "Rule-based feedback is sufficient to recommend expanding the argument premise."
                ),
                priority_patterns=priority,
                use_llm=False,
            )

        return None


class StrategicFocusRule:
    """Selects specific analysis focus based on detected patterns and user history."""

    def evaluate(
        self,
        processed_input: ProcessedInput,
        pattern_features: PatternFeatures,
        config: Dict[str, Any],
    ) -> Optional[DecisionResult]:
        # 1. Prioritize weaknesses
        priority_patterns: List[str] = []

        # High priority: Recurring mistakes from history
        if pattern_features.repeated_errors:
            priority_patterns.extend(pattern_features.repeated_errors)

        # High priority: Detected logical fallacies
        fallacy_patterns = [
            p["name"] for p in pattern_features.detected_patterns
            if p.get("category") == "logical_fallacy"
        ]
        priority_patterns.extend(fallacy_patterns)

        # Medium priority: Sentence structure issues
        priority_patterns.extend(pattern_features.sentence_structure_issues[:2])

        # Grammar & spelling patterns
        grammar_patterns = [
            p["name"] for p in pattern_features.detected_patterns
            if p.get("category") == "grammar_spelling"
        ]
        priority_patterns.extend(grammar_patterns[:3])

        # Deduplicate while preserving order
        seen = set()
        deduped_priority = []
        for p in priority_patterns:
            if p not in seen:
                seen.add(p)
                deduped_priority.append(p)

        # 2. Determine Strategy
        if fallacy_patterns:
            strategy = "fallacy_and_logic_focus"
            reason = (
                f"Argument contains identifiable rhetorical fallacies ({', '.join(fallacy_patterns)}). "
                "Prioritizing logical rebuttal and reasoning soundness."
            )
        elif len(grammar_patterns) >= 3:
            strategy = "style_and_delivery"
            reason = (
                f"Argument shows multiple linguistic/grammatical errors ({len(grammar_patterns)}). "
                "Focusing on persuasive clarity and mechanics."
            )
        elif pattern_features.repeated_errors:
            strategy = "adaptive_remediation"
            reason = (
                f"Historical patterns show recurring errors ({', '.join(pattern_features.repeated_errors)}). "
                "Tailoring feedback to break repeating habits."
            )
        else:
            strategy = "comprehensive_debate_analysis"
            reason = "Standard debate submission; applying full comprehensive rhetoric and evidence analysis."

        return DecisionResult(
            decision="PROCEED_WITH_LLM",
            analysis_strategy=strategy,
            reason=reason,
            priority_patterns=deduped_priority[:5],
            use_llm=True,
        )


class DecisionEngine:
    """Manages rules and produces decision results."""

    def __init__(self, rules: Optional[List[RuleProtocol]] = None, config: Optional[Dict[str, Any]] = None):
        self.rules: List[RuleProtocol] = rules or [
            SafetyGuardrailRule(),
            ShortInputRule(),
            StrategicFocusRule(),
        ]
        self.config = config or {
            "min_words_for_llm": int(os.getenv("MIN_WORDS_FOR_LLM", str(DEFAULT_MIN_WORDS_FOR_LLM))),
            "force_rule_based": os.getenv("FORCE_RULE_BASED", "false").lower() in ("true", "1", "yes"),
        }

    def decide(
        self,
        processed_input: ProcessedInput,
        pattern_features: PatternFeatures,
    ) -> DecisionResult:
        """Evaluate input and pattern features through registered rules sequentially."""
        # Handle explicit offline / forced rule-based configuration
        if self.config.get("force_rule_based"):
            return DecisionResult(
                decision="RULE_BASED_EVALUATION",
                analysis_strategy="quick_rule_critique",
                reason="System configured for local rule-based evaluation (offline mode).",
                priority_patterns=[p["name"] for p in pattern_features.detected_patterns[:3]],
                use_llm=False,
            )

        for rule in self.rules:
            result = rule.evaluate(processed_input, pattern_features, self.config)
            if result is not None:
                return result

        # Fallback default
        return DecisionResult(
            decision="PROCEED_WITH_LLM",
            analysis_strategy="comprehensive_debate_analysis",
            reason="Default debate analysis pipeline triggered.",
            priority_patterns=[],
            use_llm=True,
        )


def decide_strategy(
    processed_input: ProcessedInput,
    pattern_features: PatternFeatures,
    rules_config: Optional[Dict[str, Any]] = None,
) -> DecisionResult:
    """Convenience helper to invoke the DecisionEngine.

    Args:
        processed_input: Validated input object.
        pattern_features: Extracted pattern features.
        rules_config: Optional configuration overrides.

    Returns:
        DecisionResult: Decision containing pipeline strategy, safety status, and LLM flag.
    """
    engine = DecisionEngine(config=rules_config)
    return engine.decide(processed_input, pattern_features)

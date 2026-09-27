"""Pattern Detection Module for AI Penfight.

Performs rule-based linguistic and rhetorical analysis on debate arguments.
Analyzes current inputs and a bounded historical window to identify:
- Repeated grammar and spelling mistakes
- Repeated arguments, phrases, and debate clichés
- Vocabulary richness and lexical diversity (Type-Token Ratio)
- Sentence structure issues (run-ons, fragments, monotony)
- Repeated argumentative weaknesses and logical fallacy indicators
- Progress trends (improvement, stability, or decline) over time
"""

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from ai.schemas.feedback_schema import PatternFeatures, ProcessedInput

# Maximum number of previous interactions to inspect (strictly bounded)
MAX_HISTORY_WINDOW = 5

# Common grammar/spelling mistake rules: (regex pattern, error_name, suggested_correction)
GRAMMAR_RULES: List[Tuple[str, str, str]] = [
    (r"\btheir\s+(?:is|are|was|were)\b", "their/there confusion", "Use 'there' for existence or location"),
    (r"\bthere\s+(?:argument|point|evidence|thesis|claim)\b", "there/their confusion", "Use 'their' for possessive"),
    (r"\byour\s+(?:right|wrong|mistaken|correct)\b", "your/you're confusion", "Use \"you're\" (you are)"),
    (r"\byou're\s+(?:argument|point|position|claim)\b", "you're/your confusion", "Use 'your' (possessive)"),
    (r"\bits\s+(?:obvious|clear|evident|true|essential)\b", "its/it's confusion", "Use \"it's\" (it is)"),
    (r"\bit's\s+(?:impact|effect|consequence|benefit|cost)\b", "it's/its confusion", "Use 'its' (possessive)"),
    (r"\b(?:could|should|would)\s+of\b", "modal of/have confusion", "Use 'have' instead of 'of' (e.g. 'could have')"),
    (r"\bloose\s+(?:the|this|an?|your|their|our|my|alot\s+of|a\s+lot\s+of)?\s*(?:debate|argument|case|points?|credibility|ground|sight)\b|\bloose\s+(?:alot|a\s+lot)\s+of\b", "loose/lose confusion", "Use 'lose' (verb), not 'loose' (adjective)"),
    (r"\bdefinately\b", "spelling: definitely", "Correct spelling is 'definitely'"),
    (r"\bseperate\b", "spelling: separate", "Correct spelling is 'separate'"),
    (r"\balot\b", "spelling: a lot", "Write as two words: 'a lot'"),
    (r"\b(?:he|she|it)\s+have\b", "subject-verb agreement", "Use 'has' with third-person singular"),
    (r"\b(?:they|we)\s+has\b", "subject-verb agreement", "Use 'have' with plural subjects"),
    (r"\b(?:he|she|it)\s+don't\b", "subject-verb agreement", "Use \"doesn't\" with third-person singular"),
]

# Common debate clichés and filler phrases
DEBATE_CLICHES: List[str] = [
    "at the end of the day",
    "in my opinion",
    "in my humble opinion",
    "it goes without saying",
    "needless to say",
    "as we all know",
    "everyone knows that",
    "first of all second of all",
    "obviously without doubt",
    "the fact of the matter is",
]

# Weak intensifiers and vague terms
WEAK_WORDS: Set[str] = {
    "very", "really", "extremely", "basically", "literally",
    "thing", "things", "stuff", "bad", "good", "huge", "nice"
}

# Fallacy heuristic triggers
FALLACY_HEURISTICS: List[Dict[str, Any]] = [
    {
        "name": "Ad Hominem",
        "pattern": r"\b(?:you\s+are|you're)\s+(?:an?\s+)?(?:idiot|stupid|ignorant|fool|moron|clueless|hypocrite)\b|\bonly\s+a\s+fool\s+would\b",
        "severity": "high",
        "description": "Attacking the opponent's character or intelligence rather than addressing their argument."
    },
    {
        "name": "Slippery Slope",
        "pattern": r"\b(?:will\s+inevitably\s+lead\s+to|slippery\s+slope|will\s+eventually\s+destroy|disaster\s+will\s+follow|end\s+of\s+civilization)\b",
        "severity": "medium",
        "description": "Asserting without evidence that an initial step will unavoidably trigger catastrophic consequences."
    },
    {
        "name": "False Dilemma",
        "pattern": r"\b(?:either\s+you\s+(?:agree|are\s+with\s+us)|only\s+two\s+(?:options|choices|sides)|you're\s+either\s+with\s+us\s+or\s+against\s+us)\b",
        "severity": "medium",
        "description": "Framing a complex issue as a rigid binary choice when nuanced alternatives exist."
    },
    {
        "name": "Circular Reasoning",
        "pattern": r"\b(?:true\s+because\s+it\s+is\s+true|right\s+because\s+it\s+is\s+right|proves\s+itself|by\s+definition\s+it\s+is\s+always)\b",
        "severity": "medium",
        "description": "Using the claim itself as premise or justification."
    },
    {
        "name": "Hasty Generalization",
        "pattern": r"\b(?:everyone\s+always|nobody\s+ever|all\s+people\s+without\s+exception|every\s+single\s+time\s+without\s+fail)\b",
        "severity": "low",
        "description": "Drawing an absolute conclusion from isolated anecdotes or insufficient evidence."
    },
]

# Evidence indicator keywords
EVIDENCE_KEYWORDS: Set[str] = {
    "because", "for example", "for instance", "data", "study", "research",
    "evidence", "demonstrates", "according to", "statistics", "report", "finding",
    "historical", "percent", "specifically", "source"
}


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using punctuation boundaries."""
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in raw_sentences if s.strip()]
    return sentences if sentences else [text]


def _tokenize_words(text: str) -> List[str]:
    """Extract lowercased alphanumeric words."""
    return re.findall(r"\b[a-zA-Z']+\b", text.lower())


def _extract_repeated_ngrams(words: List[str], n: int = 3, min_count: int = 2) -> List[Tuple[str, int]]:
    """Extract recurring n-grams within the given word list."""
    if len(words) < n:
        return []
    ngrams: Dict[str, int] = {}
    for i in range(len(words) - n + 1):
        phrase = " ".join(words[i:i + n])
        ngrams[phrase] = ngrams.get(phrase, 0) + 1
    return [(phrase, count) for phrase, count in ngrams.items() if count >= min_count]


def detect_grammar_errors(text: str) -> List[Dict[str, str]]:
    """Identify common grammar, spelling, and agreement mistakes."""
    errors = []
    for pattern, name, fix in GRAMMAR_RULES:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for match in matches:
            errors.append({
                "type": "grammar_spelling",
                "name": name,
                "matched_text": match.group(0),
                "suggestion": fix,
                "position": match.start(),
            })
    return errors


def analyze_vocabulary(words: List[str]) -> Dict[str, Any]:
    """Calculate lexical diversity (Type-Token Ratio) and detect weak vocabulary."""
    total_words = len(words)
    if total_words == 0:
        return {"ttr": 0.0, "weak_word_ratio": 0.0, "weak_words_used": []}

    unique_words = len(set(words))
    ttr = round(unique_words / total_words, 3)

    weak_words_used = [w for w in words if w in WEAK_WORDS]
    weak_word_ratio = round(len(weak_words_used) / total_words, 3)

    return {
        "ttr": ttr,
        "total_words": total_words,
        "unique_words": unique_words,
        "weak_word_ratio": weak_word_ratio,
        "weak_words_used": list(set(weak_words_used))[:8],
    }


def analyze_sentence_structure(sentences: List[str]) -> Dict[str, Any]:
    """Check for run-on sentences, fragments, and sentence length variance."""
    issues = []
    lengths = []

    for s in sentences:
        s_words = _tokenize_words(s)
        word_count = len(s_words)
        lengths.append(word_count)

        # Run-on heuristic: > 45 words without semicolon or colon
        if word_count > 45 and ";" not in s and ":" not in s:
            issues.append(f"Potential run-on sentence ({word_count} words): \"{s[:60]}...\"")

        # Fragment heuristic: < 3 words
        elif word_count < 3 and not any(mark in s for mark in ["?", "!"]):
            issues.append(f"Short sentence fragment: \"{s}\"")

    avg_length = sum(lengths) / len(lengths) if lengths else 0.0

    # Monotony check: variance in sentence length
    std_dev = 0.0
    if len(lengths) >= 3:
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        if std_dev < 2.0 and avg_length > 5:
            issues.append("Monotonous sentence cadence: sentence lengths show minimal variety.")

    return {
        "avg_sentence_length": round(avg_length, 1),
        "sentence_length_std_dev": round(std_dev, 2),
        "sentence_count": len(sentences),
        "structure_issues": issues,
    }


def detect_argument_patterns(text: str, words: List[str]) -> Dict[str, Any]:
    """Identify rhetorical clichés, evidence indicators, and potential fallacies."""
    lower_text = text.lower()

    # Detect debate clichés
    found_cliches = [c for c in DEBATE_CLICHES if c in lower_text]

    # Detect evidence markers
    found_evidence_markers = [kw for kw in EVIDENCE_KEYWORDS if kw in lower_text]
    evidence_score = round(min(1.0, len(found_evidence_markers) / 4.0), 2)

    # Detect heuristic fallacies
    detected_fallacies = []
    for fallacy in FALLACY_HEURISTICS:
        match = re.search(fallacy["pattern"], text, re.IGNORECASE)
        if match:
            detected_fallacies.append({
                "fallacy_name": fallacy["name"],
                "matched_text": match.group(0),
                "severity": fallacy["severity"],
                "explanation": fallacy["description"],
            })

    return {
        "cliches": found_cliches,
        "evidence_markers": found_evidence_markers,
        "evidence_score": evidence_score,
        "fallacies": detected_fallacies,
    }


def analyze_history_trends(
    current_features: Dict[str, Any],
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Compare current performance features against a bounded historical window.

    Bounded to MAX_HISTORY_WINDOW (default 5 interactions).
    """
    if not history:
        return {
            "history_available": False,
            "interactions_analyzed": 0,
            "score_trend": "no_history",
            "repeated_errors": [],
            "repeated_phrases": [],
            "error_change_rate": 0.0,
            "recurring_weaknesses": [],
        }

    # Bound history strictly to the most recent window
    bounded_history = history[-MAX_HISTORY_WINDOW:]

    repeated_errors: List[str] = []
    historical_error_names: Set[str] = set()
    historical_scores: List[float] = []

    # Gather past errors and scores
    for item in bounded_history:
        # Check stored errors in history
        past_errors = item.get("errors") or item.get("repeated_errors") or []
        for e in past_errors:
            if isinstance(e, str):
                historical_error_names.add(e.lower())
            elif isinstance(e, dict) and "name" in e:
                historical_error_names.add(e["name"].lower())

        # Check stored scores
        score = item.get("overall_score") or item.get("score")
        if score is not None:
            try:
                historical_scores.append(float(score))
            except (ValueError, TypeError):
                pass

    # Check which of current errors also appeared in history
    current_error_names = [e["name"].lower() for e in current_features.get("grammar_errors", [])]
    for name in set(current_error_names):
        if name in historical_error_names:
            repeated_errors.append(f"Recurring mistake: {name}")

    # Check for repeated cliches across rounds
    historical_text = " ".join([
        str(item.get("text", "") or item.get("input", "")).lower()
        for item in bounded_history
    ])
    repeated_phrases = []
    for cliche in current_features.get("argument_patterns", {}).get("cliches", []):
        if cliche in historical_text:
            repeated_phrases.append(f"Repeated cliché from earlier rounds: \"{cliche}\"")

    # Evaluate score/quality trajectory
    score_trend = "stable"
    if historical_scores:
        avg_past_score = sum(historical_scores) / len(historical_scores)
        # Estimate current baseline score signal
        est_current = current_features.get("signals", {}).get("estimated_baseline_score", 70.0)
        delta = est_current - avg_past_score
        if delta >= 5.0:
            score_trend = "improving"
        elif delta <= -5.0:
            score_trend = "declining"
        else:
            score_trend = "stable"

    return {
        "history_available": True,
        "interactions_analyzed": len(bounded_history),
        "score_trend": score_trend,
        "repeated_errors": repeated_errors,
        "repeated_phrases": repeated_phrases,
        "recurring_weaknesses": repeated_errors + repeated_phrases,
    }


def extract_features(
    processed_input: ProcessedInput,
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Extract raw low-level features and signals from the processed input and history.

    Args:
        processed_input: Validated input object.
        history: Bounded list of prior interactions.

    Returns:
        Dictionary of raw features (grammar, vocabulary, syntax, rhetoric, trends).
    """
    text = processed_input.normalized_text
    words = _tokenize_words(text)
    sentences = _split_into_sentences(text)

    # 1. Grammar & Spelling
    grammar_errors = detect_grammar_errors(text)

    # 2. Vocabulary & TTR
    vocab_stats = analyze_vocabulary(words)

    # 3. Sentence Structure
    structure_stats = analyze_sentence_structure(sentences)

    # 4. Argument & Rhetorical Patterns
    arg_patterns = detect_argument_patterns(text, words)

    # 5. Repeated N-grams
    repeated_ngrams = _extract_repeated_ngrams(words, n=3, min_count=2)

    # 6. Baseline Quality Estimation
    baseline_score = 75.0
    baseline_score -= len(grammar_errors) * 3.0
    baseline_score -= len(arg_patterns["fallacies"]) * 8.0
    baseline_score += arg_patterns["evidence_score"] * 10.0
    if vocab_stats["ttr"] < 0.45 and len(words) > 30:
        baseline_score -= 5.0
    baseline_score = max(20.0, min(95.0, round(baseline_score, 1)))

    current_summary = {
        "grammar_errors": grammar_errors,
        "vocab_stats": vocab_stats,
        "structure_stats": structure_stats,
        "argument_patterns": arg_patterns,
        "repeated_ngrams": repeated_ngrams,
        "signals": {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "ttr": vocab_stats["ttr"],
            "evidence_score": arg_patterns["evidence_score"],
            "estimated_baseline_score": baseline_score,
            "has_fallacies": len(arg_patterns["fallacies"]) > 0,
        },
    }

    # 7. Trends against bounded history
    trends = analyze_history_trends(current_summary, history)
    current_summary["trends"] = trends

    return current_summary


def detect_patterns(
    processed_input: ProcessedInput,
    history: Optional[List[Dict[str, Any]]] = None,
) -> PatternFeatures:
    """Analyze the input and bounded history to generate structured pattern features.

    Args:
        processed_input: Validated input object
        history: Optional list of past interaction dictionaries (will be bounded)

    Returns:
        PatternFeatures: Structured features consumable by Decision Engine and Feedback Generator.
    """
    raw_feats = extract_features(processed_input, history)

    detected_patterns: List[Dict[str, Any]] = []

    # Map detected grammar issues
    for err in raw_feats["grammar_errors"]:
        detected_patterns.append({
            "category": "grammar_spelling",
            "name": err["name"],
            "detail": f"Matched '{err['matched_text']}'. Suggested: {err['suggestion']}",
            "severity": "medium",
        })

    # Map vocabulary diversity
    vocab = raw_feats["vocab_stats"]
    if vocab["ttr"] < 0.45 and vocab["total_words"] > 30:
        detected_patterns.append({
            "category": "vocabulary",
            "name": "low_lexical_diversity",
            "detail": f"Low vocabulary variety (TTR: {vocab['ttr']}). Frequent words: {', '.join(vocab['weak_words_used'][:4])}",
            "severity": "low",
        })

    # Map sentence structure issues
    for issue in raw_feats["structure_stats"]["structure_issues"]:
        detected_patterns.append({
            "category": "sentence_structure",
            "name": "structure_anomaly",
            "detail": issue,
            "severity": "medium",
        })

    # Map rhetorical fallacies
    for fallacy in raw_feats["argument_patterns"]["fallacies"]:
        detected_patterns.append({
            "category": "logical_fallacy",
            "name": fallacy["fallacy_name"],
            "detail": fallacy["explanation"],
            "matched_text": fallacy["matched_text"],
            "severity": fallacy["severity"],
        })

    # Map debate clichés
    for cliche in raw_feats["argument_patterns"]["cliches"]:
        detected_patterns.append({
            "category": "rhetorical_cliche",
            "name": "overused_debate_phrase",
            "detail": f"Debate cliché: \"{cliche}\"",
            "severity": "low",
        })

    # Map repeated errors from history
    repeated_errors: List[str] = raw_feats["trends"]["repeated_errors"]
    repeated_phrases: List[str] = raw_feats["trends"]["repeated_phrases"]
    for phrase, count in raw_feats["repeated_ngrams"]:
        repeated_phrases.append(f"Repeated phrase ({count}x): \"{phrase}\"")

    sentence_issues = raw_feats["structure_stats"]["structure_issues"]

    # Calculate overall confidence
    # Longer texts give higher confidence in pattern extraction
    word_count = raw_feats["signals"]["word_count"]
    if word_count < 10:
        confidence = 0.65
    elif word_count < 30:
        confidence = 0.80
    else:
        confidence = 0.92

    return PatternFeatures(
        detected_patterns=detected_patterns,
        repeated_errors=repeated_errors,
        improvement_trends=raw_feats["trends"],
        performance_signals=raw_feats["signals"],
        confidence=confidence,
        vocabulary_diversity=vocab["ttr"],
        repeated_phrases=repeated_phrases[:5],
        sentence_structure_issues=sentence_issues,
    )

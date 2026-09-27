# AI Penfight — AI Engine Module

The `ai/` module is the intelligent core of the **AI Penfight** debate practice platform. It analyzes user debate submissions, detects linguistic and rhetorical patterns, evaluates logical cohesion, determines an optimal feedback strategy, and generates structured, actionable critiques and scores.

---

## Architecture Overview

```text
Raw Backend Input
        │
        ▼
[Input Processing]          ai/input_processing.py
        │
        ▼
[Pattern Detection]         ai/pattern_detection.py
        │
        ▼
[Decision Engine]           ai/decision_engine.py
        │
        ├──────────────────────────┐
        ▼                          ▼
(Rule-Based Path)          (Model-Agnostic LLM Client)
                                   ai/clients/llm_client.py
                                   ai/prompts/feedback_prompt.md
        │                          │
        └──────────────┬───────────┘
                       ▼
             [Feedback Generation]  ai/feedback_generation.py
                       │
                       ▼
             [Schema Validation]    ai/schemas/feedback_schema.py
                       │
                       ▼
             Structured API Response
```

---

## File Structure & Module Responsibilities

| File | Purpose |
|---|---|
| [`ai/__init__.py`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/__init__.py) | Package entry point exposing core pipeline functions and schemas. |
| [`ai/input_processing.py`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/input_processing.py) | Sanitizes, validates, and normalizes input text (Unicode NFC, smart typography, control chars, size limits). Returns `ProcessedInput`. |
| [`ai/pattern_detection.py`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/pattern_detection.py) | Lightweight rule-based NLP engine analyzing current input and bounded history (TTR lexical diversity, grammar/spelling, clichés, run-ons, fallacies, trends). |
| [`ai/decision_engine.py`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/decision_engine.py) | Modular decision logic selecting pipeline strategy (`comprehensive`, `fallacy_focus`, `style_and_delivery`, `quick_rule_critique`), prioritizing weaknesses, enforcing safety without censoring debate opinions. |
| [`ai/feedback_generation.py`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/feedback_generation.py) | Loads prompt template, formats contextual parameters, queries the LLM or rule engine, parses JSON, handles retries, and returns validated `FeedbackResponse`. |
| [`ai/evaluation.py`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/evaluation.py) | Offline evaluation suite with curated debate test cases measuring schema validity, relevance, fallacy detection accuracy, latency, and token cost. |
| [`ai/prompts/feedback_prompt.md`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/prompts/feedback_prompt.md) | Version-controlled prompt template (`v1.2.0`) specifying scoring rubric, guidelines, input variables, and strict JSON output schema. |
| [`ai/schemas/feedback_schema.py`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/schemas/feedback_schema.py) | Pydantic v2 schemas for all inputs, outputs, scores, corrections, and evaluation reports. |
| [`ai/clients/base_client.py`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/clients/base_client.py) | Abstract `BaseLLMClient` and standardized `LLMResponse`. |
| [`ai/clients/llm_client.py`](file:///c:/Users/HP/Documents/GitHub/AI-PENFIGHT/ai/clients/llm_client.py) | Concrete client supporting OpenAI, Anthropic, and a zero-dependency development fallback generator. |

---

## Environment Configuration

Configure your environment by copying `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key environment variables:

```bash
# LLM Provider selection ('fallback', 'openai', 'anthropic')
LLM_PROVIDER=fallback
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your_api_key_here

# Timeouts and token limits
LLM_TIMEOUT=30.0
LLM_MAX_TOKENS=2048
LLM_RETRIES=2

# Input Constraints
MAX_INPUT_LENGTH=5000
MIN_INPUT_LENGTH=2
MIN_WORDS_FOR_LLM=8
```

> **Development Mode:** When `LLM_PROVIDER=fallback` or `LLM_API_KEY` is not provided, the engine automatically uses `DevelopmentFallbackClient`. It produces rich, deterministic, schema-compliant feedback without requiring external API keys or incurring costs.

---

## How the AI Pipeline Works

1. **Input Processing (`process_input`)**:
   - Strips non-printable ASCII control characters.
   - Converts curly typographic quotes and em-dashes into standard equivalents.
   - Enforces configurable boundaries (default 2 to 5000 characters).
   - Generates unique session identifiers and protects user privacy by filtering sensitive context keys.

2. **Pattern Detection (`detect_patterns`)**:
   - Inspects text for common grammatical confusions (`their/there`, `loose/lose`, `your/you're`, `its/it's`, modal verbs).
   - Calculates Type-Token Ratio (TTR) and tracks overused filler clichés (`"at the end of the day"`, `"in my opinion"`).
   - Flags sentence anomalies (run-ons > 45 words, short fragments, monotony).
   - Detects heuristic fallacy triggers (`Ad Hominem`, `Slippery Slope`, `False Dilemma`, `Circular Reasoning`).
   - Compares metrics against a strictly bounded history window (max 5 prior turns) to establish improvement or recurring error trends.

3. **Decision Engine (`decide_strategy`)**:
   - Evaluates modular rules:
     - `SafetyGuardrailRule`: Blocks prompt injection and harassment without penalizing passionate debate argumentation.
     - `ShortInputRule`: Short inputs (< 8 words) use the rule-based path to save latency and cost.
     - `StrategicFocusRule`: Ranks priority patterns (fallacies > recurring flaws > syntax > typos) and selects focus strategy.

4. **Feedback Generation (`generate_feedback`)**:
   - Injects normalized text, patterns, history, and strategy into `ai/prompts/feedback_prompt.md`.
   - Calls the LLM client or executes `generate_rule_based_feedback`.
   - Parses the JSON payload and validates with Pydantic. If malformed, retries once with error feedback.
   - Falls back gracefully to rule-based critique on upstream timeout or failure.

---

## Running Tests

Execute the automated test suite with pytest:

```bash
# Run all tests
python -m pytest -v

# Run only AI module unit tests
python -m pytest tests/test_input_processing.py tests/test_pattern_detection.py tests/test_decision_engine.py tests/test_feedback_generation.py tests/test_evaluation.py -v

# Run API integration tests
python -m pytest tests/test_backend_api.py -v
```

---

## Running Local Offline Evaluation

To benchmark feedback quality against the local ground-truth dataset without sending live API requests:

```bash
python -c "from ai.evaluation import run_local_evaluation; import json; print(json.dumps(run_local_evaluation(), indent=2))"
```

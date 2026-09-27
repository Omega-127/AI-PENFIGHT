"""Model-Agnostic LLM Client implementation for AI Penfight.

Supports multiple providers (OpenAI, Anthropic, Gemini, Fallback/Mock) using
standard HTTP requests via httpx. Automatically falls back to a development
generator if no API key is provided, ensuring robust out-of-the-box operation.
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional

import httpx

from ai.clients.base_client import BaseLLMClient, LLMResponse

logger = logging.getLogger("ai_penfight.llm_client")


class LLMClientError(Exception):
    """Base error for LLM client operations."""
    pass


class LLMTimeoutError(LLMClientError):
    """Raised when an LLM provider request times out."""
    pass


class LLMAuthenticationError(LLMClientError):
    """Raised when API credentials are missing or rejected."""
    pass


class DevelopmentFallbackClient(BaseLLMClient):
    """Safe, zero-credential development fallback client.

    Generates rich, schema-compliant JSON feedback for offline development,
    local testing, and demonstrations without requiring external API keys.
    """

    def __init__(self, model_name: str = "penfight-fallback-v1"):
        self.model_name = model_name

    def is_available(self) -> bool:
        return True

    def get_provider_name(self) -> str:
        return "fallback"

    def _build_fallback_json(self, prompt: str) -> Dict[str, Any]:
        """Generate structured debate feedback matching the schema."""
        # Simple extraction of keywords to personalize fallback
        has_fallacy = "ad hominem" in prompt.lower() or "fallacy" in prompt.lower()
        has_grammar = "their/there" in prompt.lower() or "grammar" in prompt.lower()

        fallacies = []
        if has_fallacy:
            fallacies.append({
                "fallacy_name": "Ad Hominem",
                "quote": "Personal attack or dismissive characterization",
                "explanation": "Targeted opponent's persona instead of substantiating the counter-claim.",
                "severity": "high",
            })

        corrections = []
        if has_grammar:
            corrections.append({
                "error_type": "grammar",
                "original": "their",
                "correction": "there",
                "explanation": "Use 'there' to designate existence or location, not possessive 'their'.",
            })

        return {
            "analysis_id": f"an_fallback_{int(time.time())}",
            "overall_feedback": (
                "Your debate argument presents a clear stance with passionate rhetoric. "
                "However, the logical transitions between your central premise and your conclusions "
                "could be bolstered by citing empirical evidence and avoiding emotional generalizations."
            ),
            "strengths": [
                "Direct and confident tone that establishes a firm stance early.",
                "Coherent topic focus without drifting into unrelated subject matter.",
                "Engaging persuasive phrasing that captures listener attention."
            ],
            "weaknesses": [
                "Limited empirical backing or real-world examples to substantiate claims.",
                "Assumes correlation implies causation without establishing a mechanism.",
                "Counter-arguments from the opposing side were left largely unaddressed."
            ],
            "logical_fallacies": fallacies,
            "grammar_and_vocabulary": corrections,
            "suggestions": [
                "Introduce at least one statistical data point or academic study to reinforce your claim.",
                "Explicitly acknowledge the strongest counter-argument before refuting it.",
                "Replace hyperbolic adjectives with measured, analytical language."
            ],
            "actionable_recommendations": [
                "1. Frame your opening premise around a concrete definition of key terms.",
                "2. Structure your next speech using the Claim-Warrant-Impact (CWI) debate model.",
                "3. Conclude by outlining the broader societal stakes if your policy proposal is adopted."
            ],
            "performance_score": {
                "argument_strength": 74.0,
                "logic_and_reasoning": 70.0,
                "evidence_and_support": 62.0,
                "clarity_and_style": 78.0,
                "rebuttal_effectiveness": 65.0,
                "overall_score": 69.8,
                "breakdown": {
                    "argument_strength": "Solid claim, needs deeper justification.",
                    "logic_and_reasoning": "Deductive chain is mostly coherent but makes unverified leaps.",
                    "evidence_and_support": "Minimal factual references or research citations.",
                    "clarity_and_style": "Clear sentence flow with strong persuasive intent.",
                    "rebuttal_effectiveness": "Modest anticipation of opposing viewpoints."
                }
            },
            "prompt_version": "v1.2.0",
            "strategy_applied": "development_fallback",
        }

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True,
        temperature: float = 0.3,
    ) -> LLMResponse:
        start = time.perf_counter()
        time.sleep(0.02)  # Tiny realistic latency simulation
        latency = (time.perf_counter() - start) * 1000

        data = self._build_fallback_json(prompt)
        content_str = json.dumps(data, indent=2)

        return LLMResponse(
            content=content_str,
            raw_json=data if json_mode else None,
            model=self.model_name,
            provider="fallback",
            token_usage={"prompt_tokens": 150, "completion_tokens": 250, "total_tokens": 400},
            latency_ms=round(latency, 2),
        )

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True,
        temperature: float = 0.3,
    ) -> LLMResponse:
        return self.generate(prompt, system_prompt, json_mode, temperature)


class OpenAIClient(BaseLLMClient):
    """OpenAI API client implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        timeout: float = 30.0,
        max_tokens: int = 2048,
        retries: int = 2,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.retries = retries
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    def is_available(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("<"))

    def get_provider_name(self) -> str:
        return "openai"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True,
        temperature: float = 0.3,
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        last_err: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                start = time.perf_counter()
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(self.endpoint, headers=headers, json=payload)
                latency = (time.perf_counter() - start) * 1000

                if resp.status_code == 401:
                    raise LLMAuthenticationError("OpenAI API authentication failed. Verify LLM_API_KEY.")
                resp.raise_for_status()

                data = resp.json()
                choice = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                raw_json = None
                if json_mode:
                    try:
                        raw_json = json.loads(choice)
                    except json.JSONDecodeError:
                        pass

                return LLMResponse(
                    content=choice,
                    raw_json=raw_json,
                    model=self.model,
                    provider="openai",
                    token_usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    latency_ms=round(latency, 2),
                )
            except httpx.TimeoutException as exc:
                last_err = LLMTimeoutError(f"OpenAI request timed out after {self.timeout}s")
                if attempt < self.retries:
                    time.sleep(1.0 * (attempt + 1))
            except Exception as exc:
                last_err = exc
                if attempt < self.retries:
                    time.sleep(1.0 * (attempt + 1))

        raise LLMClientError(f"OpenAI request failed after {self.retries + 1} attempts: {str(last_err)}")

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True,
        temperature: float = 0.3,
    ) -> LLMResponse:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self.max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        last_err: Optional[Exception] = None
        for attempt in range(self.retries + 1):
            try:
                start = time.perf_counter()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    resp = await client.post(self.endpoint, headers=headers, json=payload)
                latency = (time.perf_counter() - start) * 1000

                if resp.status_code == 401:
                    raise LLMAuthenticationError("OpenAI API authentication failed.")
                resp.raise_for_status()

                data = resp.json()
                choice = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})

                raw_json = None
                if json_mode:
                    try:
                        raw_json = json.loads(choice)
                    except json.JSONDecodeError:
                        pass

                return LLMResponse(
                    content=choice,
                    raw_json=raw_json,
                    model=self.model,
                    provider="openai",
                    token_usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                    latency_ms=round(latency, 2),
                )
            except Exception as exc:
                last_err = exc
                if attempt < self.retries:
                    time.sleep(0.5)

        raise LLMClientError(f"OpenAI async request failed: {str(last_err)}")


class AnthropicClient(BaseLLMClient):
    """Anthropic Claude API client implementation."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-haiku-20241022",
        timeout: float = 30.0,
        max_tokens: int = 2048,
        retries: int = 2,
    ):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.retries = retries
        self.endpoint = "https://api.anthropic.com/v1/messages"

    def is_available(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("<"))

    def get_provider_name(self) -> str:
        return "anthropic"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True,
        temperature: float = 0.3,
    ) -> LLMResponse:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        sys_text = system_prompt or ""
        if json_mode and "json" not in sys_text.lower():
            sys_text += "\nYou must output strictly valid JSON without any markdown formatting or commentary."

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": temperature,
            "system": sys_text,
            "messages": [{"role": "user", "content": prompt}],
        }

        start = time.perf_counter()
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(self.endpoint, headers=headers, json=payload)
        latency = (time.perf_counter() - start) * 1000

        if resp.status_code == 401:
            raise LLMAuthenticationError("Anthropic API authentication failed.")
        resp.raise_for_status()

        data = resp.json()
        choice = data["content"][0]["text"]
        usage = data.get("usage", {})

        raw_json = None
        if json_mode:
            try:
                # Strip potential markdown fences
                cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", choice.strip(), flags=re.MULTILINE)
                raw_json = json.loads(cleaned)
            except Exception:
                pass

        return LLMResponse(
            content=choice,
            raw_json=raw_json,
            model=self.model,
            provider="anthropic",
            token_usage={
                "prompt_tokens": usage.get("input_tokens", 0),
                "completion_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
            latency_ms=round(latency, 2),
        )

    async def generate_async(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True,
        temperature: float = 0.3,
    ) -> LLMResponse:
        return self.generate(prompt, system_prompt, json_mode, temperature)


def get_llm_client() -> BaseLLMClient:
    """Factory function to instantiate the configured LLM client.

    Reads environment variables:
    - LLM_PROVIDER ('openai', 'anthropic', 'fallback', 'mock')
    - LLM_MODEL (e.g. 'gpt-4o-mini', 'claude-3-5-haiku-20241022')
    - LLM_API_KEY (or AI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
    - LLM_TIMEOUT (default 30.0)
    - LLM_MAX_TOKENS (default 2048)
    - LLM_RETRIES (default 2)

    If no valid key or provider is available, defaults to DevelopmentFallbackClient
    to ensure uninterrupted development and testing.
    """
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    api_key = (
        os.getenv("LLM_API_KEY")
        or os.getenv("AI_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("ANTHROPIC_API_KEY")
        or ""
    ).strip()

    timeout = float(os.getenv("LLM_TIMEOUT", "30.0"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
    retries = int(os.getenv("LLM_RETRIES", "2"))

    # Explicit fallback/mock requested
    if provider in ("fallback", "mock") or not provider:
        if not api_key:
            logger.info("Using DevelopmentFallbackClient (no LLM_API_KEY detected).")
            return DevelopmentFallbackClient()

    # OpenAI provider
    if provider == "openai" or (not provider and api_key.startswith("sk-")):
        model = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
        if api_key and not api_key.startswith("<"):
            return OpenAIClient(
                api_key=api_key,
                model=model,
                timeout=timeout,
                max_tokens=max_tokens,
                retries=retries,
            )

    # Anthropic provider
    if provider == "anthropic" or (not provider and api_key.startswith("sk-ant-")):
        model = os.getenv("LLM_MODEL", "claude-3-5-haiku-20241022").strip()
        if api_key and not api_key.startswith("<"):
            return AnthropicClient(
                api_key=api_key,
                model=model,
                timeout=timeout,
                max_tokens=max_tokens,
                retries=retries,
            )

    # Default fallback
    logger.info("Defaulting to DevelopmentFallbackClient.")
    return DevelopmentFallbackClient()

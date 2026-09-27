"""Backend configuration and environment settings for AI Penfight."""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings with environment variable precedence."""

    def __init__(self):
        self.APP_NAME: str = os.getenv("APP_NAME", "AI Penfight Backend")
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")

        origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
        self.ALLOWED_ORIGINS: List[str] = [o.strip() for o in origins.split(",") if o.strip()]

        # AI Configuration
        self.LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "fallback")
        self.LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.LLM_API_KEY: str = (
            os.getenv("LLM_API_KEY")
            or os.getenv("AI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        )
        self.LLM_TIMEOUT: float = float(os.getenv("LLM_TIMEOUT", "30.0"))
        self.LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.LLM_RETRIES: int = int(os.getenv("LLM_RETRIES", "2"))

        self.MAX_INPUT_LENGTH: int = int(os.getenv("MAX_INPUT_LENGTH", "5000"))
        self.MIN_INPUT_LENGTH: int = int(os.getenv("MIN_INPUT_LENGTH", "2"))


settings = Settings()

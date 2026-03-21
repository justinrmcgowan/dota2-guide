"""LLM engine for Claude API integration.

Calls Claude Sonnet with structured JSON output, prompt caching,
and a 10-second hard timeout. Returns validated LLMRecommendation
on success, None on any failure (triggers fallback to rules-only).
"""

import json
import logging

from anthropic import (
    AsyncAnthropic,
    APITimeoutError,
    APIConnectionError,
    APIStatusError,
)

from engine.schemas import LLMRecommendation, LLM_OUTPUT_SCHEMA
from engine.prompts.system_prompt import SYSTEM_PROMPT
from config import settings

logger = logging.getLogger(__name__)


class LLMEngine:
    """Claude API wrapper with structured output, timeout, and prompt caching."""

    MODEL = "claude-sonnet-4-6-20250514"
    MAX_TOKENS = 2000
    TEMPERATURE = 0.3
    TIMEOUT_SECONDS = 10.0

    def __init__(self) -> None:
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, user_message: str) -> LLMRecommendation | None:
        """Call Claude API with structured output and return validated recommendation.

        Uses:
        - output_config.format with JSON schema (GA, not beta)
        - Prompt caching on system prompt (cache_control ephemeral)
        - 10-second hard timeout via client.with_options()
        - max_retries=0 (no retries within timeout budget)

        Returns LLMRecommendation on success, None on any failure (triggers fallback).
        """
        try:
            response = await self.client.with_options(
                timeout=self.TIMEOUT_SECONDS,
                max_retries=0,
            ).messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                temperature=self.TEMPERATURE,
                system=[
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_message}],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": LLM_OUTPUT_SCHEMA,
                    }
                },
            )

            data = json.loads(response.content[0].text)
            return LLMRecommendation.model_validate(data)

        except APITimeoutError:
            logger.warning(
                "Claude API timeout after %.1fs", self.TIMEOUT_SECONDS
            )
            return None
        except APIConnectionError:
            logger.warning("Claude API connection error")
            return None
        except APIStatusError as e:
            logger.error(
                "Claude API error: %s %s", e.status_code, e.message
            )
            return None
        except Exception as e:
            logger.exception("Unexpected error calling Claude API: %s", e)
            return None

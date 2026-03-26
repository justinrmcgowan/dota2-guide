"""LLM engine for Claude API integration.

Calls Claude Haiku with prompt-instructed JSON output and a 45-second
hard timeout. Returns validated LLMRecommendation on success, None on
any failure (triggers fallback to rules-only).
"""

import json
import logging
import re

from anthropic import (
    AsyncAnthropic,
    APITimeoutError,
    APIConnectionError,
    APIStatusError,
)

from engine.schemas import LLMRecommendation, VisionResponse
from engine.prompts.system_prompt import SYSTEM_PROMPT
from engine.prompts.vision_prompt import VISION_SYSTEM_PROMPT, build_vision_user_prompt
from config import settings

logger = logging.getLogger(__name__)


class LLMEngine:
    """Claude API wrapper with JSON output, timeout, and prompt caching."""

    MODEL = "claude-haiku-4-5-20251001"
    MAX_TOKENS = 4096
    TEMPERATURE = 0.3
    TIMEOUT_SECONDS = 45.0

    def __init__(self) -> None:
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, user_message: str) -> LLMRecommendation | None:
        """Call Claude API and return validated recommendation.

        Uses prompt-instructed JSON (no output_config schema enforcement)
        for faster response times. Pydantic validates the parsed output.

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
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_message}],
            )

            text = response.content[0].text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*\n?", "", text)
                text = re.sub(r"\n?```\s*$", "", text)

            data = json.loads(text)
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
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Claude API returned invalid JSON: %s", e)
            return None
        except Exception as e:
            logger.exception("Unexpected error calling Claude API: %s", e)
            return None

    async def parse_screenshot(
        self,
        image_base64: str,
        media_type: str,
        hero_names: list[str],
        item_names: list[str],
    ) -> VisionResponse | None:
        """Send a scoreboard screenshot to Claude Vision for structured extraction.

        Uses the same client and model as generate() but with lower temperature
        for deterministic structured extraction. Returns VisionResponse on success,
        None on any failure.
        """
        user_prompt = build_vision_user_prompt(hero_names, item_names)

        try:
            response = await self.client.with_options(
                timeout=30.0,
                max_retries=0,
            ).messages.create(
                model=self.MODEL,
                max_tokens=self.MAX_TOKENS,
                temperature=0.1,
                system=VISION_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {"type": "text", "text": user_prompt},
                        ],
                    }
                ],
            )

            text = response.content[0].text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*\n?", "", text)
                text = re.sub(r"\n?```\s*$", "", text)

            data = json.loads(text)
            return VisionResponse.model_validate(data)

        except APITimeoutError:
            logger.warning("Vision API timeout after 30s")
            return None
        except APIConnectionError:
            logger.warning("Vision API connection error")
            return None
        except APIStatusError as e:
            logger.error("Vision API error: %s %s", e.status_code, e.message)
            return None
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("Vision API returned invalid JSON: %s", e)
            return None
        except Exception as e:
            logger.exception("Unexpected error calling Vision API: %s", e)
            return None

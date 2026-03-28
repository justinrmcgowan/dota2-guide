"""Ollama API wrapper matching LLMEngine.generate() interface.

Uses the official ollama Python library's AsyncClient for async HTTP
communication with a local or remote Ollama instance. Produces
structured JSON output using Pydantic schema passed via the format
parameter.

Targets: Qwen 2.5 7B Instruct (Q4_K_M) on Unraid Ollama, ~30-40 tok/s.
"""

import json
import logging
import re

from ollama import AsyncClient

from engine.schemas import LLMRecommendation
from engine.llm import FallbackReason
from engine.prompts.system_prompt import SYSTEM_PROMPT
from config import settings

logger = logging.getLogger(__name__)


class OllamaEngine:
    """Ollama API wrapper with generate() matching LLMEngine signature."""

    def __init__(
        self,
        model: str | None = None,
        host: str | None = None,
    ) -> None:
        self.model = model or settings.ollama_model
        self.host = host or settings.ollama_url
        self.client = AsyncClient(host=self.host)

    async def generate(
        self, user_message: str
    ) -> tuple[LLMRecommendation | None, FallbackReason | None]:
        """Call Ollama chat API and return validated recommendation.

        Uses structured output via format parameter with Pydantic JSON schema.
        Returns (LLMRecommendation, None) on success,
        (None, FallbackReason.ollama_error) on any failure.
        """
        try:
            response = await self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                format=LLMRecommendation.model_json_schema(),
                options={
                    "temperature": 0.3,
                    "num_predict": 5120,
                    "num_ctx": 8192,
                },
                stream=False,
                keep_alive="30m",
            )

            text = response["message"]["content"].strip()
            # Strip markdown code fences if present (some models wrap JSON)
            if text.startswith("```"):
                text = re.sub(r"^```(?:json)?\s*\n?", "", text)
                text = re.sub(r"\n?```\s*$", "", text)

            data = json.loads(text)
            result = LLMRecommendation.model_validate(data)
            return (result, None)

        except Exception as e:
            logger.warning("Ollama generate failed: %s: %s", type(e).__name__, e)
            return (None, FallbackReason.ollama_error)

    async def health_check(self) -> bool:
        """Check if Ollama instance is reachable and has models loaded."""
        try:
            await self.client.list()
            return True
        except Exception as e:
            logger.warning("Ollama health check failed: %s", e)
            return False

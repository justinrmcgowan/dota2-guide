"""Unit tests for LLM engine with mocked Claude API.

Tests structured output parsing, error handling, prompt caching config,
and output_config format.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from engine.schemas import (
    LLMRecommendation,
    LLM_OUTPUT_SCHEMA,
    RecommendResponse,
    NeutralItemPick,
    NeutralTierRecommendation,
)


# Valid response data matching LLMRecommendation schema
VALID_RESPONSE_DATA = {
    "phases": [
        {
            "phase": "laning",
            "items": [
                {
                    "item_id": 36,
                    "item_name": "Magic Stick",
                    "reasoning": "Against Bristleback's Quill Spray, expect 10+ charges.",
                    "priority": "core",
                    "conditions": None,
                }
            ],
            "timing": "0-10 min",
            "gold_budget": 2000,
        }
    ],
    "overall_strategy": "Focus on lane sustain against spell-heavy opponents.",
}


def _make_mock_response(data: dict) -> MagicMock:
    """Create a mock API response with content[0].text as JSON string."""
    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.text = json.dumps(data)
    mock_response.content = [mock_content_block]
    return mock_response


@pytest.mark.asyncio
async def test_structured_output_mock():
    """Mock Claude API returns valid JSON, LLMEngine parses to LLMRecommendation."""
    mock_response = _make_mock_response(VALID_RESPONSE_DATA)

    with patch("engine.llm.AsyncAnthropic") as MockClient:
        mock_instance = MockClient.return_value
        mock_with_options = MagicMock()
        mock_with_options.messages.create = AsyncMock(return_value=mock_response)
        mock_instance.with_options.return_value = mock_with_options

        from engine.llm import LLMEngine

        engine = LLMEngine()
        engine.client = mock_instance

        result = await engine.generate("test message")

        assert result is not None
        assert isinstance(result, LLMRecommendation)
        assert len(result.phases) == 1
        assert result.phases[0].phase == "laning"
        assert result.phases[0].items[0].item_id == 36
        assert result.overall_strategy == "Focus on lane sustain against spell-heavy opponents."


@pytest.mark.asyncio
async def test_response_validation():
    """LLMRecommendation.model_validate works with valid data, fails with invalid."""
    # Valid data
    rec = LLMRecommendation.model_validate(VALID_RESPONSE_DATA)
    assert rec.overall_strategy == VALID_RESPONSE_DATA["overall_strategy"]
    assert len(rec.phases) == 1

    # Invalid data: missing required field "overall_strategy"
    invalid_data = {"phases": []}
    with pytest.raises(ValidationError):
        LLMRecommendation.model_validate(invalid_data)


@pytest.mark.asyncio
async def test_timeout_returns_none():
    """APITimeoutError results in None return (triggers fallback)."""
    from anthropic import APITimeoutError

    with patch("engine.llm.AsyncAnthropic") as MockClient:
        mock_instance = MockClient.return_value
        mock_with_options = MagicMock()
        mock_with_options.messages.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )
        mock_instance.with_options.return_value = mock_with_options

        from engine.llm import LLMEngine

        engine = LLMEngine()
        engine.client = mock_instance

        result = await engine.generate("test message")
        assert result is None


@pytest.mark.asyncio
async def test_connection_error_returns_none():
    """APIConnectionError results in None return (triggers fallback)."""
    from anthropic import APIConnectionError

    with patch("engine.llm.AsyncAnthropic") as MockClient:
        mock_instance = MockClient.return_value
        mock_with_options = MagicMock()
        mock_with_options.messages.create = AsyncMock(
            side_effect=APIConnectionError(request=MagicMock())
        )
        mock_instance.with_options.return_value = mock_with_options

        from engine.llm import LLMEngine

        engine = LLMEngine()
        engine.client = mock_instance

        result = await engine.generate("test message")
        assert result is None


@pytest.mark.asyncio
async def test_api_status_error_returns_none():
    """APIStatusError (e.g., 429 rate limited) results in None return."""
    from anthropic import APIStatusError

    mock_resp = MagicMock()
    mock_resp.status_code = 429
    mock_resp.headers = {}

    with patch("engine.llm.AsyncAnthropic") as MockClient:
        mock_instance = MockClient.return_value
        mock_with_options = MagicMock()
        mock_with_options.messages.create = AsyncMock(
            side_effect=APIStatusError(
                message="rate limited",
                response=mock_resp,
                body=None,
            )
        )
        mock_instance.with_options.return_value = mock_with_options

        from engine.llm import LLMEngine

        engine = LLMEngine()
        engine.client = mock_instance

        result = await engine.generate("test message")
        assert result is None


@pytest.mark.asyncio
async def test_prompt_caching_config():
    """System prompt is passed as a list with cache_control for prompt caching."""
    mock_response = _make_mock_response(VALID_RESPONSE_DATA)

    with patch("engine.llm.AsyncAnthropic") as MockClient:
        mock_instance = MockClient.return_value
        mock_with_options = MagicMock()
        mock_create = AsyncMock(return_value=mock_response)
        mock_with_options.messages.create = mock_create
        mock_instance.with_options.return_value = mock_with_options

        from engine.llm import LLMEngine

        engine = LLMEngine()
        engine.client = mock_instance

        await engine.generate("test message")

        # Verify system prompt was passed as list with cache_control
        call_kwargs = mock_create.call_args[1]
        system_arg = call_kwargs["system"]

        assert isinstance(system_arg, list), "system must be a list of content blocks"
        assert len(system_arg) == 1
        assert system_arg[0]["type"] == "text"
        assert "cache_control" in system_arg[0]
        assert system_arg[0]["cache_control"] == {"type": "ephemeral"}
        assert len(system_arg[0]["text"]) > 5000  # System prompt is substantial


@pytest.mark.asyncio
async def test_output_config_format():
    """output_config contains json_schema format with LLM_OUTPUT_SCHEMA."""
    mock_response = _make_mock_response(VALID_RESPONSE_DATA)

    with patch("engine.llm.AsyncAnthropic") as MockClient:
        mock_instance = MockClient.return_value
        mock_with_options = MagicMock()
        mock_create = AsyncMock(return_value=mock_response)
        mock_with_options.messages.create = mock_create
        mock_instance.with_options.return_value = mock_with_options

        from engine.llm import LLMEngine

        engine = LLMEngine()
        engine.client = mock_instance

        await engine.generate("test message")

        # Verify output_config
        call_kwargs = mock_create.call_args[1]
        output_config = call_kwargs["output_config"]

        assert output_config == {
            "format": {
                "type": "json_schema",
                "schema": LLM_OUTPUT_SCHEMA,
            }
        }


# --- Neutral Items Schema Tests ---


def test_neutral_items_schema_backward_compat():
    """LLMRecommendation with no neutral_items defaults to empty list."""
    rec = LLMRecommendation.model_validate(VALID_RESPONSE_DATA)
    assert rec.neutral_items == []


def test_neutral_items_schema_with_data():
    """LLMRecommendation with populated neutral_items validates correctly."""
    data_with_neutrals = {
        **VALID_RESPONSE_DATA,
        "neutral_items": [
            {
                "tier": 1,
                "items": [
                    {
                        "item_name": "Mysterious Hat",
                        "reasoning": "Mana regen helps sustain spell usage in lane.",
                        "rank": 1,
                    },
                    {
                        "item_name": "Chipped Vest",
                        "reasoning": "Damage return punishes right-click harass.",
                        "rank": 2,
                    },
                ],
            }
        ],
    }
    rec = LLMRecommendation.model_validate(data_with_neutrals)
    assert len(rec.neutral_items) == 1
    assert rec.neutral_items[0].tier == 1
    assert len(rec.neutral_items[0].items) == 2
    assert rec.neutral_items[0].items[0].item_name == "Mysterious Hat"
    assert rec.neutral_items[0].items[0].rank == 1


def test_recommend_response_neutral_items_default():
    """RecommendResponse with no neutral_items defaults to empty list."""
    resp = RecommendResponse(
        phases=VALID_RESPONSE_DATA["phases"],
        overall_strategy=VALID_RESPONSE_DATA["overall_strategy"],
    )
    assert resp.neutral_items == []

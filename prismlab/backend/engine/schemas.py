"""Pydantic models for recommendation engine request/response contracts.

Consumed by: rules engine, Claude API layer, hybrid orchestrator, API routes.
"""

from pydantic import BaseModel, Field


class RecommendRequest(BaseModel):
    """POST /api/recommend request body."""

    hero_id: int
    role: int = Field(ge=1, le=5)  # Pos 1-5
    playstyle: str
    side: str  # "radiant" | "dire"
    lane: str  # "safe" | "off" | "mid"
    lane_opponents: list[int] = Field(default_factory=list, max_length=2)
    allies: list[int] = Field(default_factory=list, max_length=4)


class RuleResult(BaseModel):
    """Output of a single deterministic rule evaluation."""

    item_id: int
    item_name: str
    reasoning: str
    phase: str  # "starting" | "laning" | "core" | "late_game"
    priority: str  # "core" | "situational" | "luxury"


class ItemRecommendation(BaseModel):
    """Single item recommendation with reasoning."""

    item_id: int
    item_name: str
    reasoning: str
    priority: str  # "core" | "situational" | "luxury"
    conditions: str | None = None  # For situational decision tree cards
    gold_cost: int | None = None  # Populated from Item.cost during validation


class RecommendPhase(BaseModel):
    """A game phase with its recommended items."""

    phase: str  # "starting" | "laning" | "core" | "late_game" | "situational"
    items: list[ItemRecommendation]
    timing: str | None = None
    gold_budget: int | None = None


class LLMRecommendation(BaseModel):
    """Schema for Claude structured output. Used to generate JSON schema for output_config."""

    phases: list[RecommendPhase]
    overall_strategy: str


class RecommendResponse(BaseModel):
    """POST /api/recommend response body."""

    phases: list[RecommendPhase]
    overall_strategy: str | None = None
    fallback: bool = False
    model: str | None = None
    latency_ms: int | None = None


# JSON schema dict generated from LLMRecommendation for Anthropic output_config
LLM_OUTPUT_SCHEMA = LLMRecommendation.model_json_schema()

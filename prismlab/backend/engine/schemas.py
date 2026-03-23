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

    # Mid-game adaptation fields (all optional for backward compatibility)
    lane_result: str | None = None  # "won" | "even" | "lost"
    damage_profile: dict[str, int] | None = None  # e.g. {"physical": 60, "magical": 30, "pure": 10}
    enemy_items_spotted: list[str] = Field(default_factory=list)  # e.g. ["bkb", "blink"]
    purchased_items: list[int] = Field(default_factory=list)  # item_ids already purchased


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


class NeutralItemPick(BaseModel):
    """Single neutral item recommendation with reasoning."""

    item_name: str
    reasoning: str
    rank: int


class NeutralTierRecommendation(BaseModel):
    """Neutral item recommendations for a single tier."""

    tier: int
    items: list[NeutralItemPick]


class LLMRecommendation(BaseModel):
    """Schema for Claude structured output. Used to generate JSON schema for output_config."""

    phases: list[RecommendPhase]
    overall_strategy: str
    neutral_items: list[NeutralTierRecommendation] = Field(default_factory=list)


class RecommendResponse(BaseModel):
    """POST /api/recommend response body."""

    phases: list[RecommendPhase]
    overall_strategy: str | None = None
    neutral_items: list[NeutralTierRecommendation] = Field(default_factory=list)
    fallback: bool = False
    model: str | None = None
    latency_ms: int | None = None


# JSON schema dict generated from LLMRecommendation for Anthropic output_config
LLM_OUTPUT_SCHEMA = LLMRecommendation.model_json_schema()

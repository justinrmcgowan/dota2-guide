"""Pydantic models for recommendation engine request/response contracts.

Consumed by: rules engine, Claude API layer, hybrid orchestrator, API routes.
"""

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("tier", mode="before")
    @classmethod
    def parse_tier(cls, v: int | str) -> int:
        """Accept 'T1', 'T2', etc. and convert to integer."""
        if isinstance(v, str):
            return int(v.replace("T", "").replace("t", "").strip())
        return v


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


# Hand-crafted inline JSON schema for Anthropic structured output.
# No $ref, no anyOf, no $defs — fully inlined for maximum API compatibility and speed.
LLM_OUTPUT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["phases", "overall_strategy"],
    "properties": {
        "phases": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["phase", "items"],
                "properties": {
                    "phase": {"type": "string"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["item_id", "item_name", "reasoning", "priority"],
                            "properties": {
                                "item_id": {"type": "integer"},
                                "item_name": {"type": "string"},
                                "reasoning": {"type": "string"},
                                "priority": {"type": "string"},
                                "conditions": {"type": "string", "nullable": True},
                                "gold_cost": {"type": "integer", "nullable": True},
                            },
                        },
                    },
                    "timing": {"type": "string", "nullable": True},
                    "gold_budget": {"type": "integer", "nullable": True},
                },
            },
        },
        "overall_strategy": {"type": "string"},
        "neutral_items": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["tier", "items"],
                "properties": {
                    "tier": {"type": "integer"},
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["item_name", "reasoning", "rank"],
                            "properties": {
                                "item_name": {"type": "string"},
                                "reasoning": {"type": "string"},
                                "rank": {"type": "integer"},
                            },
                        },
                    },
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Screenshot parsing schemas (Phase 13)
# ---------------------------------------------------------------------------


class VisionItem(BaseModel):
    """Raw item from Vision output before DB matching."""

    name: str
    confidence: str  # "certain" | "likely" | "uncertain"


class VisionHero(BaseModel):
    """Raw hero from Vision output before DB matching."""

    hero_name: str
    items: list[VisionItem] = Field(default_factory=list)
    kills: int | None = None
    deaths: int | None = None
    assists: int | None = None
    level: int | None = None


class VisionResponse(BaseModel):
    """Raw Vision output schema."""

    heroes: list[VisionHero] = Field(default_factory=list)
    error: str | None = None
    message: str | None = None


class ParsedItem(BaseModel):
    """Single item after DB matching."""

    display_name: str
    internal_name: str
    confidence: str  # "high" | "medium" | "low"


class ParsedHero(BaseModel):
    """Single enemy hero after DB matching."""

    hero_name: str
    hero_id: int | None = None
    internal_name: str | None = None
    items: list[ParsedItem] = Field(default_factory=list)
    kills: int | None = None
    deaths: int | None = None
    assists: int | None = None
    level: int | None = None


class ScreenshotParseRequest(BaseModel):
    """POST /api/parse-screenshot request."""

    image_base64: str
    media_type: str = "image/png"


class ScreenshotParseResponse(BaseModel):
    """POST /api/parse-screenshot response."""

    heroes: list[ParsedHero] = Field(default_factory=list)
    error: str | None = None
    message: str | None = None
    latency_ms: int | None = None

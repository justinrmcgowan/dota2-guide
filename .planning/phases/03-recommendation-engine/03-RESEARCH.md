# Phase 3: Recommendation Engine - Research

**Researched:** 2026-03-21
**Domain:** Hybrid recommendation engine (rules + Claude API structured outputs)
**Confidence:** HIGH

## Summary

Phase 3 is the highest-risk, highest-value phase of Prismlab. It builds the core product: a hybrid recommendation engine where a deterministic rules layer handles obvious item decisions instantly, and Claude Sonnet 4.6 provides nuanced, matchup-specific reasoning via structured JSON output. The phase encompasses six components: a rules engine (~10-15 rule functions), a context builder (assembles game state into a prompt), an LLM engine (Claude API with structured output), a hybrid orchestrator (rules first, LLM second, merge + fallback), a matchup data pipeline (OpenDota API to SQLite cache), and the POST /api/recommend endpoint that ties everything together.

The Anthropic Python SDK v0.86.0 (already in requirements.txt) supports structured outputs at GA level via `client.messages.create()` with the `output_config` parameter -- no beta headers needed. The `AsyncAnthropic` client mirrors the synchronous API with `async/await`, and per-request timeouts can be set via `client.with_options(timeout=10.0)`. Prompt caching is available for the system prompt (minimum 2,048 tokens for Sonnet 4.6), offering 90% cost reduction on cached reads. The OpenDota `/heroes/{hero_id}/matchups` endpoint returns `{hero_id, games_played, wins}` per opponent (no item data), while `/heroes/{hero_id}/itemPopularity` returns `{start_game_items, early_game_items, mid_game_items, late_game_items}` with item_id-to-count mappings by phase. These two endpoints together provide the matchup context needed for the recommendation engine.

**Primary recommendation:** Use `client.messages.create()` with `output_config.format` (GA path, not beta `.parse()`) for structured outputs. Define the response schema as a Pydantic model for validation, but serialize it to JSON schema for the API call. This gives maximum control over the prompt while still getting guaranteed JSON structure from the API.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Rules Engine: List of 10-15 rule functions, each checks a condition and returns item recommendations with short rationale. Priority-ordered, first match wins for obvious items (Magic Stick vs spell-spam, BKB vs heavy magic, MKB vs evasion, etc.). Rules provide single item recommendations with reasoning, not full builds. Rules output is deterministic and instant (no API calls).
- Claude API Integration: Use Claude Sonnet 4.6 (claude-sonnet-4-6-20250514) -- best quality/cost/speed balance. Structured output via output_config.format with JSON schema (GA, no beta headers). System prompt: Role as 8K+ MMR analytical coach + game knowledge + output schema + 1-2 few-shot examples of good reasoning. Context builder pre-filters item catalog to ~40 relevant items per request. Keep prompt under 1500 input tokens for latency management. Response schema: phases[] array with items[], each item has id, name, reasoning, priority, conditions (for decision tree cards). Analytical voice: data-driven, stats, percentages -- not personality-driven.
- Hybrid Orchestration: Rules fire first, output injected into Claude prompt as "already-recommended items" so Claude complements rather than contradicts. 10-second hard timeout on Claude API call. Fallback returns rules-only results with "fallback": true flag in response. Frontend shows "AI reasoning unavailable" notice when fallback is active.
- Matchup Data Pipeline: Background fetch per matchup pair, cached in MatchupData table. Check DB first, if stale (>24h) fetch fresh from OpenDota /heroes/{id}/matchups. Return whatever's cached even if stale (never block recommendation on data freshness). Default to "high" bracket (Legend+) data.
- Recommendation Endpoint: POST /api/recommend with full game state body: hero, allies, opponents, role, playstyle, side, lane. Response: phased timeline JSON with phases[] containing items[] with id, name, reasoning, priority, conditions. Response metadata includes fallback flag, model used, latency_ms.

### Claude's Discretion
- Exact system prompt wording and few-shot examples
- Item catalog pre-filtering logic
- Specific rule conditions beyond the documented 10-15
- Prompt caching strategy
- Error handling granularity

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ENGN-01 | Rules layer fires instantly for obvious item decisions (e.g., Magic Stick vs spell-spamming lane opponents) | Rules engine architecture with priority-ordered function list; OpenDota itemPopularity data for common items validation |
| ENGN-02 | Claude API generates item recommendations with analytical reasoning referencing specific hero abilities and matchup dynamics | Anthropic SDK structured outputs (GA via output_config.format); system prompt design with specificity constraints and few-shot examples |
| ENGN-03 | Hybrid orchestrator routes decisions: rules for known patterns, Claude for nuanced reasoning | Pipeline pattern: rules first -> inject into prompt -> LLM complements; merge logic documented |
| ENGN-04 | System falls back to rules-only mode with a visible notice when Claude API fails or times out (10s hard timeout) | AsyncAnthropic with per-request timeout via with_options(); APITimeoutError catch; fallback flag in response |
| ENGN-05 | Claude API returns structured JSON output validated against schema before rendering | output_config.format with JSON schema guarantees valid structure at token generation level; Pydantic post-validation for item_id verification against DB |
| ENGN-06 | Matchup data pipeline fetches hero-vs-hero item win rates from OpenDota/Stratz and caches in SQLite | OpenDota /heroes/{id}/matchups returns win_rate/games_played; /heroes/{id}/itemPopularity returns phase-grouped item counts; MatchupData model already exists |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | 0.86.0 | Claude API client (async + structured outputs) | Official SDK, already in requirements.txt, supports GA structured outputs |
| httpx | 0.28.1 | Async HTTP for OpenDota API calls | Already used by opendota_client.py, async-native, used internally by anthropic SDK |
| pydantic | 2.12.5 | Request/response validation + JSON schema generation | Already in stack, generates JSON schemas from models for output_config |
| fastapi | 0.135.1 | API framework with dependency injection | Already in stack, async endpoint support |
| sqlalchemy | 2.0.48 | ORM for MatchupData queries | Already in stack with async sessions |
| aiosqlite | 0.22.1 | Async SQLite driver | Already in stack |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.2 | Test framework | Unit tests for rules, integration tests for endpoint |
| pytest-asyncio | 1.3.0 | Async test support | Testing async endpoints and Claude API mocks |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw output_config | client.beta.messages.parse() | .parse() is more ergonomic but still under beta namespace in SDK; output_config is GA and gives full control |
| httpx for OpenDota | aiohttp | httpx already in stack, no reason to add another HTTP client |
| Manual JSON schema | Pydantic model_json_schema() | Use Pydantic to generate the schema, then pass to output_config -- best of both worlds |

**Installation:**
No new packages needed. All dependencies are already in `requirements.txt`.

**Version verification:**
- anthropic: 0.86.0 (latest as of 2026-03-21, confirmed via pip index)
- All other packages already installed and verified in Phase 1

## Architecture Patterns

### Recommended Project Structure
```
backend/
  engine/
    __init__.py
    recommender.py          # HybridRecommender: orchestrates rules + LLM
    rules.py                # RulesEngine: deterministic item recommendations
    llm.py                  # LLMEngine: Claude API structured output wrapper
    context_builder.py      # ContextBuilder: assembles prompt from DB data
    schemas.py              # Pydantic models for recommendation I/O + JSON schema
    prompts/
      __init__.py
      system_prompt.py      # System prompt text + few-shot examples
  api/routes/
    recommend.py            # POST /api/recommend endpoint
  data/
    matchup_service.py      # Matchup data fetch/cache logic
```

### Pattern 1: Hybrid Pipeline Orchestration
**What:** Rules engine fires first, producing a list of "already recommended" items. These are injected into the Claude prompt so the LLM complements rather than duplicates. The orchestrator merges both outputs and handles fallback.
**When to use:** Every recommendation request.
**Example:**
```python
# Source: CONTEXT.md locked decisions
class HybridRecommender:
    def __init__(self, rules: RulesEngine, llm: LLMEngine, context_builder: ContextBuilder):
        self.rules = rules
        self.llm = llm
        self.context_builder = context_builder

    async def recommend(self, request: RecommendRequest, db: AsyncSession) -> RecommendResponse:
        start = time.monotonic()

        # Step 1: Rules fire instantly
        rules_items = self.rules.evaluate(request)

        # Step 2: Build Claude prompt context
        context = await self.context_builder.build(request, rules_items, db)

        # Step 3: Call Claude with timeout + fallback
        llm_result = None
        fallback = False
        try:
            llm_result = await self.llm.generate(context)
        except (anthropic.APITimeoutError, anthropic.APIConnectionError, Exception):
            fallback = True

        # Step 4: Merge results
        phases = self._merge(rules_items, llm_result) if llm_result else self._rules_only(rules_items)

        # Step 5: Validate all item_ids against DB
        phases = await self._validate_item_ids(phases, db)

        elapsed_ms = int((time.monotonic() - start) * 1000)
        return RecommendResponse(
            phases=phases,
            fallback=fallback,
            model="claude-sonnet-4-6-20250514" if not fallback else None,
            latency_ms=elapsed_ms,
        )
```

### Pattern 2: Claude API Structured Output (GA Path)
**What:** Use `AsyncAnthropic.messages.create()` with `output_config` for guaranteed JSON structure. Define schema via Pydantic, serialize to JSON schema, pass to API.
**When to use:** Every LLM call.
**Example:**
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
import json
from pydantic import BaseModel
from anthropic import AsyncAnthropic, APITimeoutError

class ItemRec(BaseModel):
    item_id: int
    item_name: str
    reasoning: str
    priority: str  # "core" | "situational" | "luxury"
    conditions: str | None = None  # For decision tree cards

class Phase(BaseModel):
    phase: str  # "starting" | "laning" | "core" | "late_game" | "situational"
    items: list[ItemRec]
    timing: str | None = None
    gold_budget: int | None = None

class LLMRecommendation(BaseModel):
    phases: list[Phase]
    overall_strategy: str

# Generate JSON schema from Pydantic model
schema = LLMRecommendation.model_json_schema()

client = AsyncAnthropic()

async def call_claude(system_prompt: str, user_message: str) -> LLMRecommendation | None:
    try:
        response = await client.with_options(timeout=10.0).messages.create(
            model="claude-sonnet-4-6-20250514",
            max_tokens=2000,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": schema,
                }
            },
        )
        data = json.loads(response.content[0].text)
        return LLMRecommendation.model_validate(data)
    except APITimeoutError:
        return None  # Fallback to rules-only
```

### Pattern 3: Prompt Caching for Cost Reduction
**What:** Mark the system prompt with `cache_control` to cache it across requests. System prompt (hero/item knowledge + rules + examples) stays static, user message changes per request.
**When to use:** Every LLM call. Minimum 2,048 tokens for Sonnet 4.6 caching.
**Example:**
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/prompt-caching
response = await client.with_options(timeout=10.0).messages.create(
    model="claude-sonnet-4-6-20250514",
    max_tokens=2000,
    temperature=0.3,
    system=[
        {
            "type": "text",
            "text": SYSTEM_PROMPT_TEXT,  # Static: role, principles, item catalog
            "cache_control": {"type": "ephemeral"},  # 5-min cache
        }
    ],
    messages=[{"role": "user", "content": user_context}],  # Dynamic per-request
    output_config={
        "format": {
            "type": "json_schema",
            "schema": schema,
        }
    },
)
```

### Pattern 4: Rules Engine with Priority-Ordered Functions
**What:** Each rule is a function that checks a condition and returns item recommendations. Rules are evaluated in priority order. Each returns a list of `RuleResult` objects or an empty list.
**When to use:** First step of every recommendation.
**Example:**
```python
from dataclasses import dataclass

@dataclass
class RuleResult:
    item_id: int
    item_name: str
    reasoning: str
    phase: str  # Which game phase this item belongs to
    priority: str

class RulesEngine:
    def evaluate(self, request: RecommendRequest) -> list[RuleResult]:
        results = []
        for rule_fn in self._rules:
            results.extend(rule_fn(request))
        return results

    @property
    def _rules(self):
        return [
            self._magic_stick_rule,
            self._quelling_blade_rule,
            self._boots_rule,
            self._bkb_rule,
            self._mkb_rule,
            self._armor_rule,
            self._force_staff_rule,
            self._mana_sustain_rule,
            self._starting_items_rule,
            self._dust_sentries_rule,
        ]

    def _magic_stick_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Magic Stick/Wand vs heroes who spam abilities in lane."""
        SPELL_SPAMMERS = {
            12,   # Phantom Assassin (Stifling Dagger)
            22,   # Zeus
            26,   # Lion (not spammer but common support)
            69,   # Bristleback (Quill Spray)
            84,   # Ogre Magi
            110,  # Skywrath Mage
            # ... complete list of spell-heavy laners
        }
        opponent_ids = [op for op in [req.lane_opponents[0], req.lane_opponents[1]] if op]
        if any(op_id in SPELL_SPAMMERS for op_id in opponent_ids):
            return [RuleResult(
                item_id=36,  # Magic Stick
                item_name="Magic Stick",
                reasoning=f"High-priority pickup against spell-spamming lane opponent. "
                          f"Expect 10+ charges regularly from frequent ability usage.",
                phase="laning",
                priority="core",
            )]
        return []
```

### Anti-Patterns to Avoid
- **Sending the entire item catalog in every prompt:** Pre-filter to ~40 relevant items based on hero role, attribute, and game phase. Sending 200+ items wastes tokens and increases latency.
- **Letting Claude choose item names as free text:** Always use integer `item_id` in the schema and validate against the DB. Claude WILL hallucinate item names from old patches.
- **Blocking on matchup data freshness:** Never make the recommendation wait for a fresh OpenDota fetch. Return stale data if that is all that is available. Fetch fresh data in the background.
- **Single-point-of-failure on Claude API:** The rules engine is not just a fallback -- it is the primary layer that fires on every request. Claude enhances, it does not replace.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON schema generation | Manual JSON schema dict | `LLMRecommendation.model_json_schema()` | Pydantic generates correct, complete JSON schema from typed models |
| Structured output validation | Manual JSON parsing + field checking | `output_config.format` with JSON schema | Anthropic API guarantees valid JSON structure at token generation level |
| Post-validation of Pydantic models | Manual dict key/type checking | `LLMRecommendation.model_validate(data)` | Pydantic v2 validates all fields, types, and constraints automatically |
| HTTP timeout handling | Manual asyncio.wait_for() wrapping | `client.with_options(timeout=10.0)` | SDK handles timeout natively, raises `APITimeoutError` |
| Async HTTP client management | Creating new httpx.AsyncClient per request | Singleton `AsyncAnthropic()` client | SDK manages connection pooling internally |

**Key insight:** The Anthropic SDK and Pydantic together handle 90% of the "hard parts" (schema generation, JSON validation, timeout, retry). The custom code is the rules engine, context builder, and system prompt -- the domain-specific logic.

## Common Pitfalls

### Pitfall 1: Claude Hallucinating Items from Old Patches
**What goes wrong:** Claude recommends items that have been removed or renamed in recent Dota patches (e.g., "Poor Man's Shield," "Iron Talon," "Ring of Aquila" -- all removed years ago).
**Why it happens:** Claude's training data includes historical Dota content. Item IDs and names change between patches.
**How to avoid:** (1) Include a complete item_id-to-name mapping in every prompt. (2) Use integer `item_id` in the output schema, not free-text item names. (3) After receiving Claude's response, validate every `item_id` against the items table in SQLite. (4) Add a system prompt constraint: "You may ONLY recommend items from the provided item list. Do not reference items not in the list."
**Warning signs:** Recommendations containing items not in the database, items with no `img_url`, or items with `cost=null`.

### Pitfall 2: Generic "Always-Good" Recommendations
**What goes wrong:** Claude recommends BKB, Boots of Travel, and other universally good items without matchup-specific reasoning. Reasoning says "this is a strong item" instead of "against Zeus and Lina's combined magical burst, BKB prevents 70%+ of their damage output in teamfights."
**Why it happens:** Without explicit constraints, LLMs gravitate toward safe, general answers.
**How to avoid:** (1) System prompt must enforce: "Every reasoning field MUST mention at least one enemy hero by name AND reference a specific ability or interaction." (2) Include 1-2 few-shot examples showing good vs. bad reasoning. (3) Post-process: check that at least one opponent hero name appears in each reasoning string. Log warnings (but don't block) if not.
**Warning signs:** Reasoning text that could apply to any hero in any game. No enemy hero names mentioned.

### Pitfall 3: Prompt Token Budget Overflow
**What goes wrong:** The system prompt + item catalog + matchup data + few-shot examples exceed expectations, causing latency to spike above the 10-second timeout.
**Why it happens:** The item catalog has 200+ items, hero stats are verbose, and few-shot examples add tokens quickly.
**How to avoid:** (1) Pre-filter items to ~40 relevant items per request (by hero attribute, role, cost range). (2) Keep item entries compact: `{id: 116, name: "BKB", cost: 4050, tags: ["magic_immunity"]}` not full descriptions. (3) Count tokens with `client.messages.count_tokens()` during development and stay under 1500 input tokens for the user message. (4) The system prompt (cached separately) can be larger since cache hits are cheap.
**Warning signs:** Latency consistently above 5 seconds, frequent timeouts.

### Pitfall 4: Race Condition on Matchup Data Fetch
**What goes wrong:** Multiple concurrent recommendation requests for the same matchup pair trigger multiple OpenDota API calls simultaneously, wasting rate limit quota.
**Why it happens:** No deduplication of in-flight requests.
**How to avoid:** Use a simple in-memory lock per matchup pair. If a fetch is already in progress for hero_id=1 vs opponent_id=69, subsequent requests wait for the first result rather than making duplicate API calls.
**Warning signs:** OpenDota 429 rate limit errors during testing with concurrent requests.

### Pitfall 5: output_config Schema Too Complex
**What goes wrong:** Anthropic API returns "compiled grammar is too large" error when the JSON schema has deeply nested or overly complex structures.
**Why it happens:** Constrained decoding compiles the schema into a grammar, which has size limits.
**How to avoid:** Keep the schema flat and simple. Use simple types (string, int, bool, array of objects). Avoid deeply nested optionals or unions. Test the schema with a real API call before locking it down.
**Warning signs:** 400 errors from the API mentioning grammar compilation.

### Pitfall 6: Stale AsyncAnthropic Client After Config Change
**What goes wrong:** The `AsyncAnthropic()` client is created once at module import time with the API key. If the key is rotated or the config changes, the client keeps using the old key until the process restarts.
**Why it happens:** Singleton pattern without refresh mechanism.
**How to avoid:** Create the client in a FastAPI dependency or lifespan context, not at module level. Alternatively, accept this limitation for V1 since API key rotation is rare.
**Warning signs:** 401 errors after API key rotation without process restart.

## Code Examples

### Complete Recommendation Request/Response Schema
```python
# Source: CONTEXT.md locked decisions + PRISMLAB_BLUEPRINT.md
from pydantic import BaseModel, Field

class RecommendRequest(BaseModel):
    """POST /api/recommend request body."""
    hero_id: int
    role: int = Field(ge=1, le=5)
    playstyle: str
    side: str  # "radiant" | "dire"
    lane: str  # "safe" | "off" | "mid"
    lane_opponents: list[int | None] = Field(max_length=2)
    allies: list[int | None] = Field(default_factory=list, max_length=4)
    # Mid-game fields (Phase 5, but schema should accept them now)
    phase: str = "laning"
    lane_result: str | None = None
    damage_profile: dict | None = None
    enemy_items_spotted: list[dict] = Field(default_factory=list)

class ItemRecommendation(BaseModel):
    """Single item recommendation with reasoning."""
    item_id: int
    item_name: str
    reasoning: str
    priority: str  # "core" | "situational" | "luxury"
    conditions: str | None = None  # For situational decision trees

class RecommendPhase(BaseModel):
    """A game phase with its recommended items."""
    phase: str  # "starting" | "laning" | "core" | "late_game" | "situational"
    items: list[ItemRecommendation]
    timing: str | None = None
    gold_budget: int | None = None

class RecommendResponse(BaseModel):
    """POST /api/recommend response body."""
    phases: list[RecommendPhase]
    overall_strategy: str | None = None
    fallback: bool = False
    model: str | None = None
    latency_ms: int | None = None
```

### AsyncAnthropic with Per-Request Timeout
```python
# Source: https://platform.claude.com/docs/en/api/sdks/python
import anthropic
from anthropic import AsyncAnthropic, APITimeoutError, APIConnectionError

# Create client once (e.g., in FastAPI lifespan or dependency)
claude_client = AsyncAnthropic()

async def call_claude_with_timeout(
    system_prompt: str | list[dict],
    user_message: str,
    schema: dict,
    timeout_seconds: float = 10.0,
) -> dict | None:
    """Call Claude API with structured output and hard timeout.

    Returns parsed JSON dict on success, None on timeout/error (triggers fallback).
    """
    try:
        response = await claude_client.with_options(
            timeout=timeout_seconds,
            max_retries=0,  # No retries -- we have a hard timeout budget
        ).messages.create(
            model="claude-sonnet-4-6-20250514",
            max_tokens=2000,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": schema,
                }
            },
        )
        import json
        return json.loads(response.content[0].text)
    except APITimeoutError:
        # 10-second timeout exceeded -- fall back to rules-only
        return None
    except APIConnectionError:
        # Network issue -- fall back to rules-only
        return None
    except anthropic.APIStatusError as e:
        # 4xx/5xx from API -- log and fall back
        import logging
        logging.getLogger(__name__).error("Claude API error: %s %s", e.status_code, e.message)
        return None
```

### OpenDota Matchup Data Pipeline
```python
# Source: Verified against live API https://api.opendota.com/api/heroes/1/matchups
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data.models import MatchupData
from data.opendota_client import OpenDotaClient

STALE_THRESHOLD = timedelta(hours=24)

async def get_or_fetch_matchup(
    hero_id: int,
    opponent_id: int,
    db: AsyncSession,
    client: OpenDotaClient,
) -> MatchupData | None:
    """Get matchup data from cache, fetch from OpenDota if stale.

    Never blocks on freshness -- returns stale data immediately and
    schedules background refresh if needed.
    """
    # Check cache first
    result = await db.execute(
        select(MatchupData).where(
            MatchupData.hero_id == hero_id,
            MatchupData.opponent_id == opponent_id,
        )
    )
    cached = result.scalar_one_or_none()

    if cached:
        # Return cached even if stale
        if cached.updated_at and cached.updated_at < datetime.now(timezone.utc) - STALE_THRESHOLD:
            # Schedule background refresh (don't await)
            import asyncio
            asyncio.create_task(_refresh_matchup(hero_id, opponent_id, db, client))
        return cached

    # No cache -- fetch synchronously (first request only)
    return await _refresh_matchup(hero_id, opponent_id, db, client)


async def _refresh_matchup(
    hero_id: int,
    opponent_id: int,
    db: AsyncSession,
    client: OpenDotaClient,
) -> MatchupData | None:
    """Fetch fresh matchup data from OpenDota API.

    /heroes/{hero_id}/matchups returns:
    [{"hero_id": int, "games_played": int, "wins": int}, ...]
    One entry per opponent hero.

    /heroes/{hero_id}/itemPopularity returns:
    {"start_game_items": {item_id: count, ...}, "early_game_items": {...}, ...}
    """
    try:
        matchups = await client.fetch_hero_matchups(hero_id)
        opponent_data = next(
            (m for m in matchups if m["hero_id"] == opponent_id),
            None,
        )
        if not opponent_data:
            return None

        win_rate = opponent_data["wins"] / opponent_data["games_played"] if opponent_data["games_played"] > 0 else 0.5

        # Upsert matchup data
        matchup = MatchupData(
            hero_id=hero_id,
            opponent_id=opponent_id,
            win_rate=win_rate,
            games_played=opponent_data["games_played"],
            bracket="high",
            updated_at=datetime.now(timezone.utc),
        )
        await db.merge(matchup)
        await db.commit()
        return matchup
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Failed to fetch matchup data")
        return None
```

### Item Catalog Pre-Filtering for Prompt
```python
# Claude's Discretion: exact pre-filtering logic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from data.models import Item

async def get_relevant_items(
    hero_id: int,
    role: int,
    db: AsyncSession,
) -> list[dict]:
    """Filter item catalog to ~40 items relevant to this hero/role.

    Excludes: recipes, neutral items, items costing 0,
    and role-inappropriate items (e.g., no Aghs Scepter for pos 5 budget).
    """
    result = await db.execute(
        select(Item).where(
            Item.is_recipe == False,
            Item.is_neutral == False,
            Item.cost > 0,
        )
    )
    all_items = result.scalars().all()

    # Filter by role budget (pos 4/5 rarely get items > 5000g)
    max_cost = 10000 if role <= 3 else 5500
    filtered = [
        {"id": item.id, "name": item.name, "cost": item.cost}
        for item in all_items
        if item.cost and item.cost <= max_cost
    ]

    # Sort by cost (most relevant items first)
    filtered.sort(key=lambda x: x["cost"])
    return filtered[:50]  # Cap at 50 to control prompt size
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `output_format` parameter (beta) | `output_config.format` parameter (GA) | Feb 2026 | No beta headers needed, production-ready |
| `client.beta.messages.parse()` | `client.messages.create()` + `output_config` | Feb 2026 | GA path uses create() with manual JSON parse; .parse() still in beta namespace |
| Separate JSON mode (no schema) | Structured outputs with JSON schema guarantee | Nov 2025 GA Feb 2026 | 100% schema compliance at token generation level |
| Manual prompt engineering for JSON | Constrained decoding via output_config | Nov 2025 | No more "please return valid JSON" -- guaranteed by the API |

**Deprecated/outdated:**
- `anthropic-beta: structured-outputs-2025-11-13` header: No longer required. Remove if present.
- `output_format` parameter: Deprecated, use `output_config.format` instead. Still works temporarily.
- `client.beta.messages.parse()`: Still functional but lives under beta namespace. The GA path is `client.messages.create()` with `output_config`.

## Open Questions

1. **Exact spell-spammer hero list for Magic Stick rule**
   - What we know: Bristleback, Zeus, Skywrath Mage, Ogre Magi, Batrider are classic examples
   - What's unclear: Complete list of ~15-20 heroes who spam abilities frequently enough to justify Magic Stick as a priority pickup
   - Recommendation: Curate manually from Dota game knowledge during implementation. The rule should be conservative (only include clear-cut cases).

2. **OpenDota itemPopularity endpoint reliability**
   - What we know: The endpoint exists and returns `{start_game_items, early_game_items, mid_game_items, late_game_items}` with `{item_id: count}` mappings. Verified against live API for hero_id=1.
   - What's unclear: Whether the data quality is sufficient for matchup-specific recommendations (it returns per-hero data, not per-matchup). Whether the counts represent games or picks.
   - Recommendation: Use this data to enrich the context builder's item pre-filtering (which items are commonly built on this hero), but don't rely on it for matchup-specific logic. The matchup-specific reasoning comes from Claude.

3. **Prompt caching minimum token threshold**
   - What we know: Sonnet 4.6 requires 2,048 minimum tokens for caching. The system prompt must be at least this long.
   - What's unclear: Whether the system prompt with item catalog, rules, and few-shot examples will naturally exceed 2,048 tokens. If the system prompt is too short, caching won't work.
   - Recommendation: Design the system prompt to include enough context (role definition, principles, item catalog subset, few-shot examples) to comfortably exceed 2,048 tokens. This is achievable given the content needed.

4. **OpenDota `/heroes/{hero_id}/matchups` lacks item data**
   - What we know: The matchups endpoint returns only `{hero_id, games_played, wins}` -- no item data per matchup pair.
   - What's unclear: How to populate the `common_items` and `common_starting_items` JSON fields in the MatchupData model.
   - Recommendation: Use `/heroes/{hero_id}/itemPopularity` for per-hero item popularity (not per-matchup). The MatchupData `common_items` field can be populated from this endpoint, but it represents "items commonly bought on this hero" not "items commonly bought against this specific opponent." Per-matchup item data would require Stratz GraphQL or match-level analysis, which is out of scope for V1.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | None (default pytest discovery) |
| Quick run command | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| Full suite command | `cd prismlab/backend && python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ENGN-01 | Rules engine returns Magic Stick against spell-spammers | unit | `python -m pytest tests/test_rules.py::test_magic_stick_vs_spammer -x` | No -- Wave 0 |
| ENGN-01 | Rules engine returns no recommendation when no rule matches | unit | `python -m pytest tests/test_rules.py::test_no_match_returns_empty -x` | No -- Wave 0 |
| ENGN-02 | Claude API returns structured recommendation (mocked) | unit | `python -m pytest tests/test_llm.py::test_structured_output_mock -x` | No -- Wave 0 |
| ENGN-03 | Hybrid orchestrator merges rules + LLM results | unit | `python -m pytest tests/test_recommender.py::test_hybrid_merge -x` | No -- Wave 0 |
| ENGN-04 | Fallback to rules-only on Claude timeout | unit | `python -m pytest tests/test_recommender.py::test_fallback_on_timeout -x` | No -- Wave 0 |
| ENGN-04 | Response includes fallback=true flag when Claude fails | unit | `python -m pytest tests/test_recommender.py::test_fallback_flag -x` | No -- Wave 0 |
| ENGN-05 | Claude response validated against Pydantic schema | unit | `python -m pytest tests/test_llm.py::test_response_validation -x` | No -- Wave 0 |
| ENGN-05 | Invalid item_ids filtered from response | unit | `python -m pytest tests/test_recommender.py::test_invalid_item_id_filtered -x` | No -- Wave 0 |
| ENGN-06 | Matchup data cached in SQLite after fetch | integration | `python -m pytest tests/test_matchup_service.py::test_cache_after_fetch -x` | No -- Wave 0 |
| ENGN-06 | Stale matchup data returned immediately (not blocked) | integration | `python -m pytest tests/test_matchup_service.py::test_stale_data_returned -x` | No -- Wave 0 |
| E2E | POST /api/recommend returns valid response | integration | `python -m pytest tests/test_api.py::test_recommend_endpoint -x` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd prismlab/backend && python -m pytest tests/ -x -q`
- **Per wave merge:** `cd prismlab/backend && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_rules.py` -- covers ENGN-01 (rules engine unit tests)
- [ ] `tests/test_llm.py` -- covers ENGN-02, ENGN-05 (LLM engine with mocked Claude API)
- [ ] `tests/test_recommender.py` -- covers ENGN-03, ENGN-04, ENGN-05 (hybrid orchestrator tests)
- [ ] `tests/test_matchup_service.py` -- covers ENGN-06 (matchup data pipeline tests)
- [ ] `tests/test_api.py::test_recommend_endpoint` -- covers E2E (add to existing test file)
- [ ] Update `tests/conftest.py` -- add fixtures for: mock Claude client, test matchup data, test item catalog

## Sources

### Primary (HIGH confidence)
- [Anthropic Structured Outputs (GA docs)](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) -- output_config.format syntax, JSON schema guarantee, no beta header needed
- [Anthropic Python SDK docs](https://platform.claude.com/docs/en/api/sdks/python) -- AsyncAnthropic usage, timeout config via with_options(), APITimeoutError, retry behavior
- [Anthropic Prompt Caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) -- cache_control syntax, 2048 min tokens for Sonnet 4.6, 90% cost reduction on reads
- [OpenDota /heroes/1/matchups (live API)](https://api.opendota.com/api/heroes/1/matchups) -- Verified response format: {hero_id, games_played, wins}
- [OpenDota /heroes/1/itemPopularity (live API)](https://api.opendota.com/api/heroes/1/itemPopularity) -- Verified response format: {start_game_items, early_game_items, mid_game_items, late_game_items} with {item_id: count}
- [anthropic PyPI v0.86.0](https://pypi.org/project/anthropic/) -- Latest version confirmed, already in requirements.txt

### Secondary (MEDIUM confidence)
- [OpenDota MCP Server](https://github.com/hkaanengin/opendota-mcp-server) -- Confirmed existence of get_hero_item_popularity and get_hero_matchups tools
- [Anthropic Structured Outputs GA announcement](https://github.com/BerriAI/litellm/issues/20533) -- Confirmed output_format deprecated in favor of output_config.format, no beta header needed
- [OpenDota API Docs](https://docs.opendota.com/) -- Endpoint discovery (docs page renders client-side, hard to scrape)

### Tertiary (LOW confidence)
- [Thomas Wiegold blog on structured outputs](https://thomas-wiegold.com/blog/claude-api-structured-output/) -- Example code using beta.messages.parse() (pre-GA, some patterns now outdated)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in requirements.txt, versions verified against pip
- Architecture: HIGH -- hybrid pipeline pattern well-validated, CONTEXT.md decisions lock all major choices
- Pitfalls: HIGH -- LLM hallucination and timeout patterns verified against official SDK docs and live API responses
- Structured outputs: HIGH -- GA status confirmed, output_config.format syntax verified from official docs
- OpenDota data pipeline: MEDIUM -- endpoint responses verified against live API, but per-matchup item data gap identified (only per-hero item popularity available)

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (30 days -- stack is stable, API is GA)

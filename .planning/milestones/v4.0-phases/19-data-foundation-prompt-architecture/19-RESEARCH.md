# Phase 19: Data Foundation & Prompt Architecture - Research

**Researched:** 2026-03-27
**Domain:** Backend data pipeline extensions (OpenDota ability + timing endpoints) and Claude system prompt restructuring
**Confidence:** HIGH

## Summary

Phase 19 establishes the data foundation that all v4.0 feature phases (20-23) depend on. It adds three new OpenDota API client methods, two new SQLAlchemy models, two new frozen dataclass types in DataCache, extends the refresh pipeline with rate-limited ability and timing data fetches, and restructures the system prompt to enforce a clean separation between static directives (system message) and dynamic per-request data (user message).

The phase touches six existing backend files (opendota_client.py, models.py, cache.py, refresh.py, seed.py, system_prompt.py) and creates no new files. Zero new pip packages are required -- all new functionality uses existing httpx, SQLAlchemy, and stdlib dataclasses. The primary technical risks are: (1) the system prompt must stay under 5,000 tokens with only directive-style additions, (2) OpenDota timing data returns `games` and `wins` as strings not integers, and (3) the three-cache coherence protocol must extend atomically to include the new ability and timing data alongside the existing hero/item swap.

**Primary recommendation:** Implement in this order: OpenDota client methods first, then SQLAlchemy models + Alembic-free table creation, then DataCache frozen dataclasses + load/refresh extensions, then refresh pipeline integration with rate limiting, and finally system prompt restructuring. Each step is independently testable.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Item timing benchmarks use stale-while-revalidate pattern, consistent with matchup_service. Fetch per-hero on first request, cache in DB, background refresh when stale (24h threshold). Only fetches heroes that are actually queried -- no batch crawl of all 124 heroes.
- **D-02:** Timing data stored in a DB model (like MatchupData/HeroItemPopularity) with JSON column for the raw response. DataCache holds a derived in-memory index for fast synchronous lookups.
- **D-03:** Ability constants (constants/abilities + constants/hero_abilities) refresh daily alongside heroes/items in the APScheduler pipeline. Only 2 extra API calls/day. Ability data changes only on Dota patches.
- **D-04:** Ability data loaded into DataCache at startup and refreshed atomically on pipeline cycle, following the existing hero/item pattern (frozen dataclasses, atomic swap).
- **D-05:** Claude's discretion on the system-vs-user message split. Goal: system prompt stays under ~5,000 tokens with directives, identity, reasoning rules, output format, and examples. All dynamic per-request data (timing benchmarks, ability descriptions, item catalog, matchup data, popularity) stays in the user message via context_builder.
- **D-06:** System prompt will grow with new v4.0 directives (timing reasoning guidance, counter-item naming rules, win condition framing instructions) but must remain a stable, cacheable constant.
- **D-07:** Timing benchmarks always shown, annotated with confidence level: strong (1000+ games), moderate (200-999 games), weak (<200 games). No data is hidden -- downstream phases can display confidence visually. The confidence level is stored in the cache alongside the timing data.

### Claude's Discretion
- Prompt split strategy: Claude determines optimal boundary between system directives and user message data, targeting under 5K tokens for system prompt
- DataCache internal data structures for ability data (new AbilityCached dataclass fields, hero-ability index structure)
- Timing data cache structure (how to derive in-memory index from DB-stored JSON)
- Rate limiting / semaphore strategy for stale-while-revalidate background refreshes
- Three-cache coherence extension: how ability + timing data fits into DataCache -> RulesEngine -> ResponseCache invalidation chain

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | System fetches and caches hero ability metadata (behavior, damage type, BKB-pierce, dispellable) from OpenDota constants | OpenDota `/constants/abilities` endpoint verified live. Response confirmed with counter-item-relevant fields: behavior, dmg_type, bkbpierce, dispellable. AbilityCached frozen dataclass design documented in STACK.md. |
| DATA-02 | System fetches and caches hero-to-ability mapping from OpenDota constants | OpenDota `/constants/hero_abilities` endpoint verified live. Maps hero internal names to ability key lists. Requires building a hero_internal_name_to_id reverse lookup (not in current DataCache). |
| DATA-03 | System fetches and caches item timing benchmark data (hero, item, time bucket, games, win rate) from OpenDota scenarios endpoint | OpenDota `/scenarios/itemTimings` endpoint verified live. Returns time buckets with games/wins as STRINGS (must cast to int). Stale-while-revalidate pattern matches matchup_service. DB model stores JSON blob per hero+item pair. |
| DATA-04 | System prompt restructured -- directives stay in system message (~5K token budget), all dynamic data moves to user message | Current system prompt is ~3,500 chars / ~900-1000 tokens. Has ~4,000 token headroom within 5K budget. Phase 19 adds ~600 tokens of v4.0 directives. No dynamic data currently in system prompt -- architecture already correct; phase adds new directive sections and validates the split. |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy + SQLite (no ORM changes allowed)
- **Data Sources:** OpenDota API, Stratz API (OpenDota primary for v4.0)
- **Type hints throughout**, async endpoints, Pydantic models for validation
- **Hybrid engine architecture:** Rules fire first, Claude API for reasoning. Always fallback if LLM fails.
- **Structured JSON output** from Claude API -- parse and validate before returning
- **System prompt is the heart of the app** -- reasoning must sound like 8K+ MMR coach
- **Docker Compose deployment** on Unraid server, backend port 8420
- All code under `prismlab/` subdirectory

## Standard Stack

### Core (No New Packages)

| Library | Version | Purpose | Already In Use |
|---------|---------|---------|----------------|
| httpx | 0.28.1 | Async HTTP client for OpenDota API calls | Yes -- opendota_client.py |
| SQLAlchemy | 2.0.48 | ORM for new HeroAbilityData + ItemTimingData models | Yes -- models.py |
| aiosqlite | 0.22.1 | Async SQLite driver | Yes -- database.py |
| anthropic | 0.86.0 | Claude API client (system prompt changes) | Yes -- llm.py |
| apscheduler | 3.11.0 | Daily refresh pipeline scheduling | Yes -- main.py |

### Supporting (No New Packages)

| Library | Purpose | Already In Use |
|---------|---------|----------------|
| stdlib `dataclasses` | Frozen dataclasses for AbilityCached, TimingBucket | Yes -- cache.py |
| stdlib `asyncio` | Semaphore for rate-limited fetches, asyncio.Lock for dedup | Yes -- matchup_service.py |
| stdlib `datetime` | Staleness checks (24h threshold) | Yes -- matchup_service.py |
| stdlib `json` | JSON parsing of API responses | Yes -- throughout |

**Installation:** No new packages. Zero changes to `requirements.txt`.

**Confidence:** HIGH -- all libraries already validated in production across v1-v3.

## Architecture Patterns

### Files Modified (Phase 19 Scope)

```
prismlab/backend/
  data/
    opendota_client.py    # +3 new fetch methods
    models.py             # +2 new SQLAlchemy models
    cache.py              # +2 frozen dataclasses, +4 new cache dicts, +8 lookup methods, extended load()/refresh()
    refresh.py            # +ability fetch in daily pipeline, extended three-cache coherence
    seed.py               # +ability data seeding on first startup
  engine/
    prompts/
      system_prompt.py    # +~600 tokens of v4.0 directives (no dynamic data)
```

### No New Files Created

All changes extend existing modules. No new services, no new routers, no new engine modules this phase.

### Pattern 1: OpenDota Client Method Extension

**What:** Add three new `fetch_*` methods to `OpenDotaClient` following the existing pattern.
**When to use:** Whenever a new OpenDota endpoint is needed.
**Source:** Verified against existing `fetch_heroes()`, `fetch_items()`, `fetch_hero_matchups()`, `fetch_hero_item_popularity()` patterns.

```python
# Pattern from existing code (opendota_client.py line 12-24):
async def fetch_abilities(self) -> dict:
    """Fetch all ability constants from OpenDota.

    Returns dict keyed by ability internal name, e.g. {"antimage_mana_break": {...}}.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.BASE_URL}/constants/abilities",
            params=self.params,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

async def fetch_hero_abilities(self) -> dict:
    """Fetch hero-to-ability mapping from OpenDota.

    Returns dict keyed by hero internal name, e.g.
    {"npc_dota_hero_antimage": {"abilities": ["antimage_mana_break", ...], ...}}.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.BASE_URL}/constants/hero_abilities",
            params=self.params,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()

async def fetch_item_timings(self, hero_id: int) -> list[dict]:
    """Fetch item timing benchmarks for a hero from OpenDota scenarios.

    Returns list of {"hero_id": int, "item": str, "time": int,
    "games": str, "wins": str}. NOTE: games and wins are STRINGS.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{self.BASE_URL}/scenarios/itemTimings",
            params={**self.params, "hero_id": str(hero_id)},
            timeout=15.0,
        )
        response.raise_for_status()
        return response.json()
```

### Pattern 2: SQLAlchemy Model Addition (Alembic-Free)

**What:** Add new models to `models.py`. Tables auto-created by `Base.metadata.create_all` in main.py lifespan.
**Source:** Matches existing `HeroItemPopularity` and `MatchupData` patterns.

```python
# Pattern for HeroAbilityData:
class HeroAbilityData(Base):
    """Cached hero ability constants from OpenDota."""
    __tablename__ = "hero_ability_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(Integer, ForeignKey("heroes.id"), unique=True)
    abilities_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())

# Pattern for ItemTimingData:
class ItemTimingData(Base):
    """Cached item timing benchmark data per hero from OpenDota scenarios."""
    __tablename__ = "item_timing_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(Integer, ForeignKey("heroes.id"))
    item_name: Mapped[str] = mapped_column(String, nullable=False)
    timing_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
```

**Key difference from CONTEXT.md research:** The `ItemTimingData` model stores ONE row per hero-item pair (not one row per hero with all items), consistent with decision D-02 which specifies "JSON column for the raw response" per hero+item combination. This allows stale-while-revalidate per hero (decision D-01) -- you query by hero_id and get all that hero's item timing rows.

### Pattern 3: Frozen Dataclass Extension in DataCache

**What:** Add new frozen dataclasses and cache dictionaries to DataCache, extend `load()` / `refresh()` to populate them atomically alongside heroes/items.
**Source:** Matches `HeroCached` / `ItemCached` pattern in cache.py.

```python
@dataclass(frozen=True)
class TimingBucket:
    """Single time bucket from OpenDota item timing data."""
    time: int          # seconds since game start
    games: int         # PARSED from string
    wins: int          # PARSED from string
    confidence: str    # "strong" | "moderate" | "weak" (from D-07)

    @property
    def win_rate(self) -> float:
        return self.wins / self.games if self.games > 0 else 0.0

@dataclass(frozen=True)
class AbilityCached:
    """Counter-item-relevant fields for a hero ability."""
    key: str                      # e.g. "enigma_black_hole"
    dname: str                    # e.g. "Black Hole"
    behavior: tuple[str, ...]     # e.g. ("AOE", "Point Target", "Channeled")
    bkbpierce: bool               # True if "Yes"
    dispellable: str | None       # "Yes", "No", "Strong Dispels Only", None
    dmg_type: str | None          # "Magical", "Physical", "Pure", None

    @property
    def is_channeled(self) -> bool:
        return "Channeled" in self.behavior

    @property
    def is_passive(self) -> bool:
        return "Passive" in self.behavior
```

### Pattern 4: Stale-While-Revalidate for Timing Data

**What:** Timing data uses the same stale-while-revalidate pattern as matchup_service.py -- return cached data immediately, trigger background refresh if stale.
**Source:** matchup_service.py `get_or_fetch_matchup()` (lines 27-70) and `_fetch_locks` pattern.

```python
# Key pattern from matchup_service.py:
# 1. Check DB cache
# 2. If cached and fresh: return immediately
# 3. If cached and stale: return immediately + asyncio.create_task(refresh)
# 4. If not cached: await first fetch (blocks)
# 5. Per-key asyncio.Lock to deduplicate concurrent fetches

# For timing data, the key is hero_id (not hero_id+item):
# - Query all timing rows for a hero_id at once
# - If any row for that hero is stale, refresh ALL timing data for that hero
# - One API call per hero fetches all items: /scenarios/itemTimings?hero_id=X
```

### Pattern 5: Three-Cache Coherence Extension

**What:** The refresh pipeline invalidates caches in strict order: DataCache -> RulesEngine (via reference) -> ResponseCache.clear(). Ability and timing data must join this same atomic swap.
**Source:** refresh.py lines 120-134 (current three-cache protocol).

```python
# Current pattern in refresh.py:
# 1. Fetch + upsert heroes and items to DB
# 2. DataCache.refresh(fresh_session)  -- atomic swap of hero/item dicts
# 3. ResponseCache.clear()              -- invalidate stale responses

# Extended for Phase 19:
# 1. Fetch + upsert heroes, items, abilities to DB
# 2. DataCache.refresh(fresh_session)  -- atomic swap of hero/item/ability dicts
# 3. ResponseCache.clear()              -- invalidate stale responses
#
# Note: Timing data is NOT refreshed in the scheduled pipeline (D-01).
# Timing data uses stale-while-revalidate per hero on first request.
# But DataCache.refresh() must ALSO load existing timing data from DB
# so that the timing cache is populated after a restart/refresh.
```

**Critical detail:** `DataCache.load()` must build ALL new dicts (heroes, items, abilities, timing index) from DB data first, THEN swap ALL references in a single code block. This matches the existing pattern at cache.py lines 169-174 where `_heroes`, `_items`, `_hero_name_to_id`, `_item_name_to_id` are swapped together.

### Anti-Patterns to Avoid

- **Separate cache singletons for ability/timing data:** Do NOT create `AbilityCache` or `TimingCache` classes. Extend the existing `DataCache` singleton. Separate singletons break three-cache coherence.
- **Putting timing numbers in the system prompt:** The system prompt is for DIRECTIVES ("if timing data is present, flag urgency"). The actual timing numbers (e.g., "Battle Fury 62% WR at 15min") belong in the user message. This is decision D-05.
- **Fetching all 124 heroes' timing data in the scheduled pipeline:** Decision D-01 explicitly says "Only fetches heroes that are actually queried -- no batch crawl." Use stale-while-revalidate on first request.
- **Treating `games`/`wins` as integers from the API response:** They are STRINGS. Must explicitly cast with `int()`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hero internal_name to hero_id lookup | Linear scan through `_heroes` dict | Add `_hero_internal_name_to_id: dict[str, int]` in DataCache | The `/constants/hero_abilities` endpoint keys are `npc_dota_hero_X` internal names. Need O(1) lookup to join with hero_id. Currently no such mapping exists. |
| Timing data confidence classification | Complex statistical model | Simple threshold: `games >= 1000` = strong, `200-999` = moderate, `< 200` = weak | Decision D-07 specifies these exact tiers. |
| Ability behavior parsing | Custom parser for behavior strings | Handle both string and list: `tuple(b) if isinstance(b, list) else (b,)` | OpenDota returns behavior as either a string `"Passive"` or a list `["No Target", "Channeled"]`. Must normalize to tuple. |
| Rate-limited concurrent fetches | Custom rate limiter | `asyncio.Semaphore` + `asyncio.sleep` | Proven pattern. Semaphore limits concurrency, sleep between batches respects 60 req/min. |

## Common Pitfalls

### Pitfall 1: OpenDota `games`/`wins` String Types

**What goes wrong:** The `/scenarios/itemTimings` endpoint returns `games` and `wins` as JSON strings, not integers. Code like `win_rate = wins / games` fails with TypeError, or worse, string concatenation.
**Why it happens:** The go-opendota struct definition confirms these are strings. OpenDota's API is inconsistent about number types across endpoints.
**How to avoid:** Always cast explicitly: `games = int(row["games"])`, `wins = int(row["wins"])`. Add a parsing function that handles this conversion centrally.
**Warning signs:** TypeError in timing calculations, or impossibly large win rates from string math.

### Pitfall 2: Hero Internal Name Mismatch in Ability Mapping

**What goes wrong:** The `/constants/hero_abilities` endpoint keys heroes by internal name (e.g., `npc_dota_hero_antimage`), but the DataCache indexes heroes by integer ID. Without a reverse mapping, you cannot join ability data to hero data.
**Why it happens:** The current DataCache has `_hero_name_to_id` (localized_name -> ID) but not `_hero_internal_name_to_id` (internal_name -> ID).
**How to avoid:** Build a `_hero_internal_name_to_id: dict[str, int]` during the hero cache build phase (same loop that builds `_hero_name_to_id`). Use it when processing `/constants/hero_abilities` response.
**Warning signs:** Missing ability data for heroes whose internal names don't match, or O(n) scanning through the hero dict on every ability lookup.

### Pitfall 3: Ability Behavior Field Inconsistency

**What goes wrong:** The `behavior` field in `/constants/abilities` is either a string (`"Passive"`) or a list (`["No Target", "Channeled"]`). Code that assumes one format breaks on the other.
**Why it happens:** OpenDota normalizes single-behavior abilities as strings and multi-behavior abilities as lists.
**How to avoid:** Normalize during AbilityCached construction: `behavior = tuple(raw["behavior"]) if isinstance(raw["behavior"], list) else (raw["behavior"],) if raw.get("behavior") else ()`.
**Warning signs:** `TypeError: 'str' object is not iterable` when checking `"Channeled" in behavior`, or false negatives on behavior checks.

### Pitfall 4: System Prompt Token Budget Miscalculation

**What goes wrong:** Adding v4.0 directive sections pushes the system prompt beyond the 5,000 token budget or, conversely, it stays below the Haiku 4.5 4,096-token caching minimum.
**Why it happens:** The current system prompt is only ~900-1000 tokens. Haiku 4.5 requires 4,096 minimum tokens for prompt caching to activate. Adding ~600 tokens of v4.0 directives gets to ~1,500-1,600 tokens -- still well below the caching threshold.
**How to avoid:** The current implementation passes `system=SYSTEM_PROMPT` as a plain string with no `cache_control` markers (llm.py line 65). The system prompt is too short for automatic caching on Haiku 4.5 regardless. This is actually fine -- the system prompt is small enough that its cost per request is negligible (~$0.0001 at 1000 tokens). Do NOT artificially inflate the prompt to hit the caching threshold. The 5K budget is about quality and response consistency, not cost.
**Warning signs:** If someone adds `cache_control` markers expecting cache hits but the prompt is under 4,096 tokens, caching silently does not activate.

### Pitfall 5: Timing Data Atomicity During Stale-While-Revalidate

**What goes wrong:** A background refresh for one hero's timing data completes and updates DataCache, but ResponseCache still holds responses computed with the old timing data. The next cache hit returns stale timing context.
**Why it happens:** The stale-while-revalidate pattern for timing data (D-01) runs independently of the scheduled refresh pipeline. It does NOT trigger ResponseCache.clear().
**How to avoid:** Two options: (a) When timing data for a hero is refreshed in background, clear only ResponseCache entries that involved that hero (complex, overkill). (b) Accept the 5-minute TTL on ResponseCache as sufficient -- stale timing data in cached responses expires naturally. Option (b) is correct for v4.0 because timing benchmarks are statistical aggregates that change slowly.
**Warning signs:** Users see timing benchmarks that don't match across consecutive requests for the same hero.

### Pitfall 6: `generic_hidden` Ability Entries

**What goes wrong:** The `/constants/hero_abilities` response includes `generic_hidden` entries as placeholder ability slots. If these are passed to `/constants/abilities` for lookup, they either return nothing or return irrelevant generic data.
**Why it happens:** Dota 2 has hidden ability slots that are not real abilities. OpenDota includes them in the hero ability list.
**How to avoid:** Filter out `generic_hidden` entries during processing: `[a for a in abilities if not a.startswith("generic_")]`. Also filter entries that start with `special_bonus_` (talents) -- those are separate from combat abilities.
**Warning signs:** AbilityCached entries with empty dname or None fields, or talent entries showing up as "abilities" in counter-item logic.

## Code Examples

### Verified OpenDota Response: `/scenarios/itemTimings?hero_id=1`

```json
[
  {"hero_id": 1, "item": "bfury", "time": 450, "games": "6", "wins": "6"},
  {"hero_id": 1, "item": "bfury", "time": 600, "games": "12", "wins": "7"},
  {"hero_id": 1, "item": "bfury", "time": 720, "games": "40", "wins": "30"},
  {"hero_id": 1, "item": "bfury", "time": 900, "games": "277", "wins": "175"},
  {"hero_id": 1, "item": "bfury", "time": 1200, "games": "284", "wins": "114"},
  {"hero_id": 1, "item": "bfury", "time": 1500, "games": "19", "wins": "8"},
  {"hero_id": 1, "item": "bfury", "time": 1800, "games": "1", "wins": "0"}
]
```

Source: Verified live against `https://api.opendota.com/api/scenarios/itemTimings?hero_id=1&item=bfury`

### Verified OpenDota Response: `/constants/hero_abilities` (excerpt)

```json
{
  "npc_dota_hero_antimage": {
    "abilities": [
      "antimage_mana_break",
      "antimage_blink",
      "antimage_counterspell",
      "generic_hidden",
      "antimage_persectur",
      "antimage_mana_void"
    ],
    "talents": [
      {"name": "special_bonus_hp_regen_3", "level": 1}
    ]
  }
}
```

Source: Verified live against `https://api.opendota.com/api/constants/hero_abilities`

### Verified OpenDota Response: `/constants/abilities` (excerpt)

```json
{
  "antimage_mana_break": {
    "dname": "Mana Break",
    "behavior": "Passive",
    "dmg_type": "Physical",
    "bkbpierce": "No",
    "dispellable": null,
    "desc": "Burns an opponent's mana on each attack..."
  },
  "enigma_black_hole": {
    "dname": "Black Hole",
    "behavior": ["AOE", "Point Target", "Channeled"],
    "dmg_type": "Pure",
    "bkbpierce": "Yes",
    "dispellable": null
  },
  "crystal_maiden_freezing_field": {
    "dname": "Freezing Field",
    "behavior": ["No Target", "Channeled"],
    "dmg_type": "Magical",
    "bkbpierce": "No",
    "dispellable": null
  }
}
```

Source: Verified live against `https://api.opendota.com/api/constants/abilities`

### DataCache Load Extension Pattern

```python
# In DataCache.load() -- after existing hero/item loading:

# -- Build hero internal_name lookup (NEW for Phase 19) --
new_hero_internal_to_id: dict[str, int] = {}
for hero in new_heroes.values():
    new_hero_internal_to_id[hero.internal_name] = hero.id

# -- Build ability cache --
ability_result = await db.execute(select(HeroAbilityData))
ability_rows = ability_result.scalars().all()

new_hero_abilities: dict[int, list[AbilityCached]] = {}
for row in ability_rows:
    if row.abilities_json:
        abilities = []
        for key, data in row.abilities_json.items():
            behavior_raw = data.get("behavior", "")
            if isinstance(behavior_raw, list):
                behavior = tuple(behavior_raw)
            elif isinstance(behavior_raw, str) and behavior_raw:
                behavior = (behavior_raw,)
            else:
                behavior = ()

            abilities.append(AbilityCached(
                key=key,
                dname=data.get("dname", key),
                behavior=behavior,
                bkbpierce=data.get("bkbpierce") == "Yes",
                dispellable=data.get("dispellable"),
                dmg_type=data.get("dmg_type"),
            ))
        new_hero_abilities[row.hero_id] = abilities

# -- Build timing cache --
timing_result = await db.execute(select(ItemTimingData))
timing_rows = timing_result.scalars().all()

new_timing_benchmarks: dict[int, dict[str, list[TimingBucket]]] = {}
for row in timing_rows:
    if row.timing_data:
        buckets = []
        for bucket in row.timing_data:
            games = int(bucket["games"])  # CRITICAL: cast from string
            wins = int(bucket["wins"])    # CRITICAL: cast from string
            confidence = (
                "strong" if games >= 1000
                else "moderate" if games >= 200
                else "weak"
            )
            buckets.append(TimingBucket(
                time=bucket["time"],
                games=games,
                wins=wins,
                confidence=confidence,
            ))
        if row.hero_id not in new_timing_benchmarks:
            new_timing_benchmarks[row.hero_id] = {}
        new_timing_benchmarks[row.hero_id][row.item_name] = buckets

# -- Atomic swap: ALL references at once --
self._heroes = new_heroes
self._items = new_items
self._hero_name_to_id = new_hero_name_to_id
self._hero_internal_name_to_id = new_hero_internal_to_id  # NEW
self._item_name_to_id = new_item_name_to_id
self._hero_abilities = new_hero_abilities                  # NEW
self._timing_benchmarks = new_timing_benchmarks            # NEW
self._initialized = True
```

### System Prompt v4.0 Directive Additions

```python
# New sections to APPEND to existing SYSTEM_PROMPT constant.
# These are DIRECTIVES only -- no data, no examples with timing numbers.

"""
## Timing Benchmarks
If an "Item Timing Benchmarks" section is present in the context:
- Reference timing windows when explaining item urgency. "BKB is core AND time-sensitive --
  win rate drops sharply after the benchmark window."
- Differentiate urgent items (steep win rate falloff) from flexible items (flat curve).
- If the player's lane was lost, acknowledge that timing windows shift later.
  Still recommend the item, but adjust expectations.
- Never state exact minute targets as deadlines. Use the benchmark as context, not a countdown.

## Counter-Item Specificity
If an "Enemy Ability Threats" section is present in the context:
- Name the specific enemy ability being countered, not just the hero.
  GOOD: "Eul's interrupts Witch Doctor's Death Ward (channeled, 5s duration)."
  BAD: "Eul's is good against Witch Doctor."
- Distinguish BKB-piercing abilities from non-piercing. If an ability pierces BKB,
  do NOT recommend BKB as a counter for that specific ability.

## Win Condition Framing
If a "Team Strategy" section is present in the context:
- Frame overall_strategy around the team's win condition, not just enemy counters.
- Connect item timing to strategy: "Your team peaks mid-game -- completing BKB before
  the power window lets you frontline during your strongest timing."
- If the enemy team outscales, recommend items that enable early aggression.

## Build Path Awareness
When recommending items with expensive components:
- Note which component provides immediate lane/combat value.
- For BKB: "Ogre Axe first for HP if you're dying to burst; Mithril Hammer first if farming."
- For items with cheap utility components (Blight Stone in Desolator), mention the lane value.
"""
```

### Timing Data Stale-While-Revalidate Service

```python
# data/matchup_service.py already has this exact pattern.
# The timing data service follows the same structure but queries by hero_id
# and fetches all items in one call.

async def get_or_fetch_hero_timings(
    hero_id: int,
    db: AsyncSession,
    client: OpenDotaClient,
    cache: DataCache,
) -> dict[str, list[TimingBucket]]:
    """Get timing benchmarks for a hero. Stale-while-revalidate pattern.

    Returns dict of {item_name: [TimingBucket, ...]} from DataCache.
    If not in cache/DB, fetches from OpenDota and populates both.
    """
    # 1. Check DataCache first (zero DB, instant)
    cached = cache.get_hero_timings(hero_id)
    if cached is not None:
        # Check DB staleness for background refresh
        # ... (same pattern as matchup_service)
        return cached

    # 2. Check DB
    # 3. If stale: return + background refresh
    # 4. If missing: await first fetch
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Claude API `system` as plain string | System message as list of content blocks with `cache_control` | 2024 (Anthropic prompt caching GA) | Haiku 4.5 requires 4,096 token minimum for caching. Current prompt is ~1000 tokens -- too small to cache. Not a problem: system prompt cost is negligible at this size. |
| OpenDota hero-ID-based counter rules | Ability-property-based queries | Phase 19/20 (v4.0) | Dynamic counter-item logic that auto-adapts to hero reworks |

## Open Questions

1. **ItemTimingData: One row per hero or one row per hero+item?**
   - What we know: Decision D-02 says "JSON column for the raw response." The API returns all items for a hero in one call. Research STACK.md proposes one row per hero+item pair.
   - What's unclear: Whether to store one row per hero (all items in one JSON blob, ~3-5KB) or one row per hero+item pair (7 timing buckets per row, ~200 bytes each, ~2800 total rows for full coverage).
   - Recommendation: One row per hero with all item timings in a single JSON blob. This matches the "one API call = one DB write" pattern and simplifies stale-while-revalidate (check one row's updated_at, not N rows). The JSON blob is small (~5KB per hero). DataCache can parse it into the nested dict structure at load time.

2. **Ability data in DB vs. memory-only?**
   - What we know: Decision D-03 says ability data refreshes daily via APScheduler. Decision D-04 says loaded into DataCache at startup.
   - What's unclear: Whether to persist ability data in SQLite or only hold it in memory.
   - Recommendation: Persist in SQLite (`HeroAbilityData` table). This matches the hero/item pattern and handles the cold-start case: if OpenDota is down at startup, the app still loads ability data from the last successful fetch. The table is tiny (one row per hero, ~130 rows, ~2KB per row = ~260KB total).

3. **How to handle abilities not in `/constants/abilities`?**
   - What we know: Some ability keys from `/constants/hero_abilities` may not have entries in `/constants/abilities` (deprecated abilities, hidden abilities, generic slots).
   - Recommendation: Skip ability keys that don't exist in the abilities dict during processing. Log a debug message but don't fail. This gracefully handles new heroes or reworked abilities that are temporarily inconsistent.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | None (uses defaults, tests in `prismlab/backend/tests/`) |
| Quick run command | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| Full suite command | `cd prismlab/backend && python -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | Fetch + cache ability metadata (behavior, dmg_type, bkbpierce, dispellable) | unit | `python -m pytest tests/test_cache.py::test_ability_cache_load -x` | Wave 0 |
| DATA-01 | AbilityCached has is_channeled, is_passive properties | unit | `python -m pytest tests/test_cache.py::test_ability_cached_properties -x` | Wave 0 |
| DATA-02 | Hero-to-ability mapping resolves via internal_name | unit | `python -m pytest tests/test_cache.py::test_hero_ability_mapping -x` | Wave 0 |
| DATA-02 | get_hero_abilities returns abilities for hero_id | unit | `python -m pytest tests/test_cache.py::test_get_hero_abilities -x` | Wave 0 |
| DATA-03 | Timing data fetched and parsed (games/wins as ints) | unit | `python -m pytest tests/test_cache.py::test_timing_bucket_parsing -x` | Wave 0 |
| DATA-03 | Timing confidence classification (strong/moderate/weak) | unit | `python -m pytest tests/test_cache.py::test_timing_confidence_levels -x` | Wave 0 |
| DATA-03 | Stale-while-revalidate returns cached timing data | unit | `python -m pytest tests/test_matchup_service.py::test_timing_stale_while_revalidate -x` | Wave 0 |
| DATA-04 | System prompt under 5000 tokens | unit | `python -m pytest tests/test_system_prompt.py::test_token_budget -x` | Wave 0 |
| DATA-04 | System prompt contains no dynamic data (no numbers, no hero-specific text) | unit | `python -m pytest tests/test_system_prompt.py::test_no_dynamic_data -x` | Wave 0 |
| Coherence | DataCache atomic swap includes abilities + timings | integration | `python -m pytest tests/test_cache.py::test_atomic_swap_coherence -x` | Wave 0 |
| Coherence | ResponseCache cleared after refresh | integration | `python -m pytest tests/test_cache.py::test_refresh_clears_response_cache -x` | Exists (test_response_cache.py) |

### Sampling Rate
- **Per task commit:** `cd prismlab/backend && python -m pytest tests/ -x -q`
- **Per wave merge:** `cd prismlab/backend && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_cache.py` -- new file for DataCache extension tests (ability loading, timing parsing, atomic swap, lookup methods)
- [ ] `tests/test_system_prompt.py` -- new file for token budget and no-dynamic-data assertions
- [ ] Extend `tests/conftest.py` -- add test HeroAbilityData and ItemTimingData rows to test DB fixture

## Sources

### Primary (HIGH confidence)
- OpenDota `/constants/abilities` endpoint -- verified live with Enigma Black Hole, CM Freezing Field, WD Death Ward, AM Mana Break
- OpenDota `/constants/hero_abilities` endpoint -- verified live with Anti-Mage ability list
- OpenDota `/scenarios/itemTimings` endpoint -- verified live with Anti-Mage Battle Fury timing data
- Direct codebase analysis: cache.py, opendota_client.py, matchup_service.py, models.py, refresh.py, seed.py, system_prompt.py, context_builder.py, llm.py, main.py, schemas.py, conftest.py
- [Anthropic Prompt Caching Documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) -- Haiku 4.5: 4,096 token minimum, 5-min default TTL, cache_control markers required

### Secondary (MEDIUM confidence)
- [go-opendota package](https://pkg.go.dev/github.com/jasonodonnell/go-opendota) -- confirms games/wins as string fields in ItemTimings struct
- [OpenDota rate limit blog](https://blog.opendota.com/2018/04/17/changes-to-the-api/) -- 50,000 calls/month, 60 req/min

### Tertiary (LOW confidence)
- Token count estimation for system prompt (~900-1000 tokens based on character count / 4 ratio) -- should be verified with `anthropic.count_tokens()` or the tokenizer during implementation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new packages, all patterns proven in v1-v3
- Architecture: HIGH -- extends existing DataCache/refresh/matchup_service patterns exactly
- Pitfalls: HIGH -- games/wins string type confirmed from live API testing and go-opendota struct; behavior field inconsistency verified from live examples; prompt token threshold confirmed from Anthropic docs

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable -- OpenDota API and Anthropic SDK are mature)

# Stack Research: v4.0 Coaching Intelligence

**Project:** Prismlab v4.0
**Researched:** 2026-03-27
**Confidence:** HIGH
**Scope:** Stack ADDITIONS/CHANGES only for v4.0 features. Existing validated stack (React 19, Vite 8, Tailwind v4, Zustand 5, FastAPI, SQLAlchemy, SQLite, Claude API, httpx, APScheduler, DataCache singleton, WebSocket/GSI) is NOT re-evaluated.

---

## What v4.0 Needs (Feature-to-Data Mapping)

| Feature | Data Required | Source | New API Calls |
|---------|--------------|--------|---------------|
| Timing benchmarks | Per-hero item purchase time + win rate at each timing bucket | OpenDota `/scenarios/itemTimings` | Yes -- new endpoint |
| Counter-item depth | Hero ability metadata (behavior, bkbpierce, dispellable, dmg_type, channeled) | OpenDota `/constants/abilities` + `/constants/hero_abilities` | Yes -- new endpoints |
| Build path intelligence | Item component trees (which sub-items build into which final items) | OpenDota `/constants/items` (already fetched) | No -- data already in Item.components |
| Win condition framing | Hero roles + ability properties + team damage type composition | Combination of existing hero data + new ability data | No new endpoint -- derived from above |

---

## Recommended Stack Changes

### New OpenDota API Endpoints (extend existing `OpenDotaClient`)

No new pip packages needed. The existing `httpx.AsyncClient` in `opendota_client.py` handles all new endpoints.

#### 1. Item Timings: `GET /scenarios/itemTimings`

**Verified working** -- tested directly against `https://api.opendota.com/api/scenarios/itemTimings?hero_id=1&item=bfury`.

**Response structure (confirmed):**
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

**Key facts:**
- `time` is in seconds (450 = 7:30, 900 = 15:00, 1200 = 20:00)
- `games` and `wins` are strings (must parse to int)
- Time buckets are fixed: 450, 600, 720, 900, 1200, 1500, 1800 seconds
- Returns data for ~59 items per hero (tested with Anti-Mage), ~195 total rows
- Can query by `hero_id` alone (returns all items for that hero) or by `hero_id` + `item` (returns one item's timing data)
- Win rate at each timing = `int(wins) / int(games)` -- earlier completion generally means higher win rate

**Integration:** Add `fetch_item_timings(hero_id: int, item: str | None = None)` to `OpenDotaClient`. Cache in a new `HeroItemTimings` SQLite table. Load into DataCache at startup as `timing_benchmarks: dict[int, dict[str, list[TimingBucket]]]` keyed by `{hero_id: {item_name: [buckets]}}`.

**Confidence:** HIGH -- endpoint verified live, response schema confirmed, data structure understood.

#### 2. Hero Abilities: `GET /constants/hero_abilities`

**Verified working** -- tested directly against `https://api.opendota.com/api/constants/hero_abilities`.

**Response structure (confirmed):**
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
      {"name": "special_bonus_hp_regen_3", "level": 1},
      {"name": "special_bonus_unique_antimage_manavoid_aoe", "level": 1}
    ],
    "facets": [
      {"id": 0, "name": "antimage_magebanes_mirror", "deprecated": "true", "title": "Magebane's Mirror", "description": "..."}
    ]
  }
}
```

**Key facts:**
- Maps hero internal names to their ability key list
- `generic_hidden` entries are placeholder slots (skip these)
- Includes talents and facets (facets may have `"deprecated": "true"`)
- This is a constants endpoint -- data changes only on Dota 2 patches, not between matches

**Integration:** Add `fetch_hero_abilities()` to `OpenDotaClient`. Fetch once during daily refresh pipeline. Store in DataCache as `hero_abilities: dict[int, list[str]]` (hero_id to ability key list). No SQLite table needed -- this is static constants data that fits in the abilities cache.

**Confidence:** HIGH -- endpoint verified live, response schema confirmed.

#### 3. Ability Details: `GET /constants/abilities`

**Verified working** -- tested directly against `https://api.opendota.com/api/constants/abilities`.

**Response structure (confirmed, showing Anti-Mage Mana Break):**
```json
{
  "antimage_mana_break": {
    "dname": "Mana Break",
    "behavior": "Passive",
    "dmg_type": "Physical",
    "bkbpierce": "No",
    "dispellable": null,
    "desc": "Burns an opponent's mana on each attack...",
    "attrib": [
      {"key": "mana_per_hit", "header": "MANA BURNED PER HIT:", "value": ["25","30","35","40"]},
      {"key": "percent_damage_per_burn", "header": "MANA BURNED AS DAMAGE:", "value": "50"}
    ],
    "mc": null,
    "cd": null,
    "lore": "A modified technique of the Turstarkuri monks'...",
    "img": "/apps/dota2/images/dota_react/abilities/antimage_mana_break.png"
  }
}
```

**Counter-item relevant fields (confirmed by testing actual abilities):**

| Field | Values | Counter-Item Use |
|-------|--------|-----------------|
| `behavior` | `"Passive"`, `"Channeled"`, `["No Target", "Channeled"]`, `["Unit Target", "Channeled"]`, etc. | Channeled = Eul's/stuns interrupt. Passive = Silver Edge Break. |
| `bkbpierce` | `"Yes"` / `"No"` | Determines if BKB counters this ability |
| `dispellable` | `"Yes"` / `"No"` / `"Strong Dispels Only"` / `null` | Manta/Lotus/Eul's self-dispel viability |
| `dmg_type` | `"Magical"` / `"Physical"` / `"Pure"` | BKB/Pipe/armor item decisions |

**Verified examples of counter-item-relevant abilities:**
- `enigma_black_hole`: behavior `["AOE","Point Target","Channeled"]`, bkbpierce `"Yes"` -- BKB does NOT save you, need positioning items
- `crystal_maiden_freezing_field`: behavior `["No Target","Channeled"]`, bkbpierce `"No"` -- BKB + interrupts counter
- `witch_doctor_death_ward`: behavior `["Point Target","Channeled"]`, bkbpierce `"Yes"` -- stuns/Eul's interrupt
- `pugna_life_drain`: behavior `["Unit Target","Channeled"]`, bkbpierce `"No"` -- BKB breaks drain
- `huskar_berserkers_blood`: behavior `"Passive"` -- Silver Edge Break counters

**Integration:** Add `fetch_abilities()` to `OpenDotaClient`. Fetch once during daily refresh. Store in DataCache as `abilities: dict[str, AbilityCached]` keyed by ability internal name. The `AbilityCached` frozen dataclass extracts only the fields needed for counter-item logic (dname, behavior, bkbpierce, dispellable, dmg_type) -- not the full 7-field attrib arrays or lore text.

**Confidence:** HIGH -- endpoint verified live, all counter-item-relevant fields confirmed present and populated for real hero abilities.

---

### New Data Models (extend existing `data/models.py`)

No new pip packages. Uses existing SQLAlchemy + Pydantic.

#### 1. `HeroItemTimings` SQLite Table

```python
class HeroItemTimings(Base):
    """Cached item timing benchmark data per hero from OpenDota scenarios."""
    __tablename__ = "hero_item_timings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(Integer, ForeignKey("heroes.id"))
    item_internal_name: Mapped[str] = mapped_column(String, nullable=False)
    timing_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # timing_data structure: [{"time": 900, "games": 277, "wins": 175}, ...]
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
```

**Why a DB table (not just cache):** Item timing data is per-hero AND per-item. For 140 heroes x ~20 relevant items each, that is ~2800 API calls to fully populate. Must persist across restarts and refresh incrementally. Same stale-while-revalidate pattern as `HeroItemPopularity`.

**Why one row per hero-item pair with JSON timing data (not one row per timing bucket):** Keeps the table manageable (~2800 rows vs ~19,600) and the JSON blob is small (7 timing buckets per entry, ~200 bytes). The DataCache can parse and index it at load time.

#### 2. `HeroAbilityData` SQLite Table

```python
class HeroAbilityData(Base):
    """Cached hero ability constants from OpenDota."""
    __tablename__ = "hero_ability_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hero_id: Mapped[int] = mapped_column(Integer, ForeignKey("heroes.id"), unique=True)
    abilities_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # abilities_json: {"ability_key": {"dname", "behavior", "bkbpierce", "dispellable", "dmg_type"}, ...}
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=func.now())
```

**Why store per-hero (not a flat abilities table):** The hero_abilities mapping connects hero_id to ability keys, and we need to look up "what abilities does this enemy have?" during recommendation. Storing denormalized per-hero with pre-joined ability details avoids a multi-step lookup. The full abilities constants file is ~500KB of JSON; extracting only the 5 counter-item-relevant fields per ability and storing per-hero keeps each row under 2KB.

---

### New DataCache Entries (extend existing `data/cache.py`)

No new pip packages. Extends the existing `DataCache` singleton with new frozen dataclass types and lookup methods.

#### New Frozen Dataclasses

```python
@dataclass(frozen=True)
class TimingBucket:
    """Single time bucket from OpenDota item timing data."""
    time: int          # seconds since game start
    games: int
    wins: int

    @property
    def win_rate(self) -> float:
        return self.wins / self.games if self.games > 0 else 0.0

@dataclass(frozen=True)
class AbilityCached:
    """Counter-item-relevant fields for a hero ability."""
    key: str              # e.g. "enigma_black_hole"
    dname: str            # e.g. "Black Hole"
    behavior: tuple[str, ...]  # e.g. ("AOE", "Point Target", "Channeled")
    bkbpierce: bool       # True if "Yes"
    dispellable: str | None  # "Yes", "No", "Strong Dispels Only", None
    dmg_type: str | None  # "Magical", "Physical", "Pure", None

    @property
    def is_channeled(self) -> bool:
        return "Channeled" in self.behavior

    @property
    def is_passive(self) -> bool:
        return "Passive" in self.behavior
```

#### New Cache Dictionaries

```python
# In DataCache.__init__:
self._timing_benchmarks: dict[int, dict[str, list[TimingBucket]]] = {}
# {hero_id: {item_internal_name: [TimingBucket(time=900, games=277, wins=175), ...]}}

self._hero_abilities: dict[int, list[AbilityCached]] = {}
# {hero_id: [AbilityCached(key="enigma_black_hole", dname="Black Hole", ...), ...]}
```

#### New Lookup Methods

```python
def get_timing_benchmarks(self, hero_id: int, item_name: str) -> list[TimingBucket] | None:
    """Get timing benchmark data for a hero-item pair."""
    hero_timings = self._timing_benchmarks.get(hero_id)
    if hero_timings is None:
        return None
    return hero_timings.get(item_name)

def get_hero_abilities(self, hero_id: int) -> list[AbilityCached]:
    """Get all abilities for a hero. Returns empty list if not found."""
    return self._hero_abilities.get(hero_id, [])

def has_channeled_ability(self, hero_id: int) -> bool:
    """Check if a hero has any channeled ability."""
    return any(a.is_channeled for a in self.get_hero_abilities(hero_id))

def has_passive_ability(self, hero_id: int) -> bool:
    """Check if a hero has any important passive ability."""
    return any(a.is_passive for a in self.get_hero_abilities(hero_id))

def get_abilities_by_property(self, hero_id: int, bkbpierce: bool | None = None,
                               channeled: bool | None = None, dispellable: str | None = None
                               ) -> list[AbilityCached]:
    """Filter hero abilities by counter-item-relevant properties."""
    abilities = self.get_hero_abilities(hero_id)
    result = abilities
    if bkbpierce is not None:
        result = [a for a in result if a.bkbpierce == bkbpierce]
    if channeled is not None:
        result = [a for a in result if a.is_channeled == channeled]
    if dispellable is not None:
        result = [a for a in result if a.dispellable == dispellable]
    return result
```

**Memory impact:** ~140 heroes x ~4 abilities each x ~100 bytes per AbilityCached = ~56KB. Timing data for top ~20 items per hero x 7 buckets x ~30 bytes = ~600KB. Total new cache: under 1MB. Negligible.

**Confidence:** HIGH -- extends proven DataCache pattern. Frozen dataclasses match existing `HeroCached`/`ItemCached` patterns.

---

### Build Path Intelligence (NO new data source -- derive from existing)

The `Item.components` field already stores the component tree for every item. Verified:
- `bfury` components: `["pers", "broadsword", "broadsword", "quelling_blade"]`
- `manta` components: `["yasha", "diadem"]`
- `desolator` components: `["mithril_hammer", "mithril_hammer", "blight_stone"]`

**What's needed:** A `get_build_path(item_internal_name: str)` method on DataCache that recursively resolves component trees into a flat ordered purchase list with costs. This is pure computation over existing cached data.

```python
def get_build_path(self, item_internal_name: str) -> list[tuple[str, int]]:
    """Recursively resolve an item's component tree into purchase order.

    Returns list of (component_internal_name, cost) tuples from cheapest to most expensive,
    representing the order a player should buy components.
    """
    # Implementation: BFS over components, skip recipes, sort by cost ascending
```

**No new API calls, no new tables, no new dependencies.** The component data is already fetched in `refresh.py` and stored in `Item.components`. It is already in `ItemCached.components` in the DataCache.

**Confidence:** HIGH -- data already available, verified against live API.

---

### Win Condition Framing (NO new dependencies -- logic layer only)

Win condition classification is a rules-based categorization system, not a data mining task. It uses:

1. **Hero roles** (already in `HeroCached.roles`): "Carry", "Pusher", "Initiator", "Ganker", etc.
2. **Hero ability properties** (new from abilities data): channeled ults, global abilities, summons
3. **Team damage type composition** (derived from hero primary attributes + ability `dmg_type`): physical-heavy vs magic-heavy
4. **Draft timing curves** (derived from hero roles): early-game vs late-game lineup

**Win condition categories** (static classification, not mined):

| Strategy | Detection Heuristic | Item Build Implication |
|----------|--------------------|-----------------------|
| 4-protect-1 | 1 hard carry (Pos 1) + 3-4 heroes with "Support"/"Disabler" roles | Pos 1 gets greedy farming items; supports get save items |
| Deathball/Push | 2+ heroes with "Pusher" role, strong early-game heroes | Aura items (Mek, Pipe, AC), early fight items |
| Split-push | 1+ heroes with high mobility + tower damage (AM, NP, Lone Druid) | TP/BoT, escape items, farming items |
| Teamfight/5v5 | 2+ heroes with AoE channeled ults or big teamfight abilities | BKB priority, Refresher candidates, positioning items |
| Pick-off/Gank | 2+ heroes with "Ganker" role or targeted lockdown chains | Smoke, Blink, Orchid, mobility items |

**Implementation:** A `WinConditionClassifier` class that takes the 5 allied heroes (including player) and 5 enemy heroes, analyzes their roles and abilities, and returns a primary + secondary strategy classification. This feeds into the Claude system prompt as context, not as a deterministic recommendation.

**No new pip packages, no new API calls.** This is pure domain logic over cached data.

**Confidence:** HIGH -- classification logic is well-understood in Dota 2 theory. Implementation is deterministic rules, not ML.

---

### Rules Engine Expansion (extend existing `engine/rules.py`)

The current RulesEngine has 18 rules based on hardcoded hero ID sets. The v4.0 counter-item rules will be **ability-driven** instead of hero-ID-driven, using the new `AbilityCached` data.

**Example: Current approach (brittle):**
```python
# Current: hardcoded hero IDs for "channeled ult" heroes
channeled_heroes = self._hero_ids("Witch Doctor", "Crystal Maiden", "Enigma", "Pugna")
```

**New approach (ability-data-driven):**
```python
# New: query DataCache for any hero with channeled abilities
def _has_channeled_threat(self, opponent_id: int) -> tuple[bool, str]:
    abilities = self.cache.get_abilities_by_property(opponent_id, channeled=True)
    if abilities:
        return True, abilities[0].dname  # e.g. "Black Hole"
    return False, ""
```

This eliminates the need to maintain hero ID lists and automatically handles new heroes added to Dota 2.

**New ability-driven rules to add:**

| Rule | Trigger | Recommendation | Phase |
|------|---------|---------------|-------|
| Eul's vs Channeled | Enemy has channeled ability (not BKB-piercing) | Eul's Scepter | core |
| BKB urgency | 3+ enemy abilities with `dmg_type: "Magical"` and `bkbpierce: "No"` | BKB (upgrade from situational to core) | core |
| Manta/Lotus vs Dispellable | Enemy has dispellable debuffs (`dispellable: "Yes"`) | Manta Style (cores) / Lotus Orb (offlaners) | core |
| Spirit Vessel vs Heal/Regen | Enemy has heal/regen abilities (detected by desc keywords or known ability keys) | Spirit Vessel | core |
| Break vs Passive | Enemy has critical passive abilities | Silver Edge | core |

**No new pip packages.** Extends existing `RulesEngine` class and its `DataCache` dependency.

**Confidence:** HIGH -- extends proven rules engine pattern. Ability data verified to contain all needed fields.

---

### Context Builder Expansion (extend existing `engine/context_builder.py`)

The context builder needs new sections in the Claude prompt for:

1. **Timing benchmark context**: "Battle Fury timing benchmark: 63% win rate at 15:00, 40% at 20:00 -- you need it by minute 15"
2. **Enemy ability threats**: "Enigma has Black Hole (Channeled, BKB-piercing) -- positioning items critical"
3. **Build path guidance**: "Desolator build path: Blight Stone (300g, lane value) -> Mithril Hammer -> Mithril Hammer"
4. **Win condition frame**: "Enemy draft is 4-protect-1 around Medusa. Win condition: end before minute 35 or itemize to burst through"

These are string-building additions to `ContextBuilder.build()`. No new packages.

**Confidence:** HIGH -- extends existing context builder pattern.

---

### System Prompt Updates (extend existing `engine/prompts/system_prompt.py`)

New sections to add to `SYSTEM_PROMPT`:

1. **Timing urgency rules**: "If timing benchmark data is provided, reference the win rate cliff. Items purchased after the benchmark drop below 50% win rate -- flag as URGENT if player is behind."
2. **Ability-aware counters**: "If enemy ability data is provided, name the specific ability being countered. 'Eul's interrupts Witch Doctor's Death Ward' not 'Eul's is good vs WD'."
3. **Build path ordering**: "When recommending items with multiple components, specify purchase order by lane value. Components that provide immediate combat stats should be bought first."
4. **Win condition framing**: "If team composition analysis is provided, frame all item recommendations around the identified win condition. A deathball strategy prioritizes team aura items over personal farming items."

No new packages. String constant modifications.

**Confidence:** HIGH -- extends existing prompt engineering.

---

### Refresh Pipeline Updates (extend existing `data/refresh.py`)

New data to fetch during the daily refresh cycle:

1. **Abilities constants** (`/constants/abilities` + `/constants/hero_abilities`): Fetch once per refresh, ~1 second each. Static constants data.
2. **Item timings** (`/scenarios/itemTimings?hero_id=X`): Fetch per hero, ~140 calls. At 60 req/min rate limit, this takes ~2.5 minutes.

**Rate limit concern:** OpenDota free tier is 60 req/min, 50,000 calls/month. The current refresh pipeline fetches heroes + items (2 calls). Adding 140 hero timing calls + 2 ability constants calls = 144 new calls per refresh. At 24h refresh interval, that is 144 x 30 = 4,320 calls/month for timings. Well within the 50,000 monthly budget.

**Implementation:** Add a `_refresh_timings()` coroutine to `refresh.py` that fetches all hero timing data with `asyncio.Semaphore(2)` to limit concurrency and `asyncio.sleep(1.0)` between batches to respect rate limits. Same error handling pattern as existing refresh.

**Confidence:** HIGH -- rate limits verified, endpoint confirmed working.

---

## Recommended Stack (Complete v4.0 Delta)

### New Backend Code (NO new pip packages)

| Component | Type | Purpose | Integration Point |
|-----------|------|---------|-------------------|
| `OpenDotaClient.fetch_item_timings()` | Method | Fetch timing benchmark data | `opendota_client.py` |
| `OpenDotaClient.fetch_abilities()` | Method | Fetch ability constants | `opendota_client.py` |
| `OpenDotaClient.fetch_hero_abilities()` | Method | Fetch hero-to-ability mapping | `opendota_client.py` |
| `HeroItemTimings` model | SQLAlchemy table | Persist timing data across restarts | `models.py` |
| `HeroAbilityData` model | SQLAlchemy table | Persist ability data across restarts | `models.py` |
| `TimingBucket` dataclass | Frozen dataclass | In-memory timing data | `cache.py` |
| `AbilityCached` dataclass | Frozen dataclass | In-memory ability data | `cache.py` |
| `DataCache` timing/ability methods | Methods | Zero-DB lookups for new data | `cache.py` |
| `WinConditionClassifier` class | New module | Team composition classification | `engine/win_conditions.py` |
| Timing-aware rules | Rule methods | Urgency signals from timing data | `rules.py` |
| Ability-driven counter rules | Rule methods | Data-driven counter-item logic | `rules.py` |
| Timing/ability context sections | Builder methods | New prompt sections | `context_builder.py` |
| Timing/ability refresh tasks | Coroutines | Daily data pipeline expansion | `refresh.py` |

### New Frontend Code (NO new npm packages)

| Component | Type | Purpose | Integration Point |
|-----------|------|---------|-------------------|
| Timing benchmark display | React component | Show "buy by X:XX" urgency indicators | Item recommendation cards |
| Build path visualization | React component | Show component purchase order | Item recommendation cards |
| Win condition banner | React component | Show team strategy classification | Overall strategy section |

---

## What NOT to Add

| Tempting Addition | Why Not |
|-------------------|---------|
| `pandas` / `numpy` for timing data analysis | The timing data is 7 buckets per hero-item pair. Basic arithmetic (win_rate = wins/games) is trivially done with Python builtins. Adding 30MB+ of scientific computing packages for division is absurd. |
| `scikit-learn` for win condition classification | Win condition classification is a rules-based lookup (hero roles, ability properties), not a machine learning problem. A 50-line classifier function is correct; an ML pipeline is overkill for categorizing 5 heroes into 5 strategy archetypes. |
| `networkx` for build path graph traversal | Item component trees are at most 3 levels deep with 2-4 children per node. A recursive function handles this. A graph library adds dependency for what is essentially nested list traversal. |
| Stratz API integration | Stratz GraphQL API provides richer data (farm breakdowns, ward placement, replay parsing) but requires a separate auth token, adds API surface, and the OpenDota endpoints provide all data needed for v4.0 timing benchmarks and ability metadata. Stratz is a v5.0+ consideration if we need replay-level analytics. |
| `aiohttp` to replace `httpx` | The project uses `httpx.AsyncClient` throughout. Switching to `aiohttp` for the 144 new API calls in the refresh pipeline adds a second HTTP client dependency for negligible performance difference at this call volume. |
| `pydantic-ai` or LangChain | The Claude API integration is 50 lines of direct Anthropic SDK usage with prompt engineering. Adding an orchestration framework adds abstraction for a single-LLM, single-prompt-template system with no agentic behavior. |
| Redis / Memcached for timing cache | Same rationale as v3.0: single-process uvicorn, all data fits in <2MB of memory, atomic swap on refresh. An external cache adds Docker container overhead for no benefit. |
| `dotaconstants` npm package on frontend | The ability data and timing benchmarks are consumed by the backend rules engine and context builder, not displayed directly in the frontend. The frontend receives processed recommendations -- it does not need raw ability data. |
| `cron` / `celery` for background timing refresh | APScheduler is already handling the 24h refresh cycle. Adding Celery requires Redis/RabbitMQ as a broker. APScheduler can run the expanded timing refresh as part of the existing job. |

---

## Installation

```bash
# Backend -- NO new pip packages
# All new functionality uses existing: httpx, sqlalchemy, pydantic, anthropic

# Frontend -- NO new npm packages
# All new UI components use existing: React 19, Tailwind v4, Zustand 5
```

**Total new dependencies: ZERO.** Zero pip packages. Zero npm packages. This milestone is entirely about new application code using existing infrastructure.

---

## Alternatives Considered

| Category | Recommended | Alternative | When to Use Alternative |
|----------|-------------|-------------|-------------------------|
| Timing data source | OpenDota `/scenarios/itemTimings` | Stratz GraphQL `heroStats.itemTimings` | If OpenDota deprecates the scenarios endpoint or rate limits become restrictive. Stratz has a free tier with 500 calls/day. |
| Ability data source | OpenDota `/constants/abilities` + `/constants/hero_abilities` | Manually curated JSON file | If OpenDota constants become stale (they mirror dotaconstants repo which updates per patch). A manual file would be needed if OpenDota goes down permanently, but this is unlikely. |
| Ability data storage | SQLite table + DataCache frozen dataclass | Pure in-memory (no SQLite) | Ability data is static constants (~changes per Dota patch). Could skip SQLite and fetch from OpenDota on every startup. SQLite persistence avoids the startup API dependency and handles offline/rate-limited scenarios. |
| Win condition classifier | Deterministic rules (hero roles + ability properties) | LLM-based classification (ask Claude to classify the draft) | If the rules-based classifier misses nuanced draft interactions. Could add an LLM fallback for edge cases, but the 5 strategy archetypes are well-defined enough for rules. |
| Timing benchmark refresh | Per-hero serial fetch with rate limiting | Batch all heroes in parallel with high concurrency | If the app needs sub-minute freshness. Current 24h refresh is fine; OpenDota rate limits (60/min) make high concurrency risky. |

---

## Version Compatibility Matrix

| Package | Version | Compatible With | Verified |
|---------|---------|----------------|----------|
| httpx | 0.28.1 (current) | OpenDota `/scenarios/itemTimings`, `/constants/abilities`, `/constants/hero_abilities` | Yes -- all three endpoints tested live |
| SQLAlchemy | 2.0.48 (current) | New `HeroItemTimings` and `HeroAbilityData` models | Yes -- same patterns as existing `HeroItemPopularity` and `MatchupData` |
| Pydantic | 2.12.5 (current) | New `TimingBucket` and `AbilityCached` dataclasses | Yes -- frozen dataclasses use stdlib, not Pydantic |
| anthropic | 0.86.0 (current) | Extended system prompt with timing/ability/win-condition sections | Yes -- prompt content changes, not API changes |
| APScheduler | 3.11.0 (current) | Expanded refresh pipeline (144 additional API calls) | Yes -- same job scheduling, longer execution time |

---

## API Rate Limit Budget

| Refresh Task | Calls per Refresh | Frequency | Monthly Total |
|-------------|-------------------|-----------|---------------|
| Heroes constants | 1 | Daily | 30 |
| Items constants | 1 | Daily | 30 |
| Matchup data (on-demand) | ~20 per recommendation | Per request | Variable |
| Item popularity (on-demand) | ~6 per recommendation | Per request | Variable |
| **NEW: Abilities constants** | 2 | Daily | 60 |
| **NEW: Item timings (all heroes)** | 140 | Daily | 4,200 |
| **Total scheduled** | 144 | Daily | ~4,320 |

Free tier budget: 50,000 calls/month. Scheduled calls use ~4,320/month (8.6%). On-demand matchup/popularity calls use the remaining budget based on usage. Comfortable margin.

---

## Sources

- [OpenDota API Documentation](https://docs.opendota.com/) -- HIGH confidence. Canonical API reference for all endpoints.
- [OpenDota `/scenarios/itemTimings` endpoint](https://api.opendota.com/api/scenarios/itemTimings?hero_id=1&item=bfury) -- HIGH confidence. Verified live, response schema confirmed with actual data.
- [OpenDota `/constants/hero_abilities` endpoint](https://api.opendota.com/api/constants/hero_abilities) -- HIGH confidence. Verified live, response schema confirmed.
- [OpenDota `/constants/abilities` endpoint](https://api.opendota.com/api/constants/abilities) -- HIGH confidence. Verified live with specific ability examples (Black Hole, Death Ward, Freezing Field, etc.).
- [dotaconstants repository](https://github.com/odota/dotaconstants) -- HIGH confidence. Source data for OpenDota constants endpoints. Contains `build/abilities.json` and `build/hero_abilities.json`.
- [go-opendota ItemTimings struct](https://pkg.go.dev/github.com/jasonodonnell/go-opendota) -- MEDIUM confidence. Third-party Go client that documents the ItemTimings response fields (hero_id, item, time, games, wins).
- [OpenDota API rate limits](https://blog.opendota.com/2018/04/17/changes-to-the-api/) -- MEDIUM confidence. Blog post from 2018 confirming 50,000 free calls/month and 60 req/min. Rate limits verified still active by testing.
- [Stratz API](https://stratz.com/api) -- MEDIUM confidence. Confirmed GraphQL API with hero stats and item timings, but not needed for v4.0 scope.

---
*Stack research for: Prismlab v4.0 Coaching Intelligence*
*Researched: 2026-03-27*

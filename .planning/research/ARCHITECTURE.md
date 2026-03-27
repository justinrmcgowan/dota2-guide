# Architecture Patterns

**Domain:** Dota 2 item advisor -- v4.0 coaching intelligence integration
**Researched:** 2026-03-27
**Scope:** Timing benchmarks, counter-item depth, build path ordering, win condition framing -- integration with existing DataCache/RulesEngine/ContextBuilder/SystemPrompt
**Confidence:** HIGH -- based on direct reading of all backend source files and OpenDota API research

---

## 1. Current Architecture Snapshot (v3.0 Baseline)

### Backend Component Graph

```
Request flow (per /api/recommend call):

  RecommendRequest
       |
       v
  ResponseCache.get() --hit--> return cached
       |miss
       v
  RulesEngine.evaluate(request)         <-- DataCache (sync dict reads)
       |
       | rules_items: list[RuleResult]
       v
  ContextBuilder.build(request, rules_items, db)
       |                                <-- DataCache (hero/item lookups)
       |                                <-- matchup_service (DB + OpenDota API)
       |                                <-- hero_item_popularity (DB + OpenDota API)
       | user_message: str
       v
  LLMEngine.generate(user_message)
       |                                <-- SYSTEM_PROMPT (static constant)
       | LLMRecommendation | None
       v
  HybridRecommender._merge(rules, llm)
       |
  HybridRecommender._validate_item_ids()  <-- DataCache.get_item_validation_map()
       |
       v
  RecommendResponse --> ResponseCache.set() --> return
```

### Key Singleton Instances (created in recommend.py module scope)

| Instance | Class | Dependencies |
|----------|-------|-------------|
| `_rules` | `RulesEngine` | `data_cache` (DataCache singleton) |
| `_context_builder` | `ContextBuilder` | `_opendota` (OpenDotaClient), `data_cache` |
| `_llm` | `LLMEngine` | `settings.anthropic_api_key` |
| `_response_cache` | `ResponseCache` | None (standalone TTL cache) |
| `_recommender` | `HybridRecommender` | `_rules`, `_llm`, `_context_builder`, `_response_cache`, `data_cache` |

### Data Pipeline

```
APScheduler (6h interval)
       |
  refresh_all_data()
       |
       +-- OpenDota /constants/heroes --> upsert Hero rows
       +-- OpenDota /constants/items  --> upsert Item rows
       |
       v
  data_cache.refresh(session)       <-- atomic swap of hero/item dicts
  _response_cache.clear()           <-- invalidate stale Claude responses
```

### What DataCache Stores Today

| Dict | Key | Value | Lookup Methods |
|------|-----|-------|----------------|
| `_heroes` | hero_id (int) | `HeroCached` (frozen dataclass) | `get_hero()`, `get_all_heroes()`, `hero_id_to_name()` |
| `_items` | item_id (int) | `ItemCached` (frozen dataclass) | `get_item()`, `get_all_items()`, `get_relevant_items()`, `get_neutral_items_by_tier()` |
| `_hero_name_to_id` | localized_name (str) | hero_id (int) | `hero_name_to_id()` |
| `_item_name_to_id` | internal_name (str) | item_id (int) | `item_name_to_id()` |

### What the System Prompt Controls Today

The SYSTEM_PROMPT (system_prompt.py, ~13,326 chars) instructs Claude on:
- Phase-based item budgets (starting, laning <2000g, core 2000-5000g, late_game 5000g+)
- Matchup-specific reasoning requirements (name enemy hero + specific ability)
- Ally coordination (aura dedup, combo awareness)
- Enemy power levels (KDA-based threat assessment)
- Neutral item ranking per tier
- Output JSON schema constraints

### What ContextBuilder Sends Today

Per-request user message sections:
1. `## Your Hero` -- name, role, playstyle, side, lane, primary attr, attack type
2. `## Allied Heroes` -- ally names + typical builds (from popularity data)
3. `## Lane Opponents` -- opponent names + matchup win rates
4. `## Enemy Team Status` -- KDA/level from screenshots (if present)
5. `## Mid-Game Update` -- lane result, damage profile, enemy items spotted
6. `## Already Recommended` -- rules engine output (name + phase + reasoning)
7. `## Available Items` -- id: name (cost) catalog (~40-50 items, role-filtered)
8. `## Popular Items on This Hero` -- phase-grouped top-5 per phase
9. `## Neutral Items Catalog` -- tier-grouped neutral item names

---

## 2. Integration Architecture for v4.0 Features

### 2A. Timing Benchmarks

**Data Source:** OpenDota `/scenarios/itemTimings` endpoint.
- Parameters: `hero_id` (int, optional), `item` (string, optional)
- Response: `[{hero_id, item, time, games, wins}]` -- time in seconds, games/wins as strings
- Each row = "when hero X buys item Y at time T, win rate is W/G"

**New Component: `TimingService`**

```python
# data/timing_service.py (NEW)

class ItemTimingBenchmark:
    """Processed timing data for a hero-item pair."""
    hero_id: int
    item_internal_name: str
    optimal_time_seconds: int     # Time bucket with highest win rate
    win_rate_at_optimal: float    # Win rate at that timing
    games_at_optimal: int         # Sample size
    early_threshold_seconds: int  # "Ahead of schedule" if purchased before this
    late_threshold_seconds: int   # "Behind schedule" if purchased after this

async def get_item_timing(hero_id: int, item: str, db: AsyncSession, client: OpenDotaClient) -> ItemTimingBenchmark | None
async def get_hero_timings(hero_id: int, db: AsyncSession, client: OpenDotaClient) -> list[ItemTimingBenchmark]
```

**Storage: New `item_timing_data` SQLAlchemy model**

```python
class ItemTimingData(Base):
    __tablename__ = "item_timing_data"
    id: int (PK, autoincrement)
    hero_id: int (FK heroes.id)
    item_name: str               # OpenDota item internal name
    timing_data: dict (JSON)     # Raw [{time, games, wins}] from API
    updated_at: datetime
```

**DataCache Integration:** Add a new dict to DataCache:

```python
# New in DataCache
_hero_item_timings: dict[int, dict[str, ItemTimingBenchmark]]  # hero_id -> {item_name -> benchmark}

def get_item_timing(self, hero_id: int, item_name: str) -> ItemTimingBenchmark | None
def get_hero_timings(self, hero_id: int) -> list[ItemTimingBenchmark]
```

**Where It Integrates:**

| Component | Integration Point | What Changes |
|-----------|------------------|--------------|
| `refresh.py` | `refresh_all_data()` | Add step to fetch timing data for common hero-item pairs |
| `DataCache` | `load()` / `refresh()` | Load timing data from DB into new `_hero_item_timings` dict |
| `ContextBuilder` | `build()` | New section `## Item Timing Benchmarks` with optimal times + urgency signals |
| `RulesEngine` | New timing urgency rules | If GSI clock > late_threshold for a core item, flag urgency |
| `SYSTEM_PROMPT` | New instruction block | "Reference timing benchmarks. If an item is late, acknowledge urgency." |
| `RecommendResponse` | No schema change needed | Timing context flows through Claude's reasoning text, not new fields |

**ContextBuilder Addition:**

```python
# New section in build()
timing_section = self._build_timing_section(request.hero_id, relevant_items)

# Produces:
## Item Timing Benchmarks
- Battle Fury: optimal 14-16 min (62.3% WR), late after 20 min
- Power Treads: optimal 4-6 min (55.1% WR), late after 8 min
```

**Why This Approach:**
- Timing data is static per hero-item pair (changes slowly with patches), ideal for DataCache
- OpenDota `/scenarios/itemTimings` provides the exact data needed -- no scraping or aggregation
- Surfacing benchmarks in the Claude context lets Claude reason about timing urgency naturally
- Deterministic urgency rules can fire alongside: "You're at 22 min without BKB -- this is overdue"

---

### 2B. Counter-Item Depth (Ability-Specific)

**Data Source:** OpenDota `/constants/abilities` endpoint via `/constants/hero_abilities` + `/constants/abilities`.
- `hero_abilities`: `{npc_dota_hero_X: {abilities: [ability_names], talents: [...], facets: [...]}}`
- `abilities`: `{ability_name: {dname, behavior, dmg_type, bkbpierce, dispellable, desc, attrib, mc, cd, ...}}`
- Key fields for counter logic: `behavior` (array: "Channeled", "Unit Target", etc.), `bkbpierce`, `dispellable`, `dmg_type`

**New Component: `AbilityData` in DataCache**

```python
# Extend HeroCached or create new frozen dataclass
@dataclass(frozen=True)
class AbilityCached:
    name: str                    # internal name (e.g., "crystal_maiden_freezing_field")
    dname: str                   # display name (e.g., "Freezing Field")
    behavior: tuple[str, ...]    # ("No Target", "Channeled")
    dmg_type: str | None         # "Magical" | "Physical" | "Pure"
    bkbpierce: str | None        # "Yes" | "No"
    dispellable: str | None      # "Yes" | "No" | "Strong Dispels Only"
    is_channeled: bool           # derived from behavior containing "Channeled"
    is_unit_target: bool         # derived from behavior containing "Unit Target"
    cd: tuple[float, ...] | None # cooldown per level

@dataclass(frozen=True)
class HeroAbilitiesCached:
    hero_id: int
    abilities: tuple[AbilityCached, ...]
```

**DataCache Integration:**

```python
# New in DataCache
_hero_abilities: dict[int, HeroAbilitiesCached]  # hero_id -> abilities data
_ability_lookup: dict[str, AbilityCached]          # ability_internal_name -> data

def get_hero_abilities(self, hero_id: int) -> HeroAbilitiesCached | None
def has_channeled_ability(self, hero_id: int) -> bool
def has_dispellable_buff(self, hero_id: int) -> bool
def has_bkb_piercing(self, hero_id: int) -> bool
def get_ability_by_name(self, name: str) -> AbilityCached | None
```

**RulesEngine: New Ability-Aware Rules**

```python
# New rules added to RulesEngine._rules property

def _euls_vs_channeled_rule(self, req: RecommendRequest) -> list[RuleResult]:
    """Eul's Scepter vs heroes with channeled ultimates."""
    # Uses: self.cache.has_channeled_ability(opp_id)
    # Triggers for: Crystal Maiden, Witch Doctor, Enigma, Shadow Shaman, Bane, etc.
    # Does NOT hardcode hero lists -- queries ability data dynamically

def _lotus_orb_vs_single_target_rule(self, req: RecommendRequest) -> list[RuleResult]:
    """Lotus Orb vs heroes with strong single-target spells."""
    # Uses: ability.is_unit_target and ability type checks

def _manta_vs_dispellable_rule(self, req: RecommendRequest) -> list[RuleResult]:
    """Manta Style vs heroes with important dispellable debuffs."""
    # Uses: self.cache ability dispellable field

def _bkb_upgrade_rule(self, req: RecommendRequest) -> list[RuleResult]:
    """Upgrade BKB priority when multiple enemies have non-piercing magic abilities."""
    # Uses: count of non-BKB-piercing high-impact abilities across enemy team
```

**Critical Design Decision: Dynamic vs Hardcoded Hero Lists**

The current RulesEngine hardcodes hero ID sets per rule (e.g., `spammers = self._hero_ids("Phantom Assassin", "Zeus", ...)`). For v4.0 counter-item rules:

**Recommendation: Hybrid approach.**
- KEEP existing hardcoded rules as-is (they work, they're tested, 18 rules)
- NEW ability-aware rules query DataCache ability data dynamically
- Dynamic rules use ability metadata (behavior, bkbpierce, dispellable) not hero name lists
- This means new rules auto-adapt when heroes get reworked -- no manual list updates

**Where It Integrates:**

| Component | Integration Point | What Changes |
|-----------|------------------|--------------|
| `refresh.py` | `refresh_all_data()` | Fetch `/constants/abilities` + `/constants/hero_abilities`, store in DB |
| `models.py` | New model | `HeroAbilityData` table (hero_id, abilities JSON, updated_at) |
| `DataCache` | `load()` / `refresh()` | Build `_hero_abilities` and `_ability_lookup` dicts |
| `opendota_client.py` | New methods | `fetch_abilities()`, `fetch_hero_abilities()` |
| `RulesEngine` | New rule methods | 4-6 ability-aware counter rules using DataCache lookups |
| `ContextBuilder` | New section | `## Enemy Ability Threats` -- channeled ults, BKB-piercing, key dispellable debuffs |
| `SYSTEM_PROMPT` | Expanded instruction | "Reference specific enemy abilities when recommending counter items" |

**ContextBuilder Addition:**

```python
# New section surfacing ability-derived threats
## Enemy Ability Threats
- Crystal Maiden: Freezing Field (Channeled, Magical, No BKB Pierce) -- Eul's interrupts
- Enigma: Black Hole (Channeled, Pure, BKB Pierce) -- cannot be interrupted by BKB
- Lion: Finger of Death (Unit Target, Magical, No BKB Pierce) -- Linken's blocks
```

---

### 2C. Build Path Intelligence

**Problem:** Current system recommends final items but not component ordering. "Buy BKB" doesn't tell the player whether to get Ogre Axe or Mithril Hammer first.

**Data Source:** Already in DataCache -- `ItemCached.components` is a tuple of component internal_names. No new API calls needed.

**New Component: `BuildPathResolver`**

```python
# engine/build_path.py (NEW)

class ComponentStep:
    """A single step in a build path."""
    item_id: int
    item_name: str
    gold_cost: int
    reasoning: str           # Why this component first

class BuildPath:
    """Ordered component purchase sequence for a final item."""
    target_item_id: int
    target_item_name: str
    total_cost: int
    steps: list[ComponentStep]

class BuildPathResolver:
    """Resolves item recommendations into component-level purchase sequences."""

    def __init__(self, cache: DataCache):
        self.cache = cache

    def resolve(self, item_id: int, context: BuildPathContext) -> BuildPath | None:
        """Given a final item, return ordered component steps.

        Ordering heuristics:
        1. Cheapest component first (gold-efficient farming)
        2. Unless a component provides critical stats for the matchup
           (e.g., Ogre Axe first on BKB if you need HP to survive)
        3. Recipe last (unless no recipe exists)
        """

    def resolve_phase(self, phase: RecommendPhase) -> list[BuildPath]:
        """Resolve all items in a phase to build paths."""
```

**Ordering Heuristics (deterministic, no LLM needed):**

1. **Default: cheapest component first** -- most games, you buy whatever you can afford
2. **Matchup override: survival component first** -- if lane is lost or enemy has kill threat, prioritize the defensive component (e.g., Ogre Axe on BKB for +190 HP before Mithril Hammer for +24 dmg)
3. **Recipe always last** -- recipes provide no stats until completion
4. **Recursive resolution** -- if a component is itself a multi-component item (e.g., Yasha is a component of Manta Style, Yasha itself has components), resolve the sub-tree

**Where It Integrates:**

| Component | Integration Point | What Changes |
|-----------|------------------|--------------|
| `DataCache` | Already has data | `ItemCached.components` tuple already populated |
| `BuildPathResolver` | NEW module | Pure logic, depends only on DataCache |
| `HybridRecommender` | After `_validate_item_ids()` | Call `BuildPathResolver.resolve_phase()` to enrich response |
| `RecommendResponse` | Schema extension | New optional `build_path` field on `ItemRecommendation` |
| `SYSTEM_PROMPT` | Instruction addition | "When recommending items, note which component to prioritize first and why" |
| Frontend | `RecommendPhase` display | Show component steps below each recommended item |

**Schema Extension:**

```python
# In schemas.py
class ComponentStep(BaseModel):
    item_id: int
    item_name: str
    gold_cost: int
    reasoning: str | None = None

class ItemRecommendation(BaseModel):
    # ... existing fields ...
    build_path: list[ComponentStep] | None = None  # NEW optional field
```

**Why Deterministic (Not LLM):**
- Component ordering is mechanical (cheapest first, recipe last)
- LLM tokens are expensive for purely deterministic logic
- Claude can add matchup-specific component reasoning in its item reasoning text
- Keeps latency low -- build paths resolve synchronously from DataCache

**Claude's Role:**
The SYSTEM_PROMPT gets a new instruction: "When recommending core items, mention which component to buy first and why in your reasoning. Example: 'Start with Ogre Axe for the HP to survive Zeus burst, then Mithril Hammer.'" This way Claude adds matchup-aware component ordering insight while the BuildPathResolver handles the mechanical tree.

---

### 2D. Win Condition Framing

**Problem:** Current `overall_strategy` is reactive (counter-focused). V4.0 should proactively frame HOW the team wins.

**Approach: Team composition classification via deterministic hero tagging + Claude reasoning.**

**Team Composition Archetypes:**

| Archetype | Signal Heroes/Traits | Win Condition |
|-----------|---------------------|---------------|
| Teamfight | AOE ults, frontliners, aura carriers | Group at power spike, force 5v5 |
| Split-push | Tower damage, summons, mobility | Pressure multiple lanes, avoid 5v5 |
| Pick-off / Gank | Catch, burst damage, invis | Get pickoffs, snowball advantage |
| 4-protect-1 | Hard carry + 4 utility/support | Stall, create space, late-game carry |
| Deathball / Push | Summons, auras, heal, pushing | End early, group and push as 5 |
| Tempo / Midgame | Midgame power spikes, fighting cores | Win fights 15-30 min, take objectives |

**New Component: `WinConditionClassifier`**

```python
# engine/win_condition.py (NEW)

class TeamProfile:
    """Classified team composition."""
    primary_archetype: str        # "teamfight" | "split_push" | "pick_off" | etc.
    secondary_archetype: str | None
    timing_window: str            # "early" | "mid" | "late"
    key_heroes: list[str]         # Heroes driving the archetype
    confidence: float             # 0-1 how cleanly the draft fits

class WinConditionClassifier:
    """Classifies a 5-hero team into a macro strategy archetype."""

    def __init__(self, cache: DataCache):
        self.cache = cache

    def classify_team(self, hero_ids: list[int]) -> TeamProfile:
        """Classify a team's composition into a strategic archetype.

        Uses hero roles (from OpenDota data already in cache) + hero attack type
        + known hero traits to determine macro strategy.
        """

    def classify_matchup(
        self, ally_ids: list[int], enemy_ids: list[int]
    ) -> MatchupProfile:
        """Classify both teams and determine how ally team should play."""
```

**Classification Logic (deterministic):**

Hero tagging uses data already in `HeroCached.roles` (from OpenDota):
- OpenDota roles: Carry, Support, Nuker, Disabler, Jungler, Durable, Escape, Pusher, Initiator
- "Pusher" heroes on team --> push/deathball signal
- "Escape" + "Carry" heroes --> split-push signal
- Multiple "Initiator" + "Nuker" heroes --> teamfight signal
- Single hard carry with rest utility --> 4-protect-1 signal

**Where It Integrates:**

| Component | Integration Point | What Changes |
|-----------|------------------|--------------|
| `DataCache` | No change needed | `HeroCached.roles` already has OpenDota role tags |
| `WinConditionClassifier` | NEW module | Pure logic, depends only on DataCache |
| `ContextBuilder` | `build()` | New section `## Team Strategy` with archetype + timing window |
| `SYSTEM_PROMPT` | Expanded instruction | "Frame item recommendations around the team's win condition" |
| `RecommendResponse` | Optional extension | Add `win_condition` field to response (archetype + reasoning) |

**ContextBuilder Addition:**

```python
# New section
## Team Strategy
Your team: Teamfight (primary), Tempo (secondary)
Timing window: Mid-game (15-30 min power spike)
Key heroes: Tidehunter (Ravage initiation), Crystal Maiden (Freezing Field follow-up)
Enemy team: Split-push (primary) with Anti-Mage, Nature's Prophet
Strategy: Force fights before Anti-Mage completes Battle Fury. Your teamfight is stronger 15-25 min.
```

**SYSTEM_PROMPT Addition:**

```
## Win Condition Framing
If a "Team Strategy" section is present:
- Frame your overall_strategy around the team's win condition, not just countering enemies.
- Item timing matters: if your team peaks mid-game, prioritize items that spike at 20-25 min.
- If the enemy team outscales, recommend items that enable early aggression.
- Name the specific timing window and why items should be completed before/during it.
```

---

## 3. Component Dependency Graph

```
                    OpenDota API
                   /      |       \
            abilities  itemTimings  hero_abilities
                  \       |        /
                   refresh.py (extended)
                        |
                   SQLite DB (new tables)
                        |
                   DataCache.load()  (extended with new dicts)
                   /    |    \    \
                  /     |     \    \
    RulesEngine   BuildPath  WinCondition  TimingService
    (extended)    Resolver   Classifier
         |           |          |
         +-----+-----+----+----+
               |           |
          ContextBuilder   |
          (extended)       |
               |           |
          SYSTEM_PROMPT    |
          (extended)       |
               |           |
          LLMEngine        |
          (unchanged)      |
               |           |
          HybridRecommender (extended: build path enrichment)
               |
          RecommendResponse (extended: build_path, win_condition)
```

**Key Insight: All four features follow the same integration pattern:**
1. New data fetched in refresh pipeline
2. Stored in DB, loaded into DataCache
3. Consumed by RulesEngine (deterministic) and/or ContextBuilder (Claude context)
4. System prompt updated with instructions for new data types
5. Response schema optionally extended

---

## 4. Data Flow Changes

### New OpenDota API Calls (in refresh pipeline)

| Endpoint | Frequency | Data Size | Rate Limit Impact |
|----------|-----------|-----------|-------------------|
| `/constants/abilities` | Every 6h refresh | ~200KB JSON, all abilities | 1 call |
| `/constants/hero_abilities` | Every 6h refresh | ~50KB JSON, hero->ability map | 1 call |
| `/scenarios/itemTimings?hero_id=X` | Per hero, batched in refresh | ~5-20KB per hero | ~130 calls (all heroes) |

**Rate Limit Analysis:**
- Current refresh: 2 calls (`/constants/heroes` + `/constants/items`)
- New: +2 constant calls + ~130 timing calls = ~134 new calls per refresh
- OpenDota free tier: 50,000/month, 60/min
- At 6h refresh interval = 4 refreshes/day = ~536 calls/day = ~16,080/month
- Leaves ~34,000 calls for matchup/popularity on-demand requests
- **Verdict: Fits within free tier, but batch timing calls with 1s delays to respect 60/min**

### New DB Tables

| Table | Rows (est.) | Refresh Frequency |
|-------|------------|-------------------|
| `ability_data` | ~600 (all abilities) | Every 6h with heroes/items |
| `hero_ability_map` | ~130 (one per hero) | Every 6h with heroes/items |
| `item_timing_data` | ~130 (one per hero, JSON blob) | Every 6h, batched |

### DataCache Memory Impact

| New Dict | Est. Entries | Est. Memory |
|----------|-------------|-------------|
| `_hero_abilities` | ~130 heroes | ~100KB (frozen dataclasses) |
| `_ability_lookup` | ~600 abilities | ~200KB (frozen dataclasses) |
| `_hero_item_timings` | ~130 heroes x ~10 items | ~150KB (frozen dataclasses) |
| **Total new** | | **~450KB** -- negligible on any server |

---

## 5. Modified Components (Explicit Change List)

### Files Modified

| File | Changes |
|------|---------|
| `data/models.py` | Add `AbilityData`, `HeroAbilityMap`, `ItemTimingData` models |
| `data/opendota_client.py` | Add `fetch_abilities()`, `fetch_hero_abilities()`, `fetch_item_timings(hero_id)` |
| `data/refresh.py` | Extend `refresh_all_data()` with ability + timing fetch steps |
| `data/cache.py` | Add `AbilityCached`, `HeroAbilitiesCached`, `ItemTimingBenchmark` dataclasses; extend DataCache with new dicts + lookup methods |
| `engine/rules.py` | Add 4-6 new ability-aware counter rules (Eul's vs channeled, Lotus vs single-target, Manta vs dispellable, BKB priority upgrade) |
| `engine/context_builder.py` | Add `_build_timing_section()`, `_build_ability_threats_section()`, `_build_team_strategy_section()` |
| `engine/prompts/system_prompt.py` | Add timing benchmark instructions, ability-aware counter guidance, win condition framing instructions |
| `engine/recommender.py` | Add build path enrichment step after `_validate_item_ids()` |
| `engine/schemas.py` | Add `ComponentStep`, extend `ItemRecommendation` with `build_path`, extend `RecommendResponse` with `win_condition` |

### Files Created

| File | Purpose |
|------|---------|
| `engine/build_path.py` | `BuildPathResolver` -- resolves items to component purchase sequences |
| `engine/win_condition.py` | `WinConditionClassifier` -- classifies team compositions into strategic archetypes |
| `data/timing_service.py` | `TimingService` -- processes raw timing data into benchmarks (early/optimal/late thresholds) |
| `data/ability_service.py` | Helper functions for loading/caching ability data from OpenDota |

### Files Unchanged

| File | Why |
|------|-----|
| `engine/llm.py` | LLM engine is agnostic to prompt content -- just passes system + user messages |
| `api/routes/recommend.py` | Route handler unchanged -- HybridRecommender interface stays the same |
| `middleware/rate_limiter.py` | No changes to rate limiting |
| `gsi/` (all files) | GSI receiver/state manager unaffected |
| `data/matchup_service.py` | Existing matchup pipeline unchanged |

---

## 6. Frontend Impact

### Schema Changes Visible to Frontend

```typescript
// Extended ItemRecommendation
interface ComponentStep {
  item_id: number;
  item_name: string;
  gold_cost: number;
  reasoning: string | null;
}

interface ItemRecommendation {
  // ... existing fields unchanged ...
  build_path: ComponentStep[] | null;  // NEW -- optional component ordering
}

// Extended RecommendResponse
interface WinCondition {
  archetype: string;           // "teamfight" | "split_push" | "pick_off" | etc.
  timing_window: string;       // "early" | "mid" | "late"
  summary: string;             // 1-2 sentence strategy summary
}

interface RecommendResponse {
  // ... existing fields unchanged ...
  win_condition: WinCondition | null;  // NEW -- optional team strategy
}
```

### Frontend Component Changes

| Component | Change | Complexity |
|-----------|--------|------------|
| Item timeline cards | Show build path steps below item name/cost | Low -- map over `build_path` array |
| Strategy banner | New component above timeline showing win condition archetype + timing | Medium -- new UI component |
| Timing urgency indicator | Badge/color on items with timing benchmarks (on track / behind) | Low -- conditional styling |

All frontend changes are additive -- existing UI works unchanged when new fields are null.

---

## 7. Suggested Build Order

Based on data dependencies between the four features:

### Phase 1: Data Foundation (abilities + timings in DataCache)

**Build:** Ability data pipeline + timing data pipeline + DataCache extensions

```
1. opendota_client.py: add fetch_abilities(), fetch_hero_abilities(), fetch_item_timings()
2. models.py: add AbilityData, HeroAbilityMap, ItemTimingData tables
3. data/ability_service.py: helper to process raw ability JSON
4. data/timing_service.py: helper to compute optimal/early/late thresholds
5. cache.py: add AbilityCached, HeroAbilitiesCached, ItemTimingBenchmark; extend load()
6. refresh.py: extend refresh_all_data() with ability + timing fetch
```

**Why first:** Everything else depends on this data being in DataCache. No feature can fire without it.

### Phase 2: Counter-Item Depth (ability-aware rules)

**Build:** New RulesEngine rules using ability data

```
1. rules.py: add _euls_vs_channeled_rule, _lotus_orb_vs_single_target_rule,
   _manta_vs_dispellable_rule, _bkb_priority_rule, etc.
2. context_builder.py: add _build_ability_threats_section()
3. system_prompt.py: add ability-aware counter instructions
4. Tests: test each new rule with real hero/ability data
```

**Why second:** Depends on ability data from Phase 1. High-value: makes rules engine dramatically smarter without adding LLM cost.

### Phase 3: Timing Benchmarks (urgency signals)

**Build:** Timing context in Claude prompts + optional RulesEngine urgency rules

```
1. context_builder.py: add _build_timing_section()
2. system_prompt.py: add timing benchmark instructions
3. rules.py: optional urgency rules (if GSI clock available)
4. Tests: test timing section generation with sample data
```

**Why third:** Depends on timing data from Phase 1. Independent of Phase 2 (could be parallelized).

### Phase 4: Build Path Intelligence

**Build:** BuildPathResolver + schema extension + response enrichment

```
1. engine/build_path.py: BuildPathResolver class
2. schemas.py: add ComponentStep, extend ItemRecommendation
3. recommender.py: add build path enrichment step
4. system_prompt.py: add component ordering instructions
5. Frontend: item card build path display
6. Tests: test component resolution for multi-tier items
```

**Why fourth:** Uses only existing DataCache item data (components already cached). Independent of Phases 2-3. Placed here because it requires schema changes that affect frontend.

### Phase 5: Win Condition Framing

**Build:** WinConditionClassifier + context/prompt integration + response extension

```
1. engine/win_condition.py: classifier using HeroCached.roles
2. context_builder.py: add _build_team_strategy_section()
3. system_prompt.py: add win condition framing instructions
4. schemas.py: add WinCondition to RecommendResponse
5. Frontend: strategy banner component
6. Tests: test classification accuracy for known compositions
```

**Why last:** Uses only existing hero role data -- no new pipeline dependencies. But it's the most nuanced feature (classification accuracy matters), benefits from having all other context available.

---

## 8. Anti-Patterns to Avoid

### Anti-Pattern: Putting All Intelligence in the System Prompt

**What:** Trying to make Claude "just figure out" timing, counters, build paths from raw data dumps.
**Why bad:** Increases token count, increases latency, reduces consistency. Claude output quality degrades with prompt bloat.
**Instead:** Deterministic logic (RulesEngine, BuildPathResolver, WinConditionClassifier) handles what it can. Claude handles nuanced reasoning. Keep Claude's job focused: "given this pre-processed context, explain WHY."

### Anti-Pattern: Fetching Timing Data Per Request

**What:** Calling OpenDota `/scenarios/itemTimings` during recommendation requests.
**Why bad:** Adds 200-500ms latency per opponent hero. Rate limit exhaustion. Blocks the hot path.
**Instead:** Batch-fetch all timing data in the 6h refresh pipeline, cache in DB, load into DataCache.

### Anti-Pattern: Hardcoding Ability Counters Like Current Rules

**What:** Adding `channeled_heroes = self._hero_ids("Crystal Maiden", "Witch Doctor", ...)` lists.
**Why bad:** Requires manual updates on hero reworks. Misses new heroes. The whole point of ability data is dynamic countering.
**Instead:** Query `self.cache.has_channeled_ability(opp_id)` -- works for any hero automatically.

### Anti-Pattern: Making Build Path Ordering an LLM Task

**What:** Asking Claude to output component ordering per item.
**Why bad:** Wastes tokens on mechanical logic. Claude may hallucinate component trees. Inconsistent ordering across requests.
**Instead:** `BuildPathResolver` resolves component trees deterministically from DataCache. Claude adds matchup reasoning ("buy Ogre Axe first for HP vs burst").

---

## 9. System Prompt Token Budget

Current system prompt: ~13,326 chars (~3,300 tokens)

| New Section | Est. Tokens |
|-------------|-------------|
| Timing benchmark instructions | ~150 |
| Ability-aware counter guidance | ~200 |
| Win condition framing instructions | ~150 |
| Build path component notes | ~100 |
| **Total new** | **~600** |
| **New total** | **~3,900 tokens** |

Anthropic prompt caching activates at 1,024 tokens (Haiku). Current system prompt is well above this. Adding 600 tokens is safe -- prompt caching will cover the static system prompt regardless.

**User message impact:**
- New timing section: ~100-200 tokens
- Ability threats section: ~100-150 tokens
- Team strategy section: ~80-120 tokens
- **Total new per-request context: ~280-470 tokens**
- Current user message target: <1,500 tokens
- New target: <2,000 tokens (still well within Haiku's context window)

---

## Sources

- OpenDota API documentation: [docs.opendota.com](https://docs.opendota.com/)
- OpenDota `/scenarios/itemTimings` endpoint: response structure from [go-opendota package](https://pkg.go.dev/github.com/jasonodonnell/go-opendota)
- dotaconstants `abilities.json` structure: [GitHub/odota/dotaconstants](https://github.com/odota/dotaconstants/blob/master/build/abilities.json)
- dotaconstants `hero_abilities.json` structure: [GitHub/odota/dotaconstants](https://github.com/odota/dotaconstants/blob/master/build/hero_abilities.json)
- Team composition archetypes: [Steam Community Guide](https://steamcommunity.com/sharedfiles/filedetails/?id=2395798524)
- Direct codebase analysis of all files listed in Section 5 (HIGH confidence)

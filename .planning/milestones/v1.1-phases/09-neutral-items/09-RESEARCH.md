# Phase 9: Neutral Items - Research

**Researched:** 2026-03-23
**Domain:** Dota 2 neutral item data pipeline, Claude context extension, React timeline UI
**Confidence:** HIGH

## Summary

Phase 9 adds neutral item recommendations to the existing Prismlab item advisor. The core work is a data pipeline fix, a Claude context/prompt extension, schema additions, and a new frontend section. The most critical finding is a **seed data bug**: the current `seed.py` identifies neutral items via `qual == "rare"`, which is incorrect. The OpenDota API's `qual == "rare"` marks 51 regular shop items (Mekansm, Force Staff, Aghanim's Scepter, etc.) while the actual 34 neutral items are identified by having a non-null `tier` field (1-5). This means the existing `is_neutral` column in the database is populated with wrong data, and the real neutral items have `is_neutral=False`. The seed logic must be fixed first, then the database re-seeded.

The neutral item data from OpenDota is well-structured: 34 items across 5 tiers (T1: 8, T2: 6, T3: 6, T4: 6, T5: 8), each with an `abilities` array containing effect descriptions. Total effect text is approximately 6,900 characters (~1,700 tokens) -- this fits within the context builder's token budget when added as a new section using compact formatting. The architecture follows the established pattern from Phase 8 (allied heroes): new `_build_neutral_catalog()` method in context builder, new system prompt section, schema extension with a `neutral_items` field, and a new frontend component below the existing timeline.

**Primary recommendation:** Fix the seed detection bug (`tier is not None` instead of `qual == "rare"`), extend the LLM schema with a separate `neutral_items` array, and build a `NeutralItemSection` component following the existing `PhaseCard` visual pattern.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Neutral item recommendations appear as a dedicated section below the main item timeline, visually separated from purchasable items
- **D-02:** Each tier shows 2-3 ranked picks with #1 as best and #2-3 as situational alternatives
- **D-03:** All 5 tiers (T1-T5) visible from initial recommendation -- no progressive reveal
- **D-04:** Each neutral item gets short per-item reasoning (1 sentence) tied to hero/matchup
- **D-05:** Build-path interaction callouts live in the neutral item's reasoning text (no separate UI badges)
- **D-06:** Send all neutral items per tier to Claude with names, effects, and stat bonuses. Claude picks best 2-3 per tier. No pre-filtering
- **D-07:** Neutral recommendations update on Re-Evaluate, same as purchasable items

### Claude's Discretion
- Exact wording of neutral item reasoning -- follow established analytical voice
- Whether to mention tier timing (7min, 17min, etc.) in neutral section header or leave implicit
- How to handle tiers where no neutral item is particularly relevant -- "no strong preference" acceptable

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NEUT-01 | Neutral item data (name, tier, effects) stored in database | Seed bug fix needed: change detection from `qual == "rare"` to `tier is not None`. 34 items across 5 tiers available from OpenDota API with full abilities/attrib data. Item model already has `is_neutral` and `tier` columns. |
| NEUT-02 | Dedicated "Best Neutral Items" section in recommendations ranked by tier (T1-T5) | Requires: (1) new `_build_neutral_catalog()` in context_builder.py, (2) new "Neutral Items" system prompt section, (3) `neutral_items` field in LLMRecommendation schema, (4) new NeutralItemSection frontend component |
| NEUT-03 | Inline neutral item callouts in phase reasoning when a neutral item changes the build path | Handled via system prompt rules instructing Claude to cross-reference neutral items with purchasable recommendations and note build-path changes in the neutral item's reasoning text |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Frontend: React 18 + Vite + TypeScript + Tailwind CSS + Zustand
- Backend: Python 3.12 + FastAPI + SQLAlchemy + SQLite
- AI Engine: Claude API (Sonnet) for item reasoning
- Dark theme with spectral cyan (#00d4ff) primary accent
- Desktop-first layout
- Hero/item images from Steam CDN (pattern: `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/{internal_name}.png`)
- Structured JSON output from Claude API, parsed and validated
- Hybrid engine: rules first, Claude for reasoning
- Type hints throughout Python, TypeScript strict mode

## Standard Stack

No new libraries needed. This phase extends existing code using the established stack.

### Core (existing, no changes)
| Library | Purpose | Relevant to Phase 9 |
|---------|---------|---------------------|
| FastAPI | Backend API | Response schema extension |
| Pydantic | Schema validation | LLMRecommendation extension |
| SQLAlchemy | Database ORM | Neutral item queries |
| React 18 | Frontend UI | New NeutralItemSection component |
| Tailwind CSS | Styling | Tier cards, color coding |
| Zustand | State management | RecommendResponse type update |

## Architecture Patterns

### Data Flow (Neutral Items)

```
OpenDota API (/constants/items)
    |
    v  [tier field present = neutral item]
seed.py --> Item table (is_neutral=True, tier=1-5)
    |
    v  [new query: get_neutral_items_by_tier()]
matchup_service.py --> grouped by tier
    |
    v  [new _build_neutral_catalog() method]
context_builder.py --> "## Neutral Items Catalog" section in user message
    |
    v  [new "Neutral Items" section in system prompt]
Claude API --> structured JSON with neutral_items field
    |
    v  [validated via extended LLMRecommendation schema]
recommender.py --> RecommendResponse with neutral_items
    |
    v  [new NeutralItemSection component]
Frontend --> Rendered below item timeline
```

### Recommended File Changes

```
prismlab/
  backend/
    data/
      seed.py                  # FIX: is_neutral = tier is not None (not qual == "rare")
      matchup_service.py       # ADD: get_neutral_items_by_tier() query
    engine/
      schemas.py               # ADD: NeutralTierRecommendation, extend LLMRecommendation
      context_builder.py       # ADD: _build_neutral_catalog() method + wire into build()
      recommender.py           # ADD: pass neutral_items through merge/response
      prompts/
        system_prompt.py       # ADD: "## Neutral Items" reasoning rules section
    tests/
      conftest.py              # ADD: neutral item test fixtures
      test_context_builder.py  # ADD: neutral catalog tests
      test_matchup_service.py  # ADD: get_neutral_items_by_tier test
      test_recommender.py      # ADD: neutral items passthrough test
      test_llm.py              # ADD: neutral items schema test
  frontend/
    src/
      types/
        recommendation.ts      # ADD: NeutralTierRecommendation, NeutralItemPick types
      components/
        timeline/
          ItemTimeline.tsx      # MODIFY: render NeutralItemSection below phases
          NeutralItemSection.tsx # NEW: dedicated neutral items component
```

### Pattern 1: Context Builder Section (follow existing pattern)
**What:** Each section of the user message has a dedicated `_build_*` async method
**When to use:** Adding new data to Claude's context. Follow the `_build_ally_lines()` pattern in context_builder.py. New `_build_neutral_catalog()` method queries neutral items by tier and formats them as a compact markdown section. Wire into `build()` method between the popularity section and final instruction.

### Pattern 2: Schema Extension (follow existing pattern)
**What:** Separate field on LLMRecommendation for neutral items, not mixed into phases. Add `NeutralItemPick` (item_name, reasoning, rank) and `NeutralTierRecommendation` (tier, items) models. Add `neutral_items: list[NeutralTierRecommendation] = Field(default_factory=list)` to both `LLMRecommendation` and `RecommendResponse`. The `default_factory=list` ensures backward compatibility.

### Pattern 3: Frontend Component (follow PhaseCard pattern)
**What:** New `NeutralItemSection` component rendered below timeline in `ItemTimeline.tsx`. Uses the same `bg-bg-secondary rounded-lg p-4 border border-bg-elevated` card styling. Each tier gets a sub-card with tier number, timing label, and 2-3 ranked neutral item picks with reasoning. Tier timing constants: `{1: "5 min", 2: "15 min", 3: "25 min", 4: "35 min", 5: "60 min"}`.

### Anti-Patterns to Avoid
- **Mixing neutral items into phases array:** Keep them in a separate `neutral_items` field. Neutral items are not purchasable and have different semantics (tier-based, not phase-based).
- **Pre-filtering neutral items by hero attribute:** Decision D-06 explicitly says send ALL items per tier. Claude catches non-obvious synergies.
- **Using item_id for neutral items in Claude output:** Since neutral items are not in the "Available Items" list, Claude should reference them by name.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Neutral item detection | Custom heuristic (name patterns, cost=0) | `tier is not None` check on OpenDota data | The `tier` field is the canonical indicator |
| Item effect descriptions | Scraping wiki for neutral item text | `abilities[].description` from OpenDota API | Already structured, already in the API response |
| Tier timing display | Dynamic calculation | Constant dict `{1: "5:00", 2: "15:00", 3: "25:00", 4: "35:00", 5: "60:00"}` | Tier timings rarely change |

## Common Pitfalls

### Pitfall 1: Seed Detection Bug (CRITICAL)
**What goes wrong:** The current `seed.py` uses `info.get("qual") == "rare"` to set `is_neutral=True`. This incorrectly marks 51 regular shop items as neutral and leaves ALL 34 actual neutral items with `is_neutral=False`.
**Why it happens:** OpenDota's `qual=rare` indicates item quality/rarity (utility items). Neutral items have `qual=None` or `qual=common`.
**How to avoid:** Change detection to `is_neutral=info.get("tier") is not None`.
**Warning signs:** Querying `Item.is_neutral == True` returns Mekansm, Force Staff, etc.

### Pitfall 2: Token Budget Overflow
**What goes wrong:** Adding all 34 neutral items with full effect descriptions exceeds the 1500-token target.
**Why it happens:** Neutral item abilities text totals ~6,900 chars (~1,700 tokens).
**How to avoid:** Use compact formatting: item name + single-line effect summary (~500 tokens total).
**Warning signs:** Claude responses getting slower or hitting max_tokens.

### Pitfall 3: Schema Backward Compatibility
**What goes wrong:** Adding required `neutral_items` field breaks existing tests.
**How to avoid:** Use `neutral_items: list[NeutralTierRecommendation] = Field(default_factory=list)`. Update schema and prompt together.

### Pitfall 4: Neutral Items in Available Items List
**What goes wrong:** `get_relevant_items()` excludes `Item.is_neutral == False`. With wrong seed data, this excludes 51 regular items.
**How to avoid:** Fix seed detection first, then verify filter works correctly.

### Pitfall 5: Steam CDN Image URLs for Neutral Items
**What goes wrong:** Some internal names don't match CDN pattern (e.g., `desolator_2`, `demonicon`, `pogo_stick`).
**How to avoid:** Test all 34 URLs. Add fallback styling for broken images.

### Pitfall 6: Re-Seeding Required After Fix
**What goes wrong:** Fixing seed.py doesn't fix already-seeded data.
**How to avoid:** Delete `prismlab.db` and restart to re-seed.

### Pitfall 7: Neutral Item Effect Text Quality
**What goes wrong:** Seed stores `hint[0]` as `active_desc` but neutral items have empty hints. The `abilities` field has the real effect text.
**How to avoid:** Extract `abilities[0].description` for items with a `tier` field. Store as `active_desc`.

## Code Examples

### Seed Fix (Critical)

In `prismlab/backend/data/seed.py` line 97, change `is_neutral=info.get("qual") == "rare"` to `is_neutral=info.get("tier") is not None`. Also extract `abilities[0].description` for neutral items and store as `active_desc` since the `hint` field is empty for all 34 neutral items.

### New Matchup Service Query

Add `get_neutral_items_by_tier(db)` function to `matchup_service.py` following the `get_relevant_items()` pattern. Query `Item.is_neutral == True` and `Item.tier.isnot(None)`, group by tier, return dict mapping tier number to list of item dicts with id, name, internal_name, and effect fields.

### Context Builder Extension

Add `_build_neutral_catalog(self, db)` async method to `ContextBuilder` class. Query neutral items by tier via the new matchup service function. Format as compact markdown: one line per item with name and truncated effect description. Wire into `build()` method as a new section `## Neutral Items Catalog` placed after the popularity section.

### System Prompt Extension

Add a "## Neutral Items" section to `system_prompt.py` between "## Team Coordination" and "## Output Constraints". Include 5 rules: (1) rank by hero synergy, (2) note build-path interactions, (3) short per-item reasoning, (4) no strong preference is acceptable, (5) tier timing awareness. Also update Output Constraints to describe the `neutral_items` output field format.

### Schema Extension

Add `NeutralItemPick` (item_name: str, reasoning: str, rank: int) and `NeutralTierRecommendation` (tier: int, items: list[NeutralItemPick]) to `schemas.py`. Add `neutral_items: list[NeutralTierRecommendation] = Field(default_factory=list)` to both `LLMRecommendation` and `RecommendResponse`.

### Recommender Extension

In `recommender.py`, pass `neutral_items` from `llm_result` through to `RecommendResponse`. On fallback (rules-only), set `neutral_items=[]`.

### Frontend Types and Component

Add `NeutralItemPick` and `NeutralTierRecommendation` interfaces to `recommendation.ts`. Add `neutral_items` field to `RecommendResponse`. Create new `NeutralItemSection.tsx` component. Render it in `ItemTimeline.tsx` below the phase cards.

## Neutral Item Data Reference

Verified via live OpenDota API query on 2026-03-23:

| Tier | Count | Items |
|------|-------|-------|
| T1 | 8 | Chipped Vest, Occult Bracelet, Duelist Gloves, Pollywog Charm, Kobold Cup, Dormant Curio, Weighted Dice, Ash Legion Shield |
| T2 | 6 | Poor Man's Shield, Essence Ring, Tumbler's Toy, Defiant Shell, Mana Draught, Searing Signet |
| T3 | 6 | Psychic Headband, Whisper of the Dread, Unrelenting Eye, Gunpowder Gauntlet, Serrated Shiv, Jidi Pollen Bag |
| T4 | 6 | Rattlecage, Crippling Crossbow, Giant's Maul, Metamorphic Mandible, Idol of Scree'Auk, Flayer's Bota |
| T5 | 8 | Stygian Desolator, Spider Legs, Book of the Dead, Fallen Sky, Minotaur Horn, Dezun Bloodrite, Divine Regalia, Riftshadow Prism |

All 34 items have: `abilities` array with effect descriptions, `attrib` array with stat values, `cost: 0`, and NO `qual: "rare"` designation.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Neutral items drop randomly | Madstone crafting (Artifact + Enchantment) | Patch 7.38 (2025) | Players CHOOSE their neutral item per tier |
| `qual == "rare"` detects neutrals | `tier is not None` detects neutrals | Current (OpenDota API) | Seed code uses wrong heuristic |
| ~50+ neutrals rotated by season | 34 active artifacts (8/6/6/6/8) | Patch 7.38+ | Smaller pool, more meaningful recs |
| Shared team pool | Each player crafts own | Patch 7.38+ | Per-player recommendations correct |

## Open Questions

1. **Enchantment data:** OpenDota has artifacts (34 items) but not enchantments. For V1.1, recommend artifacts only.
2. **Image URL verification:** Some internal names may not match CDN. Test all 34 during implementation.
3. **Database re-seed:** Delete `prismlab.db` and restart after deploying the seed fix.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (backend), vitest (frontend) |
| Quick run | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| Full suite | `cd prismlab/backend && python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | File Exists? |
|--------|----------|-----------|-------------|
| NEUT-01 | Seed identifies neutrals by tier field | unit | No -- Wave 0 |
| NEUT-01 | get_neutral_items_by_tier groups by tier | unit | No -- Wave 0 |
| NEUT-02 | Context builder includes neutral catalog | unit | No -- Wave 0 |
| NEUT-02 | System prompt has Neutral Items section | unit | No -- Wave 0 |
| NEUT-02 | LLMRecommendation schema accepts neutral_items | unit | No -- Wave 0 |
| NEUT-02 | RecommendResponse includes neutral_items | unit | No -- Wave 0 |
| NEUT-03 | System prompt has build-path interaction rule | unit | No -- Wave 0 |

### Wave 0 Gaps
- [ ] `tests/test_context_builder.py::TestNeutralCatalog` -- neutral catalog builder tests
- [ ] `tests/test_context_builder.py::TestSystemPromptNeutralRules` -- prompt smoke tests
- [ ] `tests/test_matchup_service.py::test_get_neutral_items_by_tier` -- query test
- [ ] `tests/test_recommender.py::test_neutral_items_passthrough` -- pipeline test
- [ ] `tests/test_llm.py::test_neutral_items_schema` -- schema validation test
- [ ] `tests/conftest.py` -- add neutral item fixtures (tier field, is_neutral=True)

## Sources

### Primary (HIGH confidence)
- OpenDota API (`/api/constants/items`) -- live query verified 34 items with `tier` field, 0 overlap with `qual=rare`
- Existing codebase files (all canonical refs from CONTEXT.md)

### Secondary (MEDIUM confidence)
- [Liquipedia Neutral Items](https://liquipedia.net/dota2/Neutral_Items) -- tier timings, artifact list
- [Liquipedia Changelogs](https://liquipedia.net/dota2/Neutral_Items/Changelogs) -- Madstone system
- [OpenDota dotaconstants](https://github.com/odota/dotaconstants) -- data structure reference

### Tertiary (LOW confidence)
- Neutral item `abilities` field text -- present on all 34 items, not fully audited against game

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, extends existing patterns
- Architecture: HIGH -- follows Phase 8 pattern
- Data pipeline: HIGH -- verified with live API queries, confirmed seed bug
- Pitfalls: HIGH -- seed bug empirically verified
- Frontend: MEDIUM -- component pattern clear, image URLs not fully verified

**Research date:** 2026-03-23
**Valid until:** 2026-04-23

# Phase 28: Patch 7.41 Data Refresh - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Update the hero/item/ability database, rules engine, and system prompt to reflect Dota 2 patch 7.41 (released March 24, 2026). Ensure all recommendations use current game data.

</domain>

<decisions>
## Implementation Decisions

### Data Source Strategy
- **D-01:** Re-run the existing OpenDota seed script (`seed.py`). OpenDota's `/constants/items` and `/constants/heroes` should have 7.41 data already. This automatically picks up new items, changed costs, updated recipes, and removed items.
- **D-02:** No manual patch script needed — the seed is the single source of truth.
- **D-03:** If OpenDota is missing any 7.41 data after re-seed, file issues upstream and apply targeted manual fixes.

### Rules Engine Updates
- **D-04:** Full audit of all 23 rules against 7.41 changes. Check every rule for:
  - Stale item references (Cornucopia removed)
  - Changed costs affecting phase classification
  - Refresher Orb behavior change (no longer refreshes item cooldowns)
  - New counter opportunities from 7.41 items (Consecrated Wraps, Crella's Crozier, etc.)
- **D-05:** Add new rules for significant 7.41 items where appropriate (e.g., Crella's Crozier as anti-heal counter, Consecrated Wraps as magic defense option).

### System Prompt Updates
- **D-06:** Add brief 7.41 meta hints to the system prompt for key behavioral changes that Claude wouldn't know from the item catalog alone:
  - "Refresher Orb no longer refreshes item cooldowns — only abilities. No double-BKB, double-Scythe."
  - "Bloodstone now has 12% spell damage amplification aura (1200 radius)."
  - "Shiva's Guard cost reduced to 4500g (from 5175g) — more accessible for offlaners."
  - "Neutral T1 items available from minute 0." (already fixed)
- **D-07:** Keep hints minimal (under 200 tokens total). These supplement the data, not replace it.

### Validation Approach
- **D-08:** Automated tests verifying:
  - New 7.41 items exist in DB (Wizard Hat, Shawl, Splintmail, Chasm Stone, Consecrated Wraps, Essence Distiller, Crella's Crozier, Hydra's Breath)
  - Cornucopia is removed / not in DB
  - Changed item costs are correct (Shiva's 4500g, Blade Mail 2300g, etc.)
  - Rules engine doesn't reference removed items
  - System prompt token budget stays under 5000 tokens
- **D-09:** Tests run as part of the existing pytest suite — repeatable on every future patch.

### 7.41 Key Changes Reference
- 9 new items: Wizard Hat (250g), Shawl (450g), Chasm Stone (800g), Splintmail (950g), Consecrated Wraps (2600g), Essence Distiller (1775g), Crella's Crozier (4800g), Hydra's Breath (~4000g+), plus potential others
- Cornucopia removed (forces recipe changes for Mage Slayer, Orchid, others)
- Refresher Orb: abilities only (no item refresh)
- Shiva's Guard: 5175→4500g, builds from Splintmail + Chasm Stone
- Blade Mail: 2100→2300g, builds from Splintmail
- Bloodstone: reworked, 12% spell amp aura, requires Veil of Discord
- Facets removed entirely (innate abilities scale with level)
- Neutral T1: available from minute 0

### Claude's Discretion
- Exact re-seed procedure and error handling
- Which new items warrant new rules vs just catalog presence
- Meta hint wording and placement in system prompt
- Test fixture design for new items

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data Pipeline
- `prismlab/backend/data/seed.py` — Seed script that fetches from OpenDota and populates DB
- `prismlab/backend/data/opendota_client.py` — OpenDota API client (fetch_heroes, fetch_items)
- `prismlab/backend/data/models.py` — SQLAlchemy models (Hero, Item, HeroAbilityData, ItemTimingData)
- `prismlab/backend/data/refresh.py` — Data refresh pipeline

### Engine
- `prismlab/backend/engine/rules.py` — 23 deterministic rules to audit
- `prismlab/backend/engine/prompts/system_prompt.py` — System prompt (add meta hints)
- `prismlab/backend/data/cache.py` — DataCache with item filtering (component exclusion, EXCLUDED_ITEMS set)

### Tests
- `prismlab/backend/tests/test_system_prompt.py` — Token budget and data purity tests
- `prismlab/backend/tests/test_rules.py` — Rules engine tests

### Patch Research (from earlier this session)
- Patch 7.41 notes: https://www.dota2.com/patches
- Liquipedia 7.41: https://liquipedia.net/dota2/Version_7.41

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `seed.py` already handles full hero/item population — re-run is the primary mechanism
- `EXCLUDED_ITEMS` set in `cache.py` — add any new Roshan drops or non-purchasable items
- Component filtering logic — new items like Splintmail/Chasm Stone are components, handled automatically

### Established Patterns
- Seed uses upsert-style logic (should handle existing data gracefully)
- Tests check system prompt token budget (<5000 tokens) and no dynamic percentages
- Rules reference items by internal_name via `self._item_id()` — audit these calls

### Integration Points
- Re-seed populates DB → DataCache.load() picks up at next restart
- Rules audit requires reading each rule method and checking item/hero references
- System prompt edit is a single file change with token budget test validation

</code_context>

<specifics>
## Specific Ideas

- The seed script's IntegrityError on hero_ability_data (seen today during deploys) needs fixing as part of this phase — it should use upsert, not insert
- Cornucopia removal may break recipe lookups for items that used it as a component
- Splintmail and Chasm Stone are new components — they'll be auto-excluded from recommendations by the component filter, which is correct (they build into Blade Mail and Shiva's)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 28-patch-data-refresh*
*Context gathered: 2026-03-28*

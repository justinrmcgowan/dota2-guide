# Phase 19: Data Foundation & Prompt Architecture - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 19 adds ability metadata and item timing benchmark data to the backend data pipeline and DataCache, then restructures the Claude system prompt to separate static directives from dynamic per-request data. This is the data foundation that all v4.0 feature phases (20-23) depend on. Backend only — no frontend changes, no new recommendation logic, no new rules.

</domain>

<decisions>
## Implementation Decisions

### Timing Data Refresh
- **D-01:** Item timing benchmarks use stale-while-revalidate pattern, consistent with matchup_service. Fetch per-hero on first request, cache in DB, background refresh when stale (24h threshold). Only fetches heroes that are actually queried — no batch crawl of all 124 heroes.
- **D-02:** Timing data stored in a DB model (like MatchupData/HeroItemPopularity) with JSON column for the raw response. DataCache holds a derived in-memory index for fast synchronous lookups.

### Ability Data Refresh
- **D-03:** Ability constants (constants/abilities + constants/hero_abilities) refresh daily alongside heroes/items in the APScheduler pipeline. Only 2 extra API calls/day. Ability data changes only on Dota patches.
- **D-04:** Ability data loaded into DataCache at startup and refreshed atomically on pipeline cycle, following the existing hero/item pattern (frozen dataclasses, atomic swap).

### Prompt Architecture
- **D-05:** Claude's discretion on the system-vs-user message split. Goal: system prompt stays under ~5,000 tokens with directives, identity, reasoning rules, output format, and examples. All dynamic per-request data (timing benchmarks, ability descriptions, item catalog, matchup data, popularity) stays in the user message via context_builder.
- **D-06:** System prompt will grow with new v4.0 directives (timing reasoning guidance, counter-item naming rules, win condition framing instructions) but must remain a stable, cacheable constant.

### Data Quality
- **D-07:** Timing benchmarks always shown, annotated with confidence level: strong (1000+ games), moderate (200-999 games), weak (<200 games). No data is hidden — downstream phases can display confidence visually. The confidence level is stored in the cache alongside the timing data.

### Claude's Discretion
- Prompt split strategy: Claude determines optimal boundary between system directives and user message data, targeting under 5K tokens for system prompt
- DataCache internal data structures for ability data (new AbilityCached dataclass fields, hero-ability index structure)
- Timing data cache structure (how to derive in-memory index from DB-stored JSON)
- Rate limiting / semaphore strategy for stale-while-revalidate background refreshes
- Three-cache coherence extension: how ability + timing data fits into DataCache → RulesEngine → ResponseCache invalidation chain

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — DATA-01, DATA-02, DATA-03, DATA-04
- `.planning/ROADMAP.md` — Phase 19 success criteria (4 criteria that must be TRUE)

### Research
- `.planning/research/STACK.md` — OpenDota endpoint verification, rate limit budget, zero new dependencies
- `.planning/research/ARCHITECTURE.md` — Integration architecture, DataCache extensions, data flow
- `.planning/research/PITFALLS.md` — System prompt token budget, rate limits, three-cache coherence, games/wins string types
- `.planning/research/SUMMARY.md` — Executive summary, prompt data/instruction split

### Backend Files (existing patterns to follow)
- `prismlab/backend/data/cache.py` — DataCache singleton, HeroCached/ItemCached frozen dataclasses, atomic swap load()
- `prismlab/backend/data/opendota_client.py` — OpenDotaClient fetch_* methods (pattern for new endpoints)
- `prismlab/backend/data/matchup_service.py` — Stale-while-revalidate pattern with _fetch_locks (pattern for timing data)
- `prismlab/backend/data/models.py` — SQLAlchemy models including HeroItemPopularity (pattern for timing model)
- `prismlab/backend/data/refresh.py` — APScheduler pipeline (where ability data refresh hooks in)
- `prismlab/backend/data/seed.py` — Initial data population (where ability data seeding hooks in)
- `prismlab/backend/engine/prompts/system_prompt.py` — Current SYSTEM_PROMPT constant (~70 lines, ~3,300 tokens)
- `prismlab/backend/engine/context_builder.py` — User message assembly with section-based _build_* methods
- `prismlab/backend/engine/llm.py` — Where SYSTEM_PROMPT is consumed (system= parameter)
- `prismlab/backend/main.py` — Lifespan with startup hooks (DataCache.load, seed)

### Prior Phase Context
- `.planning/phases/16-backend-data-cache/16-CONTEXT.md` — DataCache architecture decisions, three-cache coherence protocol

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DataCache` class with frozen dataclasses + atomic swap — extend with AbilityCached and timing index dicts
- `OpenDotaClient.fetch_*` pattern — add fetch_abilities(), fetch_hero_abilities(), fetch_item_timings(hero_id)
- `matchup_service.py` stale-while-revalidate with `_fetch_locks` + `STALE_THRESHOLD` — reuse for timing data
- `HeroItemPopularity` model (uncommitted) — pattern for new ItemTimingBenchmark model

### Established Patterns
- Frozen dataclasses for cache immutability (HeroCached, ItemCached)
- Module-level singleton (`data_cache = DataCache()`)
- Context builder section methods (`_build_*`) return strings, assembled with `\n\n`.join()
- Three-layer cache invalidation in refresh.py: DataCache.refresh → RulesEngine refresh → ResponseCache.clear()

### Integration Points
- `main.py` lifespan: add ability data loading after hero/item cache load
- `refresh.py` pipeline: add ability constants refresh (2 API calls) to daily batch
- `cache.py` DataCache: add ability dicts + timing index alongside _heroes and _items
- `opendota_client.py`: add 3 new fetch methods
- `models.py`: add ItemTimingBenchmark model (DB-backed for stale-while-revalidate)
- `system_prompt.py`: restructure constant, add v4.0 directive sections
- `context_builder.py`: no changes this phase (timing/ability sections added in Phases 20-21)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — research fully specifies the data pipeline architecture. Key constraints from research:
- OpenDota `/scenarios/itemTimings` returns `games` and `wins` as strings (not ints) — must cast
- Ability data includes `behavior` field with values like "Channeled", "Passive", "Point Target" — used by Phase 20 counter rules
- Rate limit: 60 req/min for OpenDota free tier, 50K calls/month budget

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 19-data-foundation-prompt-architecture*
*Context gathered: 2026-03-27*

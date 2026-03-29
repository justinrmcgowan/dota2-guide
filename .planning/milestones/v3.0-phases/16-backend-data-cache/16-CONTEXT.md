# Phase 16: Backend Data Cache - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning
**Mode:** Research-derived (infrastructure phase, no user discussion needed)

<domain>
## Phase Boundary

Phase 16 introduces an in-memory DataCache singleton that preloads all hero and item data at startup, eliminating 12-20 SQLite queries per recommendation request. The cache refreshes atomically on the 6h pipeline cycle, coordinated with RulesEngine and ResponseCache invalidation. It also fixes the refresh_lookups() session safety issue (INT-05) and adds ResponseCache clearing on pipeline refresh (INT-06). Backend only — no frontend changes.

</domain>

<decisions>
## Implementation Decisions

### DataCache Architecture
- **D-01:** Python dict singleton (`DataCache` class) holding all heroes and items in memory. Loaded at startup after DB seeding, refreshed atomically on 6h pipeline cycle.
- **D-02:** Atomic refresh via "swap" pattern: build new cache dict, then replace reference. No lock needed for single-threaded async (uvicorn single-worker on Unraid).
- **D-03:** DataCache replaces RulesEngine's internal `init_lookups()`/`refresh_lookups()` pattern. RulesEngine consumes DataCache instead of maintaining its own separate hero/item mappings. Eliminates duplicated cache logic.
- **D-04:** Context builder and recommendation engine consume DataCache for all hero/item lookups instead of direct DB queries via SQLAlchemy session.
- **D-05:** `/api/heroes` and `/api/items` endpoints serve from DataCache instead of DB queries.

### Coordinated Invalidation
- **D-06:** After 6h pipeline refresh: (1) DataCache refreshes first (new data), (2) RulesEngine refreshes from DataCache (new rules mappings), (3) ResponseCache clears entirely (stale responses). Strict order prevents serving stale recommendations with new data.
- **D-07:** `refresh_lookups()` in refresh.py uses a fresh async session (not the pipeline's post-commit session) for safe operation (INT-05).

### Claude's Discretion
- DataCache internal data structures (dict of dicts, list of dataclasses, etc.)
- Whether to use frozen dataclasses or plain dicts for cached entries
- Max cache size cap (research suggests 100 entries for ResponseCache)
- Cold start timing — how to ensure cache loads after seed completes

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — PERF-01, PERF-02, PERF-03, INT-05, INT-06
- `.planning/ROADMAP.md` — Phase 16 success criteria (5 criteria that must be TRUE)

### Research
- `.planning/research/ARCHITECTURE.md` — DataCache design, hot path analysis, refresh coordination
- `.planning/research/PITFALLS.md` — Three-cache coherence, context builder is the actual hot path

### Backend Files
- `prismlab/backend/engine/recommender.py` — HybridRecommender with ResponseCache, consumes hero/item data
- `prismlab/backend/engine/context_builder.py` — THE hot path: queries Hero/Item tables per request
- `prismlab/backend/engine/rules.py` — RulesEngine with init_lookups()/refresh_lookups() to consolidate
- `prismlab/backend/data/refresh.py` — Pipeline refresh with refresh_lookups() session issue
- `prismlab/backend/data/models.py` — Hero, Item SQLAlchemy models
- `prismlab/backend/main.py` — Lifespan with seed_if_empty() and init_lookups() calls
- `prismlab/backend/api/routes/recommend.py` — Endpoint with rate limiter and cache
- `prismlab/backend/api/routes/heroes.py` — /api/heroes endpoint (if exists)
- `prismlab/backend/data/matchup_service.py` — Matchup caching patterns (reference for DataCache design)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `RulesEngine.init_lookups()` pattern — async DB query → dict mapping. DataCache follows same pattern at larger scale.
- `ResponseCache` in recommender.py — SHA-256 keyed dict with TTL. Reference for cache design.
- `matchup_service.py` `_fetch_locks` pattern — validates in-memory caching approach.

### Established Patterns
- FastAPI lifespan for startup/shutdown hooks
- Pydantic models for data validation
- Async SQLAlchemy sessions via `async_sessionmaker`

### Integration Points
- `main.py` lifespan — DataCache.load() after seed_if_empty()
- `refresh.py` — Coordinated invalidation after pipeline completes
- `context_builder.py` — Replace `await self._get_hero()` and item queries with DataCache lookups
- `rules.py` — Replace internal lookups with DataCache consumption
- `recommend.py` route — ResponseCache.clear() on refresh

</code_context>

<specifics>
## Specific Ideas

No specific requirements — research fully specifies the architecture. The key insight from research: the context builder is the actual hot path (12-20 queries), not the API route handlers.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 16-backend-data-cache*
*Context gathered: 2026-03-26*

# Phase 14: Recommendation Quality & System Hardening - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 14 improves the recommendation engine's accuracy, fills validation and caching gaps, hardens error handling, and adds rate limiting. No new features — only making existing systems work better and more reliably. The hallucination fix (Claude fabricating opponents), item popularity DB caching, and 6h refresh interval were already shipped during this session and are NOT in scope.

</domain>

<decisions>
## Implementation Decisions

### Rules Engine Expansion
- **D-01:** Replace all hardcoded hero IDs (74-entry HERO_NAMES dict) with DB lookups. Rules query Hero table by `localized_name` at startup, cache the name→ID mapping. Never desyncs with OpenDota data.
- **D-02:** Replace hardcoded item IDs in rules with DB lookups by `internal_name`. Both hero and item references are fully data-driven.
- **D-03:** Add 5-10 targeted high-value rules beyond the existing 12. Focus on obvious/deterministic cases: role-default boots, Raindrops vs magic harass, BKB timing by role, Mekansm/Pipe for support/offlane, Orchid vs escape heroes. Keep rules for fast/obvious decisions — Claude handles nuance.

### Rate Limiting & Request Deduplication
- **D-04:** Per-IP cooldown on `/api/recommend`: 1 request per 10 seconds per IP. Returns HTTP 429 with `Retry-After` header. In-memory dict, no external dependency (suitable for single-user Unraid deployment).
- **D-05:** Short-TTL in-memory response cache: hash the request payload, cache the full response for 5 minutes. Identical inputs return cached response instantly. Python dict with TTL expiry, no Redis needed. Covers double-clicks and repeated queries.

### Error Transparency
- **D-06:** When Claude fails, show the failure reason category + retry hint. Examples: "AI timed out — showing rules-based build. Try again in a moment." or "AI response was malformed — showing rules-based build." Actionable without being technical.
- **D-07:** Fallback notification uses both toast banner (Phase 7 auto-dismiss pattern) AND updated `overall_strategy` text. Two signals, neither blocking — toast for immediate notice, strategy text for persistent context in the timeline.
- **D-08:** Backend returns a `fallback_reason` field in the response so the frontend can display the appropriate message. Enum: `timeout | parse_error | api_error | rate_limited`.

### Validation Gaps
- **D-09:** Damage profile enforced on both frontend and backend. Frontend auto-adjusts sliders so physical + magical + pure always sum to 100% (drag one, others rebalance proportionally). Backend rejects requests where sum != 100% with 422.
- **D-10:** Backend validates playstyle against role using the same role→playstyle mapping as frontend. Rejects invalid combos with 422. Backend is single source of truth — frontend constants.ts should ideally fetch from backend in the future.
- **D-11:** Strengthen item ID guidance in system prompt: "ONLY use IDs from Available Items — any other ID is discarded." Keep post-LLM validation as safety net. Log filtered items with warning so prompt quality can be monitored.

### Claude's Discretion
- Exact wording of fallback toast messages
- Specific new rules to add (within the 5-10 targeted scope)
- Cache eviction strategy details (LRU vs TTL dict implementation)
- How the damage profile slider rebalancing works in the frontend (proportional vs sequential)
- Whether to add a `/api/playstyles` endpoint or keep the mapping as a backend constant

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Engine & Prompts
- `prismlab/backend/engine/rules.py` — Current 12 rules + hardcoded HERO_NAMES dict to replace
- `prismlab/backend/engine/prompts/system_prompt.py` — System prompt to strengthen item ID instructions
- `prismlab/backend/engine/recommender.py` — Hybrid orchestrator where fallback_reason needs to be added
- `prismlab/backend/engine/llm.py` — LLM engine where error categories are caught
- `prismlab/backend/engine/schemas.py` — RecommendResponse schema needs fallback_reason field
- `prismlab/backend/engine/context_builder.py` — Context builder assembling Claude prompts

### Data & Models
- `prismlab/backend/data/models.py` — Hero/Item models for DB lookup migration
- `prismlab/backend/data/matchup_service.py` — Matchup caching patterns to follow

### API
- `prismlab/backend/api/routes/recommend.py` — Endpoint where rate limiting applies
- `prismlab/backend/main.py` — App setup where middleware is registered

### Frontend
- `prismlab/frontend/src/components/sidebar/DamageProfileInput.tsx` — Slider rebalancing
- `prismlab/frontend/src/components/timeline/ErrorBanner.tsx` — Existing error display
- `prismlab/frontend/src/utils/constants.ts` — PLAYSTYLE_OPTIONS mapping to sync with backend

### Prior Phase Context
- `.planning/phases/07-tech-debt-polish/07-CONTEXT.md` — Toast-style error banner pattern

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ErrorBanner.tsx` — existing error display component, can be extended for fallback reason
- `DamageProfileInput.tsx` — existing three-input component, needs slider rebalancing logic
- `matchup_service.py` stale-while-revalidate pattern — same TTL cache pattern to follow for request dedup
- `_fetch_locks` dict pattern in matchup_service.py — same in-memory dict pattern for rate limiting

### Established Patterns
- Pydantic models for all request/response validation (schemas.py)
- FastAPI exception handlers for 422 validation errors
- Zustand stores with TypeScript strict mode
- Phase 7 toast pattern for non-blocking notifications

### Integration Points
- `recommend.py` route — add rate limit middleware/decorator
- `recommender.py` — add fallback_reason to response, add request hash cache
- `rules.py` — replace HERO_NAMES dict with DB-backed startup cache
- `schemas.py` — add fallback_reason field to RecommendResponse
- `system_prompt.py` — strengthen item ID instruction
- `DamageProfileInput.tsx` — add rebalancing logic
- `MainPanel.tsx` or `ItemTimeline.tsx` — display fallback toast

</code_context>

<specifics>
## Specific Ideas

- The rules engine DB lookup cache should be initialized once at startup (not per-request) and refreshed when the 6h data refresh runs
- Rate limit dict should be cleaned up periodically (evict expired entries) to prevent unbounded memory growth — same concern as `_fetch_locks` in matchup_service.py
- The 5-minute response cache TTL should be configurable via environment variable for tuning

</specifics>

<deferred>
## Deferred Ideas

- **localStorage persistence** — saving game state across page refreshes. Useful but UX feature, not hardening.
- **Frontend loading timeout** — showing error if /recommend takes >45s. Related to error transparency but frontend-specific.
- **Structured logging** — JSON logs to stdout. Operational improvement, separate phase.
- **Stratz API integration** — config wired but never used. Data enrichment, separate phase.
- **Request dedup across sessions** — Redis-backed cache for multi-instance. Overkill for single-user Unraid.

</deferred>

---

*Phase: 14-recommendation-quality-system-hardening*
*Context gathered: 2026-03-26*

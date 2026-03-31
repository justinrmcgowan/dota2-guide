# Phase 37: Latency & Caching - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped per user preference)

<domain>
## Phase Boundary

P95 full recommendation latency under 5 seconds through hierarchical caching, pre-computation, and streaming. Three sub-features:

1. **Hierarchical 3-Tier Cache** — Replace flat ResponseCache with L1 (hero+role+lane, 1h TTL), L2 (+opponents, 5min), L3 (full request, 5min). Serve best available cache tier, background-refresh with full context.
2. **Cache Warming** — On server startup (or daily pipeline), pre-compute rules-only recommendations for top 30 heroes x 3 roles = ~90 combos. Store in L1 with 24h TTL.
3. **SSE Streaming** — New POST /api/recommend/stream endpoint returning Server-Sent Events. Event 1: rules items (immediate). Event 2: Claude phases (2-5s). Event 3: enrichment (final). Frontend progressively renders.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion. Use ROADMAP success criteria and codebase conventions to guide decisions.

Key references:
- Design spec: `docs/superpowers/specs/2026-03-30-engine-hardening-design.md` (Pillar 3: sections 3A, 3B, 3D)
- Current ResponseCache: `prismlab/backend/engine/recommender.py` (ResponseCache class)
- Current recommend endpoint: `prismlab/backend/api/routes/recommend.py`
- Frontend useRecommendation: `prismlab/frontend/src/hooks/useRecommendation.ts`
- Frontend recommendationStore: `prismlab/frontend/src/stores/recommendationStore.ts`

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ResponseCache` class with TTL, hash-based keys, cleanup — will be replaced by HierarchicalCache
- `useRecommendation.recommendTwoPass()` — already does fast→full pattern, SSE replaces this
- `recommendationStore.setPartialData()` / `mergeData()` — progressive data support already exists
- `HybridRecommender._fast_path()` — rules-only already exists for cache warming

### Established Patterns
- FastAPI StreamingResponse for SSE
- Zustand store with progressive state merging
- SHA256 request hashing for cache keys

### Integration Points
- `recommender.py` — HierarchicalCache replaces ResponseCache
- `recommend.py` — new /api/recommend/stream endpoint
- `useRecommendation.ts` — EventSource/ReadableStream consumption
- `pipeline.py` / startup — cache warming trigger

</code_context>

<specifics>
## Specific Ideas

- L1 key: SHA256 of `{hero_id}:{role}:{lane}` — covers starting/laning items
- L2 key: SHA256 of `{hero_id}:{role}:{lane}:{sorted_opponent_ids}` — matchup-specific
- SSE format: `event: rules\ndata: {json}\n\n` then `event: phases\ndata: {json}\n\n` then `event: enrichment\ndata: {json}\n\n`
- Cache warming: async background task on startup, rate-limited to avoid slamming rules engine

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>

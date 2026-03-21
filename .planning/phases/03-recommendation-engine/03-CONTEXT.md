# Phase 3: Recommendation Engine - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 builds the hybrid recommendation engine: a rules layer for obvious/instant decisions, Claude API integration for nuanced matchup reasoning, a context builder that assembles game state into prompts, structured JSON output validation, matchup data pipeline from OpenDota, and the POST /api/recommend endpoint that orchestrates everything. After this phase, the backend can receive a draft context and return phased item recommendations with analytical reasoning.

</domain>

<decisions>
## Implementation Decisions

### Rules Engine
- List of 10-15 rule functions, each checks a condition and returns item recommendations with short rationale
- Priority-ordered, first match wins for obvious items (Magic Stick vs spell-spam, BKB vs heavy magic, MKB vs evasion, etc.)
- Rules provide single item recommendations with reasoning, not full builds
- Rules output is deterministic and instant (no API calls)

### Claude API Integration
- Use Claude Sonnet 4.6 (claude-sonnet-4-6-20250514) — best quality/cost/speed balance
- Structured output via output_config.format with JSON schema (GA, no beta headers)
- System prompt: Role as 8K+ MMR analytical coach + game knowledge + output schema + 1-2 few-shot examples of good reasoning
- Context builder pre-filters item catalog to ~40 relevant items per request
- Keep prompt under 1500 input tokens for latency management
- Response schema: phases[] array with items[], each item has id, name, reasoning, priority, conditions (for decision tree cards)
- Analytical voice: data-driven, stats, percentages — not personality-driven

### Hybrid Orchestration
- Rules fire first, output injected into Claude prompt as "already-recommended items" so Claude complements rather than contradicts
- 10-second hard timeout on Claude API call
- Fallback returns rules-only results with `"fallback": true` flag in response
- Frontend shows "AI reasoning unavailable" notice when fallback is active

### Matchup Data Pipeline
- Background fetch per matchup pair, cached in MatchupData table
- Check DB first, if stale (>24h) fetch fresh from OpenDota /heroes/{id}/matchups
- Return whatever's cached even if stale (never block recommendation on data freshness)
- Default to "high" bracket (Legend+) data

### Recommendation Endpoint
- POST /api/recommend with full game state body: hero, allies, opponents, role, playstyle, side, lane
- Response: phased timeline JSON with phases[] containing items[] with id, name, reasoning, priority, conditions
- Response metadata includes fallback flag, model used, latency_ms

### Claude's Discretion
- Exact system prompt wording and few-shot examples
- Item catalog pre-filtering logic
- Specific rule conditions beyond the documented 10-15
- Prompt caching strategy
- Error handling granularity

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `data/models.py` — Hero, Item, MatchupData SQLAlchemy models already defined
- `data/opendota_client.py` — OpenDota API wrapper with fetch_heroes/fetch_items
- `data/database.py` — Async SQLAlchemy session management
- `config.py` — Pydantic Settings with ANTHROPIC_API_KEY already loaded
- `api/routes/heroes.py`, `items.py` — Existing route patterns to follow

### Established Patterns
- Async FastAPI endpoints with SQLAlchemy async sessions
- Pydantic models for request/response validation
- OpenDota client pattern for external API calls

### Integration Points
- `main.py` — Needs new recommend router registered
- `config.py` — ANTHROPIC_API_KEY already available
- `data/models.py` — MatchupData model exists but seeding may need expansion
- Frontend `GetBuildButton` — Currently logs to console, will POST to /api/recommend in Phase 4

</code_context>

<specifics>
## Specific Ideas

- Research flagged: every item_id from Claude must be validated against the database before returning to frontend (LLM hallucination of old/removed items)
- Research flagged: system prompt needs explicit specificity constraints — every reasoning field must reference enemy heroes by name
- Research flagged: prompt caching can reduce Claude API costs by ~90% on the system prompt portion
- The MatchupData model already has common_items and common_starting_items JSON fields — populate these from OpenDota

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

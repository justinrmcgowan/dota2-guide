# Phase 18: Screenshot KDA Feed-Through - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning
**Mode:** Research-derived (small cross-stack feature, no user discussion needed)

<domain>
## Phase Boundary

Phase 18 extends the existing screenshot parsing pipeline to feed parsed KDA and level data into the recommendation request. Currently, Vision extracts KDA/level per enemy hero but the data is display-only in the confirmation modal. After this phase, Claude's recommendation reasoning references enemy economic state ("PA is 8-1-3 and snowballing") when screenshot data is available.

</domain>

<decisions>
## Implementation Decisions

### Schema Extension
- **D-01:** Add `enemy_context` field to `RecommendRequest` (backend Pydantic schema) — a list of objects with hero_id, kills, deaths, assists, level.
- **D-02:** Add matching `enemy_context` field to frontend `RecommendRequest` TypeScript type.
- **D-03:** `handleApply()` in ScreenshotParser collects KDA/level from parsed heroes and includes in the recommendation request alongside existing opponent/item data.

### Context Builder Integration
- **D-04:** Context builder formats enemy_context into the Claude user message: "Enemy Phantom Assassin (Lv 14): 8/1/3 — snowballing" style entries.
- **D-05:** System prompt updated to instruct Claude to consider enemy power levels and timing when KDA data is available.

### Claude's Discretion
- Exact formatting of enemy KDA in the user message
- How aggressively Claude should weight KDA data vs other factors
- Whether to include enemy level in the context or just KDA
- Backend validation rules for enemy_context field

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — INT-03
- `.planning/ROADMAP.md` — Phase 18 success criteria (2 criteria that must be TRUE)

### Research
- `.planning/research/ARCHITECTURE.md` — KDA feed-through data flow gap analysis

### Existing Code (the gap)
- `prismlab/frontend/src/components/screenshot/ScreenshotParser.tsx` — handleApply() currently applies opponents + items but discards KDA
- `prismlab/frontend/src/types/screenshot.ts` — ParsedHero already has kills, deaths, assists, level fields
- `prismlab/backend/engine/schemas.py` — RecommendRequest needs enemy_context field
- `prismlab/frontend/src/types/recommendation.ts` — Frontend RecommendRequest type
- `prismlab/backend/engine/context_builder.py` — Needs to format enemy_context into Claude prompt
- `prismlab/backend/engine/prompts/system_prompt.py` — Needs KDA reasoning instructions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ParsedHero` type already has kills, deaths, assists, level fields from Vision parsing
- `ScreenshotParser.handleApply()` already iterates parsed heroes — KDA extraction is adding 3-4 lines
- Context builder `_build_enemy_lines()` pattern (if exists) — follow for KDA formatting

### Integration Points
- `ScreenshotParser.tsx` handleApply → include enemy_context in recommendation request
- `useRecommendation.ts` recommend() → pass enemy_context from gameStore
- `schemas.py` RecommendRequest → new enemy_context field
- `context_builder.py` build() → format enemy KDA into user message
- `system_prompt.py` → add KDA reasoning guidance

</code_context>

<specifics>
## Specific Ideas

No specific requirements — research fully specifies the data flow gap. The key insight: all the data is already extracted by Vision and displayed in ParsedHeroRow. It just needs to flow through handleApply → gameStore → recommendation request → context builder → Claude prompt.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 18-screenshot-kda-feed-through*
*Context gathered: 2026-03-26*

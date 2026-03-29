# Phase 9: Neutral Items - Context

**Gathered:** 2026-03-23
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase adds neutral item recommendations to the existing item advisor. Players see which neutral items to prioritize each tier (T1-T5) and understand when a neutral item changes their build path. Covers: neutral item data pipeline to Claude, dedicated UI section, system prompt neutral reasoning rules, and schema extensions. Does NOT add new draft UI inputs — neutral items are drops, not purchases.

</domain>

<decisions>
## Implementation Decisions

### Section Placement
- **D-01:** Neutral item recommendations appear as a **dedicated section below** the main item timeline, visually separated from purchasable items. Players can't buy neutrals — only prioritize drops — so they get their own "Best Neutral Items" card.
- **D-02:** Each tier shows **2-3 ranked picks** with #1 as the best and #2-3 as situational alternatives. Mirrors how players actually think about neutrals (hope for best, have fallbacks).

### Tier Presentation
- **D-03:** All 5 tiers (T1-T5) are **visible from the initial recommendation** — no progressive reveal. Players want the full picture upfront, and knowing ideal T4/T5 neutrals informs whether to buy similar effects as purchasable items.
- **D-04:** Each neutral item gets **short per-item reasoning** (1 sentence) tied to the hero/matchup, consistent with how purchasable items show reasoning. No tier-level-only summaries.

### Build-Path Interaction
- **D-05:** When a neutral item changes the optimal build path, the callout lives **in the neutral item's reasoning text** (e.g., "Philosopher's Stone covers mana needs — skip Falcon Blade and rush Desolator if you get this"). No separate UI badges or cross-reference components needed.

### Data Scope and Filtering
- **D-06:** Send **all neutral items per tier** (~12 items each, ~60 total) to Claude with names, effects, and stat bonuses. Claude picks the best 2-3 per tier. No pre-filtering by hero attribute — Claude catches non-obvious synergies.
- **D-07:** Neutral recommendations **update on Re-Evaluate**, same as purchasable items. Changed game state (lane result, enemy items) may shift neutral priorities.

### Claude's Discretion
- Exact wording of neutral item reasoning — follow the analytical voice established in existing system prompt
- Whether to mention tier timing (7min, 17min, etc.) in the neutral section header or leave it implicit
- How to handle tiers where no neutral item is particularly relevant — "no strong preference this tier" is acceptable

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Data Layer
- `prismlab/backend/data/models.py` — Item model already has `is_neutral: bool` and `tier: int` fields
- `prismlab/backend/data/seed.py` — Neutral items seeded via `info.get("qual") == "rare"` and `info.get("tier")`
- `prismlab/backend/data/matchup_service.py` — `get_relevant_items()` currently excludes neutrals (`Item.is_neutral == False`)

### Context Builder
- `prismlab/backend/engine/context_builder.py` — `build()` method assembles user message sections; new neutral section goes here
- `prismlab/backend/engine/schemas.py` — `LLMRecommendation` schema needs neutral items field; `RecommendResponse` needs it too

### System Prompt
- `prismlab/backend/engine/prompts/system_prompt.py` — Needs neutral item reasoning rules (similar to Team Coordination section added in Phase 8)

### Frontend
- `prismlab/frontend/src/components/timeline/ItemTimeline.tsx` — Renders phase cards; new NeutralItemSection goes below
- `prismlab/frontend/src/components/timeline/PhaseCard.tsx` — Existing pattern for rendering item groups with reasoning
- `prismlab/frontend/src/types/recommendation.ts` — Frontend types need neutral items extension

### Requirements
- `.planning/REQUIREMENTS.md` — NEUT-01, NEUT-02, NEUT-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Item` model: `is_neutral` and `tier` fields already populated from OpenDota seed data — NEUT-01 is partially satisfied
- `_build_ally_lines()` / `_build_opponent_lines()` patterns: async section-builder methods in context_builder.py — follow same pattern for neutral item section
- `PhaseCard` component: renders a titled card with ItemCard children — can be adapted or a new `NeutralTierCard` component built similarly
- `_POPULARITY_PHASE_MAP` dict pattern: maps API keys to display labels — similar pattern for tier-to-timing mapping
- Steam CDN item image URL pattern already works for neutral items (`/items/{internal_name}.png`)

### Established Patterns
- Context builder sections use `## Section Name` markdown headers
- Each section has a dedicated `_build_*` async method
- Claude structured output via `LLMRecommendation` Pydantic model with `output_config`
- System prompt rules use numbered principles with concrete hero/item examples
- Frontend uses Zustand stores with separate `gameStore` and `recommendationStore`

### Integration Points
- `context_builder.py` — new `_build_neutral_catalog()` method to query neutral items by tier and format for Claude
- `system_prompt.py` — new "Neutral Items" section with ranking rules
- `schemas.py` — extend `LLMRecommendation` with `neutral_items` field (list of tier objects)
- `ItemTimeline.tsx` — render new `NeutralItemSection` component below phase cards
- `matchup_service.py` — new `get_neutral_items_by_tier()` query function
- `api/routes/recommend.py` — ensure neutral items flow through the hybrid orchestrator response

</code_context>

<specifics>
## Specific Ideas

- The dedicated section should use the spectral cyan accent color to match the rest of the timeline, but with a distinct icon/label to differentiate from purchasable items
- Tier headers should show the tier number and approximate unlock time: "T1 (7 min)", "T2 (17 min)", etc.
- Neutral item images use the same Steam CDN pattern — no special handling needed
- The Claude output schema extension should be a separate `neutral_items` field (not mixed into `phases`) to keep the separation clean on both backend and frontend

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-neutral-items*
*Context gathered: 2026-03-23*

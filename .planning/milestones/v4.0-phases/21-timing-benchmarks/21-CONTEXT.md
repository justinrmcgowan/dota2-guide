# Phase 21: Timing Benchmarks - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 21 surfaces item timing benchmark data (built in Phase 19) through the full stack: a new context builder section feeds timing data to Claude for reasoning, frontend ItemCard components display timing ranges with urgency indicators, and GSI-connected games show live gold/clock comparison against timing windows. Mixed backend+frontend phase.

</domain>

<decisions>
## Implementation Decisions

### Timing Display in Item Cards
- **D-01:** Compact horizontal bar below each item in ItemCard, with good/on-track/late zones colored green→yellow→red. Win rate shown on hover tooltip. Fits existing ItemCard layout without restructuring.
- **D-02:** Items with steep win-rate falloff (timing-critical) get a pulsing accent border using the crimson color from DESIGN.md. Non-urgent items stay neutral. Visually separates TIME-02 urgency from normal items.
- **D-03:** Confidence level (strong/moderate/weak from Phase 19 D-07) appears in tooltip only on hover over the timing bar, not inline. Keeps UI clean.
- **D-04:** All items with timing data are shown, per Phase 19 D-07 (no data hidden). Weak confidence items show with muted/reduced-opacity styling on the timing bar.

### Claude Timing Reasoning
- **D-05:** New `_build_timing_section()` method in context_builder, appended after item catalog in the user message. Format per item: "BKB: good <20min (58% WR), on-track 20-25min (52%), late >25min (41%)". Approximately 200 tokens for 5-8 items.
- **D-06:** Timing data sent only for the hero's popular items (items that appear in the hero's timing benchmark data from DataCache). Filtered to items with sufficient sample size. Avoids noise from irrelevant items.
- **D-07:** Claude references timing naturally in reasoning with specific numbers. System prompt directive (already in place at lines 49-57) guides this. No forced format -- Claude cites percentages like "BKB before 25 minutes has a 58% win rate vs. 41% after 30."

### GSI Live Timing Comparison
- **D-08:** A marker on the timing bar shows "you are here" based on current game clock from GSI. Gold comparison shown as "X gold away" text below the bar. Updates via existing GSI WebSocket pipeline.
- **D-09:** When game clock passes the "late" threshold for an item, the timing bar greys out with a "window passed" label. Item stays recommended but urgency signal shifts. Does NOT remove the item.
- **D-10:** Timing comparison shows on ALL unpurchased items, not just the next one. Already-purchased items (click-to-mark) don't show timing. Consistent with existing interaction pattern.

### Claude's Discretion
- How to derive good/on-track/late ranges from TimingBucket data (percentile thresholds, win-rate inflection points)
- How to detect "steep win-rate falloff" for urgency classification (threshold for what counts as steep)
- TimingBar component structure and animation approach for the pulsing urgency border
- How the "you are here" marker updates reactively with GSI game clock
- API response schema extension for timing data (new field on ItemRecommendation or separate timing object)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` -- TIME-01, TIME-02, TIME-03, TIME-04
- `.planning/ROADMAP.md` -- Phase 21 success criteria (4 criteria that must be TRUE)

### Phase 19 Foundation (dependency)
- `.planning/phases/19-data-foundation-prompt-architecture/19-CONTEXT.md` -- TimingBucket design, DataCache timing index, confidence levels, stale-while-revalidate pattern
- `.planning/phases/19-data-foundation-prompt-architecture/19-RESEARCH.md` -- OpenDota timing endpoint details

### Backend Files
- `prismlab/backend/data/cache.py` -- TimingBucket dataclass, DataCache.get_hero_timings(hero_id), set_hero_timings()
- `prismlab/backend/engine/context_builder.py` -- Where _build_timing_section() will be added, existing _build_* pattern
- `prismlab/backend/engine/prompts/system_prompt.py` -- Lines 49-57: existing "## Timing Benchmarks" directive section
- `prismlab/backend/engine/schemas.py` -- ItemRecommendation, RecommendationResponse (may need timing fields)
- `prismlab/backend/api/routes/recommend.py` -- API endpoint returning recommendations

### Frontend Files
- `prismlab/frontend/src/components/timeline/ItemCard.tsx` -- Where timing bar will be added
- `prismlab/frontend/src/components/timeline/PhaseCard.tsx` -- Parent of ItemCard components
- `prismlab/frontend/src/components/timeline/ItemTimeline.tsx` -- Timeline container
- `prismlab/frontend/src/components/clock/GameClock.tsx` -- GSI game clock component (pattern for live updates)
- `prismlab/frontend/src/hooks/useGameIntelligence.test.ts` -- GSI hook patterns
- `DESIGN.md` -- "Tactical Relic Editorial" design system (obsidian, crimson, gold palette, 0px corners)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TimingBucket` dataclass with `time`, `games`, `wins`, `confidence`, `win_rate` property -- ready to consume
- `DataCache.get_hero_timings(hero_id)` returns `dict[str, list[TimingBucket]]` keyed by item internal name
- `context_builder._build_*` pattern for user message sections -- follow for `_build_timing_section()`
- `ItemCard.tsx` existing component -- add timing bar as child element
- `GameClock.tsx` uses GSI WebSocket for live game clock -- pattern for timing comparison updates
- `useGameIntelligence` hook consolidates GSI state -- extend for timing comparison data

### Established Patterns
- Frontend: React 19 functional components, Tailwind v4, Zustand stores, TypeScript strict
- Backend: async endpoints, Pydantic models, context builder section pattern
- Design: DESIGN.md tokens (obsidian #131313, crimson #B22222, gold #FFDB3C, 0px corners, Newsreader/Manrope fonts)
- GSI: WebSocket pipeline from backend → frontend, gsiStore for game state

### Integration Points
- Backend: context_builder.py (new timing section), schemas.py (timing fields on response), recommend route
- Frontend: ItemCard.tsx (timing bar component), PhaseCard.tsx (pass timing data down), recommendationStore (timing data)
- GSI: gsiStore or useGameIntelligence hook (gold/clock for live comparison)

</code_context>

<specifics>
## Specific Ideas

- Timing bar uses the design system's tonal layering: green zone on obsidian surface, yellow transition, crimson for late zone
- Pulsing urgency animation should be subtle -- not distracting during gameplay. Use crimson glow matching DESIGN.md's ambient shadow pattern
- "You are here" marker should be a thin vertical line or dot on the timing bar, updating in real-time via GSI
- "X gold away" text uses Manrope (body font) in small size below the timing bar
- Win rate percentages in tooltips use the gold (#FFDB3C) accent for the "good" zone numbers

</specifics>

<deferred>
## Deferred Ideas

- Per-match timing comparison (requires Steam login + match history -- Out of Scope per REQUIREMENTS.md)
- Prescriptive exact-minute targets (Out of Scope -- false precision)
- Timing-aware re-evaluation weighting (ADVINT-02 in Future Requirements)

</deferred>

---

*Phase: 21-timing-benchmarks*
*Context gathered: 2026-03-27*

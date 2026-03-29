# Phase 5: Mid-Game Adaptation - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 adds mid-game adaptation: click-to-mark purchased items in the timeline, lane result input, damage profile toggles and sliders, enemy item tracker, and a Re-Evaluate button that regenerates only unpurchased items with updated game state. After this phase, the user can progressively feed game information and get updated recommendations as the match evolves.

</domain>

<decisions>
## Implementation Decisions

### Purchased Item Tracking
- Click item in timeline → green checkmark overlay + item dims slightly (opacity reduction)
- Clicking again un-marks it. Purchased items stay in their phase position
- Purchased item IDs sent in Re-Evaluate request so backend only generates remaining items

### Lane Result Selector
- Three-button toggle: Won (teal), Even (cyan), Lost (red)
- Same toggle pattern as role/lane selectors from Phase 2
- Injected into game state for Claude context

### Damage Profile Input
- Quick toggles for common profiles: "Heavy Physical", "Heavy Magic", "Mixed", "Pure Burst"
- Fine-tune sliders below for Physical/Magical/Pure percentage (0-100%)
- Toggles set the sliders to presets; user can adjust from there

### Enemy Item Tracker
- Grid of ~15 common counter items with toggle checkboxes
- BKB, Blink Dagger, Force Staff, Ghost Scepter, Linken's Sphere, Shiva's Guard, etc.
- Click to mark as "spotted on enemy"
- Spotted items sent in Re-Evaluate request for Claude context

### Re-Evaluate Flow
- "Re-Evaluate" button at top of mid-game panel, same style as "Get Item Build" (cyan)
- Sends full updated game state to POST /api/recommend including: lane_result, damage_profile, enemy_items_spotted, purchased_items
- Backend only generates recommendations for unpurchased item slots
- Timeline updates in-place with new recommendations
- All mid-game inputs in collapsible "Game State" section in sidebar, below draft inputs
- Section appears after first recommendation is generated

### Claude's Discretion
- Exact enemy item grid contents (which 15 items to include)
- Slider component implementation (native range input or custom)
- Collapsible section animation
- How backend handles purchased_items in the recommendation flow

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `recommendationStore.ts` — Has recommendation state, can add purchased tracking
- `useRecommendation.ts` — Has recommend() function, can extend with re-evaluate
- `gameStore.ts` — Can add laneResult, damageProfile, enemyItemsSpotted fields
- `ItemCard.tsx` — Can add click-to-purchase interaction and checkmark overlay
- `GetBuildButton.tsx` — Pattern for the Re-Evaluate button
- `RoleSelector.tsx`, `LaneSelector.tsx` — Toggle button patterns to reuse

### Established Patterns
- Zustand flat store with typed actions
- Toggle button group components
- Tailwind v4 CSS-first theming with OKLCH colors
- Controlled component pattern

### Integration Points
- `Sidebar.tsx` — Add "Game State" collapsible section
- `MainPanel.tsx` — ItemCard needs purchase click handler
- Backend POST /api/recommend — Needs to accept additional game state fields
- Backend `engine/recommender.py` — Needs to handle purchased_items filtering
- Backend `engine/context_builder.py` — Needs to include mid-game context in Claude prompt

</code_context>

<specifics>
## Specific Ideas

- Backend RecommendRequest schema needs new optional fields: lane_result, damage_profile, enemy_items_spotted, purchased_items
- Context builder should include mid-game state in the Claude prompt when present
- The Re-Evaluate flow reuses the same POST /api/recommend endpoint with additional fields
- Purchased items should be visually distinct but not removed from the timeline (user may want to un-purchase)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

# Phase 4: Item Timeline and End-to-End Flow - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 connects the frontend draft inputs to the backend recommendation engine and renders the item timeline with reasoning. After this phase, the user can fill in their draft, click "Get Item Build", see a phased item timeline with analytical reasoning, situational decision trees, loading skeletons, and error/fallback handling. This is the integration checkpoint — if this works, the product is viable.

</domain>

<decisions>
## Implementation Decisions

### Item Timeline Layout
- Vertical stack of phase cards (Starting → Laning → Core → Late Game) in the MainPanel
- Each phase card has a header bar with phase name, items displayed as horizontal row of icons
- Item icons are ~48px with gold cost displayed below
- Click an item to expand reasoning panel below the phase — shows 1-3 sentences referencing specific hero abilities
- Click another item to switch reasoning display

### Decision Trees & Error States
- Situational items display as branching cards with condition text and 2-3 item options (e.g., "If enemy has evasion → MKB | If magic immunity → Nullifier")
- Each branch shows item icon + condition text
- Errors show as inline amber alert bar at top of MainPanel with dismiss button
- Fallback notice: subtle amber banner above timeline "AI reasoning unavailable — showing basic recommendations"

### Loading States
- Skeleton placeholders matching timeline layout structure (phase card outlines with pulsing item placeholders)
- Shows within MainPanel where results will appear
- Visible during 2-10 second Claude API call

### End-to-End Wiring
- API call fires on "Get Item Build" button click — explicit user action
- After initial recommendations render, show "Select Lane Opponents" prompt — user picks 1-2 from already-chosen opponents, then can re-fire with updated context
- Recommendation state lives in separate `recommendationStore` (Zustand) — response data, loading, error, selected item for reasoning
- `useRecommendation` hook wraps store + API call: `{ recommend, data, isLoading, error, selectedItem, selectItem }`
- GetBuildButton triggers `recommend()` which reads gameStore state and POSTs to /api/recommend

### Claude's Discretion
- Exact skeleton animation style
- Phase card visual styling details (borders, backgrounds, spacing)
- Reasoning panel transition/animation approach
- Decision tree card visual layout
- Lane opponent prompt positioning and UX flow

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `api/client.ts` — fetchJson wrapper, extend with postJson for /api/recommend
- `stores/gameStore.ts` — Full draft state to send in request body
- `types/item.ts` — Item TypeScript interface
- `utils/imageUrls.ts` — itemImageUrl builder for Steam CDN
- `components/draft/GetBuildButton.tsx` — Currently logs to console, needs wiring
- `components/draft/LaneOpponentPicker.tsx` — Already built in Phase 2

### Established Patterns
- Zustand create() with typed interface
- Functional components with Tailwind v4 styling
- Dark theme with spectral cyan accent (#00d4ff), Radiant teal (#6aff97), Dire red (#ff5555)

### Integration Points
- `GetBuildButton.tsx` — onClick needs to call useRecommendation.recommend()
- `MainPanel.tsx` — Currently empty placeholder, will render Timeline or loading skeleton
- `App.tsx` — May need recommendation store provider or layout adjustments
- Backend POST /api/recommend — Expects RecommendRequest, returns RecommendResponse

</code_context>

<specifics>
## Specific Ideas

- Backend RecommendResponse schema from Phase 3: phases[] with items[] each having item_id, item_name, reasoning, priority, conditions
- The response includes metadata: fallback (boolean), model (string), latency_ms (number)
- Frontend needs TypeScript types matching backend Pydantic schemas
- Item images from Steam CDN: https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/{name}.png

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

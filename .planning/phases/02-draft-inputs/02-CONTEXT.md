# Phase 2: Draft Inputs - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 builds the complete draft input sidebar — ally hero pickers (4 slots), opponent hero pickers (5 slots), role selector (Pos 1-5), playstyle selector (role-dependent options), Radiant/Dire side selector, lane selector (Safe/Mid/Off), and a "Get Item Build" CTA button. All wired to an extended Zustand store. After this phase, the user can configure their complete draft context through the sidebar.

</domain>

<decisions>
## Implementation Decisions

### Multi-Hero Picker Layout
- Compact row of 5 circular portraits (~32px) with "+" add buttons for empty slots. Click opens same HeroPicker dropdown pattern from Phase 1
- Ally section has Radiant teal border, opponent section has Dire red border for visual distinction
- Lane opponent picker filters from already-picked enemy heroes — shows only the 5 picked opponents, user selects 1-2 as lane opponents. Separate small section below lane selector
- Sidebar order: Your hero (top) → Allies → Opponents → Role → Playstyle → Side → Lane → CTA button

### Role & Playstyle Selectors
- Role selector: 5 horizontal toggle buttons — "Pos 1 Carry", "Pos 2 Mid", "Pos 3 Off", "Pos 4 Soft Sup", "Pos 5 Hard Sup". One active at a time
- Playstyle: 3-4 pill buttons that change per role. Animate in after role selection (hidden/disabled until role picked)
- Playstyle options per role:
  - Pos 1: Farm-first, Aggressive, Split-push, Fighting
  - Pos 2: Tempo, Ganker, Greedy, Space-maker
  - Pos 3: Frontline, Aura-carrier, Initiator, Greedy
  - Pos 4: Roamer, Lane-dominator, Greedy, Save
  - Pos 5: Lane-protector, Roamer, Greedy, Save

### Side & Lane Selectors
- Side: Two-button toggle — "Radiant" (teal #6aff97) vs "Dire" (red #ff5555). Color-coded, one active
- Lane: Three horizontal buttons — "Safe", "Mid", "Off". Same toggle style as role selector
- CTA button: Prominent spectral cyan "Get Item Build" button at bottom of sidebar. Disabled until at minimum your hero + role are selected. Lights up when ready

### Zustand Store
- Extend existing gameStore with: allies (Hero[]), opponents (Hero[]), role (number | null), playstyle (string | null), side ('radiant' | 'dire' | null), lane ('safe' | 'mid' | 'off' | null), laneOpponents (Hero[]). Single flat store, all nullable, updated independently

### Claude's Discretion
- Animation approach for playstyle reveal (CSS transition, Framer Motion, or Tailwind animate)
- Exact compact portrait sizing and spacing
- HeroPicker dropdown positioning and overlay behavior
- Whether to use the same HeroPicker component or a variant for multi-slot picking

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `HeroPicker.tsx` — Already has search, portraits, excludedHeroIds prop. Can reuse for ally/opponent slots
- `HeroPortrait.tsx` — Supports "sm", "md", "lg" sizes with attribute dots. Use "sm" for compact rows
- `heroSearch.ts` — Fuse.js hybrid search ready to reuse
- `useHeroes.ts` — Hook for fetching hero list, already works
- `gameStore.ts` — Zustand store to extend (currently just selectedHero)
- `constants.ts` — ATTR_COLORS and ATTR_BG_COLORS
- `imageUrls.ts` — Steam CDN URL builders

### Established Patterns
- Tailwind v4 with CSS-first @theme config in globals.css
- OKLCH color values for theme colors
- Zustand create() with typed interface
- Functional React components with TypeScript

### Integration Points
- Sidebar.tsx — Currently renders HeroPicker for "Your Hero". Will add all new sections below it
- gameStore.ts — Needs new fields and actions for allies, opponents, role, playstyle, side, lane
- App.tsx — MainPanel may need to show draft summary

</code_context>

<specifics>
## Specific Ideas

- The excludedHeroIds prop on HeroPicker from Phase 1 is specifically designed for this phase — pass Set of all picked hero IDs to prevent duplicates across all 10 slots
- The CTA button enables the Phase 3 → Phase 4 flow (POST /api/recommend)
- Lane opponent picker is distinct from the main opponent picker — it's a secondary selection from already-chosen enemies

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

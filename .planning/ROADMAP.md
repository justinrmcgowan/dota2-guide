# Roadmap: Prismlab

## Milestones

- [x] **v1.0 MVP** - Phases 1-6 (shipped 2026-03-21)
- [x] **v1.1 Allied Synergy & Neutral Items** - Phases 7-9 (shipped 2026-03-23)
- [x] **v2.0 Live Game Intelligence** - Phases 10-14 (shipped 2026-03-26)
- [ ] **v3.0 Design Overhaul & Performance** - Phases 15-18 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

<details>
<summary>v1.0 MVP (Phases 1-6) - SHIPPED 2026-03-21</summary>

- [x] **Phase 1: Foundation** - Project scaffolding, Docker, DB models, OpenDota client
- [x] **Phase 2: Draft Inputs** - Hero picker, role/playstyle selection, lane/side UI
- [x] **Phase 3: Recommendation Engine** - Rules layer, Claude API integration, hybrid orchestrator
- [x] **Phase 4: Item Timeline & End-to-End Flow** - Phased item display with reasoning tooltips
- [x] **Phase 5: Mid-Game Adaptation** - Lane result, damage profile, enemy items, re-evaluate
- [x] **Phase 6: Data Pipeline & Hardening** - Daily refresh, error handling, polish

</details>

<details>
<summary>v1.1 Allied Synergy & Neutral Items (Phases 7-9) - SHIPPED 2026-03-23</summary>

- [x] **Phase 7: Tech Debt & Polish** - Dead code removal, tests, admin proxy
- [x] **Phase 8: Allied Synergy** - Ally item context, team coordination prompt rules
- [x] **Phase 9: Neutral Items** - Neutral item pipeline, Claude ranking, tier display

</details>

<details>
<summary>v2.0 Live Game Intelligence (Phases 10-14) - SHIPPED 2026-03-26</summary>

- [x] **Phase 10: GSI Receiver & WebSocket Pipeline** - Dota 2 GSI endpoint, WebSocket broadcast, frontend connection
- [x] **Phase 11: Live Game Dashboard** - Auto hero/role detection, item marking, stats bar, game clock
- [x] **Phase 12: Auto-Refresh & Lane Detection** - Event triggers, cooldown queue, lane auto-detect, toast notifications
- [x] **Phase 13: Screenshot Parsing** - Claude Vision endpoint, screenshot modal, clipboard paste, Apply to Build
- [x] **Phase 14: Recommendation Quality & System Hardening** - Rate limiter, response cache, validation, rules expansion

</details>

### v3.0 Design Overhaul & Performance (In Progress)

**Milestone Goal:** Transform Prismlab's visual identity to the "Tactical Relic Editorial" design system, add in-memory data caching for performance, and close integration gaps from v2.0.

- [x] **Phase 15: Store Consolidation & Tech Debt** - Merge GSI hooks, deduplicate types, auto-suggest playstyle (completed 2026-03-27)
- [x] **Phase 16: Backend Data Cache** - In-memory hero/item cache, three-layer cache coordination, session safety (completed 2026-03-27)
- [x] **Phase 17: Design System Migration** - Tactical Relic Editorial retheme across all components (see DESIGN.md) (completed 2026-03-27)
- [ ] **Phase 18: Screenshot KDA Feed-Through** - Feed parsed KDA/level data into recommendation context

## Phase Details

### Phase 15: Store Consolidation & Tech Debt
**Goal**: GSI-driven hooks are consolidated into a single, correctly-ordered subscription with no duplicated types
**Depends on**: Phase 14
**Requirements**: INT-01, INT-02, INT-04
**Success Criteria** (what must be TRUE):
  1. A single `useGameIntelligence` hook replaces both `useGsiSync` and `useAutoRefresh` with one `gsiStore` subscription
  2. When GSI detects a hero and role, a playstyle is auto-suggested without the user manually selecting one
  3. The `TriggerEvent` interface exists in exactly one file (`triggerDetection.ts`) with all consumers importing from that single source
  4. All existing GSI behavior (hero detection, item marking, event triggers, lane auto-detect, auto-refresh) still works identically
**Plans**: 2 plans

Plans:
- [x] 15-01-PLAN.md — TriggerEvent dedup, HERO_PLAYSTYLE_MAP data file
- [x] 15-02-PLAN.md — useGameIntelligence hook consolidation, App.tsx wiring, old hook deletion

### Phase 16: Backend Data Cache
**Goal**: Hero and item data is served from an in-memory cache, eliminating per-request DB queries on the recommendation hot path
**Depends on**: Phase 14 (backend only, independent of Phase 15)
**Requirements**: PERF-01, PERF-02, PERF-03, INT-05, INT-06
**Success Criteria** (what must be TRUE):
  1. The `/api/recommend` endpoint completes without any hero/item DB queries (all data comes from `DataCache`)
  2. After the 6-hour data pipeline runs, DataCache, RulesEngine, and ResponseCache all reflect fresh data without requiring a server restart
  3. The `refresh_lookups()` function uses a fresh session (not the pipeline's session) for safe async operation
  4. `/api/heroes` and `/api/items` endpoints serve data from cache with sub-millisecond reads
  5. On cold start, the cache loads after seeding completes (no empty-cache race condition)
**Plans**: 2 plans

Plans:
- [x] 16-01-PLAN.md — DataCache singleton with frozen dataclasses, RulesEngine refactor to consume cache
- [x] 16-02-PLAN.md — Hot path wiring (context builder, recommender, routes), lifespan loading, coordinated refresh invalidation

### Phase 17: Design System Migration
**Goal**: Every visual surface in Prismlab matches the "Tactical Relic Editorial" spec in DESIGN.md -- obsidian surfaces, crimson/gold accents, Newsreader/Manrope typography, 0px corners
**Depends on**: Phase 15 (hooks stable before touching component files)
**Requirements**: DESIGN-01, DESIGN-02, DESIGN-03, DESIGN-04, DESIGN-05, DESIGN-06, DESIGN-07, DESIGN-08
**Success Criteria** (what must be TRUE):
  1. The app renders with Newsreader for display/headline text and Manrope for body/label text, self-hosted with no external CDN dependency
  2. All surfaces use the obsidian tonal hierarchy (#131313 base through #353534 highest) with no visible 1px borders or rounded corners (except documented functional exceptions)
  3. Floating elements (modals, settings panel, screenshot parser) display ambient crimson glow shadows and blood-glass backdrop-blur overlays
  4. Hero and legendary item cards show gold left-accent strips; the base background has a parchment noise texture overlay
  5. A visual audit of all ~30 components finds zero instances of old tokens (cyan accent, #FFFFFF text, rounded corners, blue links)
**Plans**: 5 plans
**UI hint**: yes

Plans:
- [x] 17-01-PLAN.md — Font swap (Newsreader + Manrope) and @theme token replacement in globals.css
- [x] 17-02-PLAN.md — Layout shell (App, Header, Sidebar, MainPanel) and draft-input components migration
- [x] 17-03-PLAN.md — Timeline components (ItemCard, PhaseCard, NeutralItems) and game-state components migration
- [x] 17-04-PLAN.md — Floating overlays (SettingsPanel, ScreenshotParser, Toast, ErrorBanner) with blood-glass effects
- [x] 17-05-PLAN.md — Parchment noise texture, deprecated token removal, full visual audit and human verification

### Phase 18: Screenshot KDA Feed-Through
**Goal**: Parsed enemy KDA and level data from screenshots enriches Claude's recommendation reasoning about enemy power levels and timing windows
**Depends on**: Phase 16 (backend schema), Phase 17 (UI consistency)
**Requirements**: INT-03
**Success Criteria** (what must be TRUE):
  1. After applying a parsed screenshot, enemy KDA and level data appears in the recommendation request sent to the backend
  2. Claude's reasoning references enemy economic state (e.g., "Enemy PA is 8-1-3 and snowballing -- prioritize defensive items") when KDA data is available
**Plans**: 1 plan
**UI hint**: yes

Plans:
- [ ] 18-01-PLAN.md — EnemyContext schema, context builder KDA section, system prompt update, frontend store + handleApply wiring

## Progress

**Execution Order:**
Phases execute in numeric order: 15 -> 16 -> 17 -> 18

Note: Phase 16 is backend-only and could execute in parallel with Phase 15 (frontend-only), but sequential execution is the default.

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 15. Store Consolidation & Tech Debt | v3.0 | 2/2 | Complete    | 2026-03-27 |
| 16. Backend Data Cache | v3.0 | 2/2 | Complete    | 2026-03-27 |
| 17. Design System Migration | v3.0 | 5/5 | Complete    | 2026-03-27 |
| 18. Screenshot KDA Feed-Through | v3.0 | 0/1 | Not started | - |

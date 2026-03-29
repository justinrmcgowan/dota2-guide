# Roadmap: Prismlab

## Milestones

- [x] **v1.0 MVP** - Phases 1-6 (shipped 2026-03-21)
- [x] **v1.1 Allied Synergy & Neutral Items** - Phases 7-9 (shipped 2026-03-23)
- [x] **v2.0 Live Game Intelligence** - Phases 10-14 (shipped 2026-03-26)
- [x] **v3.0 Design Overhaul & Performance** - Phases 15-18 (shipped 2026-03-27)
- [x] **v4.0 Coaching Intelligence** - Phases 19-23 (shipped 2026-03-28)
- [x] **v5.0 Supreme Companion** - Phases 24-29, 33 (shipped 2026-03-29)
- [ ] **v6.0 Draft Intelligence** - Phases 30-31 (planned)
- [ ] **v7.0 Desktop Distribution** - Phase 32 (planned)

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

<details>
<summary>v3.0 Design Overhaul & Performance (Phases 15-18) - SHIPPED 2026-03-27</summary>

- [x] **Phase 15: Store Consolidation & Tech Debt** - Merge GSI hooks, deduplicate types, auto-suggest playstyle
- [x] **Phase 16: Backend Data Cache** - In-memory hero/item cache, three-layer cache coordination, session safety
- [x] **Phase 17: Design System Migration** - Tactical Relic Editorial retheme across all components
- [x] **Phase 18: Screenshot KDA Feed-Through** - Feed parsed KDA/level data into recommendation context

</details>

<details>
<summary>v4.0 Coaching Intelligence (Phases 19-23) - SHIPPED 2026-03-28</summary>

- [x] **Phase 19: Data Foundation & Prompt Architecture** - Ability/timing data pipeline, DataCache extensions, system-prompt-vs-user-message data split (completed 2026-03-27)
- [x] **Phase 20: Counter-Item Intelligence** - Ability-driven counter rules, counter_target tagging, threat context for Claude (completed 2026-03-27)
- [x] **Phase 21: Timing Benchmarks** - Timing windows in UI, urgency indicators, Claude timing reasoning, GSI live comparison (completed 2026-03-27)
- [x] **Phase 22: Build Path Intelligence** - Component ordering, adaptive build paths, GSI gold tracking (completed 2026-03-27)
- [x] **Phase 23: Win Condition Framing** - Draft classification, strategy anchoring, enemy win condition assessment (completed 2026-03-27)

</details>

<details>
<summary>v5.0 Supreme Companion (Phases 24-29, 33) - SHIPPED 2026-03-29</summary>

- [x] **Phase 24: Audio Prompts & Volume Control** - TTS/audio cues for item timing alerts, purchase reminders, coaching callouts with volume control (completed 2026-03-29)
- [x] **Phase 25: API-Driven Draft Input** - Auto-populate allies/opponents from OpenDota/Stratz live match API using Steam ID (completed 2026-03-28)
- [x] **Phase 26: Engine Optimization** - Reduce eval latency, rule-only fast path, local LLM via Ollama, courier exclusion, concise reasoning (completed 2026-03-28)
- [x] **Phase 27: Game Lifecycle Management** - Handle mid-game abandons, new game starts, state reset between matches, GSI reconnection (completed 2026-03-28)
- [x] **Phase 28: Patch 7.41 Data Refresh** - New items, updated costs/recipes for patch 7.41 (completed 2026-03-28)
- [x] **Phase 29: Stream Deck Integration** - Elgato Stream Deck plugin consuming existing WebSocket game state feed (completed 2026-03-29)
- [x] **Phase 33: Game Analytics & Match Logging** - Match logging, recommendation tracking, match history dashboard (completed 2026-03-28)

</details>

### v6.0 Draft Intelligence (Planned)

- [x] **Phase 30: ML Win Predictor** - XGBoost/logistic regression model trained on 200k+ recent matches, draft win probability, synergy/counter matrices by MMR bracket (completed 2026-03-29)
- [ ] **Phase 31: Hero Selector** - Role/lane-filtered hero suggestions ranked by predicted win rate, ally synergy, and enemy counter-value

### v7.0 Desktop Distribution (Planned)

- [ ] **Phase 32: Tauri Desktop App** - Native Windows app via Tauri (React frontend in native webview, Python backend as sidecar), first-run wizard with API key entry, auto-detect Dota 2 path, GSI cfg placement, system tray, native notifications

## Phase Details

### v6.0 Draft Intelligence (Planned)

**Milestone Goal:** Add statistical ML-driven draft analysis — win probability prediction from hero compositions and intelligent hero suggestions filtered by role, lane, and team context. Combines data-driven predictions with Prismlab's existing Claude reasoning for high-confidence draft decisions.

### Phase 30: ML Win Predictor
**Goal**: Users can see a statistical win probability for their draft alongside Claude's qualitative win condition assessment
**Depends on**: Phase 28 (current patch data), Phase 23 (win condition framing for comparison)
**Requirements**: PRED-01, PRED-02, PRED-03, PRED-04, PRED-05
**Success Criteria** (what must be TRUE):
  1. User sees a win probability percentage for the allied team whenever a 10-hero draft is present
  2. Win probability changes meaningfully as different hero compositions are entered
  3. Precomputed synergy and counter matrices are available to the prediction engine, segmented by MMR bracket
  4. Win probability appears in the recommendation view alongside Claude's win condition framing so users can compare statistical and reasoning-based signals
  5. The model is trained on 200k+ recent OpenDota matches filtered to current patch
**Plans**: 3 plans

Plans:
- [x] 30-01-PLAN.md — Training pipeline: OpenDota data download, XGBoost training, synergy/counter matrices (PRED-02, PRED-03, PRED-04)
- [x] 30-02-PLAN.md — Runtime integration: WinPredictor class, DataCache extension, RecommendResponse field, recommender enrichment (PRED-01)
- [x] 30-03-PLAN.md — UI display: WinConditionBadge updated to show "Teamfight 54%" (PRED-05)

### Phase 31: Hero Selector
**Goal**: Users can get ranked hero suggestions for their role and lane that account for current ally synergies and enemy counter-value before locking in their hero
**Depends on**: Phase 30 (ML model must be trained and serving predictions), Phase 25 (API-driven draft input for live draft context)
**Requirements**: HERO-01, HERO-02, HERO-03, HERO-04
**Success Criteria** (what must be TRUE):
  1. User can invoke a "Suggest Hero" flow from the draft input panel before entering a hero and receive a ranked list of candidates
  2. Suggestions are filtered to heroes viable for the user's selected position and lane
  3. Suggestions rank higher for heroes with strong synergy with already-picked allies and counter-value against already-picked enemies
  4. User can select a suggested hero directly from the list and the draft input updates, proceeding to the recommendation flow
**Plans**: 3 plans

Plans:
- [ ] 31-01-PLAN.md — Backend scoring engine: SuggestHero schemas + HeroSelector class with HERO_ROLE_VIABLE filter and matrix scoring (HERO-01, HERO-02, HERO-03)
- [ ] 31-02-PLAN.md — Frontend contracts: TypeScript types + api.suggestHero() client method (HERO-04)
- [ ] 31-03-PLAN.md — Integration: POST /api/suggest-hero route, HeroSuggestPanel component, Sidebar wiring (HERO-01, HERO-02, HERO-03, HERO-04)

### v7.0 Desktop Distribution (Planned)

**Milestone Goal:** Package Prismlab as a one-click Windows installer that non-technical users can install and run locally, with automatic Dota 2 GSI configuration, API key setup, and system tray operation.

### Phase 32: Tauri Desktop App

**Goal:** Package Prismlab as a native Windows desktop application using Tauri v2. The existing React frontend renders in a native webview (no browser tab, no Electron bloat, ~15MB footprint). The Python FastAPI backend runs as a Tauri sidecar process (bundled via PyInstaller into a standalone exe that Tauri spawns and manages). First-run wizard handles Anthropic API key entry, auto-detects Dota 2 install path (Steam registry key → libraryfolders.vdf parsing across all library folders), generates and places `gamestate_integration_prismlab.cfg` into the correct `game\dota\cfg\gamestate_integration\` directory, and prompts user to add `-gamestateintegration` to Dota 2 launch options. Native system tray icon with "Open" / "Quit" via Tauri's tray API. Native OS notifications for item timing alerts (ties into Phase 24 audio prompts). Config stored in platform-appropriate app data directory via Tauri's path API. Produces a single `.msi` or `.exe` installer via Tauri's built-in bundler (WiX-based). Docker Compose deployment remains for dev/server use — Tauri app is a separate build target
**Requirements**: TBD
**Depends on:** Phase 27 (game lifecycle must be solid before shipping to external users), Phase 28 (current patch data)
**Plans:** 3/3 plans complete

Plans:
- [ ] TBD (run /gsd:plan-phase 32 to break down)

**Architecture Notes:**
- Tauri v2 handles: native window, system tray, notifications, installer bundling (WiX `.msi`), auto-updater, app data paths
- Python backend: bundled as a PyInstaller sidecar exe, spawned by Tauri's sidecar API, communicates via localhost HTTP (same as current Docker setup)
- React frontend: builds to static files, loaded by Tauri's webview — existing code unchanged
- Dota 2 detection: Rust-side reads Windows Registry (`HKLM\SOFTWARE\WOW6432Node\Valve\Steam`), parses `libraryfolders.vdf`, locates `dota 2 beta\game\dota\cfg\gamestate_integration\`
- GSI cfg: generated and placed automatically, no user file management required
- Launch options: wizard screen explains adding `-gamestateintegration` to Dota 2 Steam properties (cannot be automated safely)

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 30. ML Win Predictor | 3/3 | Complete    | 2026-03-29 |
| 31. Hero Selector | 0/3 | Not started | - |
| 32. Tauri Desktop App | 0/TBD | Not started | - |

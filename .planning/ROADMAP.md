# Roadmap: Prismlab

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-21)
- ✅ **v1.1 Allied Synergy & Neutral Items** — Phases 7-9 (shipped 2026-03-23)
- 🚧 **v2.0 Live Game Intelligence** — Phases 10-14 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-6) — SHIPPED 2026-03-21</summary>

- [x] Phase 1: Foundation (3/3 plans) — completed 2026-03-21
- [x] Phase 2: Draft Inputs (2/2 plans) — completed 2026-03-21
- [x] Phase 3: Recommendation Engine (3/3 plans) — completed 2026-03-21
- [x] Phase 4: Item Timeline and End-to-End Flow (3/3 plans) — completed 2026-03-21
- [x] Phase 5: Mid-Game Adaptation (2/2 plans) — completed 2026-03-21
- [x] Phase 6: Data Pipeline and Hardening (1/1 plan) — completed 2026-03-21

</details>

<details>
<summary>✅ v1.1 Allied Synergy & Neutral Items (Phases 7-9) — SHIPPED 2026-03-23</summary>

- [x] Phase 7: Tech Debt & Polish (2/2 plans) — completed 2026-03-22
- [x] Phase 8: Allied Synergy (2/2 plans) — completed 2026-03-23
- [x] Phase 9: Neutral Items (2/2 plans) — completed 2026-03-23

</details>

### 🚧 v2.0 Live Game Intelligence (In Progress)

**Milestone Goal:** Transform Prismlab from manual-input advisor to live-game-aware system using Dota 2 GSI, screenshot parsing, and auto gold tracking -- recommendations evolve in real-time as the game progresses.

- [x] **Phase 10: GSI Receiver & WebSocket Pipeline** - Backend receives live game data from Dota 2 and pushes it to the frontend in real-time (completed 2026-03-26)
- [x] **Phase 11: Live Game Dashboard** - Frontend consumes GSI data to auto-detect hero, track gold, mark purchased items, and display game clock (completed 2026-03-26)
- [ ] **Phase 12: Auto-Refresh & Lane Detection** - Recommendations auto-refresh on key game events with rate limiting and auto-determined lane results
- [ ] **Phase 13: Screenshot Parsing** - User pastes scoreboard screenshots to extract enemy hero and item data via Claude Vision
- [ ] **Phase 14: Recommendation Quality & System Hardening** - Improve engine reliability, cache all API calls, add rate limiting, fix validation gaps, and harden error handling

## Phase Details

### Phase 10: GSI Receiver & WebSocket Pipeline
**Goal**: Live Dota 2 game state flows from the game client through the backend to the frontend in real-time, with infrastructure ready for all downstream features
**Depends on**: Phase 9 (v1.1 complete)
**Requirements**: GSI-01, WS-01, INFRA-01, INFRA-02
**Success Criteria** (what must be TRUE):
  1. When a Dota 2 game is running with the GSI config installed, the backend receives and parses game state updates every 0.5 seconds
  2. Frontend receives live game state via WebSocket within 1 second of the game client sending it
  3. A connection status indicator shows green when GSI is connected, gray when idle, and red when disconnected
  4. User can download a generated GSI config file with their server's IP address pre-filled
  5. WebSocket auto-reconnects after disconnection without user intervention
**Plans**: 3 plans

Plans:
- [x] 10-01-PLAN.md -- Backend GSI module (models, receiver, state manager, config generator)
- [x] 10-02-PLAN.md -- WebSocket broadcast layer and Nginx proxy config
- [x] 10-03-PLAN.md -- Frontend WebSocket hook, GSI store, status indicator, settings panel

**UI hint**: yes

### Phase 11: Live Game Dashboard
**Goal**: The player sees their live game state in the UI without any manual input -- hero auto-detected, gold tracked, purchased items marked, game clock visible
**Depends on**: Phase 10
**Requirements**: GSI-02, GSI-03, GSI-04, WS-02, WS-03, WS-04
**Success Criteria** (what must be TRUE):
  1. When a game starts, the player's hero is auto-detected and populates the hero picker without manual selection
  2. Real-time gold, GPM, and net worth display in the sidebar, replacing manual lane result input when GSI is active
  3. Items the player purchases in-game are automatically marked as bought in the item timeline within seconds
  4. Game clock is visible in the UI and neutral item tier timing updates automatically as the game progresses
  5. All manual input controls remain functional as fallback when GSI is not connected
**Plans**: 3 plans

Plans:
- [x] 11-01-PLAN.md -- Utility functions (neutralTiers, itemMatching) and useAnimatedValue hook
- [x] 11-02-PLAN.md -- useGsiSync hook, LiveStatsBar component, Sidebar/App wiring
- [x] 11-03-PLAN.md -- GameClock component, NeutralItemSection tier highlighting, Header wiring

**UI hint**: yes

### Phase 12: Auto-Refresh & Lane Detection
**Goal**: Recommendations update hands-free when the game state changes significantly, and lane outcome is determined automatically from gold data
**Depends on**: Phase 11
**Requirements**: GSI-05, REFRESH-01, REFRESH-02, REFRESH-03
**Success Criteria** (what must be TRUE):
  1. At the 10-minute mark, lane result (won/even/lost) is auto-determined from GPM vs role benchmarks and the player can confirm or override it
  2. Recommendations auto-refresh when a key event occurs (item purchase, death, tower kill, Roshan, gold swing >2000g) without the player pressing Re-Evaluate
  3. Auto-refresh never fires more than once per 2 minutes, even if multiple events occur in rapid succession
  4. A notification toast appears after each auto-refresh explaining what triggered the update
**Plans**: TBD

### Phase 13: Screenshot Parsing
**Goal**: The player can capture enemy item builds from a scoreboard screenshot instead of manually entering them, with Claude Vision extracting the data
**Depends on**: Phase 10 (uses Claude API; independent of Phases 11-12 GSI display features)
**Requirements**: SCREEN-01, SCREEN-02, SCREEN-03, SCREEN-04
**Success Criteria** (what must be TRUE):
  1. User can paste (Ctrl+V) or upload a scoreboard screenshot and the backend parses it via Claude Vision
  2. Parsed results show all 5 enemy heroes and their item builds in a confirmation UI before applying to recommendations
  3. Enemy hero identification is extracted from the scoreboard and matches against the draft inputs
  4. Kill/death scores are extracted from the scoreboard and used for game state assessment
  5. After the user confirms parsed results, enemy item data feeds into the next recommendation refresh
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 10 -> 11 -> 12 -> 13 -> 14

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-03-21 |
| 2. Draft Inputs | v1.0 | 2/2 | Complete | 2026-03-21 |
| 3. Recommendation Engine | v1.0 | 3/3 | Complete | 2026-03-21 |
| 4. Item Timeline & E2E | v1.0 | 3/3 | Complete | 2026-03-21 |
| 5. Mid-Game Adaptation | v1.0 | 2/2 | Complete | 2026-03-21 |
| 6. Data Pipeline | v1.0 | 1/1 | Complete | 2026-03-21 |
| 7. Tech Debt & Polish | v1.1 | 2/2 | Complete | 2026-03-22 |
| 8. Allied Synergy | v1.1 | 2/2 | Complete | 2026-03-23 |
| 9. Neutral Items | v1.1 | 2/2 | Complete | 2026-03-23 |
| 10. GSI Receiver & WebSocket Pipeline | v2.0 | 3/3 | Complete    | 2026-03-26 |
| 11. Live Game Dashboard | v2.0 | 3/3 | Complete   | 2026-03-26 |
| 12. Auto-Refresh & Lane Detection | v2.0 | 0/0 | Not started | - |
| 13. Screenshot Parsing | v2.0 | 0/0 | Not started | - |
| 14. Recommendation Quality & System Hardening | v2.0 | 0/0 | Not started | - |

### Phase 14: Recommendation Quality & System Hardening

**Goal:** [To be planned]
**Requirements**: TBD
**Depends on:** Phase 13
**Plans:** 3/3 plans complete

Plans:
- [ ] TBD (run /gsd:plan-phase 14 to break down)

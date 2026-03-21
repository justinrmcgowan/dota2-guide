# Roadmap: Prismlab

## Overview

Prismlab delivers a Dota 2 adaptive item advisor in six phases, following the critical path: data foundation, draft inputs, recommendation engine, timeline display, mid-game adaptation, and data pipeline hardening. The first four phases produce a working end-to-end flow (hero selection through item timeline with reasoning). Phase 5 adds the mid-game "living advisor" differentiator. Phase 6 hardens the data pipeline for production reliability. The recommendation engine (Phase 3) is the highest-risk phase and the heart of the product.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Project scaffolding, Docker deployment, database with seeded data, hero picker, dark theme
- [ ] **Phase 2: Draft Inputs** - Complete draft input sidebar with all selectors wired to state
- [ ] **Phase 3: Recommendation Engine** - Hybrid rules + Claude API engine with matchup data and fallback
- [ ] **Phase 4: Item Timeline and End-to-End Flow** - Timeline display with reasoning, loading states, and full draft-to-recommendation loop
- [ ] **Phase 5: Mid-Game Adaptation** - Purchased item tracking, game state updates, and re-evaluation
- [ ] **Phase 6: Data Pipeline and Hardening** - Automated daily data refresh and production reliability

## Phase Details

### Phase 1: Foundation
**Goal**: Player can launch the app, see a polished dark-themed interface, search for and select a hero, and the system has hero/item data ready in the database
**Depends on**: Nothing (first phase)
**Requirements**: DRFT-01, DISP-06, INFR-01, INFR-03
**Success Criteria** (what must be TRUE):
  1. Docker Compose brings up both containers (frontend on 8421, backend on 8420) with a single command
  2. User sees a dark-themed interface with spectral cyan accent, and a favicon appears in the browser tab
  3. User can type a hero name into a searchable dropdown and select from filtered results showing hero portraits from Steam CDN
  4. Backend serves hero and item data from SQLite (seeded from OpenDota) via API endpoints
  5. Environment configuration works via .env file with ANTHROPIC_API_KEY and optional API keys
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — Backend scaffolding, FastAPI, SQLAlchemy models, OpenDota seeding, Docker Compose
- [x] 01-02-PLAN.md — Frontend scaffolding, React + Vite + Tailwind v4 dark theme, layout, types, Nginx
- [x] 01-03-PLAN.md — Hero picker with Fuse.js fuzzy search, Steam CDN portraits, Zustand wiring

### Phase 2: Draft Inputs
**Goal**: Player can configure their complete draft context -- allies, opponents, role, playstyle, side, and lane -- through a polished input sidebar
**Depends on**: Phase 1
**Requirements**: DRFT-02, DRFT-03, DRFT-04, DRFT-05, DRFT-06, DRFT-07
**Success Criteria** (what must be TRUE):
  1. User can search and select 4 allied heroes and 5 opponent heroes using the same searchable dropdown pattern as the main hero picker
  2. User can select their position (Pos 1-5) and see playstyle options that change based on the selected role
  3. User can select Radiant or Dire side and their lane assignment (Safe/Off/Mid)
  4. All selections persist in the Zustand store and are visible in the sidebar simultaneously
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — Zustand store extension with tests, draft option constants, HeroPicker controlled component refactor
- [ ] 02-02-PLAN.md — All draft selector components (ally/opponent pickers, role, playstyle, side, lane, CTA) wired into Sidebar

### Phase 3: Recommendation Engine
**Goal**: Backend can receive a draft context and return phased item recommendations with analytical reasoning, using rules for obvious decisions and Claude API for nuanced matchup analysis
**Depends on**: Phase 1
**Requirements**: ENGN-01, ENGN-02, ENGN-03, ENGN-04, ENGN-05, ENGN-06
**Success Criteria** (what must be TRUE):
  1. POST /api/recommend with a hero and lane opponent returns a structured item timeline (starting, laning, core, late game) with per-item reasoning
  2. Rules engine instantly recommends obvious counter items (e.g., Magic Stick vs spell-spammers) without any API call
  3. Claude API generates matchup-specific reasoning that references actual hero abilities and enemy heroes by name
  4. When Claude API is unavailable or exceeds 10s timeout, the system returns rules-only recommendations with a visible fallback notice
  5. All Claude API responses are validated against a JSON schema before being returned to the frontend
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Item Timeline and End-to-End Flow
**Goal**: Player completes the full loop -- fills in draft inputs, hits recommend, and sees a phased item timeline with reasoning explanations and situational branching
**Depends on**: Phase 2, Phase 3
**Requirements**: DRFT-08, DISP-01, DISP-02, DISP-03, DISP-04, DISP-05
**Success Criteria** (what must be TRUE):
  1. User can select 1-2 lane opponents from the already-picked enemy heroes once they click into the laning phase
  2. Item timeline renders in distinct phases (starting, laning, core, late game) with item portraits from Steam CDN and gold costs
  3. Each recommended item displays 1-3 sentences of analytical reasoning explaining why, referencing specific abilities and matchup dynamics
  4. Situational items appear as decision tree cards showing branching conditions (e.g., "if enemy has evasion -> MKB")
  5. A loading skeleton/spinner is visible during the 2-10 second Claude API call, and errors display gracefully
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

### Phase 5: Mid-Game Adaptation
**Goal**: Player can update the game state mid-match (purchased items, lane result, damage profile, enemy items) and get refreshed recommendations for remaining items
**Depends on**: Phase 4
**Requirements**: MIDG-01, MIDG-02, MIDG-03, MIDG-04, MIDG-05
**Success Criteria** (what must be TRUE):
  1. User can click an item in the timeline to mark it as purchased, visually locking it from future re-evaluation
  2. User can select lane result (Won/Even/Lost) and input damage profile via toggles and manual percentage entry
  3. User can mark key enemy items spotted (e.g., enemy BKB, enemy Blink Dagger) from a curated list
  4. User can hit Re-Evaluate and see only the unpurchased remaining items regenerated with updated reasoning reflecting the new game state
**Plans**: TBD

Plans:
- [ ] 05-01: TBD
- [ ] 05-02: TBD

### Phase 6: Data Pipeline and Hardening
**Goal**: Matchup data stays fresh automatically via a daily refresh pipeline, and the system is production-ready for long-term use
**Depends on**: Phase 3
**Requirements**: INFR-02
**Success Criteria** (what must be TRUE):
  1. A daily scheduled pipeline fetches updated hero/item matchup data from OpenDota/Stratz and writes it to SQLite without manual intervention
  2. The system displays the data freshness date so the user knows how current the matchup data is
**Plans**: TBD

Plans:
- [ ] 06-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6
Note: Phase 2 and Phase 3 both depend only on Phase 1 and could execute in either order. Phase 4 depends on both.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete | 2026-03-21 |
| 2. Draft Inputs | 0/2 | Not started | - |
| 3. Recommendation Engine | 0/3 | Not started | - |
| 4. Item Timeline and End-to-End Flow | 0/2 | Not started | - |
| 5. Mid-Game Adaptation | 0/2 | Not started | - |
| 6. Data Pipeline and Hardening | 0/1 | Not started | - |

# Roadmap: Prismlab

## Milestones

- ✅ **v1.0 MVP** — Phases 1-6 (shipped 2026-03-21)
- 🚧 **v1.1 Allied Synergy & Neutral Items** — Phases 7-9 (in progress)

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

### 🚧 v1.1 Allied Synergy & Neutral Items (In Progress)

**Milestone Goal:** Leverage the full 10-hero draft by wiring allied heroes into Claude reasoning, add neutral item recommendations, and clean up v1.0 tech debt.

- [x] **Phase 7: Tech Debt & Polish** - Clean up dead code, fix admin proxy, fill test gaps, polish UI rough edges
- [ ] **Phase 8: Allied Synergy** - Wire allied heroes into recommendation reasoning for aura dedup, combo awareness, and role gap filling
- [ ] **Phase 9: Neutral Items** - Add neutral item data layer, dedicated recommendation section, and inline build-path callouts

## Phase Details

### Phase 7: Tech Debt & Polish
**Goal**: The codebase is clean, fully tested, and free of v1.0 rough edges before new features land
**Depends on**: Phase 6 (v1.0 complete)
**Requirements**: DEBT-01, DEBT-02, DEBT-03, DEBT-04
**Success Criteria** (what must be TRUE):
  1. No unused imports, dead API methods, or unreachable code paths remain in frontend or backend
  2. The /admin endpoint is accessible through the Nginx reverse proxy at the expected URL
  3. Test coverage includes the previously untested paths identified during v1.0 (backend and frontend), and all tests pass
  4. Loading spinners, error toasts, and empty-state messages display correctly for all user-facing flows (hero search, recommendation fetch, re-evaluate, data refresh)
**Plans:** 2 plans

Plans:
- [x] 07-01-PLAN.md — Dead code removal, admin proxy, UI polish
- [x] 07-02-PLAN.md — Fill test coverage gaps (frontend + backend)

### Phase 8: Allied Synergy
**Goal**: Recommendations account for what allies bring to the team — no duplicate auras, combo synergies exploited, role gaps filled with item choices
**Depends on**: Phase 7
**Requirements**: ALLY-01, ALLY-02, ALLY-03, ALLY-04
**Success Criteria** (what must be TRUE):
  1. When allied heroes are present in the draft, Claude reasoning text explicitly references ally names and their abilities/items when explaining recommendations
  2. If an ally is likely to build a team aura item (Pipe, Vlads, Crimson Guard, Mekansm), the recommendation does not suggest the same item for the user's hero
  3. When an ally has strong setup abilities (e.g., Enigma Black Hole, Magnus Reverse Polarity), recommendations prioritize follow-up items (BKB, damage items) with reasoning that references the combo
  4. When the team lacks a key capability (stuns, saves, wave clear), recommendations suggest items that fill that gap with explicit reasoning about the team deficit
**Plans:** 2 plans

Plans:
- [x] 08-01-PLAN.md — Wire allied heroes into context builder with names and popular items
- [x] 08-02-PLAN.md — Add Team Coordination rules to system prompt and integration tests

### Phase 9: Neutral Items
**Goal**: The player sees which neutral items to prioritize each tier and understands when a neutral item changes their build path
**Depends on**: Phase 8
**Requirements**: NEUT-01, NEUT-02, NEUT-03
**Success Criteria** (what must be TRUE):
  1. All Dota 2 neutral items are stored in the database with correct name, tier (T1-T5), and effect data
  2. A dedicated "Best Neutral Items" section appears in recommendations, showing ranked picks per tier with reasoning tied to the hero and matchup
  3. When a neutral item meaningfully affects the build path (e.g., Philosopher's Stone reducing need for mana regen items), the phase reasoning cards call it out inline
**Plans**: TBD

Plans:
- [ ] 09-01: TBD
- [ ] 09-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 7 -> 8 -> 9

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-03-21 |
| 2. Draft Inputs | v1.0 | 2/2 | Complete | 2026-03-21 |
| 3. Recommendation Engine | v1.0 | 3/3 | Complete | 2026-03-21 |
| 4. Item Timeline & E2E | v1.0 | 3/3 | Complete | 2026-03-21 |
| 5. Mid-Game Adaptation | v1.0 | 2/2 | Complete | 2026-03-21 |
| 6. Data Pipeline | v1.0 | 1/1 | Complete | 2026-03-21 |
| 7. Tech Debt & Polish | v1.1 | 2/2 | Complete | 2026-03-22 |
| 8. Allied Synergy | v1.1 | 0/2 | Not started | - |
| 9. Neutral Items | v1.1 | 0/? | Not started | - |

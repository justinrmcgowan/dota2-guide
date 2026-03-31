---
gsd_state_version: 1.0
milestone: v7.0
milestone_name: Engine Hardening
status: completed
stopped_at: Completed 38-02-PLAN.md
last_updated: "2026-03-31T09:56:12.028Z"
last_activity: 2026-03-31 -- Phase 38 plan 02 complete
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 10
  completed_plans: 10
  percent: 40
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-30)

**Core value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.
**Current focus:** Phase 37 — Latency & Caching

## Current Position

Phase: 38 (Adaptiveness & Accuracy) -- EXECUTING
Plan: 2 of 2
Status: Completed 38-02 Accuracy Insights
Last activity: 2026-03-31 -- Phase 38 plan 02 complete

Progress: [████░░░░░░] 40%

## Performance Metrics

**Velocity:**

- Total plans completed: 80 (v1.0-v7.0 combined)
- Average duration: ~5 min (v5.0+ trend)

## Accumulated Context

### Decisions

- [Phase 35-03]: 30 new deterministic rules (52 total) covering item-vs-item counters, meta-aware team comp, self-hero optimization
- [Phase 35-03]: Meta-aware rules iterate req.all_opponents for full team composition analysis
- [Phase 35-03]: _hero_attack_type helper for melee/ranged gating on hood/vanguard/skadi rules
- [Phase 34]: Two-pass recommendation (fast-mode rules first, Claude merges in) for zero-click auto-trigger
- [Phase 34]: 3s draft polling (down from 10s) during hero selection
- [Phase 34]: Auto-trigger fires from both useLiveDraft AND useGameIntelligence (GSI hero detection)
- [Phase 34]: Cross-phase item deduplication — earlier phase wins
- [Phase 34]: asyncio.gather() for parallel enrichment (timing, build paths, win condition, win probability)
- [Phase 34]: Adjustable API budget via PUT /settings/budget + Settings panel input
- [Phase 34]: Graceful fallback when win predictor models fail to load (non-fatal)
- [v7.0]: Tauri Desktop App deferred to v8.0 — engine quality before distribution
- [v7.0]: Design spec at docs/superpowers/specs/2026-03-30-engine-hardening-design.md
- [Phase 36-02]: Timing gates as post-processing filter in evaluate(), not separate rule methods
- [Phase 36-02]: BKB urgency escalation by "black king bar" name match (not "bkb" abbreviation)
- [Phase 36-02]: Frontend game_time_seconds from GSI, turbo from gameStore -- both optional/compact
- [Phase 36-02]: Unusual role detection reuses HERO_ROLE_VIABLE from hero_selector
- [Phase 38]: Follow threshold >= 0.7, deviate threshold < 0.4 for clear behavioral bucket separation
- [Phase 38]: Flagged items exclude luxury priority; 5+ recommendation minimum with < 30% purchase rate

### Pending Todos

None yet.

### Blockers/Concerns

None active.

## Session Continuity

Last session: 2026-03-31T09:56:12.025Z
Stopped at: Completed 38-02-PLAN.md
Resume file: None

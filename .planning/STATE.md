---
gsd_state_version: 1.0
milestone: v7.0
milestone_name: Engine Hardening
status: executing
stopped_at: Completed 36-02 Game Clock + Timing Gates
last_updated: "2026-03-30T20:48:51Z"
last_activity: 2026-03-30
progress:
  total_phases: 2
  completed_phases: 0
  total_plans: 0
  completed_plans: 4
  percent: 40
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-30)

**Core value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.
**Current focus:** v7.0 Engine Hardening — make recommendations monetization-ready

## Current Position

Phase: 36 (Prompt Intelligence)
Plan: 36-02 complete
Status: Executing
Last activity: 2026-03-30

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

### Pending Todos

None yet.

### Blockers/Concerns

None active.

## Session Continuity

Last session: 2026-03-30T20:48:51Z
Stopped at: Completed 36-02 Game Clock + Timing Gates
Resume file: None

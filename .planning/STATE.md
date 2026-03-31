---
gsd_state_version: 1.0
milestone: v7.0
milestone_name: Engine Hardening
status: executing
stopped_at: Completed 37-02 Cache Warming
last_updated: "2026-03-31T08:51:07Z"
last_activity: 2026-03-31
progress:
  total_phases: 2
  completed_phases: 0
  total_plans: 0
  completed_plans: 6
  percent: 55
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-30)

**Core value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.
**Current focus:** v7.0 Engine Hardening — make recommendations monetization-ready

## Current Position

Phase: 37 (Latency & Caching)
Plan: 37-02 complete
Status: Executing
Last activity: 2026-03-31

Progress: [█████░░░░░] 55%

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

- [Phase 37-01]: HierarchicalCache L2 key normalizes opponents via sorted(set(lane+all)) for order-independent matching
- [Phase 37-01]: set() writes all 3 cache tiers atomically; deleted old ResponseCache entirely
- [Phase 37-02]: CacheWarmer uses alphabetically first playstyle per role for deterministic, stable cache keys
- [Phase 37-02]: Synchronous warming in startup path (~5-7s for ~130 combos) -- acceptable given 10-30s existing startup
- [Phase 37-02]: Post-refresh re-warming: clear HierarchicalCache, then re-warm L1 with fresh data

### Pending Todos

None yet.

### Blockers/Concerns

None active.

## Session Continuity

Last session: 2026-03-31T08:51:07Z
Stopped at: Completed 37-02 Cache Warming
Resume file: None

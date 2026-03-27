---
gsd_state_version: 1.0
milestone: v4.0
milestone_name: Coaching Intelligence
status: Ready to plan
stopped_at: Completed 21-02-PLAN.md
last_updated: "2026-03-27T17:44:20.008Z"
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 8
  completed_plans: 8
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-27)

**Core value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.
**Current focus:** Phase 21 — Timing Benchmarks

## Current Position

Phase: 22
Plan: Not started

## Performance Metrics

**Velocity:**

- Total plans completed: 45 (v1.0: 14, v1.1: 6, v2.0: 15, v3.0: 10)
- Average duration: ~6 min (v3.0 trend)
- Total execution time: ~11.6 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1-6 (v1.0) | 14 | ~5.8h | ~25 min |
| 7-9 (v1.1) | 6 | ~2.5h | ~25 min |
| 10-14 (v2.0) | 15 | ~2.5h | ~5 min |
| 15-18 (v3.0) | 10 | ~0.8h | ~5 min |
| Phase 19 P01 | 5min | 2 tasks | 4 files |
| Phase 19 P02 | 6min | 2 tasks | 5 files |
| Phase 19 P03 | 4min | 2 tasks | 2 files |
| Phase 20 P03 | 5min | 1 tasks | 2 files |
| Phase 21 P01 | 6min | 2 tasks | 6 files |
| Phase 21 P02 | 4min | 2 tasks | 6 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 16]: Frozen dataclasses for cache immutability; atomic swap refresh; RulesEngine consumes DataCache via constructor injection
- [Phase 18]: Threat annotations: fed if kills>=5 and K/D>=2, behind if deaths>=3 and D/K>=2
- [Roadmap]: Prompt architecture split (DATA-04) established as Phase 19 prerequisite -- all four feature phases depend on system-vs-user message data boundary
- [Roadmap]: Phase ordering mirrors data dependency: abilities + timing first, then counter rules, then timing UI, then build path, then win condition last
- [Phase 19]: One row per hero for timing data (JSON blob) matching one API call = one DB write pattern
- [Phase 19]: Nyquist test scaffolds: tests import types that don't exist yet, fail with ImportError until implementation plan
- [Phase 19]: AbilityCached.bkbpierce is bool not string -- simpler downstream checks
- [Phase 19]: set_hero_timings does NOT clear ResponseCache -- timing data changes slowly
- [Phase 19]: Ability refresh is non-fatal try/except -- heroes/items always commit
- [Phase 19]: v4.0 directives use conditional If guards for optional context sections
- [Phase 19]: System prompt data boundary enforced: directives only, no dynamic data (token budget <5000, no percentages)
- [Phase 20]: Counter-relevant ability properties limited to 4: channeled, passive, BKB-pierce, undispellable
- [Phase 21]: 10pp urgency threshold for timing-critical items (good-zone minus late-zone WR > 10pp)
- [Phase 21]: Post-LLM enrichment pattern: timing data appended after _validate_item_ids, never sent to Claude for generation
- [Phase 21]: Zone classification uses 2% peak threshold for good zone, weighted average for ontrack/late boundary
- [Phase 21]: Proportional zone widths use bucket count ratio, not time span -- consistent with equal-interval bucket emission
- [Phase 21]: timingDataMap built with useMemo in ItemTimeline keyed by item_name for O(1) per-item lookup

### Pending Todos

None yet.

### Blockers/Concerns

- Three-cache coherence must extend to new ability + timing data (carried from Phase 16, addressed in Phase 19)
- WCON-04 requires full enemy team data -- current schema only sends lane_opponents, needs expansion (addressed in Phase 23)

## Session Continuity

Last session: 2026-03-27T17:35:38.544Z
Stopped at: Completed 21-02-PLAN.md
Resume file: None

---
gsd_state_version: 1.0
milestone: v6.0
milestone_name: Draft Intelligence
status: executing
stopped_at: "Checkpoint: 31-03 Task 3 human-verify"
last_updated: "2026-03-29T21:10:28.848Z"
last_activity: 2026-03-29
progress:
  total_phases: 2
  completed_phases: 2
  total_plans: 6
  completed_plans: 6
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-29)

**Core value:** At any point in any game, the player knows exactly what to buy next and why -- they never feel lost on itemization.
**Current focus:** Phase 31 — hero-selector

## Current Position

Phase: 31 (hero-selector) — EXECUTING
Plan: 3 of 3
Status: Ready to execute
Last activity: 2026-03-29

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**

- Total plans completed: 73 (v1.0-v5.0 combined)
- Average duration: ~5 min (v5.0 trend)
- Total execution time: ~15h+

**By Phase (recent):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| Phase 29-stream-deck P01 | 5min | 2 tasks | 20 files |
| Phase 29-stream-deck P02 | 5min | 2 tasks | 8 files |
| Phase 33-game-analytics P01-P03 | ~10min | 6 tasks | - |
| Phase 30-ml-win-predictor P01 | 12 | 3 tasks | 8 files |
| Phase 30-ml-win-predictor P02 | 4 | 2 tasks | 5 files |
| Phase 30-ml-win-predictor P03 | 3 | 1 tasks | 3 files |
| Phase 31-hero-selector P02 | 3 | 2 tasks | 2 files |
| Phase 31-hero-selector P01 | 5 | 2 tasks | 4 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Phase 23]: win_condition is post-LLM enrichment only -- WinConditionBadge displays allied/enemy archetype pills above ItemTimeline
- [Phase 25]: Dual-source live match API (Stratz primary, OpenDota fallback) wired to Steam ID in Settings
- [Phase 28]: session.merge() for upserts -- current patch data (7.41) in place, ready for ML training
- [Phase 33]: Normalized match logging schema (MatchLog + MatchItem + MatchRecommendation) live, match history page shipped
- [Phase 30-ml-win-predictor]: Placeholder .ubj and matrices.json committed to repo — real artifacts require running train_win_predictor.py from prismlab/backend/ on patch day
- [Phase 30-ml-win-predictor]: hero_id_to_index embedded in matrices.json at training time for training/inference parity in Plan 02
- [Phase 30-ml-win-predictor]: get_booster().save_model() used for XGBoost .ubj artifacts (not joblib) — version-stable across XGBoost upgrades
- [Phase 30-ml-win-predictor]: bracket_2 (Archon-Legend) default for win probability when request has no MMR field
- [Phase 30-ml-win-predictor]: WinPredictor is stateless; DataCache holds xgb.Booster instances loaded at startup
- [Phase 30-ml-win-predictor]: winProbability != null guard used (not falsy) so 0% probability renders correctly; text-secondary/80 matches confidence-opacity visual pattern
- [Phase 31-hero-selector]: snake_case field names in TypeScript interfaces match backend JSON keys exactly — no camelCase conversion middleware
- [Phase 31-hero-selector]: No engine mode injection for suggestHero (unlike recommend); suggest-hero has no engine mode concept
- [Phase 31-hero-selector]: HERO_ROLE_VIABLE transcribed from heroPlaystyles.ts as static Python mirror; synergy*0.4+counter*0.4 composite with counter[c][e]-0.5 centering
- [Phase 31-hero-selector]: onFocus prop added to HeroPicker to close HeroSuggestPanel before dropdown opens — prevents dual-open state

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 30 requires OpenDota bulk data pipeline for 200k+ matches -- data download volume and patch filtering strategy need plan-phase scoping
- Phase 31 "Suggest Hero" UI integration point needs design decision: modal vs inline expansion in draft panel

## Session Continuity

Last session: 2026-03-29T21:10:17.716Z
Stopped at: Checkpoint: 31-03 Task 3 human-verify
Resume file: None

---
phase: 23-win-condition-framing
plan: "01"
subsystem: backend-engine
tags: [win-condition, classification, context-builder, recommender, schemas]
dependency_graph:
  requires: [22-02-SUMMARY.md]
  provides: [classify_draft, WinConditionResponse, all_opponents, _build_team_strategy_section, _enrich_win_condition]
  affects: [engine/win_condition.py, engine/schemas.py, engine/context_builder.py, engine/recommender.py]
tech_stack:
  added: []
  patterns: [post-LLM enrichment, pre-LLM context injection, zero-DB-query DataCache lookups]
key_files:
  created:
    - prismlab/backend/engine/win_condition.py
    - prismlab/backend/tests/test_win_condition.py
  modified:
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/engine/context_builder.py
    - prismlab/backend/engine/recommender.py
decisions:
  - "win_condition is post-LLM enrichment only -- never in LLM_OUTPUT_SCHEMA, never Claude-generated"
  - "all_opponents (max 5) separate from lane_opponents (max 2) -- different concerns: draft classification vs matchup rules"
  - "MIN_HEROES=3 threshold prevents noisy low-signal context injection"
  - "Allied team = hero_id + allies; enemy team = all_opponents (WCON-04)"
metrics:
  duration: "4 min"
  completed: "2026-03-27"
  tasks_completed: 2
  files_changed: 5
---

# Phase 23 Plan 01: Win Condition Classifier and Context Injection Summary

**One-liner:** Pure-Python WinConditionClassifier mapping OpenDota role strings to 5 macro archetypes (teamfight/split-push/pick-off/deathball/late-game scale) with pre-LLM Team Strategy context injection and post-LLM RecommendResponse enrichment.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | WinConditionClassifier, schemas, RecommendRequest extension | b91e673 | win_condition.py, schemas.py, test_win_condition.py |
| 2 | Context builder Team Strategy section + recommender enrichment | 3a08c25 | context_builder.py, recommender.py |

## What Was Built

### Task 1: WinConditionClassifier + Schema Extensions

Created `prismlab/backend/engine/win_condition.py` with:
- `WinConditionResult` dataclass: archetype, confidence, archetype_scores
- `classify_draft(hero_ids, cache)` function: returns None for < 3 heroes, classifies 5 archetypes using weighted role scoring from ARCHETYPE_WEIGHTS
- Confidence levels: high (>= 60% top fraction), medium (40-60%), low (< 40%)
- Graceful handling of heroes with roles=None (skipped, must have 3+ heroes with role data)

Extended `prismlab/backend/engine/schemas.py`:
- Added `WinConditionResponse` Pydantic model (post-LLM, never Claude-generated): allied_archetype, allied_confidence, enemy_archetype, enemy_confidence
- Added `all_opponents: list[int]` (max 5) to `RecommendRequest` with documentation comments distinguishing from lane_opponents
- Added `win_condition: WinConditionResponse | None` to `RecommendResponse`
- `win_condition` is explicitly absent from `LLM_OUTPUT_SCHEMA`

TDD with 11 tests covering all 5 archetypes, high/medium/low confidence, None roles, empty list, insufficient hero count.

### Task 2: Context Builder + Recommender Wiring

`ContextBuilder._build_team_strategy_section()`:
- Allied team: `request.hero_id + request.allies`
- Enemy team: `request.all_opponents` (full enemy draft, not lane_opponents -- WCON-04)
- Returns empty string if neither team reaches 3-hero threshold (no noisy injection)
- Injected as `## Team Strategy` section in build() between timing benchmarks and neutral catalog

`HybridRecommender._enrich_win_condition()` (Step 6d):
- Same classify_draft logic as context builder -- ensures frontend badge matches what Claude was told
- Post-LLM enrichment, zero DB queries (DataCache only)
- Returns None if neither team qualifies
- Wired into RecommendResponse construction after build_paths (Step 6c)

## Verification

- 11 new tests in test_win_condition.py: all pass
- 257 total backend tests: all pass (2 pre-existing skips)
- System prompt token budget test: 14/14 pass
- win_condition absent from LLM_OUTPUT_SCHEMA confirmed

## Deviations from Plan

None -- plan executed exactly as written.

## Known Stubs

None -- all data is wired from DataCache. classify_draft returns real archetype classification based on hero role data. The frontend badge field is populated; frontend display of win_condition badge is out of scope for this plan (23-02 is the frontend phase).

## Self-Check: PASSED

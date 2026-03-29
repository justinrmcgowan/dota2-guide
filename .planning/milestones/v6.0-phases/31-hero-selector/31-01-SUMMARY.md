---
phase: 31-hero-selector
plan: "01"
subsystem: backend-engine
tags: [hero-selector, pydantic-schemas, scoring-engine, tdd]
dependency_graph:
  requires:
    - 30-ml-win-predictor (DataCache._matrices synergy/counter data)
  provides:
    - SuggestHeroRequest / HeroSuggestion / SuggestHeroResponse (engine/schemas.py)
    - HeroSelector.get_suggestions() (engine/hero_selector.py)
    - HERO_ROLE_VIABLE role viability map
  affects:
    - 31-02: API route calls HeroSelector.get_suggestions()
    - 31-03: Frontend consumes SuggestHeroResponse via /api/suggest-hero
tech_stack:
  added: []
  patterns:
    - TDD with --noconftest (conftest requires numpy/main.py imports not available in dev)
    - int() cast on JSON string keys from matrices.json (win_predictor.py pattern)
    - Graceful degradation to 0.0 scores when matrices empty (placeholder-safe)
    - Secondary alphabetical sort for deterministic tie-breaking
key_files:
  created:
    - prismlab/backend/engine/hero_selector.py
    - prismlab/backend/tests/test_suggest_hero_schemas.py
    - prismlab/backend/tests/test_hero_selector.py
  modified:
    - prismlab/backend/engine/schemas.py
decisions:
  - "HERO_ROLE_VIABLE populated from heroPlaystyles.ts transcription (30 Pos-1 heroes, all 5 roles)"
  - "composite score = synergy*0.4 + counter*0.4 (no individual_wr in Phase 31 per plan)"
  - "counter[a][b] - 0.5 centering applied to convert raw win rate to delta"
  - "Fallback to all heroes when HERO_ROLE_VIABLE[role] pool < 5 (Pitfall 3 mitigation)"
  - "matrices_available=False when cache._matrices is empty OR synergy array is empty"
metrics:
  duration_minutes: 5
  completed_date: "2026-03-30"
  tasks_completed: 2
  files_created: 3
  files_modified: 1
---

# Phase 31 Plan 01: Hero Selector Backend Schemas and Scoring Engine Summary

**One-liner:** Pydantic schemas for suggest-hero API plus HeroSelector scoring engine using synergy/counter matrices with graceful degradation on placeholder data.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add SuggestHeroRequest/HeroSuggestion/SuggestHeroResponse schemas | b2fdf06 | engine/schemas.py |
| 2 | Create engine/hero_selector.py with HeroSelector and HERO_ROLE_VIABLE | f86c7bc | engine/hero_selector.py |

TDD RED commits: 06cab36 (schemas tests), f0eada6 (hero_selector tests)

## Artifacts Created

### engine/schemas.py (modified)
Three new Pydantic models appended after `ScreenshotParseResponse`:
- `SuggestHeroRequest`: role (1-5), ally_ids (max 4), enemy_ids (max 5), excluded_hero_ids, top_n (default 10, max 30), bracket (default 2, range 1-4)
- `HeroSuggestion`: hero_id, hero_name, internal_name, icon_url (nullable), score, synergy_score, counter_score
- `SuggestHeroResponse`: suggestions list + matrices_available bool

### engine/hero_selector.py (new)
- `HERO_ROLE_VIABLE: dict[int, set[int]]` — 5 roles, 30+ heroes per role transcribed from heroPlaystyles.ts
- `_get_bracket_matrices(cache, bracket)` — returns (synergy, counter, hero_id_to_index) with int() key cast
- `score_candidates(...)` — returns `{hero_id: (composite, syn, ctr)}`, gracefully handles empty matrices and IndexError
- `HeroSelector.get_suggestions(request, cache)` — full pipeline: filter → score → sort → top_n

## Test Coverage

- 11 schema tests (test_suggest_hero_schemas.py) — field defaults, validators, nullable icon_url
- 18 selector tests (test_hero_selector.py) — HERO_ROLE_VIABLE structure, scoring math, empty matrices, role filter, excluded_hero_ids, alphabetical tie-break, int cast verification

All 29 tests pass.

## Key Decisions

1. **HERO_ROLE_VIABLE from heroPlaystyles.ts transcription** — Static Python mirror. Source of truth is the TypeScript file; comment documents sync requirement.
2. **composite = syn * 0.4 + ctr * 0.4** — No individual_wr component in Phase 31 per plan spec.
3. **counter[c][e] - 0.5 centering** — Raw counter value is win rate (0.0-1.0), must center to get meaningful delta.
4. **Fallback to all heroes when viable pool < 5** — Prevents empty suggestions for sparse roles.
5. **matrices_available check includes synergy array truthiness** — Empty `[]` in placeholder JSON correctly sets flag False.

## Deviations from Plan

None — plan executed exactly as written. TDD flow followed: RED commit → GREEN commit for each task.

## Known Stubs

None — scoring engine returns real computed scores (0.0 when matrices are placeholder, by design and documented in response via matrices_available flag).

## Self-Check: PASSED

- [x] engine/hero_selector.py exists and is importable
- [x] engine/schemas.py contains SuggestHeroRequest, HeroSuggestion, SuggestHeroResponse
- [x] 29 tests pass (11 schema + 18 selector)
- [x] Commits f86c7bc and b2fdf06 exist (verified via git log)
- [x] Verification command `All checks passed` confirmed

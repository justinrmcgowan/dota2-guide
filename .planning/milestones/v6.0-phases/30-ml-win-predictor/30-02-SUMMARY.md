---
phase: 30-ml-win-predictor
plan: "02"
subsystem: backend-engine
tags: [ml, xgboost, win-predictor, datacache, recommender, fastapi]
dependency_graph:
  requires:
    - 30-01  # training script, placeholder .ubj artifacts, models/ directory
  provides:
    - win_probability field in RecommendResponse
    - WinPredictor class for draft inference
    - DataCache.load_win_predictor() method
  affects:
    - prismlab/backend/engine/recommender.py
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/data/cache.py
    - prismlab/backend/main.py
tech_stack:
  added:
    - xgboost (lazy import in WinPredictor.predict() and DataCache.load_win_predictor())
    - numpy (feature vector construction in win_predictor.py)
  patterns:
    - Graceful fallback: all prediction paths return None rather than raising on missing models
    - Post-LLM enrichment: win_probability computed after Claude response, not sent to prompt
    - Stateless predictor class: WinPredictor instantiated per-request, DataCache holds model state
    - Booster API inference: xgb.Booster.load_model() + DMatrix.predict() avoids sklearn wrapper issues
key_files:
  created:
    - prismlab/backend/engine/win_predictor.py
  modified:
    - prismlab/backend/data/cache.py
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/engine/recommender.py
    - prismlab/backend/main.py
decisions:
  - Use bracket_2 (Archon-Legend) as default bracket when RecommendRequest has no MMR field
  - WinPredictor is stateless; DataCache holds the xgb.Booster instances
  - Return None (not error) for all failure modes -- partial draft, missing models, xgboost not installed
metrics:
  duration_minutes: 4
  completed_date: "2026-03-29"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 4
---

# Phase 30 Plan 02: Win Predictor Runtime Integration Summary

**One-liner:** XGBoost draft win probability wired into RecommendResponse as post-LLM enrichment using Booster API inference from DataCache-held models, with graceful null fallback for partial drafts or missing artifacts.

## What Was Built

### Task 1: Extend DataCache with win model loading

`prismlab/backend/data/cache.py` received three new `__init__` fields and one new method:

- `_win_models: dict[int, object]` — bracket number to `xgb.Booster` mapping
- `_matrices: dict[int, dict]` — bracket number to synergy/counter/hero_id_to_index data
- `_win_predictor_ready: bool` — True only when at least one bracket model loaded
- `load_win_predictor(models_dir="models")` — loads all 4 `.ubj` model files and `matrices.json`; warns and returns if xgboost not installed or files absent; called synchronously at startup after `data_cache.load()`

### Task 2: WinPredictor class, schema extension, recommender wiring, main.py startup

**`prismlab/backend/engine/win_predictor.py`** (new):
- `build_feature_vector()` — constructs 252-dim float32 numpy one-hot array (n_heroes Radiant + n_heroes Dire positions)
- `WinPredictor.predict()` — converts allied/enemy IDs to radiant/dire perspective, builds DMatrix, calls `model.predict()`, inverts for Dire side; returns `None` for partial draft (<10 heroes), missing model, or xgboost failure

**`prismlab/backend/engine/schemas.py`**:
- Added `win_probability: float | None = None` field to `RecommendResponse` after `win_condition`

**`prismlab/backend/engine/recommender.py`**:
- Imported `WinPredictor` from `engine.win_predictor`
- Extended `_enrich_all()` return type from 3-tuple to 4-tuple including `float | None`
- Added `_enrich_win_probability()` method — builds allied list (self + allies), defaults to bracket 2
- Updated all 4 `_enrich_all()` unpack sites to receive `win_probability`
- Updated all 4 `RecommendResponse()` construction sites with `win_probability=win_probability`

**`prismlab/backend/main.py`**:
- Added `data_cache.load_win_predictor(models_dir="models")` call in lifespan after `data_cache.load(session)`

## Must-Haves Satisfied

| Truth | Satisfied |
|-------|-----------|
| POST /api/recommend returns win_probability when all 10 heroes present | Yes — _enrich_win_probability builds 5+5 hero list and calls WinPredictor.predict() |
| win_probability is null when fewer than 10 total heroes | Yes — `if total_heroes < 10: return None` in WinPredictor.predict() |
| win_probability is null when model artifacts missing (no error) | Yes — _win_predictor_ready=False returns None; all exceptions caught with try/except |
| win_probability is float 0.0-1.0 from allied perspective | Yes — radiant/dire framing with `1.0 - radiant_win_prob` inversion for Dire side |
| DataCache loads XGBoost models and matrices at startup | Yes — load_win_predictor() called in lifespan; logs bracket count on success |

## Deviations from Plan

None — plan executed exactly as written. The only minor discovery was that the 4th `RecommendResponse()` site in `_auto_path` used 16-space indentation (nested inside an `if` block) rather than 12-space, requiring a separate targeted edit rather than a global replace. Fixed inline with no behavior change.

## Known Stubs

The `models/` directory contains placeholder `.ubj` files (0-byte or minimal) from Plan 01. Real models require running `prismlab/backend/scripts/train_win_predictor.py` against OpenDota after sufficient patch 7.41 match data accumulates. Until then, `_win_predictor_ready` will be False and `win_probability` will be `null` in all API responses — the app remains fully functional.

## Self-Check: PASSED

- FOUND: prismlab/backend/engine/win_predictor.py
- FOUND: .planning/phases/30-ml-win-predictor/30-02-SUMMARY.md
- FOUND: commit c97e2df (feat(30-02): extend DataCache with win model loading)
- FOUND: commit 2d22780 (feat(30-02): wire WinPredictor into FastAPI recommend pipeline)

---
phase: 30-ml-win-predictor
plan: 01
subsystem: api
tags: [xgboost, scikit-learn, numpy, opendota, machine-learning, training-pipeline]

# Dependency graph
requires:
  - phase: 28-data-pipeline
    provides: OpenDotaClient base class that fetch_explorer_sql() is appended to
provides:
  - "fetch_explorer_sql() method on OpenDotaClient for paged SQL Explorer queries"
  - "train_win_predictor.py offline script: download → featurize → train → matrices → save"
  - "models/win_predictor_bracket_{1..4}.ubj placeholder model files (replace by running script)"
  - "models/matrices.json placeholder with correct bracket_1..bracket_4 structure"
affects:
  - 30-ml-win-predictor (plan 02 — runtime integration loads these artifacts)
  - 31-hero-selector (consumes synergy/counter matrices from matrices.json)

# Tech tracking
tech-stack:
  added:
    - "xgboost==3.2.0 — XGBoost classifier, native .ubj save format"
    - "scikit-learn==1.8.0 — train_test_split, accuracy_score, roc_auc_score"
    - "numpy==2.4.4 — float32 feature vector construction"
  patterns:
    - "One model per MMR bracket (4 total) — separate files for easy swap on patch day"
    - "get_booster().save_model() for .ubj format (not joblib/pickle — XGBoost-version-stable)"
    - "hero_id_to_index built from all brackets combined — consistent between training and inference"
    - "MIN_PAIR_MATCHES=50 gate for synergy/counter inclusion — sparse pairs return None"

key-files:
  created:
    - "prismlab/backend/scripts/train_win_predictor.py — 603-line offline training pipeline"
    - "prismlab/backend/models/matrices.json — placeholder; replace with real training output"
    - "prismlab/backend/models/win_predictor_bracket_1.ubj — placeholder"
    - "prismlab/backend/models/win_predictor_bracket_2.ubj — placeholder"
    - "prismlab/backend/models/win_predictor_bracket_3.ubj — placeholder"
    - "prismlab/backend/models/win_predictor_bracket_4.ubj — placeholder"
  modified:
    - "prismlab/backend/requirements.txt — added xgboost, scikit-learn, numpy"
    - "prismlab/backend/data/opendota_client.py — appended fetch_explorer_sql() method"

key-decisions:
  - "Placeholder .ubj files committed — cannot train without real OpenDota data in CI; run script manually on patch day"
  - "fetch_explorer_sql() uses separate URL (api.opendota.com/api/explorer), not BASE_URL — Explorer is a different endpoint"
  - "get_booster().save_model() used instead of joblib.dump — native .ubj format is XGBoost-version-stable across upgrades"
  - "hero_id_to_index derived from all 4 brackets combined and embedded in matrices.json — ensures training/inference parity"

patterns-established:
  - "Offline training script: run from prismlab/backend/ so sys.path.insert(0, parent_dir) resolves project imports"
  - "Pagination: LIMIT/OFFSET loop until row_count < PAGE_SIZE or target reached, with 1.1s sleep between pages"

requirements-completed: [PRED-02, PRED-03, PRED-04]

# Metrics
duration: 12min
completed: 2026-03-29
---

# Phase 30 Plan 01: ML Win Predictor Training Pipeline Summary

**XGBoost offline training pipeline: OpenDota SQL Explorer paged download, 252-dim one-hot feature vectors, 4 bracket models (.ubj), and synergy/counter matrices in matrices.json**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-03-29T21:35:00Z
- **Completed:** 2026-03-29T21:47:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Added `fetch_explorer_sql()` to `OpenDotaClient` — paged SQL Explorer with 60s timeout, returns `rows` list
- Wrote `train_win_predictor.py` (603 lines): full pipeline from download through XGBoost training and synergy/counter matrix computation
- Committed placeholder artifact files in `prismlab/backend/models/` — Plan 02 runtime integration can proceed while real training awaits a patch-day run

## Task Commits

1. **Task 1: Add ML dependencies and fetch_explorer_sql()** - `3416a2b` (feat)
2. **Task 2: Write offline training script train_win_predictor.py** - `61a8c92` (feat)
3. **Task 3: Commit placeholder model artifacts** - `16d448c` (chore)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `prismlab/backend/requirements.txt` — added xgboost==3.2.0, scikit-learn==1.8.0, numpy==2.4.4
- `prismlab/backend/data/opendota_client.py` — appended `fetch_explorer_sql(sql)` method
- `prismlab/backend/scripts/train_win_predictor.py` — 603-line offline training script
- `prismlab/backend/models/matrices.json` — placeholder with bracket_1..bracket_4 structure
- `prismlab/backend/models/win_predictor_bracket_{1..4}.ubj` — placeholder stubs (4 files)

## Decisions Made

- **Placeholder artifacts committed**: CI cannot run actual OpenDota API calls or XGBoost training. Placeholder files ensure the file paths exist in git so Plan 02 can reference them at startup, with graceful fallback for empty/missing models.
- **`fetch_explorer_sql()` uses hardcoded URL**: The Explorer endpoint (`api.opendota.com/api/explorer`) is structurally separate from the REST API constants endpoints — not using `BASE_URL` is intentional per research notes.
- **`get_booster().save_model()` for .ubj format**: Avoids sklearn wrapper metadata instability across XGBoost version upgrades (documented pitfall in 30-RESEARCH.md).
- **`hero_id_to_index` embedded in matrices.json**: Ensures training-time and inference-time hero indexing are always in sync — Plan 02 loads this mapping rather than recomputing it.

## Deviations from Plan

None — plan executed exactly as written, with the explicit instruction from `<important_context>` to use placeholder artifacts instead of running the training script.

## Known Stubs

The following placeholder files are intentional stubs — they do NOT prevent the plan's goal (providing the training pipeline code) but will need replacing before Plan 02 can serve real predictions:

| File | Stub Type | Reason | Resolves In |
|------|-----------|--------|-------------|
| `prismlab/backend/models/win_predictor_bracket_{1..4}.ubj` | Placeholder text, not real XGBoost binary | Cannot run training in CI without OpenDota API + install time | Developer runs `python scripts/train_win_predictor.py` on patch day |
| `prismlab/backend/models/matrices.json` | Empty synergy/counter arrays, n_heroes=0 | Same as above | Same as above |

## Issues Encountered

None.

## User Setup Required

**To produce real model artifacts** (required before Plan 02 predictions work):

```bash
cd prismlab/backend
pip install "xgboost==3.2.0" "scikit-learn==1.8.0" "numpy==2.4.4"
# Optional: set OPENDOTA_API_KEY in .env for higher rate limits
python scripts/train_win_predictor.py
```

Expected output: 4 `.ubj` files (~1-3 MB each) and `matrices.json` (~20-50 MB depending on hero universe size). Training takes 5-20 minutes depending on data availability and network speed.

Re-run this script after each major Dota patch by updating `PATCH_741_START` in the script.

## Next Phase Readiness

- Plan 02 (runtime integration) can proceed — it should add graceful fallback when `n_heroes == 0` (placeholder matrix state)
- `fetch_explorer_sql()` is available for any future data pipeline needs (not just the win predictor)
- `hero_id_to_index` key is embedded in `matrices.json` per the Plan 01 spec — Plan 02 should load it from there at startup

---
*Phase: 30-ml-win-predictor*
*Completed: 2026-03-29*

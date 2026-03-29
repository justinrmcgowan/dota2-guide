---
phase: 26-engine-optimization
plan: 01
subsystem: engine
tags: [ollama, cost-tracking, mode-routing, fastapi, pydantic, sqlalchemy]

requires:
  - phase: 23-win-condition-framing
    provides: "HybridRecommender enrichment pipeline (timing, build paths, win condition)"
provides:
  - "OllamaEngine with generate() matching LLMEngine signature"
  - "CostTracker with monthly budget cap and SQLite persistence"
  - "3-mode routing in HybridRecommender (fast/auto/deep)"
  - "Settings endpoints for engine mode and budget status"
affects: [26-02, 26-03, frontend-settings-panel]

tech-stack:
  added: [ollama==0.4.8]
  patterns: [3-mode engine routing, cost tracking with budget cap, auto-escalation logic]

key-files:
  created:
    - prismlab/backend/engine/ollama_engine.py
    - prismlab/backend/engine/cost_tracker.py
  modified:
    - prismlab/backend/engine/recommender.py
    - prismlab/backend/engine/llm.py
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/config.py
    - prismlab/backend/data/models.py
    - prismlab/backend/api/routes/recommend.py
    - prismlab/backend/api/routes/settings.py
    - prismlab/backend/requirements.txt

key-decisions:
  - "budget_ok defaults True when no cost_tracker configured -- backward compatible with existing tests"
  - "Auto mode without Ollama engine falls through to Claude (deep path) -- graceful degradation"
  - "LLMEngine.last_usage stores token counts on instance to avoid changing generate() signature"
  - "CostTracker uses lazy month rollover -- no cron needed, checks on every access"
  - "_should_escalate checks 4 conditions: low rules coverage, mid-game re-eval, screenshot context, complex draft"

patterns-established:
  - "3-mode routing: recommend() dispatches to _fast_path/_auto_path/_deep_path based on mode"
  - "Auto-escalation: _should_escalate() decides when Auto mode should use Claude instead of Ollama"
  - "Shared enrichment: _enrich_all() consolidates timing/build-path/win-condition post-processing"
  - "Budget-aware routing: cost_tracker.budget_exceeded() gates Claude calls in Auto mode"
  - "Instance-level usage tracking: self.last_usage on LLMEngine for cost accounting without changing generate() interface"

requirements-completed: [ENG-01, ENG-02, ENG-03, ENG-04, ENG-05]

duration: 11min
completed: 2026-03-28
---

# Phase 26 Plan 01: Engine Optimization Summary

**3-mode recommendation engine with OllamaEngine for local LLM, CostTracker for API budget management, and fast/auto/deep routing in HybridRecommender**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-28T17:36:27Z
- **Completed:** 2026-03-28T17:47:30Z
- **Tasks:** 2/2
- **Files modified:** 10

## Accomplishments

### Task 1: OllamaEngine, CostTracker, config, schema extensions (d93c995)

- Created `OllamaEngine` in `engine/ollama_engine.py` with `generate()` matching `LLMEngine` signature. Uses official `ollama` library's `AsyncClient` with structured JSON output via Pydantic `model_json_schema()`. Includes `health_check()` for startup diagnostics.
- Created `CostTracker` in `engine/cost_tracker.py` with in-memory totals persisted to SQLite via `ApiUsage` model. Tracks monthly cost at Haiku 4.5 rates ($1/$5 per MTok). Supports `budget_exceeded()` (hard stop at 100%) and `budget_warning()` (soft at 80%).
- Extended `Settings` with `recommendation_mode`, `ollama_url`, `ollama_model`, `api_budget_monthly`.
- Extended `FallbackReason` with `ollama_error` and `budget_exceeded` variants.
- Added `mode` field to `RecommendRequest` for per-request mode override.
- Added `engine_mode`, `budget_used`, `budget_limit` to `RecommendResponse`.
- Added `ApiUsage` SQLAlchemy model in `data/models.py`.
- Added `last_usage` tracking to `LLMEngine` for post-generate token accounting.
- Added `ollama==0.4.8` to `requirements.txt`.

### Task 2: Mode routing in HybridRecommender + recommend route wiring (bbe5bcd)

- Refactored `recommend()` into a mode dispatcher routing to `_fast_path`, `_auto_path`, `_deep_path`.
- **Fast path:** Rules-only, no LLM call, returns `engine_mode="fast"` with rules-based strategy text.
- **Auto path:** Evaluates rules, checks `_should_escalate()` (4 conditions: low rules coverage, mid-game re-eval, screenshot context, complex draft). If escalation needed and budget allows, routes to deep path. Otherwise tries Ollama, falls back to Claude on failure, falls back to rules-only if budget exceeded.
- **Deep path:** Extracted from original `recommend()` logic. Always calls Claude API, tracks cost via `self.llm.last_usage` + `self.cost_tracker.record_usage()`.
- Added `_enrich_all()` to consolidate shared post-LLM enrichment pipeline across all 3 paths.
- Added `_attach_budget_info()` to stamp budget usage on every response.
- Wired `OllamaEngine` and `CostTracker` singletons in `api/routes/recommend.py`.
- Added `GET /api/settings/engine` and `GET /api/settings/budget` endpoints in `api/routes/settings.py`.
- Backward compatible: existing tests pass without ollama/cost_tracker configured (auto mode gracefully falls through to Claude).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed budget_ok logic when cost_tracker is None**
- **Found during:** Task 2
- **Issue:** `budget_ok = self.cost_tracker and not self.cost_tracker.budget_exceeded()` evaluates to `False` when cost_tracker is None, causing Auto mode to never escalate to Claude and never use Claude as fallback -- breaking backward compatibility.
- **Fix:** Changed to `budget_ok = self.cost_tracker is None or not self.cost_tracker.budget_exceeded()` so that when no cost_tracker is configured, budget is always "ok" (no cap enforced).
- **Files modified:** `prismlab/backend/engine/recommender.py`
- **Commit:** bbe5bcd

## Verification Results

All 4 plan verifications passed:
1. `OllamaEngine` and `CostTracker` importable
2. All 3 path methods exist on `HybridRecommender`
3. Config has `recommendation_mode`, `ollama_url`, `api_budget_monthly`
4. `RecommendRequest.mode` and `RecommendResponse.engine_mode/budget_used/budget_limit` work

Full test suite: 257 passed, 2 skipped, 0 failures.

## Known Stubs

None -- all data flows are wired end-to-end. Ollama engine will return `ollama_error` if the Ollama instance is unreachable, which is expected (graceful degradation).

## Self-Check: PASSED

All 11 files verified present on disk. Both commit hashes (d93c995, bbe5bcd) verified in git log.

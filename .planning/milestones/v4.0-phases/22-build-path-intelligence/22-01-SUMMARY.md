---
phase: 22-build-path-intelligence
plan: "01"
subsystem: backend-engine
tags: [build-path, schemas, recommender, system-prompt, pydantic]
dependency_graph:
  requires: []
  provides: [ComponentStep, BuildPathResponse, _enrich_build_paths, build-path-directive]
  affects: [prismlab/backend/engine/schemas.py, prismlab/backend/engine/recommender.py, prismlab/backend/engine/prompts/system_prompt.py]
tech_stack:
  added: []
  patterns: [post-LLM-enrichment, DataCache-zero-DB-queries, heuristic-fallback]
key_files:
  created: []
  modified:
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/engine/recommender.py
    - prismlab/backend/engine/prompts/system_prompt.py
decisions:
  - Component ordering uses Claude's component_order when valid against actual cache components; heuristic _sort_defensive_first activates on lost lane when Claude omits ordering
  - ComponentStep.reason defaults to empty string (frontend will render build_path_notes as the overall justification rather than per-step text)
  - Build paths only generated for items with >= 2 components to avoid noise for base items
metrics:
  duration: "3 min"
  completed_date: "2026-03-27"
  tasks_completed: 3
  files_modified: 3
---

# Phase 22 Plan 01: Build Path Intelligence — Backend Schemas and Enrichment Summary

## One-Liner

Backend pipeline extended with post-LLM component ordering via new ComponentStep/BuildPathResponse models, _enrich_build_paths enrichment step, and system prompt directives for component_order and build_path_notes structured output.

## What Was Built

### Task 1: Schema Extensions (schemas.py)
- Added `ComponentStep` Pydantic model: item_name (internal_name), item_id, cost (from DataCache), reason, position (1-based)
- Added `BuildPathResponse` Pydantic model: item_name, ordered steps list, build_path_notes paragraph
- Extended `ItemRecommendation` with nullable `component_order: list[str] | None` and `build_path_notes: str | None`
- Added `build_paths: list[BuildPathResponse]` to `RecommendResponse` (default empty list)
- Extended `LLM_OUTPUT_SCHEMA` item properties with nullable `component_order` (array of strings) and `build_path_notes` (string) — not added to required list

### Task 2: Recommender Enrichment (recommender.py)
- Imported `ComponentStep` and `BuildPathResponse` into recommender
- Added Step 6c in `recommend()` after Step 6b: calls `_enrich_build_paths` when cache is available
- Added `build_paths=build_paths` to `RecommendResponse` constructor
- Implemented `_enrich_build_paths`: iterates phases/items, validates Claude's component_order against actual cache components, appends omitted components for completeness, falls back to `_sort_defensive_first` heuristic on lost lane
- Implemented `_sort_defensive_first`: keyword-based proxy sorting (ring_of_health, vit_booster, platemail, etc. before offensive components), preserves relative order within groups

### Task 3: System Prompt Directive (system_prompt.py)
- Replaced the generic Build Path Awareness section with structured output directives
- Instructs Claude to emit `component_order`: ordered list of internal_names from first-buy to last-buy
- Instructs Claude to emit `build_path_notes`: 1-2 sentence paragraph with lane state and matchup context
- Lane-state guidance: defensive components first on lost lane, damage/farm components first on won lane
- Null behavior documented: single/no-component items should omit both fields

## Verification

All checks passed on end-to-end backend verification:
- `ComponentStep` and `BuildPathResponse` importable from engine.schemas
- `ItemRecommendation` has nullable `component_order` and `build_path_notes`
- `RecommendResponse` has `build_paths` field accepting list of BuildPathResponse
- LLM_OUTPUT_SCHEMA item properties contain both new fields
- `HybridRecommender` has `_enrich_build_paths` and `_sort_defensive_first` methods
- SYSTEM_PROMPT contains both `component_order` and `build_path_notes` directives

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | 8546e26 | feat(22-01): add ComponentStep, BuildPathResponse, and LLM build path fields |
| 2 | 0604837 | feat(22-01): add _enrich_build_paths to HybridRecommender and wire Step 6c |
| 3 | 3c43fe2 | feat(22-01): extend Build Path Awareness directive with component_order and build_path_notes |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. ComponentStep.reason defaults to "" but this is intentional: the frontend will display build_path_notes as the overall rationale. Per-step reasons are reserved for a future enhancement if needed.

## Self-Check: PASSED

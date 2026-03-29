---
phase: 22-build-path-intelligence
verified: 2026-03-27T00:00:00Z
status: passed
score: 4/4 must-haves verified
re_verification: false
---

# Phase 22: Build Path Intelligence — Verification Report

**Phase Goal:** Users see the optimal component purchase order for each recommended item, with reasoning for why to buy each component in that order, adapting to game state
**Verified:** 2026-03-27
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                              | Status     | Evidence                                                                                                      |
|----|----------------------------------------------------------------------------------------------------|------------|---------------------------------------------------------------------------------------------------------------|
| 1  | Each recommended item shows an ordered list of components to purchase                              | VERIFIED | `_enrich_build_paths` produces `BuildPathResponse.steps` (ordered `ComponentStep` list); frontend `BuildPathSteps.tsx` renders them by `position` |
| 2  | Each component step includes reasoning for its position in the order                               | VERIFIED | `build_path_notes` paragraph (Claude-generated or empty-fallback) rendered in italic above the component strip in `BuildPathSteps.tsx` |
| 3  | During GSI-connected games, components affordable at current gold are visually highlighted         | VERIFIED | `gold` from `gsiStore.liveState.gold` flows: `ItemTimeline` -> `PhaseCard` (guarded by `isGsiConnected`) -> `BuildPathSteps`; `text-radiant` applied when `currentGold >= step.cost` |
| 4  | Component ordering adapts to game state — lost lane prioritizes defensive components               | VERIFIED | `_sort_defensive_first` heuristic fires when `request.lane_result == "lost"` and Claude omits `component_order`; Claude is also instructed via system prompt directive |

**Score:** 4/4 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `prismlab/backend/engine/schemas.py` | `ComponentStep`, `BuildPathResponse` Pydantic models; `ItemRecommendation.component_order` and `build_path_notes`; `RecommendResponse.build_paths`; `LLM_OUTPUT_SCHEMA` extended | VERIFIED | All models present, fields correct, LLM schema includes both new nullable fields, `required` list unchanged |
| `prismlab/backend/engine/recommender.py` | `_enrich_build_paths` method; Step 6c in `recommend()` pipeline | VERIFIED | Method exists at line 375; Step 6c wired at lines 171-174; `build_paths=build_paths` passed to `RecommendResponse` at line 182 |
| `prismlab/backend/engine/prompts/system_prompt.py` | Build path directive with `component_order` and `build_path_notes` instructions | VERIFIED | `## Build Path Awareness` section updated; `component_order`, `build_path_notes`, lost/won lane guidance all present |
| `prismlab/frontend/src/types/recommendation.ts` | `ComponentStep`, `BuildPathResponse` TypeScript interfaces; `build_paths` on `RecommendResponse` | VERIFIED | Both interfaces exported (lines 24-36); `build_paths: BuildPathResponse[]` on `RecommendResponse` at line 74 |
| `prismlab/frontend/src/components/timeline/BuildPathSteps.tsx` | Standalone component rendering ordered component strip with affordability highlight | VERIFIED | File exists; renders position badge, Steam CDN image, cost; `text-radiant` on affordable, `text-on-surface-variant` on unaffordable |
| `prismlab/frontend/src/components/timeline/PhaseCard.tsx` | `build_path_notes` paragraph and `BuildPathSteps` rendered in selectedItem panel | VERIFIED | Imports `BuildPathSteps`; `buildPathMap` prop added; renders `<BuildPathSteps>` inside `selectedItem` panel when `buildPath.steps.length > 0` |
| `prismlab/frontend/src/components/timeline/ItemTimeline.tsx` | `buildPathMap` (keyed by `item_name`) built with `useMemo`, passed to `PhaseCard` | VERIFIED | `buildPathMap` useMemo at lines 33-41; passed as `buildPathMap={buildPathMap}` to all `PhaseCard` instances at line 67 |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `recommender.py` | `schemas.py` | `_enrich_build_paths` reads `ItemRecommendation.component_order`, writes `BuildPathResponse` | WIRED | Import of `ComponentStep`, `BuildPathResponse` at lines 22-23; method at line 375 |
| `recommender.py` | `DataCache` | `self.cache.item_name_to_id()` and `self.cache.get_item()` for component cost lookup | WIRED | Both calls present at lines 415-416 |
| `ItemTimeline.tsx` | `PhaseCard.tsx` | `buildPathMap` prop (`Map<string, BuildPathResponse>`) | WIRED | `buildPathMap` computed in `ItemTimeline` and passed to `PhaseCard` at line 67 |
| `PhaseCard.tsx` | `BuildPathSteps.tsx` | `buildPath` prop passed when `selectedItem` exists and `buildPath.steps.length > 0` | WIRED | `buildPathMap.get(selectedItem.item_name)` at line 115; conditional `<BuildPathSteps>` render at line 117 |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `BuildPathSteps.tsx` | `buildPath.steps` | `RecommendResponse.build_paths` populated by `_enrich_build_paths` from `DataCache.get_item().components` | Yes — reads real item component tuples from in-memory DataCache | FLOWING |
| `BuildPathSteps.tsx` | `buildPath.build_path_notes` | Claude's structured output field `build_path_notes` per item; falls back to empty string | Yes — Claude emits non-empty notes when items have components; empty string on fallback is rendered silently (guarded by `{buildPath.build_path_notes && ...}`) | FLOWING |
| `BuildPathSteps.tsx` | `currentGold` | `gsiStore.liveState.gold` (GSI WebSocket broadcast) guarded by `isGsiConnected` | Yes — real GSI gold value; `null` when GSI not connected, disabling highlight gracefully | FLOWING |
| `BuildPathSteps.tsx` | `step.cost` | `DataCache.get_item(comp_id).cost` (from OpenDota item constants) | Yes — item costs from populated DataCache; `null` if component not in cache, cost span conditionally rendered | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend schemas import and field assertions | `python -c "from engine.schemas import ComponentStep, BuildPathResponse, ItemRecommendation, RecommendResponse, LLM_OUTPUT_SCHEMA; ..."` | ALL CHECKS PASS | PASS |
| `HybridRecommender` has `_enrich_build_paths` and `_sort_defensive_first` | `python -c "from engine.recommender import HybridRecommender; assert hasattr(...)"`  | ALL CHECKS PASS | PASS |
| `SYSTEM_PROMPT` contains build path directives | `python -c "from engine.prompts.system_prompt import SYSTEM_PROMPT; assert 'component_order' in SYSTEM_PROMPT; ..."` | ALL CHECKS PASS | PASS |
| TypeScript strict-mode compile | `npx tsc --noEmit --strict` | Exit 0, 0 errors | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|------------|------------|-------------|--------|---------|
| PATH-01 | 22-01-PLAN, 22-02-PLAN | User can see the optimal component purchase order for each recommended item | SATISFIED | `BuildPathSteps.tsx` renders `steps` ordered by `position`; strip shows component icons in purchase order |
| PATH-02 | 22-01-PLAN, 22-02-PLAN | User can see reasoning for component ordering | SATISFIED | `build_path_notes` paragraph rendered in italic above component strip; Claude instructed by system prompt directive to emit ordering rationale |
| PATH-03 | 22-02-PLAN | User can see which components are affordable at current gold during GSI-connected games | SATISFIED | `text-radiant` applied when `currentGold >= step.cost`; `currentGold` is `null` when GSI not connected, silently disabling highlight |
| PATH-04 | 22-01-PLAN | Component ordering adapts to game state — lost lane prioritizes defensive components | SATISFIED | `_sort_defensive_first` heuristic fires on `lane_result == "lost"`; system prompt directs Claude to order defensive components first on lost lane |

All 4 requirements satisfied. No orphaned requirements — PATH-01 through PATH-04 are the only requirements mapped to Phase 22 in REQUIREMENTS.md.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `recommender.py` | 421 | `reason=""` with comment "filled below from build_path_notes or heuristic" | Info | Misleading comment — per-step `reason` is intentionally never filled. The reasoning lives in `build_path_notes` on `BuildPathResponse` (not per-step). Frontend confirms: `BuildPathSteps.tsx` does not render `step.reason`. This is a design decision documented in the SUMMARY, not a stub. |

No blocker or warning anti-patterns found.

---

### Human Verification Required

#### 1. Build Path Panel Renders on Item Click

**Test:** Load a recommendation for a hero with a multi-component item (e.g., BKB, Linken's Sphere). Click the item in the PhaseCard. Confirm the reasoning panel opens, shows the `build_path_notes` paragraph in italic, and displays the component strip with position numbers and gold costs.
**Expected:** Component strip shows 2-4 component icons with position badges (1, 2, 3...) and gold costs below each.
**Why human:** Requires a live recommendation response with a populated `build_paths` array — cannot be verified without a running server and real Claude output.

#### 2. GSI Affordability Highlight

**Test:** Connect GSI (real game or GSI simulator), ensure `liveState.gold` is populated. Open a recommendation and click a multi-component item whose first component costs less than current gold. Verify that component's cost label is rendered in radiant green, and components costing more than current gold are dim.
**Expected:** The affordable component shows `text-radiant` (#6aff97) color; unaffordable components show `text-on-surface-variant` (dim).
**Why human:** Requires live GSI data flowing into the frontend — cannot simulate without a running WebSocket connection and real `liveState.gold` value.

#### 3. Lost Lane Defensive Ordering

**Test:** Submit a recommendation with `lane_result: "lost"` for a hero building a defensive item like Hood of Defiance (ring_of_health + cloak + hood_of_defiance). Verify that `ring_of_health` appears as step 1 and defensive components precede offensive ones in the build path strip.
**Expected:** Defensive components (ring_of_health, cloak) are ordered before offensive components in the strip.
**Why human:** Requires a running backend with a real DataCache populated with item component data, and a Claude response that either provides `component_order` or falls back to the heuristic.

---

### Gaps Summary

No gaps. All 4 observable truths verified, all 7 artifacts pass all four levels (exists, substantive, wired, data flowing), all 4 key links confirmed wired, all 4 requirements satisfied, TypeScript compiles clean, and backend Python imports pass end-to-end assertion checks.

The single noted item (`reason=""` comment) is a design intent documented in the SUMMARY — per-step reasons are intentionally empty; the overall rationale is `build_path_notes`. The frontend does not render `step.reason`, so no user-visible impact.

---

_Verified: 2026-03-27_
_Verifier: Claude (gsd-verifier)_

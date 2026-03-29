---
phase: 21-timing-benchmarks
verified: 2026-03-27T17:42:08Z
status: human_needed
score: 12/13 must-haves verified
human_verification:
  - test: "Trigger a live recommendation and inspect the generated 'reasoning' field on returned items"
    expected: "At least one item's reasoning references a timing benchmark — e.g. 'BKB is time-sensitive, win rate drops after the 20-min window' or cites [TIMING-CRITICAL] context"
    why_human: "TIME-03 requires Claude's actual LLM output to contain timing-specific language. The infrastructure (system prompt directives + '## Item Timing Benchmarks' section in user message) is fully wired, but whether Claude acts on it is only verifiable by inspecting a real API response"
---

# Phase 21: Timing Benchmarks Verification Report

**Phase Goal:** Users see data-backed timing windows on recommended items — how early is good, when is on-track, when is late — with urgency signals for timing-sensitive purchases and live tracking during GSI games
**Verified:** 2026-03-27T17:42:08Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Zone classification produces good/on-track/late ranges with aggregate win rates from raw TimingBucket data | VERIFIED | `timing_zones.py` fully implemented; 11 unit tests pass; weighted-avg and peak-WR thresholds correctly partition buckets |
| 2 | Items with steep win-rate falloff (good-zone minus late-zone > 10pp) are flagged as urgent | VERIFIED | `is_urgent = (good_avg_wr - late_avg_wr) > 0.10` in `classify_timing_zones()`; test_urgency_detection_steep_falloff and test_urgency_detection_small_spread both pass |
| 3 | Context builder timing section formats timing benchmarks for Claude's user message with specific numbers | VERIFIED | `_build_timing_section()` formats per D-05 spec with minute ranges and WR%; `## Item Timing Benchmarks` header injected into `build()` output; 4 tests in TestBuildTimingSection pass |
| 4 | RecommendResponse includes pre-computed timing_data list alongside LLM-generated phases | VERIFIED | `timing_data: list[ItemTimingResponse] = Field(default_factory=list)` on `RecommendResponse`; `timing_data: ItemTimingData[]` on frontend `RecommendResponse` interface |
| 5 | Recommender enrichment step populates timing_data without touching LLM output schema | VERIFIED | `_enrich_timing_data()` runs after `_validate_item_ids` (Step 6b); LLM_OUTPUT_SCHEMA contains no timing fields |
| 6 | Each recommended item with timing data shows a horizontal bar segmented into green/gold/crimson zones | VERIFIED | `TimingBar.tsx` renders three `<div>` segments with `bg-radiant`, `bg-secondary-fixed-dim`, `bg-primary-container`; proportional widths from bucket counts |
| 7 | Items with steep win-rate falloff have a pulsing crimson glow border | VERIFIED | `timing-urgent` CSS class applied when `timingData?.is_urgent && !isPurchased`; `@keyframes pulse-urgency` defined in `globals.css` with `prefers-reduced-motion` fallback |
| 8 | Hovering over the timing bar shows a tooltip with zone ranges, win rates, confidence, and sample size | VERIFIED | Tooltip renders on `onMouseEnter`/`onFocus`; shows Good/On-track/Late rows with ranges, WR%, and "Based on N games (confidence)" footer |
| 9 | Weak confidence items show the timing bar at reduced opacity | VERIFIED | `opacity = confidence === "strong" ? 1 : confidence === "moderate" ? 0.7 : 0.4` applied inline on segments container |
| 10 | During GSI-connected games, a vertical marker shows current game clock position on the timing bar | VERIFIED | `LiveTimingMarker` computed with `(currentGameClock / maxTime) * 100` clamped 0-100%; hidden when window passed |
| 11 | During GSI-connected games, 'Xg away' text shows gold needed for each item | VERIFIED | Gold away / "Affordable now" logic wired via `currentGold` from `useGsiStore`; only shown when `!isWindowPassed` |
| 12 | When game clock passes the late threshold, the timing bar greys out with 'Window passed' label | VERIFIED | `isWindowPassed` check replaces zone segments with `bg-surface-container-high`; "Window passed" label rendered below bar |
| 13 | Claude's reasoning references specific timing benchmarks when explaining item urgency (TIME-03) | NEEDS HUMAN | System prompt `## Timing Benchmarks` directive and `## Item Timing Benchmarks` context section are fully wired; whether Claude acts on them requires inspecting real LLM output |

**Score:** 12/13 truths verified (1 requires human confirmation)

---

## Required Artifacts

### Plan 01 Artifacts (Backend)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `prismlab/backend/engine/timing_zones.py` | `classify_timing_zones()` utility | VERIFIED | 135 lines; full implementation with zone classification, urgency detection, time formatting, confidence aggregation |
| `prismlab/backend/engine/schemas.py` | `ItemTimingResponse` model and `timing_data` field on `RecommendResponse` | VERIFIED | `class ItemTimingResponse` at line 149; `timing_data: list[ItemTimingResponse] = Field(default_factory=list)` at line 175 |
| `prismlab/backend/engine/context_builder.py` | `_build_timing_section()` method | VERIFIED | Method at line 439; integrated into `build()` at line 128-131 |
| `prismlab/backend/engine/recommender.py` | `_enrich_timing_data()` method | VERIFIED | Method at line 326; called in `recommend()` at lines 164-167; `timing_data` passed to `RecommendResponse` constructor at line 174 |
| `prismlab/backend/tests/test_timing_zones.py` | Unit tests for zone classification | VERIFIED | 11 tests across `TestClassifyTimingZones` and `TestItemTimingResponseSchema`; all pass |
| `prismlab/backend/tests/test_context_builder.py` | `TestBuildTimingSection` tests | VERIFIED | 4 tests added at lines 658-745; all pass |

### Plan 02 Artifacts (Frontend)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `prismlab/frontend/src/types/recommendation.ts` | `TimingBucketUI`, `ItemTimingData` interfaces, `timing_data` on `RecommendResponse` | VERIFIED | `TimingBucketUI` at line 3, `ItemTimingData` at line 11, `timing_data: ItemTimingData[]` at line 59 |
| `prismlab/frontend/src/components/timeline/TimingBar.tsx` | `TimingBar` component with tooltip/urgency/GSI integration | VERIFIED | 223 lines; full implementation including tooltip, LiveTimingMarker, WindowPassedOverlay, gold text, accessibility attrs |
| `prismlab/frontend/src/components/timeline/ItemCard.tsx` | Modified `ItemCard` accepting timing data and urgency class | VERIFIED | `timingData` prop at line 12; `timing-urgent` class at line 58; `<TimingBar>` rendered at lines 100-116 |
| `prismlab/frontend/src/components/timeline/PhaseCard.tsx` | Modified `PhaseCard` passing timing data to `ItemCard`s | VERIFIED | `timingDataMap: Map<string, ItemTimingData>` prop at line 10; passed to each `ItemCard` at line 85 |
| `prismlab/frontend/src/components/timeline/ItemTimeline.tsx` | Modified `ItemTimeline` building timing map and wiring GSI state | VERIFIED | `timingDataMap` built with `useMemo` at lines 23-31; `gold` from `useGsiStore` at line 17; passed to `PhaseCard`s at lines 54-57 |
| `prismlab/frontend/src/styles/globals.css` | `pulse-urgency` keyframes and reduced-motion fallback | VERIFIED | `@keyframes pulse-urgency` at line 66; `.timing-urgent` class at line 71; `@media (prefers-reduced-motion: reduce)` at line 75 |

---

## Key Link Verification

### Plan 01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `timing_zones.py` | `data/cache.py` | `from data.cache import TimingBucket` | VERIFIED | Line 13 of `timing_zones.py` |
| `recommender.py` | `timing_zones.py` | `from engine.timing_zones import classify_timing_zones` | VERIFIED | Line 28 of `recommender.py` |
| `context_builder.py` | `timing_zones.py` | `from engine.timing_zones import classify_timing_zones` | VERIFIED | Line 22 of `context_builder.py` |
| `recommender.py` | `schemas.py` | Constructs `ItemTimingResponse` objects | VERIFIED | Line 21 imports `ItemTimingResponse`; used at line 353 in `_enrich_timing_data()` |

### Plan 02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `ItemTimeline.tsx` | `gsiStore.ts` | `useGsiStore` selectors for `game_clock` and `gold` | VERIFIED | Lines 15-17; `gold` at line 17, `gameClock` at line 16 |
| `PhaseCard.tsx` | `ItemCard.tsx` | Passes `timingData`, `currentGameClock`, `currentGold` | VERIFIED | Lines 85-87 of `PhaseCard.tsx` |
| `ItemCard.tsx` | `TimingBar.tsx` | `<TimingBar>` render when timing data present and not purchased | VERIFIED | Lines 100-116; conditional on `timingData && !isPurchased` |
| `recommendation.ts` | Backend `schemas.py` | `interface ItemTimingData` mirrors `ItemTimingResponse` | VERIFIED | All fields match; snake_case preserved for JSON deserialization |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `TimingBar.tsx` | `buckets`, `goodWinRate`, `lateWinRate` | `ItemTimingData` from `RecommendResponse.timing_data` | Yes — populated by `_enrich_timing_data()` from `DataCache.get_hero_timings()` | FLOWING |
| `_enrich_timing_data()` | `timings` dict | `self.cache.get_hero_timings(hero_id)` | Yes — DataCache populated from OpenDota scenarios endpoint (Phase 19) | FLOWING |
| `_build_timing_section()` | `timings` dict | `self.cache.get_hero_timings(hero_id)` | Yes — same DataCache source; returns `""` gracefully when no data | FLOWING |
| `ItemTimeline.tsx` | `timingDataMap` | `data.timing_data` from API response | Yes — `useMemo` builds Map from array; guarded with `if (data.timing_data)` | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All timing zone tests pass | `python -m pytest tests/test_timing_zones.py -q` | 11 passed | PASS |
| All context builder timing tests pass | `python -m pytest tests/test_context_builder.py -q -k "timing or Timing"` | 4 passed | PASS |
| Full backend suite — no regressions | `python -m pytest tests/ -x -q` | 246 passed, 2 skipped, 0 failures | PASS |
| TypeScript compiles clean | `npx tsc --noEmit` | 0 errors | PASS |
| LLM schema not contaminated | `grep "timing" schemas.py` (excluding ItemTimingResponse/timing_data/#) | `timing` appears only in `RecommendPhase.timing` (phase timing string, present in LLM schema as existing field) | PASS |
| Commit hashes verified | `git log --oneline` | ee9eff4, d910b79, 6bb913b, b17efd5 all present | PASS |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| TIME-01 | 21-01, 21-02 | User can see timing benchmarks (good/average/late window with win rate gradients) on each recommended item | SATISFIED | `TimingBar.tsx` renders three-zone bar; `timing_data` flows from backend to frontend; `ItemTimingResponse` carries pre-formatted ranges and WR floats |
| TIME-02 | 21-01, 21-02 | User can see urgency indicators distinguishing timing-sensitive items from flexible items | SATISFIED | `is_urgent` flag from 10pp threshold; `timing-urgent` CSS class applies pulsing crimson glow; `[TIMING-CRITICAL]` tag in Claude context |
| TIME-03 | 21-01 | Claude's reasoning references specific timing benchmarks when explaining item urgency | NEEDS HUMAN | Infrastructure complete: system prompt `## Timing Benchmarks` directive (lines 49-57), `## Item Timing Benchmarks` section injected into user message with specific WR% and minute ranges, `[TIMING-CRITICAL]` markers. REQUIREMENTS.md shows `[ ]` Pending — behavioral verification requires inspecting real LLM output |
| TIME-04 | 21-02 | User can see live comparison of current gold/clock against timing benchmarks during GSI-connected games | SATISFIED | `LiveTimingMarker` positions from `game_clock`; gold-away text from `gold` via `useGsiStore`; `WindowPassedOverlay` when clock exceeds late threshold; all three propagated through `ItemTimeline -> PhaseCard -> ItemCard -> TimingBar` chain |

### Orphaned Requirements Check

REQUIREMENTS.md maps TIME-01, TIME-02, TIME-03, TIME-04 to Phase 21. All four appear in plan frontmatter (TIME-01/02/03 in 21-01; TIME-01/02/04 in 21-02). No orphaned requirements.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `TimingBar.tsx` | 23 | `isUrgent: _isUrgent` — prop renamed with underscore prefix, not directly used in JSX logic | Info | `isUrgent` is destructured and renamed `_isUrgent` (unused directly); urgency CSS class is applied by `ItemCard.tsx` at the call site instead. This is an intentional design choice: the parent owns the urgency class. Not a stub — the urgency glow works correctly. |

No blocker or warning anti-patterns found. The `_isUrgent` naming is a minor stylistic observation; the urgency animation is correctly applied by `ItemCard.tsx` before passing to `TimingBar`.

---

## Human Verification Required

### 1. TIME-03: Claude Timing Benchmark References in Reasoning

**Test:** Request a recommendation for a hero with known timing data (e.g., Juggernaut Pos 1 vs a spell-spammer like Skywrath or Lina). Open browser devtools Network tab, find the `/api/recommend` response, and read the `reasoning` fields on core items like Maelstrom, BKB, or Battlefury.

**Expected:** At least one item's reasoning text references timing context — e.g., language like "timing window," a specific minute range, "win rate drops," or "time-sensitive" that clearly traces back to the `## Item Timing Benchmarks` section Claude received.

**Why human:** TIME-03 requires observing actual LLM output quality. The infrastructure is fully wired — the system prompt instructs Claude to "reference timing windows when explaining item urgency" and the user message contains `## Item Timing Benchmarks` with specific WR% and minute-range data plus `[TIMING-CRITICAL]` flags. Whether Claude's output quality meets the requirement can only be verified by inspecting a real API response. REQUIREMENTS.md tracks this as `Pending`.

---

## Gaps Summary

No blocking gaps. All 12 programmatically-verifiable must-haves pass: zone classification utility, urgency detection, schema extension, context builder section, recommender enrichment, TypeScript types, TimingBar component, component tree wiring, CSS animation, GSI live tracking, window-passed state, and the full data flow from DataCache through API response to rendered UI.

The single pending item (TIME-03) requires human inspection of a live LLM response to confirm that Claude actually acts on the timing context it receives. The infrastructure for this is complete — the gap is verification of behavioral output quality, not missing code.

---

_Verified: 2026-03-27T17:42:08Z_
_Verifier: Claude (gsd-verifier)_

---
phase: 23-win-condition-framing
verified: 2026-03-27T21:52:00Z
status: human_needed
score: 5/6 must-haves verified
human_verification:
  - test: "Submit a recommendation request with 5 allied heroes (hero_id + 4 allies) and 5 all_opponents hero IDs. Confirm the overall_strategy text frames the recommendation around the classified archetype (e.g. 'Your teamfight draft should snowball before the enemy scaling carries come online') rather than only individual matchup counters."
    expected: "overall_strategy references the allied team's classified archetype and contextualizes item timing relative to the win condition, not just hero-specific counters."
    why_human: "WCON-02/WCON-03 depend on Claude's adherence to the Win Condition Framing directive in the system prompt. Code delivers the ## Team Strategy context section and the directive exists, but whether Claude actually anchors overall_strategy to it and deprioritizes luxury items in early-win-condition drafts requires a live response."
  - test: "Submit a request with 5 all_opponents heroes that classify as 'late-game scale' (e.g. 3x Carry-tagged heroes). Confirm the recommendation includes items that enable early aggression and that luxury items are either absent or explicitly noted as lower priority."
    expected: "WCON-03: When enemy team is late-game scale, luxury items move to situational/absent from core slots; early power-spike items are elevated to core."
    why_human: "The system prompt instructs Claude to 'recommend items that enable early aggression' when the enemy outscales, but there is no programmatic enforcement of priority labels. Observable only in a live response."
---

# Phase 23: Win Condition Framing Verification Report

**Phase Goal:** Item recommendations are anchored by a team-level win condition statement that classifies how the draft wins, frames the overall strategy, and accounts for the enemy team's macro plan
**Verified:** 2026-03-27T21:52:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Given 3+ allied hero IDs, classify_draft() returns a WinConditionResult with one of the 5 archetypes | VERIFIED | 11/11 tests pass including all 4 named archetypes; deathball covered by set assertion |
| 2 | Given 3+ enemy hero IDs, classify_draft() returns a separate WinConditionResult for the enemy team | VERIFIED | `_enrich_win_condition()` calls classify_draft with `request.all_opponents` (line 461 recommender.py); `_build_team_strategy_section` calls classify_draft with `request.all_opponents` (line 496 context_builder.py) |
| 3 | When fewer than 3 hero IDs are supplied, classify_draft() returns None | VERIFIED | test_empty_returns_none and test_two_heroes_returns_none both pass |
| 4 | The user message includes a ## Team Strategy section when 3+ allied or enemy heroes are computed | VERIFIED | context_builder.py line 135-137: `sections.append(f"## Team Strategy\n{strategy_section}")` conditional on strategy_section being non-empty |
| 5 | RecommendResponse.win_condition carries classified archetypes to the frontend | VERIFIED | schemas.py line 219 adds `win_condition: WinConditionResponse | None = None` to RecommendResponse; recommender.py lines 179-190 populate and include it in response construction; TypeScript interface matches (recommendation.ts line 82) |
| 6 | Item priorities adjust based on win condition — luxury items deprioritized under early-aggression win conditions | UNCERTAIN | System prompt directive at lines 69-75 instructs Claude to frame strategy around win condition and adjust item timing recommendations. No programmatic enforcement of `priority` label changes. Observable behavior requires live LLM response. |

**Score:** 5/6 truths verified (1 uncertain — requires human)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `prismlab/backend/engine/win_condition.py` | WinConditionClassifier with classify_draft() + WinConditionResult | VERIFIED | 77-line file, exports `classify_draft` and `WinConditionResult`, implements 5-archetype weighted scoring, confidence thresholds |
| `prismlab/backend/engine/schemas.py` | WinConditionResponse Pydantic model + all_opponents on RecommendRequest + win_condition on RecommendResponse | VERIFIED | WinConditionResponse at line 126; all_opponents at line 40; win_condition at line 219; absent from LLM_OUTPUT_SCHEMA |
| `prismlab/backend/engine/context_builder.py` | `_build_team_strategy_section()` method | VERIFIED | Method at line 481, injected at lines 134-137, uses `request.all_opponents` for enemy team (not lane_opponents) |
| `prismlab/backend/engine/recommender.py` | `_enrich_win_condition()` post-LLM enrichment step | VERIFIED | Method at line 444, called at line 181, result wired into RecommendResponse at line 190 |
| `prismlab/backend/tests/test_win_condition.py` | Tests covering archetype classification and confidence thresholds | VERIFIED | 11 tests, all pass (teamfight, split-push, pick-off, late-game scale, high/low confidence, None roles, minimum threshold) |
| `prismlab/frontend/src/types/recommendation.ts` | WinConditionResponse TypeScript interface + all_opponents + win_condition on RecommendResponse | VERIFIED | WinConditionResponse interface at line 38, all_opponents at line 101, win_condition at line 82 |
| `prismlab/frontend/src/components/timeline/WinConditionBadge.tsx` | Archetype pill component with allied/enemy display and confidence styling | VERIFIED | 49-line component, exports default WinConditionBadge, allied in text-secondary (gold), enemy in text-dire (red), opacity-100/75/50 for confidence |
| `prismlab/frontend/src/components/timeline/ItemTimeline.tsx` | WinConditionBadge rendered above strategy text | VERIFIED | Import at line 5, rendered at lines 52-54 (within overall_strategy block) and lines 62-69 (fallback edge case) |
| `prismlab/frontend/src/hooks/useRecommendation.ts` | all_opponents field wired from game.opponents into RecommendRequest | VERIFIED | Line 40: `all_opponents: game.opponents.filter(Boolean).map((h) => h!.id)` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| engine/recommender.py recommend() | engine/context_builder.py _build_team_strategy_section() | pre-LLM context injection using request.all_opponents | WIRED | context_builder.py line 135 calls `_build_team_strategy_section(request)` inside `build()` |
| engine/recommender.py recommend() | engine/win_condition.py classify_draft() | post-LLM _enrich_win_condition() step | WIRED | recommender.py line 181 calls `_enrich_win_condition(request)`; method calls classify_draft at lines 459, 461 |
| engine/context_builder.py | ## Team Strategy (LLM user message) | sections.append conditional | WIRED | context_builder.py lines 136-137: `sections.append(f"## Team Strategy\n{strategy_section}")` |
| useRecommendation.ts | RecommendRequest.all_opponents | game.opponents.filter(Boolean).map | WIRED | useRecommendation.ts line 40 |
| ItemTimeline.tsx | WinConditionBadge.tsx | data.win_condition prop | WIRED | ItemTimeline.tsx lines 5, 52-54, 62-69 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| WinConditionBadge.tsx | winCondition (WinConditionResponse) | RecommendResponse.win_condition, populated by _enrich_win_condition() | Yes — calls classify_draft() against DataCache.get_hero() using request.all_opponents | FLOWING |
| ItemTimeline.tsx (strategy) | data.win_condition | RecommendResponse from /api/recommend | Yes — backend enrichment, not hardcoded | FLOWING |
| _build_team_strategy_section | allied_result, enemy_result | classify_draft() against DataCache | Yes — reads HeroCached.roles from in-memory cache populated at startup | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| classify_draft returns correct archetypes | `python -m pytest tests/test_win_condition.py -v` | 11 passed in 0.03s | PASS |
| Full backend test suite — no regressions | `python -m pytest tests/ -q` | 257 passed, 2 skipped | PASS |
| Frontend TypeScript compilation | `npx tsc --noEmit` | 0 errors | PASS |
| Frontend unit tests — no regressions | `npm test -- --run` | 163 passed (16 test files) | PASS |
| win_condition absent from LLM_OUTPUT_SCHEMA | `grep -n "win_condition" schemas.py` | Line 219 only (RecommendResponse, not LLM_OUTPUT_SCHEMA) | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| WCON-01 | 23-01-PLAN.md | System classifies 10-hero drafts into macro strategy archetypes (teamfight, split-push, pick-off, deathball, late-game scale) with a confidence indicator | SATISFIED | `classify_draft()` in win_condition.py implements 5-archetype weighted scoring with high/medium/low confidence; 11 tests verify all cases |
| WCON-02 | 23-01-PLAN.md, 23-02-PLAN.md | Win condition statement anchors overall_strategy and frames all item recommendations | SATISFIED (with human caveat) | `_build_team_strategy_section()` injects ## Team Strategy into Claude's user message; system prompt directive at lines 69-71 instructs Claude to frame overall_strategy around win condition; WinConditionBadge displays archetype above strategy text in UI |
| WCON-03 | 23-01-PLAN.md | Item priorities adjust based on win condition — early win condition deprioritizes luxury items | SATISFIED via LLM instruction (human verification recommended) | System prompt lines 72-74 instruct Claude to connect item timing to strategy and recommend early aggression items when enemy outscales. No programmatic priority label enforcement. Behavior depends on Claude's adherence to the directive. |
| WCON-04 | 23-01-PLAN.md, 23-02-PLAN.md | System assesses enemy team's win condition and recommends counter-strategy items | SATISFIED | Enemy classification uses `request.all_opponents` (full 5-hero enemy team) in both context_builder.py (line 496) and recommender.py (line 461); WinConditionBadge renders enemy archetype in dire red; system prompt at line 74-75 instructs counter-strategy recommendations |

All 4 WCON requirements mapped. No orphaned requirements for Phase 23.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| tests/test_win_condition.py | 42 | "deathball" archetype tested only via set membership, not dedicated test case | Info | Test coverage gap — deathball classification correctness not independently verified. Not a functional blocker; the archetype is correctly defined in ARCHETYPE_WEIGHTS. |

No blockers, no stubs, no hardcoded empty data, no TODO/FIXME markers in any phase 23 files.

### Human Verification Required

#### 1. Win Condition Anchors overall_strategy (WCON-02)

**Test:** Submit a POST to `/api/recommend` with `hero_id` + 4 `allies` hero IDs (3+ total producing a classified archetype, e.g. 3 teamfight heroes) and 5 `all_opponents` hero IDs. Review the `overall_strategy` text in the response.
**Expected:** The overall_strategy text references the team's classified archetype or explicitly frames items around the team's macro goal (e.g. "Your teamfight draft needs to force fights before the enemy late-game carries come online — BKB ensures you initiate without being kited"). It should not read like pure matchup counters disconnected from team composition.
**Why human:** Claude's adherence to the "Win Condition Framing" system prompt directive (lines 69-75) can only be assessed by reading an actual LLM response. The context injection is verified — whether Claude produces the expected framing is LLM behavior.

#### 2. Luxury Item Deprioritization Under Early Win Conditions (WCON-03)

**Test:** Submit a recommendation with 5 `all_opponents` heroes that all have "Carry" role tags (classifying enemy as "late-game scale"). Review the `phases[].items` for priority values.
**Expected:** Core item slots should favor power spikes that enable early aggression. Luxury late-game items (e.g. Butterfly, Satanic on most heroes) should appear as `situational` or be absent from the recommendation entirely when the enemy draft forces early pressure.
**Why human:** WCON-03 is implemented entirely through the system prompt directive — no programmatic enforcement changes `priority` labels. Observable only in a live Claude response against a qualifying game state.

### Gaps Summary

No gaps blocking goal achievement. All artifacts exist, are substantive, are wired, and data flows through the full pipeline (DataCache → classify_draft → context injection → LLM → post-LLM enrichment → frontend badge). The two human verification items are behavioral quality checks on LLM instruction-following, not code failures.

The minor coverage gap (no dedicated deathball test) is informational only — the archetype is correctly implemented in `ARCHETYPE_WEIGHTS` and covered by the set membership assertion.

---

_Verified: 2026-03-27T21:52:00Z_
_Verifier: Claude (gsd-verifier)_

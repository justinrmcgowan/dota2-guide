---
phase: 31-hero-selector
verified: 2026-03-29T22:00:00Z
status: human_needed
score: 10/10 must-haves verified
human_verification:
  - test: "End-to-end hero suggestion flow in browser"
    expected: "Suggest Hero button appears below hero picker when role is set but no hero selected; clicking it expands a list of ranked heroes; clicking a hero populates the hero picker and closes the panel; focusing the hero search input collapses the panel"
    why_human: "UI visibility, animated reveal behavior, and interaction flow cannot be verified programmatically without a running browser"
  - test: "matrices_available=false notice rendered correctly"
    expected: "When backend returns matrices_available=false (placeholder matrices not yet trained), panel shows 'Training data pending — showing all viable picks' notice and score bars are hidden"
    why_human: "Requires visual inspection of the rendered component with a known backend state"
---

# Phase 31: Hero Selector Verification Report

**Phase Goal:** Users can get ranked hero suggestions for their role and lane that account for current ally synergies and enemy counter-value before locking in their hero
**Verified:** 2026-03-29T22:00:00Z
**Status:** human_needed (all automated checks pass; 2 items require browser verification)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | POST /api/suggest-hero returns a ranked list of hero candidates when called | VERIFIED | `router.routes` confirms path `/suggest-hero`; Python import `from api.routes.suggest_hero import router` succeeds; route delegates to `HeroSelector.get_suggestions()` |
| 2 | Heroes are filtered to only those viable for the requested role (Pos 1-5) | VERIFIED | `HERO_ROLE_VIABLE` populated with {1: 30 heroes, 2: 36, 3: 34, 4: 38, 5: 29}; `HeroSelector.get_suggestions()` applies viable_ids filter before scoring |
| 3 | Each candidate is scored using synergy + counter matrices from DataCache | VERIFIED | `score_candidates()` reads `synergy[c_idx][a_idx]` for allies and `counter[c_idx][e_idx] - 0.5` for enemies; composite = syn*0.4 + ctr*0.4 |
| 4 | When matrices are empty/placeholder, scoring degrades to 0.0 for all candidates (no IndexError) | VERIFIED | `if not synergy or not counter: return {hid: (0.0, 0.0, 0.0) for hid in candidate_ids}` — confirmed by passing automated test with `cache._matrices = {}` |
| 5 | hero_id_to_index JSON string keys are cast to int before lookup (no silent miss) | VERIFIED | Line 351: `hero_id_to_index: dict[int, int] = {int(k): v for k, v in raw_mapping.items()}` |
| 6 | TypeScript interfaces for SuggestHeroRequest, HeroSuggestion, SuggestHeroResponse are defined | VERIFIED | All three interfaces present in `src/types/hero.ts` with correct snake_case fields |
| 7 | api.suggestHero() calls POST /api/suggest-hero | VERIFIED | `client.ts` line 72: `postJson<SuggestHeroRequest, SuggestHeroResponse>("/suggest-hero", req)` |
| 8 | Suggest Hero button appears in sidebar when no hero selected and role is set | VERIFIED (code) | Sidebar.tsx: `{!selectedHero && role !== null && (<div>...<button>...Suggest Hero`)` — requires human to confirm visual render |
| 9 | Clicking a suggested hero populates selectedHero and closes panel | VERIFIED (code) | `onSelect={(hero) => { selectHero(hero); setShowSuggestions(false); }}` — requires human to confirm interaction |
| 10 | When HeroPicker input is focused, suggestion panel auto-closes | VERIFIED (code) | HeroPicker.tsx line 153: `onFocus={() => { onFocus?.(); setIsOpen(true); }}`; Sidebar.tsx: `onFocus={() => setShowSuggestions(false)}` |

**Score:** 10/10 truths verified (8 fully automated, 2 code-verified pending human browser confirmation)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `prismlab/backend/engine/schemas.py` | SuggestHeroRequest, HeroSuggestion, SuggestHeroResponse Pydantic models | VERIFIED | Lines 380-408; all three classes present with correct fields and defaults |
| `prismlab/backend/engine/hero_selector.py` | HeroSelector class with score_candidates(), role_filter(), get_suggestions() | VERIFIED | 505 lines; `HERO_ROLE_VIABLE`, `score_candidates()`, `_get_bracket_matrices()`, `HeroSelector.get_suggestions()` all present |
| `prismlab/backend/api/routes/suggest_hero.py` | POST /api/suggest-hero FastAPI route | VERIFIED | Route at `/suggest-hero`; module-level `_selector = HeroSelector()`; delegates to `_selector.get_suggestions(request, data_cache)` |
| `prismlab/backend/main.py` | suggest_hero router registered at /api prefix | VERIFIED | Line 22: import; line 107: `app.include_router(suggest_hero_router, prefix="/api")` |
| `prismlab/frontend/src/types/hero.ts` | SuggestHeroRequest, HeroSuggestion, SuggestHeroResponse TypeScript interfaces | VERIFIED | Lines 26-48; snake_case fields match backend JSON keys exactly |
| `prismlab/frontend/src/api/client.ts` | api.suggestHero() method | VERIFIED | Lines 71-72; typed against new interfaces; calls POST /api/suggest-hero |
| `prismlab/frontend/src/components/draft/HeroSuggestPanel.tsx` | Ranked suggestion list with hero portraits and score bars | VERIFIED | 165 lines; useEffect fetches on mount/change; renders HeroPortrait rows; score bars omitted when `matrices_available=false`; fallback text-row when hero not in cache |
| `prismlab/frontend/src/components/layout/Sidebar.tsx` | Suggest Hero button + panel wired below Your Hero section | VERIFIED | Lines 57-83; conditional on `!selectedHero && role !== null`; animated reveal; `onFocus` prop wired to HeroPicker |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `hero_selector.py` | `data/cache.py` | `getattr(cache, "_matrices", {})` reads | VERIFIED | Line 349: `getattr(cache, "_matrices", {}).get(bracket, {})` — safe access with fallback |
| `hero_selector.py` | `heroPlaystyles.ts` | `HERO_ROLE_VIABLE` Python mirror | VERIFIED | 168 entries transcribed; comment: "SOURCE OF TRUTH: heroPlaystyles.ts — keep in sync when map is updated" |
| `HeroSuggestPanel.tsx` | `api/client.ts` | `api.suggestHero()` on mount/change | VERIFIED | Line 37: `api.suggestHero({role, ally_ids, enemy_ids, excluded_hero_ids, top_n: 10, bracket: 2})` |
| `suggest_hero.py` | `engine/hero_selector.py` | `HeroSelector().get_suggestions(request, data_cache)` | VERIFIED | Line 33: `response = _selector.get_suggestions(request, data_cache)` |
| `Sidebar.tsx` | `HeroSuggestPanel.tsx` | Conditional render when `!selectedHero && role !== null` | VERIFIED | Lines 58-83; correct props passed including `excludedHeroIds`, `allyIds`, `enemyIds` |
| `client.ts` | `suggest_hero.py` | POST /api/suggest-hero fetch call | VERIFIED | URL string `/suggest-hero` in client.ts; registered with `/api` prefix in main.py yielding `/api/suggest-hero` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `HeroSuggestPanel.tsx` | `result: SuggestHeroResponse` | `api.suggestHero()` POST call in `useEffect` | Yes — calls live backend endpoint; populated with heroes from DataCache | FLOWING |
| `HeroSelector.get_suggestions()` | `candidates: list[HeroCached]` | `cache.get_all_heroes()` from DataCache | Yes — DataCache._heroes populated from OpenDota on startup | FLOWING |
| `score_candidates()` | `synergy`, `counter` matrices | `cache._matrices[bracket]` from `matrices.json` | Conditional — scores are 0.0 when matrices not yet trained (by design, `matrices_available=false` signals this) | FLOWING (with documented degradation) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| HeroSelector import and empty-matrix degradation | `python -c "from engine.hero_selector import HeroSelector, HERO_ROLE_VIABLE; ... resp = hs.get_suggestions(req, cache); assert resp.matrices_available == False"` | All checks passed; Pos1 count: 30 | PASS |
| Route path registration | `python -c "from api.routes.suggest_hero import router; print([r.path for r in router.routes])"` | `['/suggest-hero']` | PASS |
| 29 unit tests (schemas + selector) | `pytest tests/test_hero_selector.py tests/test_suggest_hero_schemas.py --noconftest -q` | `29 passed in 0.08s` | PASS |
| TypeScript compile | `npx tsc --noEmit` | No output (zero errors) | PASS |
| HERO_ROLE_VIABLE keys cover all 5 roles | Python assertion: `set(HERO_ROLE_VIABLE.keys()) == {1,2,3,4,5}` | Passed; counts: {1:30, 2:36, 3:34, 4:38, 5:29} | PASS |
| Anti-Mage (hero_id=1) in Pos 1 | Python assertion: `1 in HERO_ROLE_VIABLE[1]` | Passed | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| HERO-01 | 31-01, 31-03 | Given a partial draft, role, and lane, system suggests top N hero picks ranked by predicted win rate | SATISFIED | `HeroSelector.get_suggestions()` scores all viable candidates, returns top_n sorted by composite score; POST `/api/suggest-hero` delivers this to the frontend |
| HERO-02 | 31-01 | Hero suggestions factor in synergy with allies and counter-value against enemies | SATISFIED | `score_candidates()` computes `syn_score` from `synergy[c_idx][a_idx]` for each ally and `ctr_score` from `counter[c_idx][e_idx] - 0.5` for each enemy; composite = syn*0.4 + ctr*0.4 |
| HERO-03 | 31-01, 31-03 | Suggestions are filtered by role/lane viability | SATISFIED | `HERO_ROLE_VIABLE` dict keyed by role 1-5 with hero_id sets; candidates filtered to `viable_ids` before scoring; fallback to all heroes when pool < 5 |
| HERO-04 | 31-02, 31-03 | Hero suggestion UI integrates into draft flow as optional step | SATISFIED | "Suggest Hero" toggle button in Sidebar below HeroPicker; panel only appears when `!selectedHero && role !== null`; selecting a hero calls `selectHero()` and closes panel |

No orphaned requirements — all four HERO-0x IDs mapped in REQUIREMENTS.md to Phase 31 are claimed and implemented by the phase plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | — |

"placeholder" appearing in docstrings (hero_selector.py lines 10, 347; suggest_hero.py line 26; Sidebar.tsx line 53) refers to the documented data-degradation scenario and the HTML input placeholder attribute — neither is a code stub. `return null` at HeroSuggestPanel.tsx line 67 is a legitimate pre-fetch guard, not an empty implementation.

### Human Verification Required

#### 1. End-to-end hero suggestion flow

**Test:** Open `http://localhost:8421`, leave "Your Hero" empty, set Role to any position (e.g. Pos 1). Confirm "Suggest Hero" button appears below the hero picker. Click it — panel should expand with a list of heroes. Click any hero — hero should populate "Your Hero" and the panel should close. Add an ally hero, clear "Your Hero", reopen suggestions — that ally should not appear in the list.
**Expected:** Animated reveal shows up to 10 hero portraits/rows. Selecting a suggestion populates `selectedHero` in the game store. Excluded heroes (allies, opponents) are absent from the list.
**Why human:** UI visibility, animated CSS transitions, and Zustand store interaction cannot be verified with grep or Python/TS compile checks.

#### 2. matrices_available=false notice and score bar suppression

**Test:** With no ML training run yet (placeholder matrices), open the Suggest Hero panel. Observe the notice text and the hero rows.
**Expected:** Notice "Training data pending — showing all viable picks" is visible above the hero list. No score bars appear below hero portraits. Heroes are sorted alphabetically (deterministic tie-break at score 0.0).
**Why human:** Requires visual inspection of the rendered component with backend returning `matrices_available: false`; cannot programmatically assert CSS visibility or absence of rendered child elements without a running browser.

### Gaps Summary

No gaps found. All artifacts exist, are substantive, are wired end-to-end, and data flows from DataCache through the API to the frontend component. 29 unit tests pass. TypeScript compiles clean. Two items are routed to human verification because they require a running browser to confirm visual and interaction behavior.

---

_Verified: 2026-03-29T22:00:00Z_
_Verifier: Claude (gsd-verifier)_

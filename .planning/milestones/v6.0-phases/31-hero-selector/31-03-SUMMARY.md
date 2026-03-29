---
phase: 31-hero-selector
plan: "03"
subsystem: hero-selector
tags: [fastapi, react, hero-suggestions, ui, integration]
dependency_graph:
  requires: [31-01, 31-02]
  provides: [POST /api/suggest-hero endpoint, HeroSuggestPanel UI]
  affects: [prismlab/backend/main.py, prismlab/frontend/src/components/layout/Sidebar.tsx]
tech_stack:
  added: []
  patterns: [module-level singleton for stateless engine, animated reveal via max-h transition, stable serialized deps for useEffect arrays]
key_files:
  created:
    - prismlab/backend/api/routes/suggest_hero.py
    - prismlab/frontend/src/components/draft/HeroSuggestPanel.tsx
  modified:
    - prismlab/backend/main.py
    - prismlab/frontend/src/components/layout/Sidebar.tsx
    - prismlab/frontend/src/components/draft/HeroPicker.tsx
decisions:
  - "HeroPicker.onFocus prop added to close suggest panel before dropdown opens — prevents dual-open state (Pitfall 5)"
  - "Stable serialized keys (join(',')) used in useEffect deps instead of array/set refs to avoid infinite fetch loops"
  - "Score bar omitted entirely when matrices_available=false to avoid misleading 50%-bar display"
  - "Fallback hero object built from HeroSuggestion when heroMap lookup misses — protects against cache race"
metrics:
  duration: "~8 min"
  completed: "2026-03-29"
  tasks: 2
  files: 5
---

# Phase 31 Plan 03: Hero Selector — Route and UI Integration Summary

End-to-end hero suggestion flow: POST /api/suggest-hero FastAPI route calling HeroSelector.get_suggestions(), and HeroSuggestPanel React component wired into Sidebar.tsx below "Your Hero".

## Tasks Completed

| Task | Description | Commit | Files |
|------|-------------|--------|-------|
| 1 | Create POST /api/suggest-hero backend route and register in main.py | f643572 | suggest_hero.py, main.py |
| 2 | Create HeroSuggestPanel component and wire into Sidebar.tsx | a570e91 | HeroSuggestPanel.tsx, Sidebar.tsx, HeroPicker.tsx |
| 3 | Human verification of end-to-end flow | — (checkpoint) | — |

## What Was Built

### Backend: POST /api/suggest-hero
- `prismlab/backend/api/routes/suggest_hero.py`: New FastAPI route following recommend.py singleton pattern. Module-level `_selector = HeroSelector()` instance. Delegates fully to `HeroSelector.get_suggestions(request, data_cache)`.
- `prismlab/backend/main.py`: Import `suggest_hero_router` + `app.include_router(suggest_hero_router, prefix="/api")` added after match_history_router.
- Route returns `SuggestHeroResponse` with `suggestions: list[HeroSuggestion]` and `matrices_available: bool`.

### Frontend: HeroSuggestPanel
- `prismlab/frontend/src/components/draft/HeroSuggestPanel.tsx`: Self-contained panel component.
  - Props: `role`, `allyIds`, `enemyIds`, `excludedHeroIds`, `onSelect`
  - Fetches on mount and when role/allies/enemies/excluded changes (stable serialized string keys as deps)
  - Loading/error/empty states
  - "Training data pending — showing all viable picks" notice when `matrices_available=false`
  - Renders up to 10 hero rows via `HeroPortrait` with score bars (omitted when matrices unavailable)
  - Score bar formula: `min(100, max(5, (score + 0.5) * 100))%` — centers 0.0 at 50%, positive synergy wider
  - Fallback text-row render when hero not yet in `useHeroes()` cache

### Sidebar Integration
- `prismlab/frontend/src/components/layout/Sidebar.tsx`: `showSuggestions` state, "Suggest Hero" / "Hide Suggestions" toggle button appears when `!selectedHero && role !== null`. Animated reveal via `max-h-96 → max-h-0` transition. Selecting a suggestion calls `selectHero()` and closes the panel.
- `prismlab/frontend/src/components/draft/HeroPicker.tsx`: Added optional `onFocus?: () => void` prop. Wired to input's `onFocus` handler — fires before `setIsOpen(true)`, closing the suggestion panel before the hero search dropdown opens.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all data is wired from the live API endpoint. When `matrices_available=false` (placeholder matrices), the notice is shown and score bars are hidden, preventing misleading display.

## Verification

TypeScript strict-mode compile: zero errors.
Python import check: `from api.routes.suggest_hero import router` → `Route OK: ['/suggest-hero']`

Human browser verification (Task 3 checkpoint): Approved by user on 2026-03-29.

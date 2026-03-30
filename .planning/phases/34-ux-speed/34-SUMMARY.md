# Phase 34: UX Speed & Instant Items — Summary

**Status:** Complete
**Completed:** 2026-03-30

## One-liner
Two-pass recommendation (rules-fast → Claude-full), 3s draft polling, GSI auto-trigger from both hooks, parallel enrichment, cross-phase dedup, adjustable budget UI.

## What was built

### Backend
- `asyncio.gather()` in `_enrich_all` — 4 enrichment steps run in parallel
- `_deduplicate_across_phases()` — strips duplicate items across phases (earlier phase wins)
- Graceful win predictor model loading (non-fatal on placeholder .ubj files)
- `PUT /settings/budget` endpoint for runtime budget adjustment

### Frontend
- `recommendationStore`: `isPartial`, `setPartialData()`, `mergeData()` for two-pass flow
- `useRecommendation`: `recommendTwoPass()` fires fast-mode first, full auto/deep merges in
- `useLiveDraft`: 3s polling (down from 10s), auto-triggers `recommendTwoPass` on hero+role detection
- `useGameIntelligence`: also auto-triggers `recommendTwoPass` on GSI hero+role detection (fallback when live match API doesn't return data)
- `ItemTimeline`: partial loading spinner while full results stream in
- `GetBuildButton`: "Updating..." label during two-pass merge
- `SettingsPanel`: editable budget input field

## Commits
- `ce138f5` perf: parallelize enrichment pipeline
- `e4d4495` feat: isPartial + mergeData in store
- `cc2f92c` feat: two-pass recommendation
- `ceec58a` feat: 3s polling + auto-trigger
- `17f2e26` feat: GSI hero change triggers draft fetch
- `574e581` feat: partial loading state in UI
- `1e6028d` fix: pre-existing build errors
- `984dca6` fix: auto-trigger from GSI hero detection
- `461ab44` fix: cross-phase item deduplication
- `6d1dc0f` feat: adjustable API budget
- `0711b7e` fix: API_BASE in setEngineBudget
- `5d92784` fix: graceful win predictor model loading

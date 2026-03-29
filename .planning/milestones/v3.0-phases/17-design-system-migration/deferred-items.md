# Deferred Items - Phase 17

## Pre-existing TypeScript Errors in Test Files

Discovered during 17-01 build verification. These errors exist in test files and are unrelated to the design system migration:

1. **GameClock.test.tsx** - Missing `roshan_state`, `radiant_tower_count`, `dire_tower_count` properties on `GsiLiveState` mock objects
2. **LiveStatsBar.test.tsx** - `roshan_state` type incompatibility (string | undefined vs string)
3. **GsiStatusIndicator.test.tsx** - Same missing `GsiLiveState` properties
4. **useGameIntelligence.test.ts** - Missing `fallback_reason` on `RecommendResponse` mock
5. **recommendationStore.test.ts** - Missing `fallback_reason` on `RecommendResponse` mock
6. **itemMatching.test.ts** - Missing `fallback_reason` on `RecommendResponse` mock
7. **triggerDetection.test.ts** - Type-only import issues with `verbatimModuleSyntax`

These are all test fixture/mock issues from type changes in earlier phases that were not propagated to test files. The `tsc -b` step in `npm run build` catches them. The actual vite build (CSS + JS bundling) succeeds.

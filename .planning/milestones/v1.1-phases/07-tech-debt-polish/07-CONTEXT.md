# Phase 7: Tech Debt & Polish - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase cleans up v1.0 tech debt, fills test coverage gaps, polishes UI rough edges, and fixes the admin proxy. No new features — only improving what exists.

</domain>

<decisions>
## Implementation Decisions

### Dead Code Removal
- Remove `getHero`, `getItems`, `getItem` from `frontend/src/api/client.ts` — unused anywhere in the codebase
- Light scan for other dead code: unused imports, unreachable branches
- Remove orphaned `Item` type import from client.ts if no other consumer exists

### Test Coverage
- Frontend: Add tests for `recommendationStore` and `useRecommendation` hook — highest value, lowest effort
- Backend: Add `test_context_builder.py` — core logic untested, will change in Phase 8
- Focus on critical paths rather than arbitrary coverage percentage
- Match existing test style: Vitest + @testing-library with jsdom (frontend), pytest (backend)

### UI Polish
- Ensure LoadingSkeleton covers hero search, recommendation fetch, and re-evaluate flows with visible pulse animation
- Toast-style error banners that auto-dismiss after 5s — non-blocking
- Friendly empty state in MainPanel before first recommendation: "Select a hero and get your build"
- `/admin/` proxied to backend `/admin/` in nginx.conf — matches existing `/api/` pattern

### Claude's Discretion
- Specific implementation details for error toast component (animation, positioning)
- Exact wording of empty state messages
- Which specific unused imports/dead branches to remove beyond the known API methods

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ErrorBanner.tsx` — existing error display component in timeline/
- `LoadingSkeleton.tsx` — existing loading component in timeline/
- `fetchJson` / `postJson` — generic API helpers in client.ts
- 2 frontend test files: `gameStore.test.ts`, `heroSearch.test.ts`
- 6 backend test files: test_api, test_config, test_llm, test_matchup_service, test_recommender, test_rules

### Established Patterns
- Zustand stores with TypeScript strict mode
- Vitest + jsdom + @testing-library for frontend tests
- pytest with async session fixtures for backend tests
- Tailwind v4 CSS-first with OKLCH color system

### Integration Points
- `nginx.conf` — add `/admin/` location block
- `client.ts` — remove dead methods
- `MainPanel.tsx` — empty state rendering
- `recommendationStore` — add test file
- `useRecommendation` hook — add test file
- `context_builder.py` — add test file

</code_context>

<specifics>
## Specific Ideas

No specific requirements — standard cleanup and polish following established codebase patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

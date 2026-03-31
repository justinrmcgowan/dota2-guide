---
phase: 38-adaptiveness-accuracy
plan: 01
subsystem: engine
tags: [context-builder, diff-context, token-optimization, eval-snapshot, recommender]

# Dependency graph
requires:
  - phase: 36-prompt-quality
    provides: game_time_seconds and turbo fields in RecommendRequest
provides:
  - EvalSnapshot dataclass for request diff detection
  - build_diff() method producing compact re-evaluation context
  - Snapshot-based session tracking in HybridRecommender
  - input_tokens field on RecommendResponse for monitoring
affects: [38-02, api-monitoring, cost-tracking]

# Tech tracking
tech-stack:
  added: []
  patterns: [diff-based context building for LLM token optimization, frozen dataclass snapshots for immutable state comparison]

key-files:
  created:
    - prismlab/backend/tests/test_diff_context.py
  modified:
    - prismlab/backend/engine/context_builder.py
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/engine/recommender.py
    - prismlab/backend/data/refresh.py

key-decisions:
  - "EvalSnapshot uses frozen dataclass with sorted tuples for deterministic equality checks"
  - "build_diff returns None when opponents/allies change to force full context rebuild"
  - "Snapshots keyed by hero_id:role -- one active build per hero+role per session"
  - "Snapshots cleared on data refresh to prevent stale diff contexts"

patterns-established:
  - "Diff context pattern: summarize unchanged state + only changed fields for LLM re-evaluation"
  - "Snapshot lifecycle: store after successful LLM call, clear on cache/data refresh"

requirements-completed: [ADAPT-01, ADAPT-02]

# Metrics
duration: 8min
completed: 2026-03-31
---

# Phase 38 Plan 01: Diff-Based Re-Evaluation Context Summary

**EvalSnapshot-tracked diff context builder reducing mid-game re-evaluation token usage by 40%+ via selective field diffing**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-31T09:52:16Z
- **Completed:** 2026-03-31T10:00:30Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Diff-based context builder that omits static sections (item catalog, popularity, pro reference, timing benchmarks, exemplars, neutral catalog) from re-evaluation prompts, saving ~1450 tokens per re-eval
- EvalSnapshot frozen dataclass capturing all request fields for deterministic diff detection between evaluations
- Snapshot lifecycle management: store after successful LLM call, clear on data refresh
- Graceful fallback to full context when opponents/allies change (new matchup data needed)
- input_tokens field on RecommendResponse for production token monitoring
- 18 unit tests covering snapshot creation, diff generation, opponent/ally fallback, token reduction verification

## Task Commits

Each task was committed atomically:

1. **Task 1: Add diff-aware context builder and eval snapshot tracking** - `e62a72d` (feat)
2. **Task 2: Unit tests for diff context builder and snapshot lifecycle** - `e2eb3b8` (test)

## Files Created/Modified
- `prismlab/backend/engine/context_builder.py` - Added EvalSnapshot dataclass and build_diff() method
- `prismlab/backend/engine/schemas.py` - Added input_tokens field to RecommendResponse
- `prismlab/backend/engine/recommender.py` - Added snapshot management, diff routing in _deep_path and recommend_stream, _is_reevaluation, _snapshot_key, clear_snapshots
- `prismlab/backend/data/refresh.py` - Clear eval snapshots on data refresh
- `prismlab/backend/tests/test_diff_context.py` - 18 tests for diff context and snapshot lifecycle

## Decisions Made
- EvalSnapshot uses frozen dataclass (not Pydantic) for lightweight immutable snapshots -- dataclass equality is sufficient since we compare individual fields
- build_diff returns None (not raises) when opponents/allies change -- caller falls through to full build transparently
- Snapshots keyed by hero_id:role -- assumes one active build per hero+role combination per session, which matches the UI workflow
- Enemy context change detection uses MD5 hash of sorted JSON -- avoids deep comparison of nested Pydantic models
- Snapshots cleared on data refresh (via refresh.py) alongside HierarchicalCache clear -- prevents stale diff contexts after hero/item data updates

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added clear_snapshots() call in data/refresh.py**
- **Found during:** Task 1
- **Issue:** Plan mentioned clearing snapshots when HierarchicalCache clears but didn't specify the exact integration point
- **Fix:** Added _recommender.clear_snapshots() call in refresh.py right after _response_cache.clear()
- **Files modified:** prismlab/backend/data/refresh.py
- **Verification:** grep confirms clear_snapshots call present in refresh pipeline
- **Committed in:** e62a72d (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for preventing stale diff contexts after data refresh. No scope creep.

## Issues Encountered
- Token reduction test initially failed at 39.1% (just under 40% threshold) because mock DB produced minimal full context without items/popularity/timing data. Fixed by using test_db_setup fixture which loads real heroes/items into DataCache, making the full context realistically sized. With loaded cache, reduction exceeds 40%.

## Known Stubs
None -- all functionality is fully wired.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Diff-based context builder is ready for production use
- input_tokens field enables monitoring token savings per request
- Plan 02 can build on snapshot infrastructure for additional accuracy improvements

## Self-Check: PASSED

All 5 created/modified files verified on disk. Both task commits (e62a72d, e2eb3b8) verified in git log.

---
*Phase: 38-adaptiveness-accuracy*
*Completed: 2026-03-31*

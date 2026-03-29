---
phase: 26-engine-optimization
plan: 03
subsystem: engine
tags: [training-data, fine-tuning, ollama, jsonl, chatml, claude-api, unsloth]

# Dependency graph
requires:
  - phase: 26-engine-optimization-01
    provides: LLMEngine.last_usage token tracking, OllamaEngine, 3-mode architecture
provides:
  - Offline training data generation script producing ChatML JSONL for Unsloth fine-tuning
  - Hero/role/matchup combination generator covering ~7500 combos
affects: [26-engine-optimization (fine-tuning workflow)]

# Tech tracking
tech-stack:
  added: []
  patterns: [standalone async script reusing FastAPI engine components outside app context]

key-files:
  created:
    - prismlab/backend/scripts/__init__.py
    - prismlab/backend/scripts/generate_training_data.py
  modified: []

key-decisions:
  - "Hero role mapping uses conservative manual dict (~100 heroes) with DB-role fallback for unmapped heroes"
  - "ChatML format (system/user/assistant messages) for Unsloth compatibility, not Alpaca"
  - "Random seed (default 42) for reproducible combination shuffling across runs"
  - "Flush after each JSONL line so interrupted runs preserve all completed examples"

patterns-established:
  - "Standalone script pattern: reuse DataCache, ContextBuilder, LLMEngine outside FastAPI via direct async_session"

requirements-completed: [ENG-07]

# Metrics
duration: 3min
completed: 2026-03-28
---

# Phase 26 Plan 03: Training Data Generation Summary

**Offline CLI script generating ChatML JSONL training pairs via Claude API across ~7500 hero/role/matchup combinations using the actual ContextBuilder pipeline**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-28T17:51:49Z
- **Completed:** 2026-03-28T17:54:44Z
- **Tasks:** 1
- **Files created:** 2

## Accomplishments
- Standalone `generate_training_data.py` script that iterates hero/role/playstyle/matchup combinations
- Uses the real ContextBuilder.build() pipeline for training prompt generation (not simplified templates)
- Outputs ChatML-format JSONL compatible with Unsloth fine-tuning (system/user/assistant messages)
- CLI with --output, --limit, --resume, --delay, --seed for flexible usage
- Cost tracking using Haiku pricing ($1/$5 per MTok) with progress logging every 50 examples

## Task Commits

Each task was committed atomically:

1. **Task 1: Training data generation script** - `3c58c3e` (feat)

## Files Created/Modified
- `prismlab/backend/scripts/__init__.py` - Package init for scripts module
- `prismlab/backend/scripts/generate_training_data.py` - Training data generation CLI (545 lines)

## Decisions Made
- **Hero role mapping approach:** Conservative manual mapping dict covering ~100 common heroes with 1-2 roles each, plus a DB-role heuristic fallback for unmapped heroes. Quality over 100% coverage.
- **Output format:** ChatML JSONL (messages array with system/user/assistant) for Unsloth compatibility, matching the research recommendation.
- **Combination strategy:** 2-3 random matchups per hero/role/playstyle with 1-2 lane opponents each, producing ~7500 total combinations. Shuffled with a fixed seed for reproducibility.
- **Resume support:** Append mode when --resume is used; line-level flush so interrupted runs lose zero completed examples.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. Script uses existing ANTHROPIC_API_KEY from .env.

## Known Stubs
None - script is fully functional. Running it requires an API key and seeded database (existing prerequisites).

## Next Phase Readiness
- Training data pipeline ready: run `python -m scripts.generate_training_data --output data/training_data.jsonl --limit 10` for a test batch
- Full generation (~7500 examples) estimated at $11-19 USD via Haiku API
- Output JSONL feeds directly into Unsloth QLoRA fine-tuning pipeline

---
*Phase: 26-engine-optimization*
*Completed: 2026-03-28*

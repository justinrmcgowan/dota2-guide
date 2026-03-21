---
phase: 03-recommendation-engine
plan: 02
subsystem: ai-engine
tags: [claude-api, anthropic, structured-output, prompt-caching, llm, system-prompt, context-builder]

# Dependency graph
requires:
  - phase: 03-recommendation-engine/01
    provides: "Engine schemas (LLMRecommendation, LLM_OUTPUT_SCHEMA), matchup service (get_or_fetch_matchup, get_relevant_items, get_hero_item_popularity)"
provides:
  - "SYSTEM_PROMPT: 9600+ char 8K MMR analytical coach persona with specificity constraints and few-shot examples"
  - "ContextBuilder: assembles game state + matchup data + item catalog into compact Claude user message"
  - "LLMEngine: Claude API wrapper with structured JSON output, prompt caching, 10s timeout, fallback-safe"
affects: [03-recommendation-engine/03, 04-item-timeline]

# Tech tracking
tech-stack:
  added: [anthropic-sdk]
  patterns: [structured-output-via-output-config, prompt-caching-ephemeral, fallback-safe-none-return]

key-files:
  created:
    - prismlab/backend/engine/prompts/__init__.py
    - prismlab/backend/engine/prompts/system_prompt.py
    - prismlab/backend/engine/context_builder.py
    - prismlab/backend/engine/llm.py
    - prismlab/backend/tests/test_llm.py
  modified: []

key-decisions:
  - "System prompt at 9610 chars with specificity constraints requiring enemy hero names and ability references in every reasoning field"
  - "output_config.format with json_schema (GA path, not beta) for Claude structured output"
  - "cache_control ephemeral on system prompt block for 90% cost reduction on cached requests"
  - "max_retries=0 within 10s timeout budget to avoid consuming retry time"
  - "All LLMEngine failure paths return None to trigger rules-only fallback in orchestrator"

patterns-established:
  - "Fallback-safe LLM calls: every API error returns None, orchestrator decides fallback behavior"
  - "Prompt caching: system prompt as list of content blocks with cache_control"
  - "Structured output: Pydantic model -> model_json_schema() -> output_config.format"
  - "Context builder pre-filters items by role budget (10000g cores, 5500g supports)"

requirements-completed: [ENGN-02, ENGN-05]

# Metrics
duration: 4min
completed: 2026-03-21
---

# Phase 3 Plan 2: Claude API Integration Summary

**Claude API engine with 8K MMR system prompt, context builder for matchup-aware prompts, and structured JSON output via output_config with prompt caching and 10s timeout**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-21T21:01:38Z
- **Completed:** 2026-03-21T21:06:17Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- System prompt (9610 chars) enforces matchup-specific reasoning with enemy hero names and ability references in every recommendation
- ContextBuilder assembles hero data, matchup win rates, item catalog (~50 items), and rules output into compact user message
- LLMEngine uses Claude Sonnet structured output (GA output_config.format), prompt caching (cache_control ephemeral), and 10s hard timeout
- 7 unit tests verify structured output parsing, all error paths (timeout, connection, status), prompt caching config, and output_config format

## Task Commits

Each task was committed atomically:

1. **Task 1: Create system prompt and context builder** - `09a6379` (feat)
2. **Task 2: Create LLM engine with structured output, timeout, and prompt caching** - `21010da` (feat)

## Files Created/Modified
- `prismlab/backend/engine/prompts/__init__.py` - Empty package init for prompts module
- `prismlab/backend/engine/prompts/system_prompt.py` - 8K MMR coach system prompt with specificity constraints, game knowledge principles, output rules, and good/bad few-shot examples
- `prismlab/backend/engine/context_builder.py` - Assembles hero data, opponent matchup stats, rules output, item catalog, and popularity data into Claude user message
- `prismlab/backend/engine/llm.py` - AsyncAnthropic wrapper with structured JSON output, prompt caching, 10s timeout, and None-return fallback for all errors
- `prismlab/backend/tests/test_llm.py` - 7 tests covering structured output, validation, timeout, connection error, status error, caching config, and output format

## Decisions Made
- System prompt designed at 9610 chars (well above 2048 token cache minimum for Sonnet) with explicit specificity constraints: every reasoning must name enemy hero and reference ability
- Used output_config.format with json_schema (GA path) rather than beta.messages.parse() for structured output
- max_retries=0 to avoid consuming timeout budget on retries; single attempt within 10s window
- All LLMEngine failures return None; the orchestrator (Plan 03) treats None as fallback trigger

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - ANTHROPIC_API_KEY already configured in .env from Phase 1 setup.

## Next Phase Readiness
- System prompt, context builder, and LLM engine ready for hybrid orchestrator in Plan 03
- Plan 03 will wire rules engine + LLM engine together via POST /api/recommend endpoint
- LLMEngine returns None on failure, which Plan 03's orchestrator uses to trigger rules-only fallback

## Self-Check: PASSED

All 5 created files verified on disk. Both task commits (09a6379, 21010da) verified in git log.

---
*Phase: 03-recommendation-engine*
*Completed: 2026-03-21*

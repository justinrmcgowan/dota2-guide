---
phase: 13-screenshot-parsing
plan: 01
subsystem: api
tags: [claude-vision, screenshot-parsing, fuzzy-matching, fastapi, pydantic, nginx]

# Dependency graph
requires:
  - phase: 03-recommendation-engine
    provides: LLMEngine with AsyncAnthropic client, Pydantic schemas pattern
provides:
  - POST /api/parse-screenshot endpoint accepting base64 image data
  - Vision system prompt for Dota 2 scoreboard extraction
  - Fuzzy name matching (hero + item) against DB with confidence scoring
  - VisionResponse, ParsedHero, ParsedItem, ScreenshotParseRequest, ScreenshotParseResponse schemas
  - Nginx configured for 10MB image uploads
affects: [13-screenshot-parsing, 14-recommendation-quality-system-hardening]

# Tech tracking
tech-stack:
  added: []
  patterns: [base64 image content blocks for Claude Vision API, SequenceMatcher fuzzy matching with confidence resolution]

key-files:
  created:
    - prismlab/backend/engine/prompts/vision_prompt.py
    - prismlab/backend/engine/name_matcher.py
    - prismlab/backend/api/routes/screenshot.py
  modified:
    - prismlab/backend/engine/schemas.py
    - prismlab/backend/engine/llm.py
    - prismlab/backend/main.py
    - prismlab/frontend/nginx.conf

key-decisions:
  - "Base64 JSON body (not multipart) for screenshot upload -- no new dependencies, consistent with Anthropic API pattern"
  - "Temperature 0.1 for Vision extraction -- lower than recommendation engine (0.3) for deterministic structured output"
  - "SequenceMatcher with 0.7 threshold for fuzzy name matching -- stdlib, no new dependency"
  - "Confidence scoring combines Vision self-reported certainty with DB match ratio"

patterns-established:
  - "Vision API pattern: base64 image + text prompt in user content blocks with structured JSON output"
  - "Name matching pattern: exact case-insensitive first, SequenceMatcher fallback with ratio threshold"
  - "Confidence resolution: combine AI certainty + match quality into high/medium/low"

requirements-completed: [SCREEN-01, SCREEN-03, SCREEN-04]

# Metrics
duration: 3min
completed: 2026-03-26
---

# Phase 13 Plan 01: Backend Screenshot Parsing Pipeline Summary

**Claude Vision endpoint with DB-anchored prompt, fuzzy hero/item name matching, and nginx 10MB upload config**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-26T20:23:04Z
- **Completed:** 2026-03-26T20:26:28Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- POST /api/parse-screenshot endpoint wired end-to-end: base64 image in, ParsedHero[] out
- Vision prompt engineered with DB-anchored hero/item name lists to prevent hallucination
- Fuzzy name matching with confidence scoring (high/medium/low) based on Vision certainty + match ratio
- Nginx configured for 10MB uploads to support high-resolution scoreboard screenshots

## Task Commits

Each task was committed atomically:

1. **Task 1: Vision prompt, Pydantic schemas, LLMEngine.parse_screenshot(), and name matcher** - `e27a9a7` (feat)
2. **Task 2: Screenshot API route, main.py registration, and nginx body size config** - `754aca1` (feat)

## Files Created/Modified
- `prismlab/backend/engine/prompts/vision_prompt.py` - Vision system prompt with VISION_SYSTEM_PROMPT and build_vision_user_prompt()
- `prismlab/backend/engine/name_matcher.py` - Fuzzy matching with match_hero_name, match_item_name, resolve_confidence
- `prismlab/backend/engine/schemas.py` - Added VisionItem, VisionHero, VisionResponse, ParsedItem, ParsedHero, ScreenshotParseRequest, ScreenshotParseResponse
- `prismlab/backend/engine/llm.py` - Added parse_screenshot() method to LLMEngine with temp=0.1 and 30s timeout
- `prismlab/backend/api/routes/screenshot.py` - POST /api/parse-screenshot endpoint with Vision call + DB matching
- `prismlab/backend/main.py` - Registered screenshot_router with prefix=/api
- `prismlab/frontend/nginx.conf` - Added client_max_body_size 10m to /api/ location block

## Decisions Made
- Used base64 JSON body instead of multipart upload -- avoids python-multipart dependency, consistent with how Anthropic API accepts images
- Set Vision temperature to 0.1 (vs 0.3 for recommendations) for more deterministic structured extraction
- Used difflib.SequenceMatcher (stdlib) with 0.7 threshold for fuzzy matching -- no new dependencies
- Confidence resolution combines Vision self-reported certainty ("certain"/"likely"/"uncertain") with DB match ratio to produce "high"/"medium"/"low"
- Inject full valid hero/item name lists into Vision user prompt to anchor Claude and prevent name hallucination
- Singleton LLMEngine in screenshot route matches singleton pattern in recommend route

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Known Stubs

None - all data paths are fully wired (Vision API call, DB lookup, name matching, confidence scoring, structured response).

## Next Phase Readiness
- Backend screenshot parsing pipeline complete and ready for frontend consumption (Plan 02/03)
- POST /api/parse-screenshot returns structured ParsedHero[] with confidence levels
- Frontend can call endpoint with base64 image data and render confirmation UI from response

## Self-Check: PASSED

All 7 files verified present. Both task commits (e27a9a7, 754aca1) found in git history.

---
*Phase: 13-screenshot-parsing*
*Completed: 2026-03-26*

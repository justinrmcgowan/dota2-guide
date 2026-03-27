# Deferred Items — Phase 19

## Pre-existing Test Failures

### 1. TestSystemPromptAllyRules in test_context_builder.py

Tests expect `## Team Coordination`, `Aura and utility deduplication`, `Combo and setup awareness`, `Team role gap filling` in SYSTEM_PROMPT, but the prompt uses `## Allies` with different phrasing. These tests were written for a prompt version that was later compacted.

- **File:** prismlab/backend/tests/test_context_builder.py (lines 358-379)
- **Impact:** 4 tests fail
- **Fix:** Either update tests to match current prompt phrasing, or expand `## Allies` section back to the expected text

### 2. TestSystemPromptNeutralRules in test_context_builder.py

Tests expect `Rank by hero synergy`, `Note build-path interactions`, `Tier-based timing context` in SYSTEM_PROMPT, but the prompt uses compact phrasing. Pre-existing since the prompt was compacted.

- **File:** prismlab/backend/tests/test_context_builder.py (lines ~440-460)
- **Impact:** 3 tests fail
- **Fix:** Either update tests to match current compact phrasing, or restore expanded text

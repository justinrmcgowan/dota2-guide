---
phase: 08-allied-synergy
verified: 2026-03-23T09:45:10Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 8: Allied Synergy Verification Report

**Phase Goal:** Recommendations account for what allies bring to the team — no duplicate auras, combo synergies exploited, role gaps filled with item choices
**Verified:** 2026-03-23T09:45:10Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | When allied heroes are present, Claude reasoning text explicitly references ally names and their abilities/items when explaining recommendations | VERIFIED | system_prompt.py Output Constraint rule 2 updated: "When allied hero synergy affects the recommendation, ALSO reference the ally hero by name and explain the team coordination benefit." Ally-aware GOOD example demonstrates this at line 187. |
| 2 | If an ally is likely to build a team aura item (Pipe, Vlads, Crimson Guard, Mekansm), the recommendation does not suggest the same item for the user's hero | VERIFIED | system_prompt.py `## Team Coordination` rule 1 "Aura and utility deduplication" lists Pipe of Insight, Vladmir's Offering, Crimson Guard, Mekansm/Guardian Greaves, Assault Cuirass, Drum of Endurance with explicit "do NOT recommend the same item" instruction. |
| 3 | When an ally has strong setup abilities (e.g., Enigma Black Hole, Magnus Reverse Polarity), recommendations prioritize follow-up items with reasoning that references the combo | VERIFIED | system_prompt.py `## Team Coordination` rule 2 "Combo and setup awareness" lists Enigma (Black Hole), Magnus (Reverse Polarity), Tidehunter (Ravage), Faceless Void (Chronosphere), Dark Seer (Vacuum + Wall) as triggers. The ally-aware GOOD example at line 196-212 demonstrates BKB reasoning referencing Enigma's Black Hole explicitly. |
| 4 | When the team lacks a key capability (stuns, saves, wave clear), recommendations suggest items that fill that gap with explicit reasoning about the team deficit | VERIFIED | system_prompt.py `## Team Coordination` rule 3 "Team role gap filling" lists specific gaps (stuns, save, wave clear, healing sustain) and corresponding items, with explicit instruction to explain the team deficit. |
| 5 | When allies are present in the request, the Claude user message contains an "## Allied Heroes" section listing each ally by name, role, and popular items | VERIFIED | context_builder.py `_build_ally_lines()` method at lines 196-225 fetches hero name and top 5 popular items via `get_hero_item_popularity()`. `build()` appends `f"## Allied Heroes\n{ally_lines}"` at line 92. TestBuildAllyLines (7 tests) and TestAllyIntegration (2 tests) all pass. |
| 6 | When no allies are present, the user message has no Allied Heroes section (backward compatible) | VERIFIED | `_build_ally_lines()` returns `""` immediately when `not allies` (line 203). `build()` only appends the section `if ally_lines:` (line 91). `test_build_without_allies_no_section` passes. |
| 7 | Ally item popularity is fetched using the existing get_hero_item_popularity function | VERIFIED | `_build_ally_lines()` calls `await get_hero_item_popularity(ally_id, db, self.opendota)` (line 212). Function imported from `data.matchup_service` at line 16. |
| 8 | The system prompt contains a Team Coordination section with rules for aura dedup, combo awareness, and gap filling | VERIFIED | `## Team Coordination` section at system_prompt.py line 75. TestSystemPromptAllyRules (4 tests) all pass, and spot-check `python -c` confirms presence. System prompt length: 13326 chars (above 10000 caching threshold). |
| 9 | Claude is instructed to reference ally hero names when ally synergy affects recommendations | VERIFIED | Output Constraint rule 2 at system_prompt.py line 112-114 and rule 9 at lines 131-134 both updated with explicit ally name reference instructions. |
| 10 | The system prompt includes at least one GOOD reasoning example showing ally-aware recommendation | VERIFIED | `## Example: GOOD Ally-Aware Reasoning (Emulate This)` at line 187-217 shows Juggernaut + Enigma + Crystal Maiden combo with full JSON output and reasoning. |

**Score:** 10/10 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `prismlab/backend/engine/context_builder.py` | `_build_ally_lines()` method and integration into `build()` | VERIFIED | Method exists at lines 196-225. `_extract_top_items()` helper at lines 227-261. Wired into `build()` at lines 61, 91-92. |
| `prismlab/backend/engine/prompts/system_prompt.py` | Team Coordination section in SYSTEM_PROMPT | VERIFIED | `## Team Coordination` section at lines 75-103. Ally-aware example at lines 187-217. Output Constraints updated at lines 112-114 and 131-134. |
| `prismlab/backend/tests/test_context_builder.py` | TestBuildAllyLines and TestAllyIntegration test classes | VERIFIED | `TestBuildAllyLines` (7 tests, lines 153-298), `TestAllyIntegration` (2 tests, lines 306-380), `TestSystemPromptAllyRules` (4 tests, lines 388-409). |
| `prismlab/backend/tests/conftest.py` | Enigma (id=33) and Magnus (id=97) in extra_heroes | VERIFIED | Enigma at lines 89-94, Magnus at lines 95-100. Both fully seeded with correct ids, names, attributes, and roles. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `context_builder.py` | `data.matchup_service.get_hero_item_popularity` | async call per ally hero_id in `_build_ally_lines()` | WIRED | Import at line 16, called at line 212 with `(ally_id, db, self.opendota)`. Return value drives popular item extraction. |
| `context_builder.py` | `engine.schemas.RecommendRequest.allies` | `request.allies` list iteration in `build()` | WIRED | `request.allies` passed to `_build_ally_lines()` at line 61. `RecommendRequest.allies` field confirmed in schemas.py line 18 as `list[int]`. |
| `system_prompt.py` | `context_builder.py` | System prompt references "Allied Heroes" section in user message | WIRED | `## Team Coordination` rule header reads "When allied heroes are listed in the 'Allied Heroes' section of the user message" (line 77). Both the section name and the instruction are present. |
| `system_prompt.py` | `engine/llm.py` | SYSTEM_PROMPT constant imported and sent to Claude API | WIRED | `from engine.prompts.system_prompt import SYSTEM_PROMPT` at llm.py line 19. Used in `system` parameter of `messages.create()` at llm.py lines 55-59 with `cache_control: ephemeral`. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `context_builder.py` `_build_ally_lines()` | `popularity` | `get_hero_item_popularity(ally_id, db, self.opendota)` — same function used for player hero popularity | Yes — fetches from OpenDota API via existing production path | FLOWING |
| `system_prompt.py` `SYSTEM_PROMPT` | Static constant | Hard-coded multi-line string, not dynamic | N/A — prompt text is intentionally static | FLOWING (expected) |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All context builder + ally tests pass | `python -m pytest tests/test_context_builder.py -v` | 26 passed in 0.21s | PASS |
| Full backend test suite — no regressions | `python -m pytest tests/ -v` | 82 passed in 2.89s | PASS |
| System prompt imports and contains all ally sections | `python -c "...assert checks..."` | Length: 13326 chars, ALL CHECKS PASSED | PASS |
| SYSTEM_PROMPT above 10000 char prompt caching threshold | Included in above | 13326 > 10000 | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| ALLY-01 | 08-01-PLAN.md | Allied heroes are passed to Claude context builder for recommendation reasoning | SATISFIED | `_build_ally_lines()` in context_builder.py fetches ally names and item popularity, inserting `## Allied Heroes` section into every build() call when allies present. 7 dedicated tests in TestBuildAllyLines pass. |
| ALLY-02 | 08-02-PLAN.md | Recommendations avoid duplicating team aura/utility items (Pipe, Vlads, Crimson, etc.) | SATISFIED | `## Team Coordination` rule 1 "Aura and utility deduplication" in system_prompt.py explicitly lists the aura items and instructs Claude not to recommend duplicates, with a named-ally example. |
| ALLY-03 | 08-02-PLAN.md | Recommendations factor in allied combo/setup potential (Enigma + follow-up items, Magnus + BKB priority) | SATISFIED | `## Team Coordination` rule 2 "Combo and setup awareness" in system_prompt.py lists Enigma, Magnus, and 3 other initiators by name with specific abilities. Ally-aware GOOD example demonstrates Enigma + BKB reasoning. |
| ALLY-04 | 08-02-PLAN.md | Recommendations identify and fill team role gaps (missing stuns, save, wave clear) via item priorities | SATISFIED | `## Team Coordination` rule 3 "Team role gap filling" in system_prompt.py maps gap types to specific item recommendations and requires explicit team deficit reasoning. |

All 4 requirements for Phase 8 are satisfied. No orphaned requirements found — REQUIREMENTS.md traceability table maps exactly ALLY-01 through ALLY-04 to Phase 8 and all are marked Complete.

---

### Anti-Patterns Found

No anti-patterns detected.

- No TODO/FIXME/placeholder comments in modified files
- No empty implementations (`return null`, `return {}`, `return []`) in production code paths
- No hardcoded empty data flowing to output — `_build_ally_lines()` returns `""` only for the zero-allies case (correct gating, not a stub)
- No `console.log`-only handlers
- The `if not allies: return ""` guard in `_build_ally_lines()` is correct backward-compatibility logic, not a stub — all other paths make real async DB and API calls

---

### Human Verification Required

The following cannot be verified by static analysis alone:

**1. End-to-end Claude API response quality with ally data**

Test: Send a POST to `/api/recommend` with a hero, lane opponents, and 2 allied heroes (e.g., hero_id=1 Anti-Mage, allies=[33, 3] Enigma + Crystal Maiden) against enemies with magic burst. Observe the returned `reasoning` fields.

Expected: The `overall_strategy` and at least one `reasoning` field should reference both an ally hero by name AND an enemy hero by name. If Enigma is an ally, BKB should be prioritized with reasoning mentioning Enigma's Black Hole.

Why human: Claude API responses are non-deterministic. The system prompt instructs the desired behavior but only a live call verifies Claude actually follows the ally coordination rules in practice.

**2. Aura deduplication in a real recommendation**

Test: Send a request where an ally (e.g., hero_id=97 Magnus) would typically build Assault Cuirass. Observe whether the player's recommendation avoids suggesting AC.

Expected: The recommendation should suggest a different armor-reduction item (e.g., Desolator) with reasoning mentioning that Magnus is likely to build AC.

Why human: The aura dedup behavior is prompt-instructed, not rule-enforced. Static analysis can only verify the instruction exists in the prompt, not that Claude acts on it correctly.

---

### Gaps Summary

No gaps found. Phase 8 goal is fully achieved.

All four requirements (ALLY-01 through ALLY-04) are satisfied:
- ALLY-01: Allied hero data flows from `RecommendRequest.allies` through `_build_ally_lines()` to the Claude user message with hero names and top 5 popular items from OpenDota data.
- ALLY-02: System prompt contains an explicit "Aura and utility deduplication" rule naming all major team aura items and instructing Claude to avoid recommending duplicates.
- ALLY-03: System prompt contains a "Combo and setup awareness" rule naming specific initiators (Enigma, Magnus, etc.) and a complete ally-aware GOOD reasoning example demonstrating BKB + Enigma Black Hole logic.
- ALLY-04: System prompt contains a "Team role gap filling" rule mapping team deficits to specific item solutions with required explicit reasoning.

The context builder (Plan 01) provides ally data to Claude, and the system prompt (Plan 02) instructs Claude how to use that data — both halves of the pipeline are substantive, wired, and tested. 82 backend tests pass with no regressions.

---

_Verified: 2026-03-23T09:45:10Z_
_Verifier: Claude (gsd-verifier)_

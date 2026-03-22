# Phase 8: Allied Synergy - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase wires allied hero data into the Claude recommendation pipeline so that item advice accounts for team composition — avoiding duplicate aura items, exploiting combo setups, and filling team capability gaps. No new UI components; all changes are backend (context builder, system prompt).

</domain>

<decisions>
## Implementation Decisions

### Ally Context Format
- Add a new `## Allied Heroes` section in the context builder's user message
- List each ally with hero name and role (e.g., "Enigma (Pos 3)")
- Include typical ally item builds derived from OpenDota item popularity data (same `get_hero_item_popularity` already used for player's hero)
- Do NOT explicitly list abilities — Claude knows hero abilities from training data

### System Prompt Updates
- Add a `## Team Coordination` section to the system prompt with 3 rules: aura dedup, combo awareness, gap filling
- Extend the "must name enemy hero" constraint to also require ally hero name references when ally synergy affects the recommendation
- Add one ally-aware GOOD reasoning example showing aura dedup or combo reasoning

### Aura Dedup Approach
- Prompt-only approach — no new deterministic rules. Claude reasons about team aura coordination holistically
- Convey "likely ally builds" to Claude by fetching OpenDota item popularity data for each allied hero
- When ally coordination is relevant, the overall_strategy field should mention it

### Claude's Discretion
- Exact wording of Team Coordination section rules
- How many ally items to show in the "typical builds" summary (suggested: top 3-5 most popular)
- Whether to include ally item popularity counts or just item names
- Prompt length management — keep total system prompt under prompt caching threshold

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `context_builder.py` — `ContextBuilder.build()` method, already has `_build_opponent_lines()` pattern to follow for allies
- `get_hero_item_popularity()` in `data/matchup_service.py` — fetches item popularity from OpenDota, already used for player's hero
- `system_prompt.py` — `SYSTEM_PROMPT` constant, 194 lines, 9610 chars
- `schemas.py` — `RecommendRequest.allies: list[int]` already exists (line 18)
- `test_context_builder.py` — newly added in Phase 7, pattern to extend for ally tests

### Established Patterns
- Context builder sections use markdown headers (`## Section Name`)
- Each section has a dedicated `_build_*` async method
- System prompt uses numbered principles and explicit GOOD/BAD examples
- Item popularity fetched via `get_hero_item_popularity(hero_id, db, opendota)` returning dict

### Integration Points
- `context_builder.py` — add `_build_ally_lines()` method, call it in `build()`, add ally section between "Your Hero" and "Lane Opponents"
- `system_prompt.py` — add Team Coordination section after Game Knowledge Principles
- `test_context_builder.py` — extend with ally context tests
- No frontend changes needed — AllyPicker already sends ally hero IDs in the request

</code_context>

<specifics>
## Specific Ideas

- Ally section should be compact — hero name + role + top 3 popular items, ~50 tokens per ally
- Follow the existing `_build_opponent_lines()` async pattern for the new `_build_ally_lines()` method
- System prompt Team Coordination rules should mirror the specificity of existing Output Constraints (concrete examples, not vague guidance)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

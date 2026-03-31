# Phase 36: Prompt Intelligence - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Claude's reasoning consistently matches the quality of an expert coach through few-shot exemplars, game-clock awareness, and graceful handling of edge cases. Three sub-features:

1. **Exemplar Few-Shot Prompting** — 15-20 curated gold-standard recommendations stored as JSON, archetype matcher selects 1-2 closest, injected into user message as few-shot examples
2. **Time-Aware Reasoning** — Game clock injected into context, rules hard-block timing-inappropriate items (no Midas after 20 min, BKB timing gates), context builder includes game time
3. **Edge Case Handling** — Unusual roles detected via HERO_ROLE_VIABLE and flagged to Claude, partial drafts (<10 heroes) get appropriate caveats, Turbo mode flag halves timing benchmarks

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key references:
- Design spec: `docs/superpowers/specs/2026-03-30-engine-hardening-design.md` (Pillar 3: sections 1B, 4D, 4B)
- System prompt: `prismlab/backend/engine/prompts/system_prompt.py`
- Context builder: `prismlab/backend/engine/context_builder.py`
- Rules engine: `prismlab/backend/engine/rules.py`
- Schemas: `prismlab/backend/engine/schemas.py`
- Hero playstyles: `prismlab/frontend/src/utils/heroPlaystyles.ts` (HERO_ROLE_VIABLE reference)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ContextBuilder._build_*_section()` pattern for adding new context sections
- `RulesEngine.evaluate()` with helper methods for ability/item queries
- `HERO_PLAYSTYLE_MAP` in frontend heroPlaystyles.ts — reference for role viability
- `RecommendRequest` schema with existing optional fields pattern

### Established Patterns
- System prompt is a single string constant in `system_prompt.py`
- Context builder methods are async, return strings, called from `build()`
- Rules return `RuleResult` objects, evaluated in `evaluate()` method
- Schema fields are optional with `| None` type annotations

### Integration Points
- `engine/prompts/exemplars/` — new directory for JSON exemplar files
- `engine/exemplar_matcher.py` — new module for archetype matching
- `schemas.py` — new `game_time_seconds` and `turbo` fields on RecommendRequest
- `context_builder.py` — game clock injection + exemplar injection
- `rules.py` — timing-gated rule blocks

</code_context>

<specifics>
## Specific Ideas

- Exemplar JSON format: `{"role": 1, "threat_profile": "burst", "matchup_type": "physical", "recommendation": {...}}`
- Archetype matcher: simple scoring based on role match + threat profile overlap
- Timing rules: Midas after 20min → never, BKB before 10min → only if 3+ disables, Rapier before 35min → only traditional carriers when losing
- Turbo mode: `turbo: bool` field on request, halve all timing thresholds

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

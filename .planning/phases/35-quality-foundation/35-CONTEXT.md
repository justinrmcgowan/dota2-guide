# Phase 35: Quality Foundation - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped per user preference)

<domain>
## Phase Boundary

Recommendations are grounded in what top players actually build, validated for logical consistency, and cover 50+ deterministic matchup scenarios. Three sub-features:

1. **Pro/High-MMR Build Baselines** — Fetch Divine/Immortal item win rates per hero from OpenDota, add "What top players build" section to Claude context, explain deviations from pro builds
2. **Response Validation Layer** — Post-parse sanity checks on Claude output (phase-cost ranges, cross-phase duplicates, missing counter items, empty phases), retry once on failure, log validation failure rates
3. **Expanded Rules Engine** — 30+ new deterministic rules covering item-vs-item counters, meta-aware team composition rules, and timing-aware item blocks

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key references:
- Design spec: `docs/superpowers/specs/2026-03-30-engine-hardening-design.md` (Pillar 1 sections 1A, 1C and Pillar 4 section 4A)
- Current rules engine: `prismlab/backend/engine/rules.py`
- Current context builder: `prismlab/backend/engine/context_builder.py`
- Current recommender: `prismlab/backend/engine/recommender.py`
- OpenDota client: `prismlab/backend/data/opendota_client.py`
- DataCache: `prismlab/backend/data/cache.py`
- Data pipeline: `prismlab/backend/data/pipeline.py`

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `DataCache` singleton with frozen dicts for zero-DB-query lookups — new baseline data should follow this pattern
- `RulesEngine.evaluate()` with ability-based helper methods — new rules extend this class
- `ContextBuilder.build()` with 12 data sections — new pro reference section added here
- `HybridRecommender._validate_item_ids()` — validation pipeline lives here, new validator integrates nearby
- `_deduplicate_across_phases()` already handles cross-phase dedup (Phase 34)

### Established Patterns
- Rules return `RuleResult` objects with item_id, item_name, reasoning, phase, priority, counter_target
- DataCache uses atomic reference swap for thread-safe updates
- Context builder sections are method-based (`_build_X_section()`)
- OpenDota client uses async httpx with rate limiting

### Integration Points
- `opendota_client.py` for new API endpoint methods (hero item popularity by bracket)
- `cache.py` for new cached data structures (hero item baselines)
- `pipeline.py` for refresh cycle integration
- `recommender.py` for validation layer insertion (after LLM parse, before enrichment)

</code_context>

<specifics>
## Specific Ideas

- OpenDota endpoint: `heroes/{id}/itemPopularity` with `?minMmr=5420` for Divine+ data
- Validation should retry once with error description appended to user message
- Rules should cover: Nullifier vs Aeon Disk/Eul's, Silver Edge vs passive heroes (BB/PA/Spectre), Spirit Vessel vs high-regen (Huskar/Alch/Morph), team-wide armor/magic resist when 3+ physical/magic cores

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 35-quality-foundation*
*Context gathered: 2026-03-30 via auto-generation (discuss skipped)*

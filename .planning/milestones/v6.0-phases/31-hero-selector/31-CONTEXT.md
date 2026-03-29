# Phase 31: Hero Selector - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Role/lane-filtered hero suggestions ranked by predicted win rate, ally synergy, and enemy counter-value. Integrates into existing draft input flow as an optional "Suggest Hero" step before the recommendation engine runs.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key context from Phase 30:
- WinPredictor class exists with predict() method returning win probability
- Synergy/counter matrices loaded in DataCache (matrices.json with hero_id_to_index, synergy[], counter[])
- XGBoost models per MMR bracket available via DataCache
- Phase 31 consumes the matrices computed by Phase 30's training pipeline

</decisions>

<code_context>
## Existing Code Insights

Codebase context will be gathered during plan-phase research.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — discuss phase skipped. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discuss phase skipped.

</deferred>

# Phase 38: Adaptiveness & Accuracy - Context

**Gathered:** 2026-03-31
**Status:** Ready for planning
**Mode:** Auto-generated (discuss skipped via workflow.skip_discuss)

<domain>
## Phase Boundary

Mid-game re-evaluations are faster and cheaper via diff-based context, and post-match tracking proves recommendation value.

Success Criteria:
1. Re-evaluations send only what changed since last eval (new enemy items, deaths, gold swings, phase transitions)
2. Diff-based context reduces token usage by 40%+ for mid-game re-evals
3. Post-match accuracy score computed: % of core recommendations purchased
4. Match history dashboard shows "follow rate" and "follow win rate vs deviate win rate"
5. Items frequently recommended but rarely purchased are flagged for prompt review

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — discuss phase was skipped per user setting. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

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

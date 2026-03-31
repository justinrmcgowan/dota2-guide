---
status: human_needed
phase: 38-adaptiveness-accuracy
verified: 2026-03-31
score: 8/8
human_verification_count: 2
---

# Phase 38: Adaptiveness & Accuracy — Verification

## Must-Haves

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Re-evaluations send only changed fields | ✓ | build_diff() at context_builder.py:267 omits static sections, emits "Re-Evaluation Context" header |
| 2 | Diff-based context reduces token usage by 40%+ | ✓ | test_diff_at_least_40_percent_shorter passes; ~1450 static tokens omitted |
| 3 | EvalSnapshot captures game state for diff detection | ✓ | Frozen dataclass at context_builder.py:42 with from_request() classmethod |
| 4 | Diff routing wired in deep_path and recommend_stream | ✓ | _deep_path (line 619) and recommend_stream (line 337) both check for snapshots |
| 5 | Post-match accuracy score (follow_rate) | ✓ | follow_win_rate and deviate_win_rate computed from match_log with threshold buckets |
| 6 | Match history shows follow/deviate win rates | ✓ | Accuracy Insights section in MatchHistory.tsx:458 with stat cards |
| 7 | Flagged items (recommended but rarely purchased) | ✓ | FlaggedItemResponse schema + SQL query: core/situational, 5+ recs, <30% purchase rate |
| 8 | input_tokens tracking on RecommendResponse | ✓ | schemas.py:235 field present, populated from llm.last_usage |

## Requirement Traceability

| Req ID | Plan | Status |
|--------|------|--------|
| ADAPT-01 | 38-01 | ✓ Verified |
| ADAPT-02 | 38-01 | ✓ Verified |
| ADAPT-03 | 38-02 | ✓ Verified |
| ADAPT-04 | 38-02 | ✓ Verified |
| ADAPT-05 | 38-02 | ✓ Verified |

## Human Verification Items

1. **Visual rendering** — Verify Accuracy Insights section renders correctly with real match data (follow/deviate win rates, flagged items table)
2. **Token reduction** — Observe actual input_tokens reduction in production Claude API calls during mid-game re-evaluations

## Notes

- 18 diff context tests + 46 total backend tests passing
- Snapshots cleared on data refresh alongside HierarchicalCache
- Flagged items use Tactical Relic design system tokens

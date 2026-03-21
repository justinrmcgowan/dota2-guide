---
phase: 3
slug: recommendation-engine
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (backend) |
| **Config file** | prismlab/backend/pytest.ini or pyproject.toml |
| **Quick run command** | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd prismlab/backend && python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick pytest
- **After every plan wave:** Run full pytest suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ENGN-01 | unit | `python -m pytest tests/test_rules.py -v` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | ENGN-02,05 | unit | `python -m pytest tests/test_llm.py -v` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 3 | ENGN-03,04 | integration | `python -m pytest tests/test_recommender.py -v` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 3 | ENGN-06 | unit | `python -m pytest tests/test_matchup_pipeline.py -v` | ❌ W0 | ⬜ pending |

---

## Wave 0 Requirements

- [ ] `tests/test_rules.py` — rules engine behavioral tests
- [ ] `tests/test_llm.py` — Claude API integration tests (with mocked responses)
- [ ] `tests/test_recommender.py` — hybrid orchestrator integration tests
- [ ] `tests/test_matchup_pipeline.py` — matchup data pipeline tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Claude reasoning references actual hero abilities by name | ENGN-02 | LLM output quality | Send recommend request, verify reasoning text |
| Fallback notice is visible in response when API fails | ENGN-04 | Response structure | Kill API key, send request, check fallback flag |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity
- [ ] Wave 0 covers all MISSING references
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

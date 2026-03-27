---
phase: 19
slug: data-foundation-prompt-architecture
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 19 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend) |
| **Config file** | prismlab/backend/pytest.ini |
| **Quick run command** | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd prismlab/backend && python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd prismlab/backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd prismlab/backend && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 19-01-01 | 01 | 1 | DATA-01 | unit | `pytest tests/test_cache.py -k ability` | ❌ W0 | ⬜ pending |
| 19-01-02 | 01 | 1 | DATA-02 | unit | `pytest tests/test_cache.py -k hero_ability` | ❌ W0 | ⬜ pending |
| 19-02-01 | 02 | 1 | DATA-03 | unit | `pytest tests/test_matchup_service.py -k timing` | ❌ W0 | ⬜ pending |
| 19-03-01 | 03 | 2 | DATA-04 | unit | `pytest tests/test_context_builder.py -k system_prompt` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_cache.py` — extend with ability data and timing data cache tests
- [ ] `tests/test_matchup_service.py` — extend with timing benchmark stale-while-revalidate tests

*Existing infrastructure covers test framework and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| System prompt token count < 5000 | DATA-04 | Token counting requires tokenizer | Copy system prompt text, count tokens via Anthropic tokenizer or estimate by chars/4 |
| Three-cache coherence after refresh | DATA-01, DATA-02 | Integration across cache layers | Trigger refresh pipeline, verify DataCache has ability data, RulesEngine re-initialized, ResponseCache cleared |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

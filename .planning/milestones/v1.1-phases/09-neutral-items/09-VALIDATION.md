---
phase: 09
slug: neutral-items
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-23
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (backend), vitest 3.x (frontend) |
| **Config file** | `prismlab/backend/pyproject.toml`, `prismlab/frontend/vitest.config.ts` |
| **Quick run command** | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd prismlab/backend && python -m pytest tests/ -v && cd ../../prismlab/frontend && npx vitest run` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd prismlab/backend && python -m pytest tests/ -x -q`
- **After every plan wave:** Run full suite (backend + frontend)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | NEUT-01 | unit | `pytest tests/test_matchup_service.py -k neutral` | No - W0 | pending |
| 09-01-02 | 01 | 1 | NEUT-02, NEUT-03 | unit | `pytest tests/test_context_builder.py -k neutral` | No - W0 | pending |
| 09-02-01 | 02 | 2 | NEUT-02 | unit | `npx vitest run` | No - W0 | pending |
| 09-02-02 | 02 | 2 | NEUT-02 | manual | Browser check | N/A | pending |

---

## Wave 0 Requirements

- [ ] `tests/test_context_builder.py::TestNeutralCatalog` — neutral catalog builder tests
- [ ] `tests/test_context_builder.py::TestSystemPromptNeutralRules` — prompt smoke tests
- [ ] `tests/test_matchup_service.py::test_get_neutral_items_by_tier` — query test
- [ ] `tests/test_recommender.py::test_neutral_items_passthrough` — pipeline test
- [ ] `tests/conftest.py` — add neutral item fixtures (tier field, is_neutral=True)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Neutral section renders below timeline in browser | NEUT-02 | Visual layout verification | Load app, get recommendation with hero, verify "Best Neutral Items" section appears below phase cards |
| Claude reasoning references neutral item build-path impacts | NEUT-03 | LLM output quality | Check that at least one neutral item reasoning mentions a build-path change (e.g., "skip X if you get Y") |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-03-23

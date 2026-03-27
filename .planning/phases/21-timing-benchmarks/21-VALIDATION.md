---
phase: 21
slug: timing-benchmarks
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 21 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (backend), vitest (frontend) |
| **Config file** | prismlab/backend/pytest.ini, prismlab/frontend/vitest.config.ts |
| **Quick run command** | `cd prismlab/backend && python -m pytest tests/test_rules.py tests/test_context_builder.py -x -q` |
| **Full suite command** | `cd prismlab/backend && python -m pytest tests/ -x -q && cd ../../prismlab/frontend && npx vitest run --reporter=verbose` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick command for the modified layer (backend or frontend)
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 21-01-01 | 01 | 1 | TIME-01 | unit | `pytest tests/test_timing.py -x -q` | ❌ W0 | ⬜ pending |
| 21-01-02 | 01 | 1 | TIME-02 | unit | `pytest tests/test_timing.py -k "urgency"` | ❌ W0 | ⬜ pending |
| 21-01-03 | 01 | 1 | TIME-03 | unit | `pytest tests/test_context_builder.py -k "timing"` | ❌ W0 | ⬜ pending |
| 21-02-01 | 02 | 2 | TIME-01 | component | `npx vitest run src/components/timeline/TimingBar.test.tsx` | ❌ W0 | ⬜ pending |
| 21-02-02 | 02 | 2 | TIME-02 | component | `npx vitest run src/components/timeline/ItemCard.test.tsx` | ❌ W0 | ⬜ pending |
| 21-03-01 | 03 | 3 | TIME-04 | component | `npx vitest run src/components/timeline/ItemCard.test.tsx -t "GSI"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_timing.py` — stubs for zone classification, urgency detection, timing enrichment
- [ ] `tests/test_context_builder.py` — stubs for _build_timing_section
- [ ] `src/components/timeline/TimingBar.test.tsx` — stubs for timing bar rendering
- [ ] `src/components/timeline/ItemCard.test.tsx` — stubs for timing integration

*Existing test infrastructure covers framework and base fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual appearance of timing bar zones | TIME-01 | CSS rendering verification | Inspect ItemCard in browser, verify green/yellow/red zones render with correct proportions |
| Pulsing urgency border animation | TIME-02 | CSS animation verification | Inspect timing-critical item, verify crimson pulse is visible and not distracting |
| Claude references timing in reasoning | TIME-03 | Requires Claude API call | Send recommendation request for hero with timing data, verify reasoning mentions specific timing benchmarks |
| GSI live comparison updates | TIME-04 | Requires live GSI connection | Connect to Dota 2 client, verify "you are here" marker moves with game clock |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
phase: 20
slug: counter-item-intelligence
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-27
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | prismlab/backend/pytest.ini |
| **Quick run command** | `cd prismlab/backend && python -m pytest tests/test_rules.py tests/test_cache.py -x -q` |
| **Full suite command** | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd prismlab/backend && python -m pytest tests/test_rules.py tests/test_cache.py -x -q`
- **After every plan wave:** Run `cd prismlab/backend && python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 1 | CNTR-01 | unit | `pytest tests/test_rules.py -k "ability_property"` | ❌ W0 | ⬜ pending |
| 20-01-02 | 01 | 1 | CNTR-01 | unit | `pytest tests/test_rules.py -k "fallback"` | ❌ W0 | ⬜ pending |
| 20-02-01 | 02 | 1 | CNTR-02 | unit | `pytest tests/test_rules.py -k "channeled or linken or dispel or escape"` | ❌ W0 | ⬜ pending |
| 20-02-02 | 02 | 1 | CNTR-03 | unit | `pytest tests/test_rules.py -k "counter_target"` | ❌ W0 | ⬜ pending |
| 20-03-01 | 03 | 2 | CNTR-03 | unit | `pytest tests/test_rules.py -k "ability_context"` | ❌ W0 | ⬜ pending |
| 20-03-02 | 03 | 2 | CNTR-04 | unit | `pytest tests/test_rules.py -k "threat_escalation"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_rules.py` — test stubs for ability-driven rules (CNTR-01, CNTR-02)
- [ ] `tests/conftest.py` — expanded fixtures with AbilityCached data for test heroes
- [ ] Hero ability fixtures for: Witch Doctor, Enigma, Puck, Storm Spirit, Slark, PA, Bristleback, Huskar, Alchemist

*Existing test infrastructure covers framework and base fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Claude reasoning names specific abilities | CNTR-03 | Requires Claude API call with real prompt | Send test recommendation request, verify reasoning string contains ability names |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

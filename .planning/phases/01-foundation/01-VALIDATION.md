---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (frontend), pytest 8.x (backend) |
| **Config file** | vitest.config.ts, pytest.ini |
| **Quick run command** | `cd prismlab/frontend && npx vitest run --reporter=verbose` / `cd prismlab/backend && python -m pytest -x` |
| **Full suite command** | `cd prismlab/frontend && npx vitest run` && `cd prismlab/backend && python -m pytest` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command for the affected layer
- **After every plan wave:** Run full suite command for both layers
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INFR-01 | integration | `docker compose up -d && curl localhost:8420/health` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | INFR-03 | unit | `cd prismlab/backend && python -m pytest tests/test_config.py` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | DISP-06 | manual | Visual check: dark theme, cyan accent, favicon | N/A | ⬜ pending |
| 01-02-02 | 02 | 1 | DRFT-01 | unit | `cd prismlab/frontend && npx vitest run src/components/draft/HeroPicker.test.tsx` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | DRFT-01 | integration | `curl localhost:8420/api/heroes \| python3 -c "import sys,json; d=json.load(sys.stdin); assert len(d)>100"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `prismlab/backend/tests/conftest.py` — shared fixtures (test DB, test client)
- [ ] `prismlab/backend/tests/test_config.py` — env var loading tests
- [ ] `prismlab/frontend/src/components/draft/HeroPicker.test.tsx` — hero picker component tests
- [ ] pytest + httpx install in backend requirements
- [ ] vitest install in frontend dev dependencies

*These are created as part of the scaffolding plans.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dark theme renders correctly | DISP-06 | Visual appearance cannot be automated | Open app in browser, verify #0f1419 background, cyan accent, Inter font |
| Favicon visible in browser tab | DISP-06 | Browser tab rendering | Open app, check browser tab for prism icon |
| Hero portraits load from CDN | DRFT-01 | External CDN dependency | Search for "Anti-Mage", verify portrait loads |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

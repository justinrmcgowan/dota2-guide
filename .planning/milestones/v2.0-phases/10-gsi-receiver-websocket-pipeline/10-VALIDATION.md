---
phase: 10
slug: gsi-receiver-websocket-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-25
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework (backend)** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Framework (frontend)** | vitest 4.1.0 + jsdom + @testing-library/react |
| **Config file (backend)** | pytest.ini or pyproject.toml (uses default discovery) |
| **Config file (frontend)** | `prismlab/frontend/vitest.config.ts` |
| **Quick run command (backend)** | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| **Quick run command (frontend)** | `cd prismlab/frontend && npx vitest run` |
| **Full suite command** | `cd prismlab/backend && python -m pytest tests/ -v && cd ../frontend && npx vitest run` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd prismlab/backend && python -m pytest tests/test_gsi.py tests/test_ws.py -x -q`
- **After every plan wave:** Run full suite (backend + frontend)
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | GSI-01 | unit | `python -m pytest tests/test_gsi.py -x` | ❌ W0 | ⬜ pending |
| 10-01-02 | 01 | 1 | GSI-01 | unit | `python -m pytest tests/test_gsi.py::test_auth_token -x` | ❌ W0 | ⬜ pending |
| 10-01-03 | 01 | 1 | GSI-01 | unit | `python -m pytest tests/test_gsi.py::test_parse_fields -x` | ❌ W0 | ⬜ pending |
| 10-01-04 | 01 | 1 | INFRA-02 | unit | `python -m pytest tests/test_gsi.py::test_config_generation -x` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 1 | WS-01 | integration | `python -m pytest tests/test_ws.py -x` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 1 | WS-01 | unit | `python -m pytest tests/test_ws.py::test_throttle -x` | ❌ W0 | ⬜ pending |
| 10-02-03 | 02 | 1 | WS-01 | unit | `python -m pytest tests/test_ws.py::test_change_detection -x` | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 2 | INFRA-01 | manual | Manual: docker compose up + curl | N/A | ⬜ pending |
| 10-04-01 | 04 | 2 | Frontend | unit | `npx vitest run src/hooks/useWebSocket.test.ts` | ❌ W0 | ⬜ pending |
| 10-04-02 | 04 | 2 | Frontend | unit | `npx vitest run src/stores/gsiStore.test.ts` | ❌ W0 | ⬜ pending |
| 10-04-03 | 04 | 2 | Frontend | unit | `npx vitest run src/components/settings/SettingsPanel.test.tsx` | ❌ W0 | ⬜ pending |
| 10-04-04 | 04 | 2 | Frontend | unit | `npx vitest run src/components/layout/GsiStatusIndicator.test.tsx` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `prismlab/backend/tests/test_gsi.py` — stubs for GSI-01, INFRA-02 (receiver, parser, config generator)
- [ ] `prismlab/backend/tests/test_ws.py` — stubs for WS-01 (WebSocket connection, throttle, change detection)
- [ ] `prismlab/frontend/src/hooks/useWebSocket.test.ts` — stubs for WebSocket hook behavior
- [ ] `prismlab/frontend/src/stores/gsiStore.test.ts` — stubs for GSI store state management
- [ ] `prismlab/frontend/src/components/settings/SettingsPanel.test.tsx` — stubs for settings panel UI
- [ ] `prismlab/frontend/src/components/layout/GsiStatusIndicator.test.tsx` — stubs for status indicator

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Nginx routes /gsi and /ws correctly | INFRA-01 | Requires running Docker containers with Nginx | 1. `docker compose up` 2. `curl -X POST http://localhost:8421/gsi -d '{}'` 3. Verify 200 response 4. Open ws://localhost:8421/ws in browser devtools |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

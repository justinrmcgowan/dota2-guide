---
phase: 11
slug: live-game-dashboard
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-26
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest 3.x (frontend) |
| **Config file** | prismlab/frontend/vitest.config.ts |
| **Quick run command** | `cd prismlab/frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd prismlab/frontend && npx vitest run` |
| **Estimated runtime** | ~8 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd prismlab/frontend && npx vitest run`
- **After every plan wave:** Run `cd prismlab/frontend && npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 0 | GSI-02 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | GSI-02, GSI-03 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | GSI-04 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| 11-02-02 | 02 | 1 | WS-03, WS-04 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `prismlab/frontend/src/hooks/useGsiSync.test.ts` — stubs for GSI-02, GSI-03, GSI-04
- [ ] `prismlab/frontend/src/components/game/LiveStatsBar.test.tsx` — stubs for WS-04
- [ ] `prismlab/frontend/src/components/game/GameClock.test.tsx` — stubs for WS-03

*Existing vitest infrastructure covers framework requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Gold counter animation | GSI-03 | Visual animation timing | Open app, send GSI data, verify smooth counting animation on gold changes |
| Color pulse on death/gold swing | GSI-03 | Visual feedback | Send GSI payload with death increment, verify red pulse |
| Neutral tier highlighting | WS-03 | Visual tier indicator | Send GSI data at different game clock values, verify tier highlights |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

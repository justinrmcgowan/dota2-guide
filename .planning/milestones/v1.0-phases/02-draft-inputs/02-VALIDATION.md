---
phase: 2
slug: draft-inputs
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (already installed from Phase 1) |
| **Config file** | prismlab/frontend/vitest.config.ts |
| **Quick run command** | `cd prismlab/frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd prismlab/frontend && npx vitest run` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick vitest for affected files
- **After every plan wave:** Run full vitest suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | DRFT-02,03 | unit | `npx vitest run src/stores/gameStore.test.ts` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | DRFT-04,05 | unit | `npx vitest run src/components/draft/RoleSelector.test.tsx` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | DRFT-06,07 | unit | `npx tsc --noEmit` | ✅ | ⬜ pending |
| 02-02-02 | 02 | 1 | ALL | integration | `npm run build` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/stores/gameStore.test.ts` — store extension tests (add/remove allies, opponents, role changes)
- [ ] `src/components/draft/RoleSelector.test.tsx` — role selection + playstyle reveal tests

*These should be created as part of plan tasks.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Compact hero portraits display correctly | DRFT-02,03 | Visual rendering | Verify 32px circular portraits with attribute dots |
| Playstyle animates in after role selection | DRFT-05 | CSS animation | Select a role, verify smooth reveal |
| Radiant teal / Dire red visual distinction | DRFT-06 | Color verification | Toggle side, verify color changes |
| CTA button enables when hero+role selected | ALL | Interactive state | Fill minimum inputs, verify button lights up |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

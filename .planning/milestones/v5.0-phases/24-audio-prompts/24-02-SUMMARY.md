---
phase: 24-audio-prompts
plan: "02"
subsystem: frontend-hooks
tags: [audio, hooks, zustand, speech, gsi]
dependency_graph:
  requires:
    - 24-01 (audioStore, audioUtils, SettingsPanel audio section)
  provides:
    - useAudio hook subscribed to refreshStore and recommendationStore
    - AudioContext autoplay unlock on first user click
  affects:
    - prismlab/frontend/src/App.tsx (hook registration)
tech_stack:
  added: []
  patterns:
    - Zustand store.subscribe() outside React render cycle
    - getState() inside subscribe callbacks to avoid stale closures
    - prevDataRef object ref (not useRef) inside useEffect for double-fire guard
    - AudioContext unlock pattern via document click listener
key_files:
  created:
    - prismlab/frontend/src/hooks/useAudio.ts
  modified:
    - prismlab/frontend/src/App.tsx
decisions:
  - useAudioStore.getState() used inside Zustand subscribe callbacks — never call React hooks inside non-hook callbacks
  - prevDataRef declared inside useEffect (plain object) not useRef — Zustand subscribe is outside React lifecycle, useRef would be stale
  - subscribe count is 2 live subscriptions (refreshStore + recommendationStore); AudioContext uses addEventListener not subscribe
key_decisions:
  - useAudioStore.getState() inside subscribe callbacks avoids stale closure issue that would occur with useAudioStore() (React hook)
  - prevDataRef plain object inside useEffect closure avoids stale ref problem since subscribe runs outside React lifecycle
metrics:
  duration: "~3 min"
  completed: "2026-03-29T10:54:46Z"
  tasks: 2
  files: 2
---

# Phase 24 Plan 02: useAudio Hook Integration Summary

useAudio hook wiring GSI toast speech and recommendation callouts via Zustand store subscriptions with AudioContext autoplay compliance.

## What Was Built

Created `useAudio.ts` — a self-contained App-level hook with three `useEffect` blocks:

1. **AudioContext unlock** — listens for the first `document.click` to create/resume AudioContext, satisfying browser autoplay policy.

2. **Toast subscription** — `useRefreshStore.subscribe()` fires whenever `lastToast` changes; if audio is enabled, speaks the sanitized message immediately.

3. **Recommendation subscription** — `useRecommendationStore.subscribe()` fires on any store change; when `state.data` is a new reference (not the same object), not loading, speaks "Consider buying [Item Name]" for the top item in `phases[0].items[0]`.

Registered `useAudio()` in `App.tsx` immediately after `useLiveDraft(heroes)`.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | useAudio hook | c0d1674 | prismlab/frontend/src/hooks/useAudio.ts (created) |
| 2 | Register useAudio in App.tsx | 375adef | prismlab/frontend/src/App.tsx (modified) |

## Verification

- `npx tsc --noEmit` exits 0 — full project compiles cleanly
- `grep "useAudio" App.tsx` — import and call both present
- `grep -c "subscribe" useAudio.ts` — returns 3 (2 live + 1 in comment)
- `grep "prismlab-audio" audioStore.ts` — persist key confirmed

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — hook is fully wired to live store subscriptions.

## Self-Check: PASSED

- `prismlab/frontend/src/hooks/useAudio.ts` — FOUND
- `prismlab/frontend/src/App.tsx` — FOUND (modified)
- commit c0d1674 — FOUND
- commit 375adef — FOUND

---
phase: 24-audio-prompts
plan: 01
subsystem: ui
tags: [zustand, tts, speech-synthesis, settings, audio]

# Dependency graph
requires: []
provides:
  - useAudioStore Zustand persist store (enabled=true, volume=0.7, key prismlab-audio)
  - speak() utility with Chrome 15s keepalive, cancel-before-speak, rate=1.1
  - sanitizeForSpeech() strips visual-only notation for natural TTS output
  - humanizeItemName() converts snake_case item keys to Title Case
  - Audio Coaching section in SettingsPanel with toggle and conditional volume slider
affects: [24-02, any future audio coaching callout integration]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Zustand persist store for boolean+number settings (simple primitives, no custom storage adapter needed)
    - Chrome SpeechSynthesis keepalive: setInterval pause/resume every 10s in onstart, cleared on onend/onerror
    - Conditional volume slider: only rendered when audioEnabled is true (space-efficient settings UI)

key-files:
  created:
    - prismlab/frontend/src/stores/audioStore.ts
    - prismlab/frontend/src/utils/audioUtils.ts
  modified:
    - prismlab/frontend/src/components/settings/SettingsPanel.tsx

key-decisions:
  - "useAudioStore uses standard Zustand persist with name/version only — no custom storage adapter needed since only primitive types (bool, number)"
  - "speak() does NOT set utterance.voice to avoid getVoices() async race condition on Chrome"
  - "Volume slider uses accent-secondary (gold #C5A02A per DESIGN.md), toggle pill has no rounded-full per --radius-*: 0px design token"
  - "Volume slider hidden when audio disabled — clean UI with no redundant controls"

patterns-established:
  - "audioUtils functions are pure/stateless; callers read audioStore and pass volume to speak()"
  - "SpeechSynthesis keepalive: local let keepaliveTimer in speak() closure — no module-level state"

requirements-completed: [AUDIO-01, AUDIO-02, AUDIO-05]

# Metrics
duration: 2min
completed: 2026-03-29
---

# Phase 24 Plan 01: Audio Store and Settings Summary

**Zustand persist audio store + speak() TTS utility with Chrome keepalive + Audio Coaching toggle and volume slider in SettingsPanel**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-29T10:48:29Z
- **Completed:** 2026-03-29T10:50:30Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- `useAudioStore` Zustand persist store (enabled=true, volume=0.7) persists audio preferences across browser sessions via localStorage key `prismlab-audio`
- `speak()` wraps Web Speech API with Chrome 15-second keepalive (pause/resume interval), cancel-before-speak, rate=1.1 for coach urgency, silent degradation when SpeechSynthesis unavailable
- `sanitizeForSpeech()` strips dash-dash separators, clock notation, and converts gold shorthand to natural language before TTS
- `humanizeItemName()` converts snake_case item names to Title Case for natural speech output
- SettingsPanel now has "Audio Coaching" section: toggle with active left-border indicator + pill, volume slider (only visible when enabled) showing current percentage

## Task Commits

Each task was committed atomically:

1. **Task 1: audioStore and speak utility** - `a580723` (feat)
2. **Task 2: Audio Coaching section in SettingsPanel** - `ba95dcf` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `prismlab/frontend/src/stores/audioStore.ts` - Zustand persist store: enabled, volume, setEnabled, setVolume
- `prismlab/frontend/src/utils/audioUtils.ts` - speak(), sanitizeForSpeech(), humanizeItemName()
- `prismlab/frontend/src/components/settings/SettingsPanel.tsx` - Added Audio Coaching section with toggle + volume slider

## Decisions Made
- Standard Zustand persist (no custom storage adapter) because audioStore only holds primitive types (bool, number)
- `utterance.voice` intentionally not set — avoids `getVoices()` async race condition
- Toggle pill uses square corners (no `rounded-full`) per `--radius-*: 0px` design token
- Volume slider hidden when audio disabled to keep settings UI clean

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Audio foundation complete: store + utility ready for consumption by Plan 24-02 (audio event wiring)
- `speak(text, volume)` API: callers read `useAudioStore` for volume, check `enabled` before calling
- All TypeScript compiles cleanly (tsc --noEmit exits 0)

---
*Phase: 24-audio-prompts*
*Completed: 2026-03-29*

## Self-Check: PASSED

- FOUND: prismlab/frontend/src/stores/audioStore.ts
- FOUND: prismlab/frontend/src/utils/audioUtils.ts
- FOUND: prismlab/frontend/src/components/settings/SettingsPanel.tsx
- FOUND: .planning/phases/24-audio-prompts/24-01-SUMMARY.md
- FOUND commit: a580723 (feat(24-01): add audioStore and speak utility)
- FOUND commit: ba95dcf (feat(24-01): add Audio Coaching section to SettingsPanel)

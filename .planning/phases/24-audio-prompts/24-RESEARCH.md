# Phase 24: Audio Prompts & Volume Control - Research

**Researched:** 2026-03-29
**Domain:** Browser Web Audio / Speech Synthesis + React state management
**Confidence:** HIGH

## Summary

Phase 24 adds a TTS / audio cue system to Prismlab that speaks item timing alerts, purchase reminders, and coaching callouts triggered by existing GSI events. The app already has a rich event pipeline: `detectTriggers()` emits `TriggerEvent` objects (phase transitions, deaths, gold swings, etc.), `refreshStore` holds toast state, and `useGameIntelligence` fires all of these. Audio is a new consumer of that same event bus — it does not need to produce new events, only react to existing ones.

Two browser APIs are available: the **Web Speech API** (`SpeechSynthesis`) and the **Web Audio API** (`AudioContext`). For this phase, `SpeechSynthesis` is the primary mechanism because its output is a natural-language spoken sentence rather than a sound file — matching the "coaching callout" goal with zero asset management. The Web Audio API handles pure-tone notification beeps as an optional supplement, but is secondary to TTS.

Volume is a single `0–1` float persisted to `localStorage` via Zustand `persist` (same pattern as `gameStore` and `recommendationStore`). An audio-enable toggle (on/off) sits alongside volume in the same store. The UI surface lives in the existing `SettingsPanel` as a new "Audio" section — consistent with how Engine mode and Steam ID are already managed there.

**Primary recommendation:** Use `window.speechSynthesis` directly (no third-party library needed). Wrap it in a custom `useAudio` hook that subscribes to `refreshStore` and `recommendationStore` for trigger text, with a `audioStore` (Zustand + persist) holding enabled/volume settings. The Chrome 15-second timeout bug requires the pause/resume keepalive workaround for utterances longer than ~10 words.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None — discuss phase was skipped. All implementation choices are at Claude's discretion.

### Claude's Discretion
All implementation choices: API choice (SpeechSynthesis vs Web Audio), trigger mapping, volume control UI, store design, and utterance scripting.

### Deferred Ideas (OUT OF SCOPE)
None specified.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUDIO-01 | Audio is enabled/disabled via a toggle in Settings | audioStore.enabled flag + SettingsPanel section |
| AUDIO-02 | Volume is configurable 0–1, persists across sessions | audioStore.volume + Zustand persist middleware |
| AUDIO-03 | TTS speaks item timing alerts triggered by GSI events | useAudio subscribes to refreshStore.lastToast |
| AUDIO-04 | TTS speaks coaching callouts when recommendations arrive | useAudio subscribes to recommendationStore.data |
| AUDIO-05 | Audio respects browser autoplay policy | AudioContext unlocked on first user click |

*Note: IDs are assigned here since REQUIREMENTS.md has no formal AUDIO-XX block yet. Planner should formalize these or fold them into the REQUIREMENTS.md.*
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

- **Frontend stack:** React 18 + Vite + TypeScript + Tailwind CSS + Zustand — no new frameworks
- **Dark theme:** spectral cyan (#00d4ff)... actually the current design uses Crimson/Gold palette (DESIGN.md migration). Use `text-secondary` (gold), `text-primary` (crimson), `text-on-surface-variant` for muted text
- **No rounded corners** (all `--radius-*: 0px` in design tokens)
- **Desktop-first:** Don't optimize for mobile but don't break it
- **Zustand for state:** New audio settings store follows the same `persist` pattern as `gameStore` and `recommendationStore`
- **Functional components + hooks only:** No class components
- **TypeScript strict mode throughout**
- **Settings UI pattern:** New sections added to existing `SettingsPanel.tsx` — look at Steam ID and Engine Mode sections as the template

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `window.speechSynthesis` | Browser built-in | TTS utterances | Zero install, 95.75% global support, no assets required |
| `window.AudioContext` | Browser built-in | Tone beeps (optional) | Zero install, universal support for programmatic sounds |
| Zustand 5.0.12 | Already installed | Audio settings store | Project-standard state management with persist middleware |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `use-sound` | 5.0.0 | Pre-built sound files | Only if custom audio files (MP3/WAV) are used — NOT needed for TTS |

**Decision: Do NOT install `use-sound`.** The TTS path uses `window.speechSynthesis` directly. Pure-tone beeps use raw `AudioContext`. Neither needs Howler.js overhead. Zero new npm dependencies for this phase.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `window.speechSynthesis` | `use-sound` + MP3 files | MP3s need asset management, CDN hosting, and voice recording — overkill for coaching callouts |
| `window.speechSynthesis` | ElevenLabs / cloud TTS | Network round-trip during gameplay — unacceptable latency; also adds backend cost |
| Zustand store for audio settings | `localStorage` direct reads | Zustand persist is the project standard; direct reads don't trigger React re-renders |

**Installation:**
```bash
# No new packages needed
```

**Version verification:** All dependencies are already installed or built-in browser APIs.

---

## Architecture Patterns

### Recommended Project Structure
```
src/
├── stores/
│   └── audioStore.ts          # NEW: enabled, volume, persist
├── hooks/
│   └── useAudio.ts            # NEW: subscribes to refreshStore + recommendationStore
└── components/
    └── settings/
        └── SettingsPanel.tsx  # MODIFIED: add Audio section
```

No new component files needed beyond the store and hook. The SettingsPanel modification is a self-contained section addition (~40 lines).

### Pattern 1: audioStore — Zustand with persist

**What:** A Zustand store holding `enabled: boolean` and `volume: number` (0–1). Persisted to `localStorage` under key `"prismlab-audio"`. Follows identical pattern to `gameStore` and `recommendationStore`.

**When to use:** Any component that needs to read or write audio settings.

```typescript
// Source: project pattern (gameStore.ts, recommendationStore.ts)
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AudioStore {
  enabled: boolean;
  volume: number;  // 0.0 to 1.0
  setEnabled: (v: boolean) => void;
  setVolume: (v: number) => void;
}

export const useAudioStore = create<AudioStore>()(
  persist(
    (set) => ({
      enabled: true,
      volume: 0.7,
      setEnabled: (enabled) => set({ enabled }),
      setVolume: (volume) => set({ volume: Math.max(0, Math.min(1, volume)) }),
    }),
    { name: "prismlab-audio", version: 1 },
  ),
);
```

### Pattern 2: useAudio hook — subscribe to existing event bus

**What:** A custom React hook (called in `App.tsx` alongside `useGameIntelligence`) that subscribes to `refreshStore` for trigger events and `recommendationStore` for new data. Calls `speak()` when audio is enabled and a notable event fires.

**When to use:** Instantiated once at App level — same lifecycle as `useGameIntelligence`.

```typescript
// Source: pattern derived from refreshStore.ts toast subscription
export function useAudio(): void {
  // Unlock AudioContext on first user interaction (autoplay policy)
  const audioCtxRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    const unlock = () => {
      if (!audioCtxRef.current) {
        audioCtxRef.current = new AudioContext();
      } else if (audioCtxRef.current.state === "suspended") {
        audioCtxRef.current.resume();
      }
    };
    document.addEventListener("click", unlock, { once: false });
    return () => document.removeEventListener("click", unlock);
  }, []);

  // Subscribe to toast events (GSI triggers: phase, death, gold swing, etc.)
  useEffect(() => {
    return useRefreshStore.subscribe((state) => {
      const { enabled, volume } = useAudioStore.getState();
      if (!enabled || !state.lastToast) return;
      speak(state.lastToast.message, volume);
    });
  }, []);

  // Subscribe to new recommendations (announce the top priority item)
  useEffect(() => {
    let prevData: RecommendResponse | null = null;
    return useRecommendationStore.subscribe((state) => {
      const { enabled, volume } = useAudioStore.getState();
      if (!enabled) return;
      if (state.data && state.data !== prevData && !state.isLoading) {
        prevData = state.data;
        const topItem = state.data.phases[0]?.items[0];
        if (topItem) {
          speak(`Consider buying ${topItem.item_name.replace(/_/g, " ")}`, volume);
        }
      }
    });
  }, []);
}
```

### Pattern 3: speak() utility — SpeechSynthesis with Chrome keepalive

**What:** A pure utility function wrapping `window.speechSynthesis.speak()`. Applies the Chrome pause/resume keepalive to prevent the 15-second timeout bug.

**When to use:** Called only from `useAudio`. Never called directly from components.

```typescript
// Source: Chrome bug workaround (bugs.chromium.org/p/chromium/issues/detail?id=335907)
export function speak(text: string, volume: number): void {
  if (!("speechSynthesis" in window)) return;

  // Cancel any pending speech (don't stack callouts)
  window.speechSynthesis.cancel();

  const utterance = new SpeechSynthesisUtterance(text);
  utterance.volume = volume;  // 0.0 to 1.0
  utterance.rate = 1.1;       // Slightly faster than default for urgency
  utterance.pitch = 1.0;

  // Chrome keepalive: pause/resume every 10s to prevent 15s timeout
  let keepaliveTimer: ReturnType<typeof setInterval> | null = null;
  utterance.onstart = () => {
    keepaliveTimer = setInterval(() => {
      if (!window.speechSynthesis.speaking) {
        if (keepaliveTimer) clearInterval(keepaliveTimer);
        return;
      }
      window.speechSynthesis.pause();
      window.speechSynthesis.resume();
    }, 10_000);
  };
  utterance.onend = () => {
    if (keepaliveTimer) clearInterval(keepaliveTimer);
  };
  utterance.onerror = () => {
    if (keepaliveTimer) clearInterval(keepaliveTimer);
  };

  window.speechSynthesis.speak(utterance);
}
```

### Pattern 4: SettingsPanel Audio Section

**What:** A new "Audio" section inserted into the existing `SettingsPanel.tsx` above or below the "Recommendation Engine" section. Contains a toggle (enabled/disabled) and a volume slider.

**When to use:** Follows the exact same styling conventions as the existing Engine Mode section — `bg-surface-container-lowest border-b border-outline-variant/15`, gold accent on selected state.

```typescript
// Source: SettingsPanel.tsx Engine Mode section pattern
<div className="space-y-4 mt-8">
  <h3 className="text-sm font-semibold text-on-surface uppercase tracking-wider">
    Audio Coaching
  </h3>

  {/* Enable toggle */}
  <button
    type="button"
    onClick={() => setAudioEnabled(!audioEnabled)}
    className={`w-full flex items-center justify-between px-3 py-3
      bg-surface-container-lowest border-b border-outline-variant/15
      border-l-2 ${audioEnabled ? "border-l-primary" : "border-l-transparent"}
      hover:bg-surface-container-low transition-colors`}
  >
    <span className="text-sm text-on-surface">Speak item alerts</span>
    {/* toggle pill */}
  </button>

  {/* Volume slider */}
  {audioEnabled && (
    <div className="px-3 py-3 bg-surface-container-lowest border-b border-outline-variant/15">
      <label className="block text-sm text-on-surface-variant mb-2">
        Volume
      </label>
      <input
        type="range" min={0} max={1} step={0.05}
        value={audioVolume}
        onChange={(e) => setAudioVolume(parseFloat(e.target.value))}
        className="w-full accent-secondary"
      />
    </div>
  )}
</div>
```

### Anti-Patterns to Avoid

- **Do not call `speak()` inside render**: Audio is a side effect — always in `useEffect` or event handlers.
- **Do not create a new `SpeechSynthesisUtterance` without canceling first**: Stacking utterances causes overlapping callouts. Always `cancel()` before `speak()`.
- **Do not create `AudioContext` at module level**: Browsers block audio contexts created before user interaction. Always lazily initialize inside a user-triggered callback.
- **Do not persist `lastToast` subscription without a guard**: The `refreshStore` subscription fires every state update, not just on new toasts. Guard with `if (!state.lastToast) return`.
- **Do not announce every recommendation update**: Only announce when `data` reference changes AND `isLoading` is false — prevents double-fire on re-renders.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| TTS in browser | Custom TTS engine | `window.speechSynthesis` | Browser handles voice, pronunciation, locale |
| Audio file playback | Custom audio loader | `use-sound` / Howler | Already abstracted — but NOT needed for this phase |
| State persistence | Manual localStorage read/write | Zustand `persist` | Project standard; handles hydration and versioning |
| Volume clamping | Custom clamp logic | `Math.max(0, Math.min(1, v))` inline | One-liner in the store setter |

**Key insight:** The browser already has a production-quality TTS engine. The entire audio layer is a thin wrapper over `window.speechSynthesis` plus one Zustand store. Resist any urge to bring in a dedicated TTS library — the value is not there for short coaching callouts.

---

## Common Pitfalls

### Pitfall 1: Chrome 15-second TTS Timeout
**What goes wrong:** On Chrome (Windows/Linux), utterances longer than ~12–15 seconds stop mid-speech with no error. The `speaking` property remains `true` but no audio plays.
**Why it happens:** Known Chromium bug (issue #335907) specific to Google-provided voices on those platforms.
**How to avoid:** Apply the pause/resume keepalive in `speak()` — see code example above. Set a `setInterval` at 10 seconds that calls `speechSynthesis.pause()` then `speechSynthesis.resume()`.
**Warning signs:** Callouts > 15 words that cut off silently. Test with a long string like "Lane phase ended, your team is behind, consider rushing Blade Mail before the next fight."

### Pitfall 2: AudioContext Suspended by Autoplay Policy
**What goes wrong:** `new AudioContext()` created outside a user gesture starts in `"suspended"` state. Subsequent `play()` or `speak()` calls fail silently.
**Why it happens:** Chrome and Firefox enforce autoplay policies since 2018. Web Audio contexts are blocked until the user interacts with the page.
**How to avoid:** For Web Audio (beeps): lazily initialize `AudioContext` on the first `document` click via a one-time listener with `{ once: false }`. For `SpeechSynthesis`: it uses a different internal mechanism and does NOT require this — but it still requires a prior user gesture on the page before the first `speak()` call.
**Warning signs:** First callout in a fresh browser tab is silent; subsequent ones work after the user clicks anything.

### Pitfall 3: voices Array Empty on First `getVoices()` Call
**What goes wrong:** `window.speechSynthesis.getVoices()` returns `[]` on initial load. Code that tries to select a specific voice (e.g., "Google US English") fails.
**Why it happens:** Voices load asynchronously. The `voiceschanged` event fires when they become available.
**How to avoid:** For this phase, do NOT select a specific voice. Use the browser default (pass no `voice` property on the utterance). This skips voice selection entirely and works immediately on all browsers.
**Warning signs:** Voice selection code that runs at module import time or before any user gesture.

### Pitfall 4: Double-Fire on Recommendation Subscription
**What goes wrong:** `useRecommendationStore.subscribe()` fires on every state update, not just when `data` changes. Without a reference check, the hook announces the same item on every store tick.
**Why it happens:** Zustand subscriptions receive the full new state on any mutation (loading, error, selected item change).
**How to avoid:** Store the previous `data` reference in a `useRef` inside the `useEffect`. Only announce when `state.data !== prevDataRef.current`.
**Warning signs:** Item callout repeating every second during GSI-connected play.

### Pitfall 5: Overlapping Callouts During Rapid Events
**What goes wrong:** Multiple events fire in quick succession (phase transition + gold swing + item mark) and speech utterances stack, creating garbled audio.
**Why it happens:** `speechSynthesis.speak()` queues utterances by default — they play sequentially, but that queue can get long.
**How to avoid:** Always call `window.speechSynthesis.cancel()` before each new `speak()` call. This discards the queue and speaks only the latest (most relevant) event.
**Warning signs:** Multiple overlapping voices or a long queue that plays 5–10 seconds after the triggering event.

---

## Code Examples

### Trigger Event Text Mapping
The `TriggerEvent.message` strings from `triggerDetection.ts` are already human-readable:
- `"Late game reached (35:00)"` — speaks as-is
- `"Mid-game reached (20:00)"` — speaks as-is
- `"Lane phase ended (10:00)"` — speaks as-is
- `"3 deaths -- reassessing priorities"` — needs cleanup: strip `--` → `,`
- `"Roshan killed -- updating"` — needs cleanup
- `"Tower destroyed -- map changed"` — needs cleanup
- `"Gold swing: +2000g"` — should be filtered or simplified to "Gold spike"

**Sanitize utility:**
```typescript
// Source: derived from triggerDetection.ts message format
function sanitizeForSpeech(msg: string): string {
  return msg
    .replace(/--/g, ",")         // "--" is not spoken naturally
    .replace(/\(\d+:\d+\)/g, "") // strip "(35:00)" clock notation
    .replace(/\+(\d+)g/, "$1 gold") // "+2000g" → "2000 gold"
    .trim();
}
```

### App.tsx Integration
```typescript
// Source: App.tsx pattern — hooks called at top level
import { useAudio } from "./hooks/useAudio";

function App() {
  const { heroes } = useHeroes();
  useGameIntelligence(heroes);
  useLiveDraft(heroes);
  useAudio();  // NEW — add after existing hooks
  // ...
}
```

### Item Name Humanization
Recommendation `item_name` values are snake_case internal names (e.g., `"blade_mail"`, `"black_king_bar"`). Replace underscores for speech:
```typescript
function humanizeItemName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  // "blade_mail" → "Blade Mail"
  // "black_king_bar" → "Black King Bar"
}
```

---

## Existing Event Pipeline (What Already Exists)

The planner does NOT need to create new trigger detection. These already fire:

| Source | Event / State Change | When |
|--------|---------------------|------|
| `triggerDetection.ts` + `refreshStore.lastToast` | Phase transitions (10:00, 20:00, 35:00) | Game clock crosses threshold |
| `refreshStore.lastToast` | Death milestone (every 3 deaths) | `live.deaths % 3 === 0` |
| `refreshStore.lastToast` | Roshan killed | `roshan_state === "respawn_base"` |
| `refreshStore.lastToast` | Tower destroyed | Total tower count decreases |
| `refreshStore.lastToast` | Gold swing >= 2000g | Net worth delta from last refresh |
| `recommendationStore.data` | New recommendations arrive | After `api.recommend()` resolves |

Audio is a **read-only consumer** of `refreshStore` and `recommendationStore`. No modifications to trigger detection, event pipeline, or recommendation engine are needed.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flash/Silverlight audio | Web Audio API / SpeechSynthesis | ~2014-2015 | No plugins needed |
| External TTS APIs (Google TTS over HTTP) | Browser-native `SpeechSynthesis` | 2014 (Chrome) | Zero latency, offline |
| Manual localStorage for settings | Zustand `persist` middleware | Project standard since Phase 15 | Versioned, type-safe |

**Deprecated/outdated:**
- `react-speech-kit`: Last published 3+ years ago, unmaintained. Use `window.speechSynthesis` directly.
- `use-sound` for TTS: Designed for audio files, not TTS. Adds Howler.js (10KB) for no benefit here.

---

## Open Questions

1. **Which events should speak vs. stay silent?**
   - What we know: All 5 trigger types produce a `lastToast` message. New recommendations also arrive.
   - What's unclear: Should ALL events speak, or only the most actionable ones? Gold swings may be noise at high frequency.
   - Recommendation: Start with phase transitions + new recommendations. Suppress gold swings (too frequent). Gate deaths and tower events behind volume > 0.3 threshold optionally. This is a Claude discretion area — planner should pick a default set.

2. **Should the callout quote the item name or just signal "new recommendations ready"?**
   - What we know: `recommendationStore.data.phases[0].items[0]` is the top priority item.
   - What's unclear: Speaking "Buy Blade Mail" is more actionable than "Recommendations updated" but assumes the player isn't already looking at the screen.
   - Recommendation: "Consider buying Blade Mail" for the top core item only. Skip neutral items and luxuries.

3. **Voice selection UI?**
   - What we know: `getVoices()` returns different voices on different OSes (Windows has "Microsoft David", macOS has "Alex", etc.).
   - What's unclear: Is exposing a voice picker in Settings worth the complexity?
   - Recommendation: No voice picker in v1 of this phase. Use browser default. A voice dropdown can always be added later.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `window.speechSynthesis` | TTS callouts | Assumed yes — 95.75% global support | Browser built-in | Silently degrade if not available (guard with `"speechSynthesis" in window`) |
| `window.AudioContext` | Tone beeps (optional) | Assumed yes — universal modern browser | Browser built-in | Skip beep if not available |
| Zustand 5.0.12 | audioStore | Already installed | 5.0.12 | — |

**Missing dependencies with no fallback:** None — this phase has zero new npm dependencies.

**Step 2.6: SKIPPED (no external service dependencies — all browser built-in APIs)**

---

## Validation Architecture

> nyquist_validation is `false` in .planning/config.json — this section is SKIPPED.

---

## Sources

### Primary (HIGH confidence)
- MDN Web Docs — SpeechSynthesis API: methods, properties, voice loading behavior
- MDN Web Docs — Web Audio API Best Practices: AudioContext lifecycle, autoplay policy, GainNode
- CanIUse.com — Speech Synthesis: 95.75% global support, Chrome/Firefox/Edge/Safari desktop all green
- Project codebase — `triggerDetection.ts`, `refreshStore.ts`, `useGameIntelligence.ts`, `gsiStore.ts`, `recommendationStore.ts`, `SettingsPanel.tsx`

### Secondary (MEDIUM confidence)
- Chromium bug tracker issue #335907 — Chrome 15-second TTS timeout (multiple sources confirm, workaround is widely deployed)
- `use-sound` npm page — v5.0.0 confirmed current; Howler.js dependency confirmed

### Tertiary (LOW confidence)
- Community blog posts on Chrome pause/resume keepalive — multiple sources confirm the workaround works; Chromium bug remains open

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — browser built-ins confirmed via MDN/CanIUse; no third-party libraries needed
- Architecture: HIGH — directly extends proven project patterns (Zustand persist, App-level hooks, SettingsPanel sections)
- Pitfalls: HIGH — Chrome timeout bug is documented in Chromium tracker; autoplay policy is official Chrome/MDN documentation

**Research date:** 2026-03-29
**Valid until:** 2027-03-29 (stable browser APIs — low churn)

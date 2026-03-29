# Phase 15: Store Consolidation & Tech Debt - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 15 consolidates the two independent gsiStore subscription hooks (useGsiSync + useAutoRefresh) into a single useGameIntelligence hook, adds hero+role-aware playstyle auto-suggestion, and deduplicates the TriggerEvent interface. All behavioral changes, no UI changes. After this phase, GSI data flows through a single orchestrator hook with deterministic ordering and playstyle is automatically set for every detected hero.

</domain>

<decisions>
## Implementation Decisions

### Hook Consolidation
- **D-01:** Merge `useGsiSync` and `useAutoRefresh` into a single `useGameIntelligence` hook in a new file. Delete the two original hook files.
- **D-02:** Keep SEPARATE `gsiStore.subscribe()` calls within the consolidated hook — do NOT merge into a single callback. Co-locate, not merge. Research identified that a single callback causes cross-store write cascades that freeze the browser during live games.
- **D-03:** Ordering within the hook: hero detection → item marking → lane detection → event detection → cooldown → refresh. Hero detection must complete before event detection to ensure `game.role` is available for lane benchmarks.
- **D-04:** The 1Hz cooldown interval stays in the consolidated hook. Single `setInterval` for countdown ticks and queued event firing.

### Playstyle Auto-Suggestion
- **D-05:** Hero+role-aware playstyle map: `HERO_PLAYSTYLE_MAP` keyed as `"{hero_id}-{role}"` → playstyle string. Covers ~80 popular heroes across their common positions.
- **D-06:** When GSI detects hero and role, look up `HERO_PLAYSTYLE_MAP[hero_id + "-" + role]`. If found, auto-set playstyle in gameStore. If not found, fall back to `PLAYSTYLE_OPTIONS[role][0]`.
- **D-07:** User can always override the auto-suggested playstyle manually. Override persists until GSI detects a new hero (new game).
- **D-08:** The HERO_PLAYSTYLE_MAP lives as a TypeScript constant file (e.g., `heroPlaystyles.ts` in utils/). Not fetched from backend — static data maintained in code.

### TriggerEvent Deduplication
- **D-09:** Remove the `TriggerEvent` interface declaration from `refreshStore.ts`. Import it from `triggerDetection.ts` instead. All consumers use the single source in `triggerDetection.ts`.
- **D-10:** Update `refreshStore.test.ts` to import `TriggerEvent` from `triggerDetection.ts` instead of `refreshStore.ts`.

### Claude's Discretion
- Exact hero-playstyle mappings for the ~80 entries (use Dota knowledge to assign appropriate playstyles)
- Internal structure of useGameIntelligence (ref naming, subscription grouping)
- Whether to extract the recommend-request builder into a shared utility (fireRefresh duplicates useRecommendation logic)
- Test migration strategy (adapt existing useGsiSync and useAutoRefresh tests to useGameIntelligence)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — INT-01, INT-02, INT-04 requirement definitions
- `.planning/ROADMAP.md` — Phase 15 success criteria (4 criteria that must be TRUE)

### Research
- `.planning/research/ARCHITECTURE.md` — Hook consolidation architecture, subscription callback warning
- `.planning/research/PITFALLS.md` — Pitfall: co-locate but do NOT merge subscribe() callbacks

### Existing Hooks (being consolidated)
- `prismlab/frontend/src/hooks/useGsiSync.ts` — Hero detection, role inference, item marking. Subscribe to gsiStore.
- `prismlab/frontend/src/hooks/useAutoRefresh.ts` — Event detection, cooldown, lane detect, refresh firing. Subscribe to gsiStore + recommendationStore.
- `prismlab/frontend/src/hooks/useGsiSync.test.ts` — 9 tests for hero/role/item sync
- `prismlab/frontend/src/hooks/useAutoRefresh.ts` — Tests for auto-refresh behavior (if exist)

### Stores (read, not modified)
- `prismlab/frontend/src/stores/gsiStore.ts` — GsiLiveState interface, subscribe target
- `prismlab/frontend/src/stores/gameStore.ts` — selectHero, setRole, setPlaystyle, setLaneResult actions
- `prismlab/frontend/src/stores/recommendationStore.ts` — togglePurchased, isLoading, data
- `prismlab/frontend/src/stores/refreshStore.ts` — Cooldown, toast, queue, laneAutoDetected. Has duplicate TriggerEvent.

### Utilities
- `prismlab/frontend/src/utils/triggerDetection.ts` — TriggerEvent canonical source, detectTriggers()
- `prismlab/frontend/src/utils/laneBenchmarks.ts` — detectLaneResult()
- `prismlab/frontend/src/utils/itemMatching.ts` — findPurchasedKeys()
- `prismlab/frontend/src/utils/constants.ts` — PLAYSTYLE_OPTIONS per role

### App Wiring
- `prismlab/frontend/src/App.tsx` — Currently mounts useGsiSync(heroes) and useAutoRefresh() separately

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `useGsiSync.ts` — 94 lines, hero detection + item marking logic to preserve
- `useAutoRefresh.ts` — 263 lines, event detection + cooldown + lane detect + refresh logic to preserve
- `inferRole()` function in useGsiSync — role inference from hero.roles array, reuse as-is
- `fireRefresh()` function in useAutoRefresh — recommendation request builder, reuse as-is
- All existing test files for both hooks — adapt to test useGameIntelligence

### Established Patterns
- Zustand `subscribe()` outside render cycle for non-reactive state sync
- Refs for mutable state to avoid stale closures in subscriptions
- `useEffect` cleanup returning unsubscribe functions

### Integration Points
- `App.tsx` — Replace two hook calls with single `useGameIntelligence(heroes)` call
- `refreshStore.ts` — Remove TriggerEvent declaration, add import from triggerDetection
- New `utils/heroPlaystyles.ts` — HERO_PLAYSTYLE_MAP constant

</code_context>

<specifics>
## Specific Ideas

- User wants per-hero playstyle accuracy via a hero+role keyed map (~80 entries)
- Flex picks handled correctly (Mirana pos 2 = Tempo, Mirana pos 4 = Roamer)
- Fallback to PLAYSTYLE_OPTIONS[role][0] for unmapped heroes guarantees a valid value

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 15-store-consolidation-tech-debt*
*Context gathered: 2026-03-26*

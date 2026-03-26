# Phase 11: Live Game Dashboard - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 11 delivers the live game dashboard: GSI data auto-populates the draft (hero, role), real-time gold/GPM/net worth/KDA display in the sidebar, automatic item purchase detection that marks items in the timeline, and a game clock in the header tied to neutral item tier timing. All manual input controls remain functional as fallback when GSI is not connected. After this phase, the player sees their live game state without any manual input.

</domain>

<decisions>
## Implementation Decisions

### Auto-detect & Store Sync
- **D-01:** GSI hero detection auto-fills the hero picker silently — no toast, no confirmation dialog. User can still click to change manually.
- **D-02:** Role auto-suggested from OpenDota most-played position data for the detected hero (e.g., Anti-Mage → Pos 1 at 95%). Pre-selects role but user can override. Fallback: if no data, leave role unselected.
- **D-03:** GSI is source of truth while connected — overwrites hero, gold, GPM, net worth, inventory, game clock. Manual edits are possible but next GSI update will overwrite GSI-controlled fields.
- **D-04:** Priority chain: (1) GSI connected → GSI data wins, (2) GSI disconnects → last GSI values persist, manual edits resume control, (3) No GSI ever → fully manual mode.
- **D-05:** Fields GSI controls: hero, role (suggest only), gold, GPM, net worth, inventory items, game clock, kills, deaths, assists. Fields always manual: playstyle, side, lane, lane opponents, enemy items spotted.

### Live Gold & Stats Display
- **D-06:** New compact stats bar in the sidebar, positioned above the existing GameStatePanel. Shows Gold | GPM | Net Worth on one line, KDA on a second line.
- **D-07:** Stats bar only visible when GSI is connected and in-game. Hidden otherwise.
- **D-08:** Counting animation — numbers smoothly interpolate to new values over ~300ms (slot machine style). Gold ticks up as creeps die.
- **D-09:** Color flash on significant changes: brief green pulse on large gold gains (+300g), brief red pulse on death.
- **D-10:** Existing manual controls (lane result, damage profile, enemy items) remain visible and functional below the stats bar. They are not replaced or hidden.

### Auto-mark Purchased Items
- **D-11:** Reuse existing green checkmark overlay and dimmed card visual for auto-detected purchases. Same visual as manual click — no separate "GSI detected" indicator.
- **D-12:** Only mark completed items. Components in inventory (e.g., Ogre Axe toward BKB) do not trigger partial progress indicators. Item marked only when full item appears in inventory.
- **D-13:** Manual click still toggles purchased state. GSI effectively overrides manual unmarks on next update (1s later) if item is still in inventory. This is correct — you do have the item.
- **D-14:** Item name matching: GSI inventory item names matched against recommended item internal names from the database. Claude has discretion on exact matching strategy (fuzzy vs exact, handling of recipe variants).

### Game Clock & Neutral Tiers
- **D-15:** Game clock displays in the header bar, between GSI status indicator and data freshness. Format: MM:SS. Only visible when GSI is active and game is in progress.
- **D-16:** Neutral item section auto-highlights current tier based on game clock (e.g., clock > 7:00 = Tier 1 active). Next tier shows countdown to activation.
- **D-17:** NeutralItemSection component receives a `currentTier` prop derived from GSI game clock. Tier boundaries are the standard Dota 2 timing (7:00, 17:00, 27:00, 37:00, 60:00).

### Claude's Discretion
- Exact implementation of counting animation (CSS transitions, requestAnimationFrame, library choice)
- GSI item name → DB item name matching strategy (exact match on internal_name, fuzzy fallback)
- Stats bar layout and spacing within sidebar
- Game clock formatting for negative time (pre-horn) or paused states
- How gsiStore updates flow into gameStore (subscription, effect, derived state)
- WebSocket message parsing and validation in the frontend

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — GSI-02, GSI-03, GSI-04, WS-02, WS-03, WS-04 requirement definitions
- `.planning/ROADMAP.md` — Phase 11 success criteria (5 criteria that must be TRUE)

### Phase 10 Context (upstream dependency)
- `.planning/phases/10-gsi-receiver-websocket-pipeline/10-CONTEXT.md` — GSI data fields (D-13), WebSocket throttle (D-15/D-16), store patterns, Nginx routing decisions

### Existing Stores & Hooks
- `prismlab/frontend/src/stores/gsiStore.ts` — GsiLiveState interface with all GSI fields, connection status management
- `prismlab/frontend/src/stores/gameStore.ts` — Manual game state (hero, role, lane, etc.) — Phase 11 syncs GSI data into this
- `prismlab/frontend/src/stores/recommendationStore.ts` — Purchased item tracking (purchasedItems set) — Phase 11 auto-marks here
- `prismlab/frontend/src/hooks/useWebSocket.ts` — WebSocket hook with auto-reconnect, exponential backoff

### Existing Components
- `prismlab/frontend/src/components/layout/Header.tsx` — Header with GSI indicator and settings gear; game clock goes here
- `prismlab/frontend/src/components/game/GameStatePanel.tsx` — Manual mid-game controls; stats bar sits above this
- `prismlab/frontend/src/components/timeline/ItemCard.tsx` — Item cards with click-to-mark purchased (green checkmark overlay)
- `prismlab/frontend/src/components/timeline/NeutralItemSection.tsx` — Neutral item display by tier; needs currentTier prop

### Data
- `prismlab/backend/data/models.py` — Hero model with roles field (for role inference), Item model with internal_name (for matching)
- `PRISMLAB_BLUEPRINT.md` — Original project spec with data models and hero/item data patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `gsiStore.ts` — Already has GsiLiveState interface with hero_name, gold, gpm, net_worth, items_inventory, items_backpack, game_clock, kills, deaths, assists. Connection status management (connected/idle/lost) already implemented.
- `useWebSocket.ts` — Auto-reconnect hook with exponential backoff (1s, 2s, 4s, 8s, max 10s). Returns status + lastMessage. Already wired into App.tsx.
- `gameStore.ts` — Has selectHero, setRole, and all manual state setters. Phase 11 needs to call these from GSI data.
- `recommendationStore.ts` — Has purchasedItems Set and togglePurchased action. Phase 11 auto-marks use this same mechanism.
- `GsiStatusIndicator.tsx` — Green/gray/red dot already in header. Game clock adds to the same header area.
- `NeutralItemSection.tsx` — Displays neutral items by tier. Needs currentTier prop to highlight active tier and show countdown.

### Established Patterns
- Zustand stores with `create<T>()((set, get) => ...)` pattern
- Functional components with hooks
- Tailwind v4 for all styling (dark theme tokens: bg-bg-secondary, text-text-muted, text-cyan-accent)
- Steam CDN for hero/item images

### Integration Points
- `App.tsx` — Already has useWebSocket hook and passes messages to gsiStore. Phase 11 adds gsiStore → gameStore sync.
- `Sidebar.tsx` — Renders GameStatePanel. Stats bar component inserted above it.
- `Header.tsx` — Already has GsiStatusIndicator. Game clock component added next to it.
- `ItemTimeline.tsx` / `ItemCard.tsx` — Already reads purchasedItems from recommendationStore. Auto-mark writes to same store.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. User chose all recommended defaults, prioritizing minimal friction (silent auto-fill, GSI as source of truth, reuse existing visuals, counting animations for live feel).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-live-game-dashboard*
*Context gathered: 2026-03-26*

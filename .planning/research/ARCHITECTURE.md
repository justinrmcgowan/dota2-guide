# Architecture Patterns

**Domain:** Dota 2 item advisor -- v3.0 integration architecture
**Researched:** 2026-03-26
**Scope:** Design system migration, in-memory cache, store consolidation, integration gap fixes
**Confidence:** HIGH -- based on direct codebase analysis of all source files, not speculation

---

## 1. Current Architecture Snapshot

Before defining integration points, here is exactly what exists today.

### Frontend (React 19 + Vite 8 + Tailwind v4)

```
App.tsx
  +-- useWebSocket(wsUrl) --> gsiStore.setWsStatus / updateLiveState
  +-- useGsiSync(heroes)  --> subscribes gsiStore, writes gameStore + recommendationStore
  +-- useAutoRefresh()     --> subscribes gsiStore, fires api.recommend(), writes refreshStore
  +-- useScreenshotPaste() --> screenshotStore.openModal
  |
  +-- Header              --> data freshness, GsiStatusIndicator, GameClock, settings button
  +-- Sidebar             --> HeroPicker, AllyPicker, OpponentPicker, RoleSelector,
  |                           PlaystyleSelector, SideSelector, LaneSelector,
  |                           LaneOpponentPicker, LiveStatsBar, GameStatePanel, GetBuildButton
  +-- MainPanel           --> item timeline, reasoning panel
  +-- SettingsPanel       --> GSI config download
  +-- AutoRefreshToast    --> event-triggered refresh notifications
  +-- ScreenshotParser    --> paste/upload screenshot, parsed hero rows, Apply to Build
```

**Stores:** gameStore, gsiStore, recommendationStore, refreshStore, screenshotStore (5 total)

**CSS:** Single `globals.css` with `@theme` block defining 6 color tokens + 2 font families via Tailwind v4 CSS-first config. No tailwind.config file.

**Fonts:** Inter (body) + JetBrains Mono (stats), loaded via `@fontsource` packages.

### Backend (Python 3.13 + FastAPI)

```
main.py (lifespan)
  +-- create tables, seed_if_empty()
  +-- _rules.init_lookups(session)       --> loads hero/item ID maps into memory
  +-- scheduler: refresh_all_data() 6h   --> OpenDota fetch, DB upsert, _rules.refresh_lookups()
  +-- ws_manager.start_broadcast_loop()  --> 1Hz GSI state broadcast

Routes:
  /api/heroes       --> SELECT * FROM heroes (every request)
  /api/items        --> SELECT * FROM items (every request)
  /api/recommend    --> RulesEngine.evaluate() + ContextBuilder.build() + LLMEngine.generate()
  /api/parse-screenshot  --> Claude Vision parse
  /api/data-freshness    --> last DataRefreshLog
  /api/settings     --> GSI config
  /gsi              --> GSI POST receiver
  /ws               --> WebSocket for live state
```

**Hot path DB queries per /api/recommend request:**
1. `SELECT Hero WHERE id = hero_id` (player hero)
2. `SELECT Hero WHERE id = opp_id` (per opponent, up to 2x)
3. `SELECT Hero WHERE id = ally_id` (per ally, up to 4x)
4. `SELECT MatchupData WHERE hero_id AND opponent_id` (per opponent)
5. `SELECT HeroItemPopularity WHERE hero_id` (player hero + each ally)
6. `SELECT Item WHERE NOT recipe AND NOT neutral AND cost > 0` (filtered catalog)
7. `SELECT Item WHERE is_neutral AND tier IS NOT NULL` (neutral catalog)
8. `SELECT Item` (full table, for name resolution in popularity) -- called multiple times
9. `SELECT Item.id, Item.cost, Item.internal_name` (validation pass)

This is 12-20 DB queries per recommendation, all hitting the same SQLite file. The hero and item tables change only every 6 hours (data refresh), making them ideal cache candidates.

---

## 2. Design System Migration

### What Changes

The current theme is "spectral cyan" -- 6 custom colors in `globals.css @theme`, Inter + JetBrains Mono fonts, rounded corners throughout, 1px borders for section separation.

The new "Tactical Relic Editorial" theme from DESIGN.md changes:

| Aspect | Current | New |
|--------|---------|-----|
| Primary accent | `oklch(80.4% 0.146 219.5)` cyan | `#B22222` crimson |
| Secondary accent | N/A | `#FFDB3C` gold |
| Background | `oklch(18.8%)` blue-ish | `#131313` obsidian |
| Surface system | 3 tones (primary, secondary, elevated) | 6 tones (surface, dim, low, high, highest, bright) |
| Typography display | N/A | Newsreader (serif, headlines) |
| Typography body | Inter | Manrope |
| Typography stats | JetBrains Mono | Manrope (body class) |
| Corner radius | rounded-md/lg throughout | 0px everywhere -- strict prohibition |
| Borders | 1px solid borders | No-line rule: surface color shifts only |
| Elevation | Standard Tailwind shadows | Ambient glows (crimson-tinted, 5% opacity, 32px blur) |
| Attribute colors | Custom oklch per str/agi/int/all | Keep (DESIGN.md is silent -- preserve game-semantic colors) |

### Integration Points

**New files to create:**

| File | Purpose |
|------|---------|
| `src/styles/globals.css` | Complete rewrite -- new @theme tokens, Newsreader + Manrope font families, surface scale, 0px radius defaults |

**Package changes:**

| Action | Package |
|--------|---------|
| Install | `@fontsource/newsreader`, `@fontsource/manrope` |
| Remove | `@fontsource/inter`, `@fontsource/jetbrains-mono` |

**Entry point changes:**

| File | Change |
|------|--------|
| `src/main.tsx` | Swap font imports: Newsreader 400/500/600/700 + Manrope 400/500/600/700 (replacing Inter + JetBrains Mono) |

**Existing files to modify (every component with Tailwind classes):**

This is the largest change surface. Every component uses `bg-bg-primary`, `bg-bg-secondary`, `bg-bg-elevated`, `text-cyan-accent`, `text-radiant`, `text-dire`, `rounded-*`, `border-*`, and `font-body`/`font-stats` classes.

Strategy: Change the token names in `globals.css` first, then update component classes in a systematic sweep. Tailwind v4's `@theme` block means we define new token names and all components referencing old names will break at build time (Tailwind v4 purges unknown utilities), making it safe to do this as a hard cutover rather than gradual migration.

**Recommended token mapping:**

```css
@theme {
  /* Surface hierarchy (6 levels per DESIGN.md) */
  --color-surface: #131313;
  --color-surface-dim: #1A1919;
  --color-surface-low: #1C1B1B;
  --color-surface-high: #2B2A2A;
  --color-surface-highest: #353534;
  --color-surface-bright: #3A3939;

  /* Accent colors */
  --color-crimson: #B22222;
  --color-gold: #FFDB3C;
  --color-gold-dim: #C6A200;
  --color-gold-leaf: #FFE16D;

  /* Text hierarchy */
  --color-on-surface: #E5E2E1;
  --color-on-surface-variant: #E2BEBA;
  --color-outline-variant: #5A403E;

  /* Game-semantic (preserved from v2) */
  --color-radiant: oklch(89.5% 0.192 150.6);
  --color-dire: oklch(68.2% 0.206 24.4);
  --color-attr-str: oklch(68% 0.19 25);
  --color-attr-agi: oklch(75% 0.18 145);
  --color-attr-int: oklch(70% 0.15 250);
  --color-attr-all: oklch(80% 0.1 90);

  /* Tactical HUD (for dense data viz per DESIGN.md section 5) */
  --color-slate: #4E5E6D;

  /* Typography */
  --font-display: "Newsreader", "Georgia", serif;
  --font-body: "Manrope", "Inter", system-ui, sans-serif;
}
```

**Component class migration map (systematic):**

| Old class pattern | New class pattern | Notes |
|-------------------|-------------------|-------|
| `bg-bg-primary` | `bg-surface` | Base background |
| `bg-bg-secondary` | `bg-surface-low` | Sidebar, secondary panels |
| `bg-bg-elevated` | `bg-surface-high` | Elevated containers, hover states |
| `bg-bg-elevated/50` | `bg-surface-high/50` | Semi-transparent overlays |
| `text-cyan-accent` | `text-crimson` or `text-gold` | Context-dependent (see accent rules below) |
| `hover:text-cyan-accent` | `hover:text-gold` | Interactive hover states |
| `text-gray-100` | `text-on-surface` | Primary text (warm ivory, not white) |
| `text-gray-400` | `text-on-surface-variant` | Secondary text (parchment) |
| `text-gray-500` | `text-on-surface-variant/70` | Tertiary text |
| `text-gray-600` | `text-on-surface-variant/50` | Muted text |
| `border-bg-elevated` | Remove (no-line rule) | Use surface color shifts instead |
| `border-b border-bg-elevated` | Remove or use `border-outline-variant/15` | Ghost border only when necessary |
| `ring-1 ring-cyan-accent` | `ring-1 ring-crimson` | Focus/selected ring |
| `rounded-md` | Remove (0px corners) | Strict prohibition per DESIGN.md |
| `rounded-lg` | Remove (0px corners) | Strict prohibition per DESIGN.md |
| `rounded-full` | Keep for small indicators only | Checkmark badges, status dots |
| `font-body` | `font-body` | Same token name, Manrope underneath |
| `font-stats` | `font-body` | JetBrains Mono replaced by Manrope |
| `shadow-2xl` | `shadow-[0_0_32px_rgba(178,34,34,0.05)]` | Crimson ambient glow |

**Accent color context rules (when to use crimson vs gold):**
- `crimson` (#B22222): Primary CTA buttons, active states, selected items, primary accent, loading spinners
- `gold` (#FFDB3C): Section headlines (with `font-display`), hover accents, gold cost displays, legendary item left-strip accent
- `gold-dim` (#C6A200): Links (replacing blue)
- `on-surface` (#E5E2E1): Primary body text (NOT #FFFFFF per DESIGN.md)
- `on-surface-variant` (#E2BEBA): Secondary text, descriptions, parchment-like

**Components requiring the most attention (highest class density):**

1. `Header.tsx` -- prism SVG gradient needs crimson/gold replacement, bg/border classes, text colors
2. `Sidebar.tsx` -- bg, border, section headers (uppercase tracking h2 elements)
3. `ItemCard.tsx` -- priority border colors, purchased overlay, rounded corners to remove, ring
4. `ScreenshotParser.tsx` -- modal backdrop, upload zone border, error states, all buttons
5. `GetBuildButton.tsx` -- primary CTA, loading state, disabled state
6. All draft pickers (HeroPicker, AllyPicker, OpponentPicker) -- dropdown backgrounds, selected states, hover
7. `GameStatePanel.tsx` -- toggle buttons, slider tracks, section dividers
8. `AutoRefreshToast.tsx` -- toast container, timer display
9. `SettingsPanel.tsx` -- slide-over panel, close button
10. `constants.ts` -- LANE_RESULT_OPTIONS bg/border/color class strings

### Build Order for Design System

The design system must be done in this exact order because of dependency chains:

1. **Install new fonts** -- `@fontsource/newsreader` + `@fontsource/manrope`, update `main.tsx` imports, remove old font packages
2. **Rewrite `globals.css`** -- New @theme block with all tokens. This intentionally breaks every component referencing old tokens.
3. **Update `App.tsx`** -- Root container classes (`bg-surface`, `text-on-surface`, `font-body`)
4. **Layout shell** -- Header.tsx, Sidebar.tsx, MainPanel.tsx (sets the visual frame)
5. **Interactive primitives** -- Buttons (GetBuildButton), inputs (HeroPicker search), selectors
6. **Content components** -- ItemCard, PhaseCard, ReasoningPanel, NeutralItemsSection
7. **Modals and overlays** -- ScreenshotParser, SettingsPanel
8. **Status indicators** -- GsiStatusIndicator, GameClock, AutoRefreshToast, LiveStatsBar
9. **Utility updates** -- constants.ts color references (LANE_RESULT_OPTIONS bg/border classes)

---

## 3. In-Memory Hero/Item Cache

### Problem

The backend makes 12-20 SQLite queries per `/api/recommend` request. Hero and item data only changes every 6 hours (data refresh). The `/api/heroes` and `/api/items` endpoints also do full table scans on every call. The context builder does `SELECT Item` (full table) multiple times per request for name resolution.

### Recommended Architecture

Add a singleton `DataCache` class that loads all heroes and items into memory at startup, refreshes on the data pipeline cycle, and serves as the primary data source for the hot path.

**New file: `backend/data/cache.py`**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class HeroCached:
    id: int
    name: str
    localized_name: str
    internal_name: str
    primary_attr: str | None
    attack_type: str | None
    roles: tuple[str, ...]  # tuple for immutability
    base_health: float | None
    base_mana: float | None
    base_armor: float | None
    base_str: float | None
    base_agi: float | None
    base_int: float | None
    str_gain: float | None
    agi_gain: float | None
    int_gain: float | None
    base_attack_min: int | None
    base_attack_max: int | None
    attack_range: int | None
    move_speed: int | None
    img_url: str | None
    icon_url: str | None

@dataclass(frozen=True)
class ItemCached:
    id: int
    name: str
    internal_name: str
    cost: int | None
    is_recipe: bool
    is_neutral: bool
    tier: int | None
    bonuses: dict | None  # frozen dataclass, but dict content read-only by convention
    active_desc: str | None
    passive_desc: str | None
    category: str | None
    tags: tuple[str, ...] | None
    img_url: str | None


class DataCache:
    """In-memory cache for hero and item data.

    Loaded at startup from DB. Refreshed after each data pipeline cycle.
    Thread-safe for reads (Python GIL + immutable snapshots via dict replacement).
    """

    def __init__(self):
        self._heroes: dict[int, HeroCached] = {}
        self._items: dict[int, ItemCached] = {}
        self._hero_name_to_id: dict[str, int] = {}
        self._item_name_to_id: dict[str, int] = {}
        self._initialized: bool = False

    async def load(self, db: AsyncSession) -> None:
        """Load all heroes and items from DB into memory."""
        # Build new dicts, then atomic swap
        ...

    async def refresh(self, db: AsyncSession) -> None:
        """Reload after data pipeline. Same as load -- atomic swap."""
        await self.load(db)

    # Lookup methods -- all pure reads from dicts, no DB
    def get_hero(self, hero_id: int) -> HeroCached | None: ...
    def get_item(self, item_id: int) -> ItemCached | None: ...
    def get_all_heroes(self) -> list[HeroCached]: ...
    def get_all_items(self) -> list[ItemCached]: ...
    def hero_name_to_id(self, name: str) -> int | None: ...
    def item_name_to_id(self, internal_name: str) -> int | None: ...
    def hero_id_to_name(self, hero_id: int) -> str: ...
    def get_relevant_items(self, role: int) -> list[ItemCached]: ...
    def get_neutral_items_by_tier(self) -> dict[int, list[ItemCached]]: ...
    def get_item_name_map(self) -> dict[int, str]: ...
    def get_item_validation_map(self) -> dict[int, tuple[int | None, str]]: ...
```

Use frozen dataclasses (not Pydantic) to avoid serialization overhead on reads. The cache is read-heavy, write-rare. Use `tuple` instead of `list` for immutable sequence fields.

### Integration Points

**Files to create:**

| File | Purpose |
|------|---------|
| `backend/data/cache.py` | DataCache class + HeroCached/ItemCached frozen dataclasses |

**Files to modify:**

| File | Change | Detail |
|------|--------|--------|
| `backend/main.py` | Add cache init in lifespan | `data_cache.load(session)` after seed, before rules init. Pass cache to RulesEngine constructor. |
| `backend/data/refresh.py` | Add cache refresh | `data_cache.refresh(session)` after DB upsert. Remove `_rules.refresh_lookups(session)` call (and its circular import). |
| `backend/api/routes/heroes.py` | Read from cache | `data_cache.get_all_heroes()` replaces `SELECT Hero`. Need to serialize HeroCached to HeroResponse. |
| `backend/api/routes/items.py` | Read from cache | `data_cache.get_all_items()` replaces `SELECT Item`. Need to serialize ItemCached to ItemResponse. |
| `backend/engine/context_builder.py` | Replace all DB calls with cache reads | `_get_hero()` -> `cache.get_hero()`. `get_relevant_items()` -> `cache.get_relevant_items()`. `get_neutral_items_by_tier()` -> `cache.get_neutral_items_by_tier()`. `_extract_top_items()` -> `cache.get_item_name_map()`. `_build_popularity_section()` -> item name resolution from cache. |
| `backend/engine/recommender.py` | Replace validation DB query | `_validate_item_ids()` reads `cache.get_item_validation_map()` instead of `SELECT Item.id, Item.cost, Item.internal_name`. |
| `backend/engine/rules.py` | Take cache reference, remove init_lookups/refresh_lookups | Constructor accepts `DataCache`. `_hero_id()`, `_item_id()`, `_hero_name()` delegate to cache. Remove `init_lookups()` and `refresh_lookups()` methods entirely. |
| `backend/data/matchup_service.py` | Move `get_relevant_items()` and `get_neutral_items_by_tier()` functions to cache | These functions currently live here but query Item table -- they belong in cache now. `get_hero_item_popularity()` item name resolution uses cache. |
| `backend/api/routes/recommend.py` | Pass cache to singleton constructors | `_rules = RulesEngine(cache=data_cache)`. `_context_builder = ContextBuilder(opendota_client=_opendota, cache=data_cache)`. `_recommender` gets cache for validation. |

### What Stays in DB (Not Cached)

- **MatchupData** -- ~15,000 possible hero pairs. Fetched on-demand with stale-while-revalidate and per-pair asyncio locks. This pattern is correct and stays.
- **HeroItemPopularity** -- Per-hero, fetched on-demand with stale-while-revalidate. Could be cached but current pattern works. Low priority.
- **DataRefreshLog** -- Write-heavy, read-rare. Stays in DB.

### Rules Engine Simplification

The RulesEngine currently maintains its own `_hero_name_to_id`, `_hero_id_to_name`, `_item_name_to_id` dicts loaded via `init_lookups()`. With DataCache, these become fully redundant:

```python
# BEFORE (current):
class RulesEngine:
    async def init_lookups(self, db): ...       # loads from DB
    async def refresh_lookups(self, db): ...    # reloads from DB
    def _hero_id(self, name): ...               # reads from internal dict
    def _item_id(self, internal_name): ...      # reads from internal dict

# AFTER (with cache):
class RulesEngine:
    def __init__(self, cache: DataCache):
        self.cache = cache
    # No init/refresh needed -- cache is always current
    def _hero_id(self, name): return self.cache.hero_name_to_id(name)
    def _item_id(self, name): return self.cache.item_name_to_id(name)
    def _hero_name(self, hero_id): return self.cache.hero_id_to_name(hero_id)
```

This eliminates `init_lookups()`, `refresh_lookups()`, the `_rules.refresh_lookups(session)` call in `refresh.py`, and the circular import from `refresh.py` -> `api.routes.recommend`.

### Refresh Lifecycle

```
Startup:
  1. create tables, seed_if_empty()
  2. data_cache.load(session)        # heroes + items into memory
  3. RulesEngine(cache=data_cache)   # rules reads from cache, no init_lookups
  4. Start scheduler, WS broadcast

Every 6 hours (refresh_all_data):
  1. Fetch from OpenDota, upsert to DB
  2. data_cache.refresh(session)     # atomic swap of in-memory dicts
  3. (rules engine automatically sees new data via cache reference)

Per request (/api/recommend):
  1. rules.evaluate(request)         # reads cache (0 DB queries)
  2. context_builder.build(...)      # hero/item lookups from cache, matchup from DB
  3. llm.generate(user_message)      # no DB
  4. recommender._validate_item_ids()# reads cache (0 DB queries)

  Total DB queries reduced from 12-20 to 1-5 (only matchup + popularity lookups)
```

### Serialization for API Routes

The `/api/heroes` and `/api/items` endpoints currently return SQLAlchemy model instances that Pydantic serializes via `from_attributes=True`. With frozen dataclasses, the response models need a slight adapter:

```python
# Option A: Make HeroCached fields match HeroResponse exactly
# Then in the route:
@router.get("/heroes", response_model=list[HeroResponse])
async def list_heroes():
    heroes = data_cache.get_all_heroes()
    return [HeroResponse(**h.__dict__) for h in heroes]  # dataclass __dict__ works

# Option B: Return dicts directly
@router.get("/heroes")
async def list_heroes():
    return [asdict(h) for h in data_cache.get_all_heroes()]
```

Option A is cleaner -- keeps Pydantic validation on the response boundary.

---

## 4. Store Subscription Consolidation

### Problem

Two hooks independently subscribe to `gsiStore` with the same pattern:
- `useGsiSync` -- subscribes to `gsiStore`, writes to `gameStore` (hero, role) and `recommendationStore` (purchased items)
- `useAutoRefresh` -- subscribes to `gsiStore`, writes to `recommendationStore`, `refreshStore`, and `gameStore` (lane result)

Both are activated in `App.tsx` at the top level. Both use `useGsiStore.subscribe()` outside the render cycle. This creates:
1. **Two independent subscription callbacks** firing on every gsiStore update (1Hz from WebSocket)
2. **Potential ordering issues** -- useGsiSync sets hero/role, useAutoRefresh checks hero/role to decide whether to fire refresh. If useAutoRefresh fires first, it may skip because hero isn't set yet.
3. **TriggerEvent type duplication** -- defined identically in both `src/utils/triggerDetection.ts` (lines 17-25) and `src/stores/refreshStore.ts` (lines 3-11)

### Recommended Architecture

Merge into a single `useGameIntelligence` hook that handles all gsiStore-to-application-state bridging in one subscription callback with explicit ordering.

**New file: `src/hooks/useGameIntelligence.ts`**

```
useGameIntelligence(heroes: Hero[])
  |
  +-- Single gsiStore.subscribe() callback:
  |     1. Guard: gsiStatus !== "connected" => return
  |     2. Handle reconnect: sync prev state to avoid false triggers
  |     3. Hero auto-detection (from useGsiSync)
  |     4. Role inference (from useGsiSync)
  |     5. Playstyle auto-suggest (NEW v3.0 feature)
  |     6. Item auto-marking (from useGsiSync)
  |     7. Guard: game_state !== GAME_IN_PROGRESS => return
  |     8. Lane auto-detection at 10:00 (from useAutoRefresh)
  |     9. Event detection + cooldown + refresh (from useAutoRefresh)
  |
  +-- Single recommendationStore.subscribe() callback:
  |     Cooldown reset on manual recommend complete (from useAutoRefresh)
  |
  +-- Single 1Hz interval:
        Cooldown tick + queued event drain (from useAutoRefresh)
```

The explicit ordering within a single callback guarantees that hero/role are set before event detection checks them.

### Integration Points

**Files to create:**

| File | Purpose |
|------|---------|
| `src/hooks/useGameIntelligence.ts` | Consolidated GSI sync + auto-refresh + playstyle suggest |
| `src/hooks/useGameIntelligence.test.ts` | Tests migrated from useGsiSync.test.ts + new tests |

**Files to modify:**

| File | Change |
|------|--------|
| `src/App.tsx` | Replace `useGsiSync(heroes)` + `useAutoRefresh()` with single `useGameIntelligence(heroes)` call |
| `src/stores/refreshStore.ts` | Remove duplicate `TriggerEvent` interface (lines 3-11), import from `src/utils/triggerDetection.ts` instead |

**Files to delete:**

| File | Reason |
|------|--------|
| `src/hooks/useGsiSync.ts` | All logic absorbed into useGameIntelligence |
| `src/hooks/useAutoRefresh.ts` | All logic absorbed into useGameIntelligence |
| `src/hooks/useGsiSync.test.ts` | Replaced by useGameIntelligence.test.ts |

**Test files to update:**

| File | Change |
|------|--------|
| `src/stores/refreshStore.test.ts` | Update import path for TriggerEvent if referenced |
| `src/hooks/useWebSocket.test.ts` | No change needed (independent) |

### TriggerEvent Dedup Detail

Currently `TriggerEvent` is defined in two places with identical shape:

```typescript
// src/utils/triggerDetection.ts (lines 17-25) -- canonical, exported alongside detectTriggers()
export interface TriggerEvent {
  type: "death" | "gold_swing" | "tower_kill" | "roshan_kill" | "phase_transition";
  message: string;
}

// src/stores/refreshStore.ts (lines 3-11) -- duplicate
export interface TriggerEvent {
  type: "death" | "gold_swing" | "tower_kill" | "roshan_kill" | "phase_transition";
  message: string;
}
```

Fix: Delete the definition in `refreshStore.ts` and add `import type { TriggerEvent } from "../utils/triggerDetection"` at the top. The store's `queueEvent` action type and `queuedEvent` state type both reference this interface.

---

## 5. Playstyle Auto-Suggest (New Feature)

### Current Gap

When GSI detects a hero, `useGsiSync` auto-sets hero and infers role via `inferRole()`. But playstyle is never auto-suggested, leaving the user to manually select it even during live games when GSI has already identified hero and role.

### Architecture

Add a `suggestPlaystyle(heroId: number, role: number): string | null` function that maps hero + role to the most common playstyle. This fires in `useGameIntelligence` immediately after role inference succeeds.

**New file: `src/utils/playstyleSuggestion.ts`**

```typescript
/**
 * Hero+role -> default playstyle mapping.
 * Only populated for heroes with a clear "obvious" playstyle.
 * Returns null for ambiguous cases -- user selects manually.
 */
const HERO_PLAYSTYLE_MAP: Record<number, Record<number, string>> = {
  // Pos 1 carries
  1:  { 1: "Farm-first" },    // Anti-Mage
  44: { 1: "Aggressive" },    // Phantom Assassin
  81: { 1: "Split-push" },    // Terrorblade
  // Pos 2 mids
  11: { 2: "Tempo" },         // Shadow Fiend
  74: { 2: "Ganker" },        // Invoker
  // ... etc, ~50-80 entries covering common heroes
};

export function suggestPlaystyle(heroId: number, role: number): string | null {
  return HERO_PLAYSTYLE_MAP[heroId]?.[role] ?? null;
}
```

**Integration in `useGameIntelligence`:**

After role inference succeeds, and only if playstyle is currently null (user hasn't manually chosen):
```typescript
const playstyle = suggestPlaystyle(hero.id, role);
if (playstyle !== null && useGameStore.getState().playstyle === null) {
  useGameStore.getState().setPlaystyle(playstyle);
}
```

This is a soft suggest -- never overwrites user selection. The `playstyle === null` guard ensures manual choices are respected.

### Files

| File | Status |
|------|--------|
| `src/utils/playstyleSuggestion.ts` | NEW |
| `src/hooks/useGameIntelligence.ts` | Modified (adds call after role inference) |

---

## 6. Screenshot KDA/Level Feed (New Feature)

### Current Gap

The screenshot parser extracts `kills`, `deaths`, `assists`, and `level` per parsed hero (see `ParsedHero` in `src/types/screenshot.ts` and `VisionHero` in `backend/engine/schemas.py`). However, the `handleApply` callback in `ScreenshotParser.tsx` only applies:
- Enemy hero opponents (lines 102-107)
- Enemy items spotted (lines 110-114)

KDA and level data is parsed and displayed but never fed into the recommendation context. This means Claude does not know if an enemy is fed (10/1) or behind (1/8) when reasoning about items.

### Recommended Architecture (Path A: Request-level context)

Add an optional `enemy_context` field to `RecommendRequest` that carries enemy KDA/level data. The context builder includes this as a "## Enemy Team Status" prompt section when present.

**Schema changes (`backend/engine/schemas.py`):**

```python
class EnemyContext(BaseModel):
    """Per-enemy hero context from screenshots."""
    hero_id: int
    kills: int | None = None
    deaths: int | None = None
    assists: int | None = None
    level: int | None = None

class RecommendRequest(BaseModel):
    # ... existing fields ...
    enemy_context: list[EnemyContext] = Field(default_factory=list)
```

**Context builder addition (`backend/engine/context_builder.py`):**

New method `_build_enemy_context_section()` that produces:
```
## Enemy Team Status
- Phantom Assassin: 8/2/3, Level 15 (fed -- high threat, prioritize defensive items)
- Lion: 1/5/6, Level 10 (behind -- lower threat)
```

This section goes between "## Lane Opponents" and "## Mid-Game Update" in the prompt.

**Frontend changes:**

In `ScreenshotParser.tsx` `handleApply`, collect KDA/level from parsedHeroes and store in gameStore. Then the next recommendation request (manual or auto-refresh) includes this data.

Option: Add `enemyContext` field to gameStore to persist across re-evaluations:
```typescript
// gameStore addition
enemyContext: EnemyContext[];
setEnemyContext: (ctx: EnemyContext[]) => void;
```

### Integration Points

| File | Change |
|------|--------|
| `backend/engine/schemas.py` | Add `EnemyContext` model, add `enemy_context` field to `RecommendRequest` |
| `backend/engine/context_builder.py` | Add `_build_enemy_context_section()`, include in assembled prompt |
| `frontend/src/types/recommendation.ts` | Add `EnemyContext` interface, add `enemy_context` to `RecommendRequest` |
| `frontend/src/stores/gameStore.ts` | Add `enemyContext` state + `setEnemyContext` action |
| `frontend/src/components/screenshot/ScreenshotParser.tsx` | In `handleApply`, build EnemyContext from parsedHeroes with KDA/level |
| `frontend/src/hooks/useRecommendation.ts` | Include `gameStore.enemyContext` in request payload |
| `frontend/src/hooks/useGameIntelligence.ts` | Include `gameStore.enemyContext` in auto-refresh request payload |

---

## 7. Session Safety Fix (refresh_lookups)

### Current Problem

In `backend/data/refresh.py` line 122:
```python
await _rules.refresh_lookups(session)
```

Two issues:
1. Reuses the `session` that just committed the data refresh. If `refresh_lookups` fails, the session may be in an inconsistent state.
2. Circular import: `refresh.py` imports from `api.routes.recommend` to access the `_rules` singleton.

### Resolution via DataCache

With the in-memory cache architecture, this problem disappears entirely:
1. `data_cache` is a module-level singleton in `data/cache.py` (no circular imports)
2. `refresh.py` calls `data_cache.refresh(session)` -- this opens a fresh read
3. Rules engine reads from cache automatically (no explicit refresh call)
4. The `from api.routes.recommend import _rules` circular import in refresh.py is deleted

No interim fix needed if cache is implemented first (which is the recommended build order).

---

## 8. Data Flow Diagrams

### Recommendation Hot Path (After Cache)

```
Frontend                          Backend
   |                                 |
   |-- POST /api/recommend --------->|
   |                                 |-- rules.evaluate(request)     [cache, 0 DB]
   |                                 |-- context_builder.build(...)
   |                                 |     +-- cache.get_hero(id)    [cache, 0 DB]
   |                                 |     +-- get_or_fetch_matchup  [DB, stale-while-revalidate]
   |                                 |     +-- cache.get_items(...)  [cache, 0 DB]
   |                                 |     +-- get_hero_item_pop     [DB, stale-while-revalidate]
   |                                 |-- llm.generate(msg)           [Claude API, 10s timeout]
   |                                 |-- recommender._validate(...)  [cache, 0 DB]
   |<-- RecommendResponse -----------|
```

### GSI Live State Flow (After Consolidation)

```
Dota 2 Client --> POST /gsi --> gsi_state_manager --> ws_manager (1Hz broadcast)
                                                          |
                                                     WebSocket
                                                          |
                                                     useWebSocket hook
                                                          |
                                                     gsiStore.updateLiveState
                                                          |
                                              useGameIntelligence (single subscription)
                                                          |
                                    +---------+-----------+-----------+----------+
                                    |         |           |           |          |
                                  Hero     Role      Playstyle    Item       Event
                                  detect   infer     suggest      marking    detection
                                  (gameS)  (gameS)   (gameS)     (recS)    (refreshS)
                                                                               |
                                                                        api.recommend()
                                                                        (if cooldown clear)
```

### Screenshot Parse + KDA Feed Flow (After v3.0)

```
User pastes screenshot --> ScreenshotParser
                              |
                         POST /api/parse-screenshot
                              |
                         Claude Vision --> ParsedHero[] with KDA/level
                              |
                         handleApply()
                              |
                    +--------------------+-------------------+
                    |                    |                   |
              setOpponent(i, hero)  setEnemyItems([])  setEnemyContext([{hero_id, kda, level}])
              (gameStore)           (gameStore)         (gameStore)
                    |                    |                   |
                    +--------------------+-------------------+
                              |
                         recommend() --> POST /api/recommend
                              |             includes enemy_context
                         context_builder adds "## Enemy Team Status" section
```

---

## 9. Component Boundaries (New vs Modified)

### New Components/Files

| Component | Layer | Purpose |
|-----------|-------|---------|
| `backend/data/cache.py` | Backend | In-memory hero/item cache with frozen dataclasses |
| `frontend/src/hooks/useGameIntelligence.ts` | Frontend | Consolidated GSI sync + auto-refresh + playstyle suggest |
| `frontend/src/utils/playstyleSuggestion.ts` | Frontend | Hero+role to default playstyle mapping |

### Modified Components (Cache Integration)

| File | Change Scope | Risk |
|------|-------------|------|
| `backend/main.py` | Add cache init, simplify rules init | Low -- additive |
| `backend/data/refresh.py` | Add cache refresh, remove circular import | Low -- simplification |
| `backend/engine/rules.py` | Take cache ref, remove init/refresh_lookups | Medium -- interface change |
| `backend/engine/context_builder.py` | Replace 8+ DB calls with cache reads | Medium -- many call sites |
| `backend/engine/recommender.py` | Replace validation DB query with cache | Low -- single call site |
| `backend/api/routes/heroes.py` | Return from cache | Low -- simple swap |
| `backend/api/routes/items.py` | Return from cache | Low -- simple swap |
| `backend/api/routes/recommend.py` | Wire cache into constructors | Low -- initialization only |
| `backend/data/matchup_service.py` | Remove get_relevant_items, get_neutral_items_by_tier (moved to cache) | Low -- function relocation |

### Modified Components (Store Consolidation)

| File | Change Scope | Risk |
|------|-------------|------|
| `frontend/src/App.tsx` | Replace 2 hook calls with 1 | Low |
| `frontend/src/stores/refreshStore.ts` | Import TriggerEvent instead of defining | Low |

### Deleted Components

| File | Reason |
|------|--------|
| `frontend/src/hooks/useGsiSync.ts` | Absorbed into useGameIntelligence |
| `frontend/src/hooks/useAutoRefresh.ts` | Absorbed into useGameIntelligence |
| `frontend/src/hooks/useGsiSync.test.ts` | Tests migrated to useGameIntelligence.test.ts |

### Modified Components (Design System -- all visual, no logic)

Every frontend component with Tailwind classes needs class updates. The highest-impact files ordered by change density:

| Component | Key Changes |
|-----------|-------------|
| `globals.css` | Complete rewrite (new tokens) |
| `main.tsx` | Font import swap |
| `Header.tsx` | SVG gradient, bg, border, text colors |
| `Sidebar.tsx` | Background, borders, section headers |
| `ItemCard.tsx` | Priority borders, corners, purchased overlay |
| `ScreenshotParser.tsx` | Modal, upload zone, buttons |
| `GetBuildButton.tsx` | Primary CTA colors |
| `GameStatePanel.tsx` | Toggle buttons, sliders |
| `HeroPicker.tsx` + all pickers | Dropdown bg, hover, selected |
| `SettingsPanel.tsx` | Slide-over panel |
| `AutoRefreshToast.tsx` | Toast container |
| `GsiStatusIndicator.tsx` | Status dot colors |
| `GameClock.tsx` | Text colors |
| `LiveStatsBar.tsx` | Stat display colors |
| `constants.ts` | LANE_RESULT_OPTIONS class strings |

### Modified Components (KDA Feed)

| File | Change |
|------|--------|
| `backend/engine/schemas.py` | Add EnemyContext model + field |
| `backend/engine/context_builder.py` | Add enemy context prompt section |
| `frontend/src/types/recommendation.ts` | Add EnemyContext type |
| `frontend/src/stores/gameStore.ts` | Add enemyContext state |
| `frontend/src/components/screenshot/ScreenshotParser.tsx` | Build + apply EnemyContext in handleApply |
| `frontend/src/hooks/useRecommendation.ts` | Include enemyContext in request |

---

## 10. Suggested Build Order

Based on dependency analysis, the work should be ordered:

### Phase 1: In-Memory Cache (Backend only, no frontend changes)
**Rationale:** Pure backend change with no visual impact. Can be tested independently via existing test suite. Eliminates the session safety bug as a side effect. Simplifies the rules engine interface. Provides performance foundation for everything else.

Build steps:
1. Create `backend/data/cache.py` with DataCache + frozen dataclasses
2. Wire into `main.py` lifespan (load at startup)
3. Wire into `refresh.py` (refresh on pipeline cycle, remove _rules circular import)
4. Migrate `rules.py` to take cache reference (remove init_lookups/refresh_lookups)
5. Migrate `context_builder.py` to use cache for all hero/item lookups
6. Migrate `recommender.py` _validate_item_ids to use cache
7. Migrate `api/routes/heroes.py` and `items.py` to serve from cache
8. Clean up `matchup_service.py` (remove relocated functions)
9. Run full test suite -- behavior must be identical

### Phase 2: Store Consolidation + TriggerEvent Dedup (Frontend, no visual changes)
**Rationale:** Structural refactor before the visual sweep. Doing this after cache means the backend is stable. Doing this before the design system migration means we are not simultaneously changing hook structure and all CSS classes.

Build steps:
1. Fix TriggerEvent dedup in `refreshStore.ts` (import from triggerDetection.ts)
2. Create `useGameIntelligence.ts` combining useGsiSync + useAutoRefresh logic
3. Add playstyle auto-suggest call after role inference
4. Create `playstyleSuggestion.ts` with hero+role mapping
5. Update `App.tsx` to use single `useGameIntelligence(heroes)` call
6. Migrate tests from useGsiSync.test.ts, add new test cases
7. Delete useGsiSync.ts, useAutoRefresh.ts, useGsiSync.test.ts

### Phase 3: Design System Migration (Frontend, visual only)
**Rationale:** Largest change surface but purely visual -- no logic changes. Can be done as a systematic sweep now that structural refactoring is complete. Hard cutover via @theme rewrite ensures no half-migrated state.

Build steps:
1. Install `@fontsource/newsreader` + `@fontsource/manrope`, remove old font packages
2. Update `main.tsx` font imports
3. Rewrite `globals.css` with complete new token system
4. Update App.tsx root classes
5. Sweep layout components (Header, Sidebar, MainPanel)
6. Sweep interactive primitives (buttons, pickers, selectors)
7. Sweep content components (ItemCard, phase cards, reasoning)
8. Sweep modals/overlays (ScreenshotParser, SettingsPanel)
9. Sweep status indicators and toasts
10. Update constants.ts color class references
11. Visual QA pass against DESIGN.md requirements

### Phase 4: Screenshot KDA Feed (Full stack, small scope)
**Rationale:** Depends on cache being in place for context builder. Small, targeted change across both layers. Natural final phase since it extends an existing feature.

Build steps:
1. Add `EnemyContext` model to backend schemas
2. Add `_build_enemy_context_section()` to context builder
3. Add `enemyContext` state to frontend gameStore
4. Update frontend recommendation types
5. Update ScreenshotParser handleApply to collect and store KDA/level
6. Update useRecommendation and useGameIntelligence to include in requests
7. Test end-to-end with a real screenshot

### Phase ordering rationale:
- **Cache before everything** -- Fixes session safety bug, simplifies rules engine, provides performance gains that benefit all subsequent work
- **Store consolidation before design** -- Changing hook structure while simultaneously changing all CSS classes is error-prone and hard to debug
- **Design system as its own phase** -- Largest change surface, easiest to visually QA in isolation
- **KDA feed last** -- Smallest scope, extends existing feature, benefits from all prior improvements

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Incremental Token Migration
**What:** Adding new design tokens alongside old ones and migrating component by component over multiple phases.
**Why bad:** Creates a period where both old (`bg-bg-primary`) and new (`bg-surface`) tokens coexist, making the UI inconsistent and debugging confusing. Half-migrated components look broken.
**Instead:** Hard cutover -- rewrite globals.css, then sweep all components in one phase. Tailwind v4 will flag missing utilities at build time, ensuring complete migration.

### Anti-Pattern 2: Cache-Then-DB Fallback
**What:** Reading from cache first, falling back to DB if cache miss.
**Why bad:** For hero/item data that is fully loaded at startup, a cache miss means the data genuinely does not exist -- not that it needs a DB lookup. Fallback paths add complexity without value and mask data issues.
**Instead:** Cache is authoritative for hero/item data. If it is not in cache, it does not exist. DB access for heroes/items should only happen during cache load/refresh.

### Anti-Pattern 3: Partial Hook Consolidation
**What:** Keeping useGsiSync and useAutoRefresh as separate hooks but sharing state through refs or a module-level object.
**Why bad:** Two subscriptions still fire independently at 1Hz. Ordering remains non-deterministic. Shared mutable state across hooks creates debugging nightmares.
**Instead:** Single hook, single subscription callback, explicit ordering within the callback body.

### Anti-Pattern 4: Maintaining Both Font Families During Migration
**What:** Installing Newsreader and Manrope while keeping Inter and JetBrains Mono "just in case."
**Why bad:** Four font families means ~800KB+ of font files, confusing `font-*` token semantics, and developers unsure which to use.
**Instead:** Clean swap. Remove old, install new, update all references in one phase.

---

## Sources

- Direct codebase analysis of all files listed in this document
- Tailwind CSS v4 `@theme` block documentation (CSS-first configuration, no tailwind.config)
- DESIGN.md at repo root (canonical "Tactical Relic Editorial" design specification)
- PROJECT.md in .planning/ (v3.0 milestone context, tech debt inventory)
- Existing .planning/research/ARCHITECTURE.md (v2.0 architecture reference)

---
*Architecture research for: Prismlab v3.0 Design Overhaul & Performance*
*Researched: 2026-03-26*

# Technology Stack: v3.0 Design Overhaul & Performance

**Project:** Prismlab v3.0
**Researched:** 2026-03-26
**Confidence:** HIGH
**Scope:** Stack ADDITIONS/CHANGES only for v3.0 features. Existing validated stack (React 19, Vite 8, Tailwind v4.2, Zustand 5, FastAPI, SQLAlchemy, SQLite, Claude API, WebSocket, GSI, Pillow) is NOT re-evaluated.

---

## Recommended Stack Changes

### Font Packages (REPLACE existing)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `@fontsource-variable/newsreader` | ^5.2.10 | Display/headline font (DESIGN.md "chiseled engravings") | Variable font = single file serves all weights (300-700) with optical sizing (`opsz`) axis. DESIGN.md requires tight letter-spacing (-0.02em) and display-scale headlines; the `opsz` axis automatically adjusts stroke contrast and spacing at different font sizes, which fixed-weight Newsreader cannot do. Fontsource packages are already the established import pattern in this codebase. |
| `@fontsource-variable/manrope` | ^5.2.8 | Body/label/tactical data font | Variable font supports weights 200-800 in one file. DESIGN.md specifies distinct Manrope weights for body-sm, label-md, and technical data. Variable version keeps bundle smaller than importing 6+ discrete weight CSS files. Manrope supports `tnum` (tabular numbers) feature settings for stat displays, replacing JetBrains Mono's role. |

**REMOVE:**
- `@fontsource/inter` (^5.2.8) -- replaced by Manrope for body text
- `@fontsource/jetbrains-mono` (^5.2.8) -- replaced by Manrope with `font-variant-numeric: tabular-nums` for stats. DESIGN.md does not specify any monospace font.

**Confidence:** HIGH -- both packages verified on npm registry (latest versions confirmed via `npm info`). Variable font versions confirmed available. Project already imports `@fontsource/*` packages via Vite CSS pipeline without issues.

---

### CSS Architecture (NO new packages -- Tailwind v4 native)

Every visual requirement in DESIGN.md maps to existing Tailwind v4 capabilities. No CSS libraries, plugins, or PostCSS tools are needed.

| DESIGN.md Requirement | Tailwind v4 Implementation | Why No Package |
|----------------------|---------------------------|----------------|
| Custom color palette (obsidian/crimson/gold/slate) | `@theme` directive with `--color-*` variables in globals.css | Current globals.css already uses this exact pattern for `--color-cyan-accent`, `--color-radiant`, `--color-dire`, `--color-bg-primary`. Just swap values. `@theme` creates utility classes (`bg-surface`, `text-on-surface`) automatically. |
| Surface hierarchy (7 tones from #0E0E0E to #353534) | `--color-surface-*` namespace in `@theme` | Tailwind v4 `@theme` supports arbitrary naming depth. `--color-surface-container-lowest` creates `bg-surface-container-lowest` utility. |
| Font families (Newsreader display, Manrope body) | `--font-display` and `--font-body` in `@theme` | Already using `--font-body` and `--font-stats` in current globals.css. Same pattern, new values. |
| Font optical sizing / variation settings | `--font-display--font-variation-settings: "opsz" 32` in `@theme` | Tailwind v4 supports companion `--font-*--font-variation-settings` and `--font-*--font-feature-settings` variables alongside each `--font-*` entry. Official docs confirm this syntax. |
| Ambient glow shadows (crimson aura, 32px blur, 5% opacity) | `@theme` with `--shadow-*` variables | Tailwind v4 custom shadows: `--shadow-glow: 0 0 32px oklch(68% 0.08 25 / 0.05)` creates `shadow-glow` utility class. Shadow-color utilities (`shadow-red-500/50`) compose with shadow shapes. Verified in official Tailwind v4 box-shadow docs. |
| Backdrop blur ("blood-glass" overlay, 12px blur) | `backdrop-blur-md` utility (12px) | Built into Tailwind v4 core. DESIGN.md specifies `backdrop-blur` of 12px, which is the exact value of `backdrop-blur-md`. |
| 0px corners (sharp, non-negotiable) | Reset `--radius-*: initial` in `@theme` or apply `rounded-none` globally | Setting `--radius-*: initial` in `@theme` removes all default border-radius utilities, making `rounded-none` the only option. Alternatively, a single CSS rule `* { border-radius: 0; }` achieves this globally. |
| Ghost borders (15% opacity outlines) | `outline` utilities with opacity modifiers | `outline outline-1 outline-[#5A403E]/15` maps directly to DESIGN.md ghost border spec. No plugin needed. |
| Parchment noise/grain texture | SVG `feTurbulence` filter as data URI | Pure CSS: `background-image: url("data:image/svg+xml,<svg>...</svg>")` with `feTurbulence` noise at low opacity. ~200 bytes of inline SVG. Apply via `::after` pseudo-element on the base `#131313` surface. No asset, no package, no build step. |
| "Gold leaf" shimmer gradient | `bg-gradient-to-r` + `from-secondary` + `to-secondary-fixed-dim` | Tailwind v4 gradient utilities work with custom `@theme` colors. DESIGN.md gold shimmer is a linear gradient from `secondary` to `secondary_fixed_dim`. |
| No 1px borders (the "No-Line Rule") | Content separation via background color shifts only | This is a design discipline, not a technical requirement. Existing Tailwind background utilities (`bg-surface-container-low`, `bg-surface-container-lowest`) handle section separation. |

**Confidence:** HIGH -- all capabilities verified against Tailwind v4.2 official documentation. Current globals.css already uses `@theme` for custom colors and fonts; this is a value replacement, not an architecture change.

---

### Backend In-Memory Data Cache (NO new packages)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python `dict` + module-level singleton | stdlib | In-memory hero/item data cache to eliminate DB queries on hot path | Pattern already proven twice in this codebase: `RulesEngine` caches hero name-to-id and item name-to-id dicts at startup; `ResponseCache` uses a dict with TTL for recommendation responses. Extend with a dedicated `DataCache` class holding the full hero and item catalogs. |

**Why no external package:**
1. **Single-process uvicorn** -- no cross-process cache sharing needed
2. **Data refreshes on a schedule** (every 6h via APScheduler) -- no per-key TTL eviction needed
3. **Full dataset fits in ~2MB** (~140 heroes + ~300 items as Python dicts) -- no memory pressure concerns
4. **Refresh is atomic** -- pipeline loads new data, then swaps the entire cache dict
5. **`cachetools`** adds a dependency for TTL/LRU eviction we do not need
6. **Redis** adds a Docker container, network hop, and serialization overhead for 2MB of data
7. **`fastapi-cache`** is for response caching (which `ResponseCache` already handles)

**What gets cached:**
- `heroes_by_id: dict[int, HeroData]` -- hero ID to hero data (name, attr, roles, stats, URLs)
- `items_by_id: dict[int, ItemData]` -- item ID to item data (name, cost, components, bonuses, URLs)
- `items_by_internal_name: dict[str, ItemData]` -- internal name lookup (for GSI item matching)
- `neutral_items_by_tier: dict[int, list[ItemData]]` -- pre-grouped neutral items

**What changes in existing code:**

| File | Current (DB query per request) | After (cache read) |
|------|-------------------------------|-------------------|
| `context_builder.py` `_get_hero()` | `db.execute(select(Hero).where(Hero.id == hero_id))` | `data_cache.get_hero(hero_id)` |
| `context_builder.py` `_extract_top_items()` | `db.execute(select(Item))` -- loads ALL items every call | `data_cache.get_item_name(item_id)` |
| `context_builder.py` `_build_popularity_section()` | `db.execute(select(Item))` -- loads ALL items again | `data_cache.get_item_name(item_id)` |
| `context_builder.py` `_build_neutral_catalog()` | Calls `get_neutral_items_by_tier(db)` which queries DB | `data_cache.neutral_items_by_tier` |
| `matchup_service.py` `get_relevant_items()` | `db.execute(select(Item).where(...))` with cost filter | `data_cache.get_relevant_items(role)` |
| `matchup_service.py` `get_neutral_items_by_tier()` | `db.execute(select(Item).where(is_neutral, tier))` | `data_cache.neutral_items_by_tier` |

**What does NOT change:**
- `matchup_service.get_or_fetch_matchup()` -- hero-pair matchup data is fetched on demand from OpenDota, cached in SQLite with stale-while-revalidate. Not suitable for startup preload (would require ~140x140 = 19,600 API calls).
- `HeroItemPopularity` -- per-hero, fetched on demand, already stale-while-revalidate cached in SQLite. Same API call concern.
- `ResponseCache` -- stays as-is, caches full recommendation responses. Orthogonal to data cache.
- `RulesEngine` lookups -- keep as-is. The rules engine only needs name-to-id mappings, not full hero/item objects. Extending `DataCache` to also serve the rules engine would create coupling between the data layer and the engine layer.

**Lifecycle:**
1. App startup (`lifespan()` in `main.py`): `await data_cache.load(session)` after `seed_if_empty()` and `_rules.init_lookups(session)`
2. Data refresh (`refresh_all_data()` in `data/refresh.py`): `await data_cache.reload(session)` after `_rules.refresh_lookups(session)`
3. Request handling: `data_cache.get_hero(id)` / `data_cache.get_item(id)` -- plain dict lookups, no async, no DB

**Confidence:** HIGH -- pattern proven in codebase. No new dependencies. Python stdlib dict is the correct tool for a static dataset of this size in a single-process server.

---

### Frontend Store/Hook Consolidation (NO new packages)

| Change | Approach | Why |
|--------|----------|-----|
| Merge `useGsiSync` + `useAutoRefresh` into `useGsiLive` | Single hook, single `useGsiStore.subscribe()` call | Both hooks independently subscribe to `gsiStore` via `useEffect` + `.subscribe()`, both use refs for mutable state, both access `useGameStore` and `useRecommendationStore`. Two separate subscriptions means every GSI update (arriving at 2Hz from WebSocket) is processed twice by two independent listeners. Merging into one subscription halves the processing and eliminates the TriggerEvent deduplication issue (which exists because both hooks see the same state transitions independently and can race). |
| Keep stores separate | `gsiStore`, `gameStore`, `recommendationStore`, `refreshStore` remain 4 stores | Zustand's recommended pattern is separate stores for separate domains. The problem is not the store count -- it is subscription duplication in hooks. Merging stores would create a mega-store violating single-responsibility and causing unnecessary re-renders across unrelated UI components. The Zustand slices pattern is for when you want one store with multiple concerns; that is the opposite of what is needed here. |

**Confidence:** HIGH -- this is a refactoring decision, not a library decision. Zustand 5's `.subscribe()` API is stable.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Fonts | `@fontsource-variable/*` | Google Fonts CDN `@import url()` | Self-hosted via npm = no external CDN dependency at runtime. Docker on Unraid has no guaranteed fast CDN access. Consistent with existing import pattern. No FOUT from DNS lookup. |
| Fonts | `@fontsource-variable/*` | Static `@fontsource/*` (non-variable) | Would need 5+ separate CSS imports per font (400, 500, 600, 700, italic variants). Variable font = 1 file per family, smaller total bundle, optical sizing axis. |
| CSS shadows/glows | Tailwind v4 `@theme --shadow-*` | `tailwindcss-glow` plugin | Third-party plugin for something achievable with 3 lines in `@theme`. Plugin may lag behind Tailwind v4.x releases. The glow effect is just `box-shadow` with large blur radius and tinted color. |
| Noise texture | Inline SVG `feTurbulence` data URI | Static `noise.png` asset | SVG data URI is ~200 bytes vs PNG at 50KB+. SVG scales to any resolution. No additional asset pipeline or CDN path. |
| Noise texture | Inline SVG `feTurbulence` data URI | CSS `background: repeating-conic-gradient(...)` | Conic gradient noise is a clever hack but produces geometric patterns, not organic grain. `feTurbulence` produces actual Perlin noise matching the "parchment" feel DESIGN.md requests. |
| Backend cache | Python dict singleton | `cachetools.TTLCache` | TTL eviction is unnecessary -- data refreshes atomically on a schedule, not per-key. Adds dependency for unneeded functionality. |
| Backend cache | Python dict singleton | Redis | Over-engineered. Adds Docker container, network hop, serialization for 2MB of static data in a single-process server. |
| Backend cache | Python dict singleton | `fastapi-cache` decorator | Designed for response caching via decorator pattern. Not the right abstraction for a startup-loaded data catalog with explicit reload. |
| Store consolidation | Merge hooks, keep stores | Merge into Zustand slices pattern | Stores are correctly separated. Problem is hook subscription duplication, not store boundaries. |
| Design tokens | Tailwind `@theme` block | Style Dictionary / Theo | Overkill for a single-app system. The `@theme` block IS the token file. |
| Animations | Tailwind `transition-*` + CSS `@keyframes` | Framer Motion | DESIGN.md specifies hover states and "charging" button effects, not complex animations. Framer Motion adds 32KB+ to bundle for what CSS transitions handle natively. |

---

## Installation

```bash
# In prismlab/frontend/

# Remove old fonts
npm uninstall @fontsource/inter @fontsource/jetbrains-mono

# Add new variable fonts
npm install @fontsource-variable/newsreader @fontsource-variable/manrope
```

**No backend pip changes.** No new Docker dependencies. No infrastructure changes.

**Net dependency change:** Remove 2 npm packages, add 2 npm packages. Zero new backend packages.

---

## Integration Points

### 1. Font Imports (main.tsx)

**Replace:**
```typescript
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "@fontsource/jetbrains-mono/400.css";
import "@fontsource/jetbrains-mono/500.css";
```

**With:**
```typescript
import "@fontsource-variable/newsreader";
import "@fontsource-variable/manrope";
```

Two imports replace six. Variable fonts include all weights in a single file each.

### 2. Theme Variables (globals.css)

**Replace** the entire `@theme` block. The new block defines:

```css
@theme {
  /* === Surface Hierarchy (DESIGN.md Section 2) === */
  --color-surface: #131313;
  --color-surface-dim: #131313;
  --color-surface-bright: #3A3939;
  --color-surface-container-lowest: #0E0E0E;
  --color-surface-container-low: #1C1B1B;
  --color-surface-container: #201F1F;
  --color-surface-container-high: #2B2A29;
  --color-surface-container-highest: #353534;

  /* === Accent Colors === */
  --color-primary: #FFB4AC;
  --color-primary-container: #B22222;
  --color-secondary: #FFDB3C;
  --color-secondary-container: #FFDB3C;
  --color-secondary-fixed: #FFE16D;
  --color-secondary-fixed-dim: #D4A017;
  --color-tertiary: #8DA4B8;
  --color-tertiary-container: #4E5E6D;

  /* === Game Colors (preserved) === */
  --color-radiant: #6AFF97;
  --color-dire: #FF5555;

  /* === Text === */
  --color-on-surface: #E5E2E1;
  --color-on-surface-variant: #E2BEBA;
  --color-outline-variant: #5A403E;

  /* === Attribute Colors (preserved) === */
  --color-attr-str: oklch(68% 0.19 25);
  --color-attr-agi: oklch(75% 0.18 145);
  --color-attr-int: oklch(70% 0.15 250);
  --color-attr-all: oklch(80% 0.1 90);

  /* === Typography === */
  --font-display: "Newsreader Variable", Georgia, serif;
  --font-display--font-variation-settings: "opsz" 32;
  --font-body: "Manrope Variable", system-ui, sans-serif;
  --font-body--font-feature-settings: "tnum";

  /* === Ambient Glow Shadows === */
  --shadow-glow: 0 0 32px rgb(255 180 172 / 0.05);
  --shadow-glow-gold: 0 0 24px rgb(255 219 60 / 0.08);
  --shadow-glow-active: 0 0 16px rgb(178 34 34 / 0.15);

  /* === Disable all rounded corners === */
  --radius-*: initial;
}
```

**Key differences from current globals.css:**
- 7 surface tones replace 3 background colors
- Crimson/gold/slate accent palette replaces spectral cyan
- Newsreader + Manrope replace Inter + JetBrains Mono
- Custom shadow tokens for ambient glows
- All border-radius utilities disabled via `--radius-*: initial`
- Game colors (radiant/dire) and attribute colors preserved unchanged

### 3. Backend Data Cache (new file + startup wiring)

**New file:** `data/cache.py` with `DataCache` class

**Wire into `main.py` lifespan:**
```python
# After seed_if_empty() and _rules.init_lookups(session)
from data.cache import data_cache
await data_cache.load(session)
```

**Wire into `data/refresh.py` refresh_all_data():**
```python
# After _rules.refresh_lookups(session)
from data.cache import data_cache
await data_cache.reload(session)
```

**Modify `context_builder.py`:**
- Remove `db` parameter from `_get_hero()`, `_extract_top_items()`, `_build_popularity_section()`, `_build_neutral_catalog()`
- Replace SQLAlchemy queries with `data_cache.get_hero(id)` / `data_cache.get_item(id)` / `data_cache.neutral_items_by_tier`
- `build()` method still takes `db` parameter for matchup queries (those stay DB-backed)

### 4. Hook Consolidation

**Delete:** `useGsiSync.ts`, `useAutoRefresh.ts`
**Create:** `useGsiLive.ts` combining both
**Merge tests:** `useGsiSync.test.ts` + `useAutoRefresh.test.ts` into `useGsiLive.test.ts`
**Update:** `App.tsx` (or wherever hooks are mounted) to call `useGsiLive(heroes)` instead of separate `useGsiSync(heroes)` + `useAutoRefresh()`

---

## What NOT to Add

| Tempting Addition | Why Not |
|-------------------|---------|
| CSS-in-JS (styled-components, Emotion, Panda CSS) | Tailwind v4 `@theme` handles all design token needs. Adding CSS-in-JS creates two competing styling systems and increases bundle size. |
| Framer Motion / React Spring | DESIGN.md specifies hover states and "charging" button effects, not choreographed animations. CSS `transition` and `@keyframes` handle this. Adding Framer Motion adds 32KB+ gzipped for hover effects. |
| Design token package (Style Dictionary, Theo, Tokens Studio) | Overkill for a single-app design system with one consumer. The `@theme` block IS the token file. |
| Storybook | Not warranted for a single-developer project. The app itself is the component showcase. |
| PostCSS plugins (autoprefixer, postcss-nesting) | Tailwind v4 uses its own compiler via `@tailwindcss/vite`, bypassing PostCSS entirely. PostCSS plugins are not compatible with the Vite plugin integration path. |
| Icon library (Lucide, Heroicons, Phosphor) | DESIGN.md does not specify icon changes. Current app uses inline SVGs where needed. |
| `cachetools` or `aiocache` (Python) | Dict singleton is the correct tool for this use case. See Backend Cache section. |
| `@fontsource/newsreader` (non-variable static) | Variable version is strictly better: fewer files, optical sizing axis, full weight range in one import. |
| Tailwind CSS plugins (`@tailwindcss/typography`, `daisyui`) | DESIGN.md defines a bespoke design system incompatible with pre-built component libraries. Typography plugin's prose styles would conflict with the Newsreader/Manrope hierarchy. |
| CSS custom properties library (Open Props) | Would conflict with `@theme` definitions. The design system defines its own tokens; importing a generic token set creates naming collisions and unused values. |

---

## Version Compatibility Matrix

| Package | Version | Compatible With | Verified |
|---------|---------|----------------|----------|
| `@fontsource-variable/newsreader` | 5.2.10 | Vite 8, @tailwindcss/vite 4.2 | Yes -- fontsource packages are plain CSS + woff2 files, framework-agnostic |
| `@fontsource-variable/manrope` | 5.2.8 | Vite 8, @tailwindcss/vite 4.2 | Yes -- same as above |
| Tailwind v4.2 `@theme` | 4.2.2 (current) | All `--color-*`, `--font-*`, `--shadow-*`, `--radius-*` namespaces | Yes -- verified against official Tailwind v4.2 docs |
| Python dict (stdlib) | 3.13 | FastAPI, SQLAlchemy async | Yes -- stdlib, no version concern |
| Zustand `.subscribe()` | 5.0.12 (current) | React 19 | Yes -- already in production use by `useGsiSync` and `useAutoRefresh` |

---

## Summary of Changes from v2.0 Stack

| What | Change | Impact |
|------|--------|--------|
| Frontend: font packages | Replace `@fontsource/inter` + `@fontsource/jetbrains-mono` with `@fontsource-variable/newsreader` + `@fontsource-variable/manrope` | 2 packages swapped. Net zero dependency count. |
| Frontend: globals.css | Replace `@theme` block with expanded design tokens (surfaces, accents, fonts, shadows, radius reset) | Config change only. No structural CSS changes. |
| Frontend: main.tsx imports | 2 variable font imports replace 6 static weight imports | Simpler, smaller bundle. |
| Frontend: hooks | Merge `useGsiSync` + `useAutoRefresh` into `useGsiLive` | 2 files become 1. Halves GSI subscription overhead. |
| Backend: data cache | New `data/cache.py` module with dict-based hero/item cache | Eliminates ~8 DB queries per recommendation request. Zero new pip packages. |
| Backend: context_builder | Replace DB queries with cache reads | Removes `db` parameter from several internal methods. |
| Docker | No changes | Same containers, same ports, same volumes. |
| Infrastructure | No changes | No new services, no new ports, no new config files. |

**Total new dependencies: Zero.** Two npm packages swapped, zero pip packages added.

---

## Sources

- [Tailwind v4 Theme Variables](https://tailwindcss.com/docs/theme) -- HIGH confidence, official docs. Verified `@theme` directive, `--color-*`, `--font-*`, `--shadow-*`, `--radius-*` namespaces, and companion `--font-*--font-variation-settings` syntax.
- [Tailwind v4 Font Family](https://tailwindcss.com/docs/font-family) -- HIGH confidence, official docs. Verified `--font-*` custom font pattern and `@font-face` integration.
- [Tailwind v4 Box Shadow](https://tailwindcss.com/docs/box-shadow) -- HIGH confidence, official docs. Verified custom `--shadow-*` definitions, shadow-color composition, and arbitrary value syntax.
- [Tailwind v4 Backdrop Blur](https://tailwindcss.com/docs/backdrop-filter-blur) -- HIGH confidence, official docs. Confirmed `backdrop-blur-md` = 12px.
- [@fontsource-variable/newsreader on npm](https://www.npmjs.com/package/@fontsource-variable/newsreader) -- HIGH confidence, npm registry. Version 5.2.10 confirmed via `npm info`.
- [@fontsource-variable/manrope on npm](https://www.npmjs.com/package/@fontsource-variable/manrope) -- HIGH confidence, npm registry. Version 5.2.8 confirmed via `npm info`.
- [Fontsource Installation Guide](https://fontsource.org/docs/getting-started/install) -- HIGH confidence, official docs. Confirmed variable font import pattern.
- [Zustand GitHub](https://github.com/pmndrs/zustand) -- HIGH confidence, official repo. Store separation and `.subscribe()` patterns.
- [CSS Grainy Gradients (CSS-Tricks)](https://css-tricks.com/grainy-gradients/) -- MEDIUM confidence, established technique. SVG `feTurbulence` noise texture approach.
- [FastAPI Caching Discussion](https://github.com/fastapi/fastapi/issues/3044) -- MEDIUM confidence. Confirms `functools.lru_cache` and dict-based caching are safe in single-process FastAPI.

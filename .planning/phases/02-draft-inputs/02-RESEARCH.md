# Phase 2: Draft Inputs - Research

**Researched:** 2026-03-21
**Domain:** React UI components (selectors, toggle groups, multi-slot pickers) + Zustand store extension
**Confidence:** HIGH

## Summary

Phase 2 is a frontend-only UI composition phase. All required libraries are already installed from Phase 1 (React 19, Zustand 5, Tailwind v4, Fuse.js). No new dependencies are needed. The work involves: (1) extending the Zustand `gameStore` with new state fields and actions, (2) building 5 new selector components (RoleSelector, PlaystyleSelector, SideSelector, LaneSelector, and a multi-slot hero picker for allies/opponents), (3) refactoring the existing `HeroPicker` to accept a generic `onSelect`/`onClear` callback instead of being hardwired to `gameStore.selectHero`, and (4) wiring everything into the existing `Sidebar.tsx`.

The existing `HeroPicker` component was designed with Phase 2 reuse in mind -- it already accepts `excludedHeroIds: Set<number>` for preventing duplicate hero selections across all 10 slots. The existing `HeroPortrait` component supports "sm" and "lg" sizes. The primary refactoring challenge is decoupling `HeroPicker` from the single `selectedHero` store field so it can serve multiple independent hero slots (4 allies + 5 opponents).

**Primary recommendation:** Refactor `HeroPicker` to accept `value: Hero | null`, `onSelect: (hero: Hero) => void`, and `onClear: () => void` props (controlled component pattern). Then compose it into `AllyPicker` and `OpponentPicker` wrapper components that each manage a row of compact slots, each wired to the appropriate Zustand store array index.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Compact row of 5 circular portraits (~32px) with "+" add buttons for empty slots. Click opens same HeroPicker dropdown pattern from Phase 1
- Ally section has Radiant teal border, opponent section has Dire red border for visual distinction
- Lane opponent picker filters from already-picked enemy heroes -- shows only the 5 picked opponents, user selects 1-2 as lane opponents. Separate small section below lane selector
- Sidebar order: Your hero (top) -> Allies -> Opponents -> Role -> Playstyle -> Side -> Lane -> CTA button
- Role selector: 5 horizontal toggle buttons -- "Pos 1 Carry", "Pos 2 Mid", "Pos 3 Off", "Pos 4 Soft Sup", "Pos 5 Hard Sup". One active at a time
- Playstyle: 3-4 pill buttons that change per role. Animate in after role selection (hidden/disabled until role picked)
- Playstyle options per role:
  - Pos 1: Farm-first, Aggressive, Split-push, Fighting
  - Pos 2: Tempo, Ganker, Greedy, Space-maker
  - Pos 3: Frontline, Aura-carrier, Initiator, Greedy
  - Pos 4: Roamer, Lane-dominator, Greedy, Save
  - Pos 5: Lane-protector, Roamer, Greedy, Save
- Side: Two-button toggle -- "Radiant" (teal #6aff97) vs "Dire" (red #ff5555). Color-coded, one active
- Lane: Three horizontal buttons -- "Safe", "Mid", "Off". Same toggle style as role selector
- CTA button: Prominent spectral cyan "Get Item Build" button at bottom of sidebar. Disabled until at minimum your hero + role are selected. Lights up when ready
- Zustand store: Extend existing gameStore with allies (Hero[]), opponents (Hero[]), role (number | null), playstyle (string | null), side ('radiant' | 'dire' | null), lane ('safe' | 'mid' | 'off' | null), laneOpponents (Hero[]). Single flat store, all nullable, updated independently

### Claude's Discretion
- Animation approach for playstyle reveal (CSS transition, Framer Motion, or Tailwind animate)
- Exact compact portrait sizing and spacing
- HeroPicker dropdown positioning and overlay behavior
- Whether to use the same HeroPicker component or a variant for multi-slot picking

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DRFT-02 | User can search and select 4 allied heroes from searchable dropdowns with portraits | Refactored HeroPicker with controlled props + AllyPicker wrapper component managing 4 indexed slots in Zustand store |
| DRFT-03 | User can search and select 5 opponent heroes from searchable dropdowns with portraits | Same refactored HeroPicker + OpponentPicker wrapper managing 5 indexed slots; Dire red border styling |
| DRFT-04 | User can select their role/position (Pos 1-5) via button selector | RoleSelector component using accessible toggle button group pattern with `role="radiogroup"` |
| DRFT-05 | User can select a playstyle from role-dependent options | PlaystyleSelector with PLAYSTYLE_OPTIONS constant keyed by role; conditionally rendered with CSS transition animation |
| DRFT-06 | User can select Radiant or Dire side | SideSelector two-button toggle using Radiant/Dire theme colors from globals.css |
| DRFT-07 | User can select their lane assignment (Safe/Off/Mid) | LaneSelector three-button toggle following same pattern as RoleSelector |

</phase_requirements>

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.4 | Component framework | Already installed from Phase 1 |
| zustand | 5.0.12 | State management | Already installed; single flat store pattern established |
| tailwindcss | 4.2.2 | Styling | Already installed; CSS-first @theme config established |
| fuse.js | 7.1.0 | Hero search | Already installed; used by heroSearch.ts |

### Supporting (Already Installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @fontsource/inter | 5.2.8 | Body font | Already configured |
| @fontsource/jetbrains-mono | 5.2.8 | Stats/numbers font | Already configured |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tailwind CSS transitions | Framer Motion | Framer Motion adds ~30KB for a simple reveal animation. Tailwind v4 CSS transitions handle the playstyle reveal without any new dependency |
| Custom toggle buttons | Radix Toggle Group | Adds dependency for simple single-select radio-like behavior achievable with native `role="radiogroup"` + ARIA |

**Installation:**
```bash
# No new packages needed. Phase 2 uses existing dependencies only.
```

## Architecture Patterns

### New Files to Create
```
prismlab/frontend/src/
+-- components/
|   +-- draft/
|       +-- HeroPicker.tsx          # REFACTOR: controlled component props
|       +-- AllyPicker.tsx          # NEW: 4-slot ally hero row
|       +-- OpponentPicker.tsx      # NEW: 5-slot opponent hero row
|       +-- RoleSelector.tsx        # NEW: Pos 1-5 toggle buttons
|       +-- PlaystyleSelector.tsx   # NEW: role-dependent pill buttons
|       +-- SideSelector.tsx        # NEW: Radiant/Dire toggle
|       +-- LaneSelector.tsx        # NEW: Safe/Mid/Off toggle
|       +-- HeroSlot.tsx            # NEW: single compact slot (portrait or "+" button)
+-- stores/
|   +-- gameStore.ts                # EXTEND: add allies, opponents, role, playstyle, side, lane
+-- utils/
    +-- constants.ts                # EXTEND: add ROLE_OPTIONS, PLAYSTYLE_OPTIONS, LANE_OPTIONS
```

### Pattern 1: Controlled HeroPicker Refactor
**What:** Transform HeroPicker from an internally-wired component (reads/writes gameStore directly) to a controlled component that accepts value/callbacks as props.
**When to use:** Whenever the same picker UI must serve multiple independent slots.
**Example:**
```typescript
// BEFORE (Phase 1 -- hardwired to single selectedHero)
interface HeroPickerProps {
  excludedHeroIds?: Set<number>;
}
// Internally: useGameStore((s) => s.selectedHero)

// AFTER (Phase 2 -- controlled)
interface HeroPickerProps {
  value: Hero | null;
  onSelect: (hero: Hero) => void;
  onClear: () => void;
  excludedHeroIds?: Set<number>;
  placeholder?: string;
  compact?: boolean;  // For ally/opponent rows: smaller input, fewer results
}
```

The "Your Hero" section in Sidebar.tsx updates to pass `value={selectedHero}`, `onSelect={selectHero}`, `onClear={clearHero}` from the store, preserving identical behavior.

### Pattern 2: Toggle Button Group
**What:** A reusable pattern for single-select button groups (role, lane, side).
**When to use:** Any set of mutually exclusive options rendered as adjacent buttons.
**Example:**
```typescript
// Generic toggle group pattern used by RoleSelector, LaneSelector, SideSelector
interface ToggleOption<T> {
  value: T;
  label: string;
  colorClass?: string; // For SideSelector radiant/dire colors
}

// Usage in RoleSelector
const ROLE_OPTIONS: ToggleOption<number>[] = [
  { value: 1, label: "Pos 1 Carry" },
  { value: 2, label: "Pos 2 Mid" },
  { value: 3, label: "Pos 3 Off" },
  { value: 4, label: "Pos 4 Soft Sup" },
  { value: 5, label: "Pos 5 Hard Sup" },
];

// Accessibility: role="radiogroup" on container, role="radio" + aria-checked on each button
<div role="radiogroup" aria-label="Position">
  {options.map(opt => (
    <button
      key={opt.value}
      role="radio"
      aria-checked={selected === opt.value}
      onClick={() => onSelect(opt.value)}
      className={selected === opt.value ? activeClass : inactiveClass}
    >
      {opt.label}
    </button>
  ))}
</div>
```

### Pattern 3: Zustand Flat Store Extension
**What:** Extend the existing gameStore with new nullable fields and independent setters.
**When to use:** This is the single store for all draft state.
**Example:**
```typescript
interface GameStore {
  // Phase 1 (existing)
  selectedHero: Hero | null;
  selectHero: (hero: Hero) => void;
  clearHero: () => void;

  // Phase 2 (new)
  allies: (Hero | null)[];      // [null, null, null, null] -- 4 slots
  opponents: (Hero | null)[];   // [null, null, null, null, null] -- 5 slots
  role: number | null;          // 1-5
  playstyle: string | null;
  side: 'radiant' | 'dire' | null;
  lane: 'safe' | 'mid' | 'off' | null;
  laneOpponents: Hero[];        // 0-2 heroes from opponents array

  // Phase 2 actions
  setAlly: (index: number, hero: Hero) => void;
  clearAlly: (index: number) => void;
  setOpponent: (index: number, hero: Hero) => void;
  clearOpponent: (index: number) => void;
  setRole: (role: number) => void;
  setPlaystyle: (playstyle: string) => void;
  setSide: (side: 'radiant' | 'dire') => void;
  setLane: (lane: 'safe' | 'mid' | 'off') => void;
  toggleLaneOpponent: (hero: Hero) => void; // Add/remove from lane opponents
  clearLaneOpponents: () => void;
}
```

**Key behavior:** When `role` changes, check if the current `playstyle` is still valid for the new role. If not, reset `playstyle` to `null`. This prevents stale playstyle selections.

### Pattern 4: Playstyle Conditional Reveal Animation
**What:** Animate playstyle pills appearing when role is selected.
**When to use:** Playstyle section should be hidden/collapsed until role is picked.

**Recommendation: Use Tailwind CSS transitions with conditional rendering.**

Tailwind v4 supports the `starting:` variant (maps to CSS `@starting-style`) which enables entry animations without JavaScript animation libraries. However, browser support for `@starting-style` is still maturing. The safer approach is a simple height/opacity CSS transition controlled by a wrapper div with `overflow-hidden` and dynamic max-height.

```typescript
// Simple, reliable approach (no @starting-style needed):
<div
  className={`transition-all duration-300 ease-out overflow-hidden ${
    role !== null ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'
  }`}
>
  {role !== null && <PlaystyleSelector role={role} />}
</div>
```

This avoids Framer Motion (unnecessary dependency) and avoids `@starting-style` browser compatibility concerns while providing a smooth reveal effect.

### Pattern 5: Excluded Hero ID Aggregation
**What:** Compute a single `Set<number>` of all selected hero IDs across all 10 slots (your hero + 4 allies + 5 opponents) and pass it to every HeroPicker as `excludedHeroIds`.
**When to use:** Always -- prevents selecting the same hero twice.
**Example:**
```typescript
// In Sidebar.tsx or a shared hook
const excludedIds = useMemo(() => {
  const ids = new Set<number>();
  if (selectedHero) ids.add(selectedHero.id);
  allies.forEach(a => { if (a) ids.add(a.id); });
  opponents.forEach(o => { if (o) ids.add(o.id); });
  return ids;
}, [selectedHero, allies, opponents]);
```

### Anti-Patterns to Avoid
- **Separate stores per section:** Do NOT create separate Zustand stores for allies, role, lane, etc. The CONTEXT.md explicitly locks "single flat store, all nullable, updated independently."
- **Uncontrolled hero pickers reading different store slices:** Do NOT create AllyHeroPicker1, AllyHeroPicker2, etc. as separate components each hardwired to a specific store slot. Use a single controlled HeroPicker and pass the slot index.
- **Animating with JavaScript timers:** Do NOT use `setTimeout`/`requestAnimationFrame` for UI reveals. Use CSS transitions.
- **Inline playstyle data:** Do NOT hardcode playstyle labels inside components. Define them as a typed constant in `constants.ts` for maintainability.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hero search/fuzzy match | Custom string matching | Existing `heroSearch.ts` (Fuse.js hybrid) | Already handles abbreviations, initials, typos |
| Hero image URLs | Manual CDN paths | Existing `imageUrls.ts` helpers | URL patterns already encapsulated |
| Outside-click detection | Custom event listener | Existing pattern from HeroPicker | `useRef` + `mousedown` listener pattern already proven |
| Animation library | Framer Motion install | Tailwind CSS `transition-all` + conditional classes | Sub-300ms reveal animation doesn't justify 30KB dependency |

**Key insight:** Phase 2 requires zero new dependencies. Everything is achievable with the existing stack. The complexity is in component composition and state wiring, not in introducing new tools.

## Common Pitfalls

### Pitfall 1: Stale Playstyle on Role Change
**What goes wrong:** User selects Pos 1 + "Farm-first", then switches to Pos 3. "Farm-first" is not a valid Pos 3 playstyle, but the store still holds it.
**Why it happens:** Role and playstyle are independent store fields with no automatic invalidation.
**How to avoid:** In the `setRole` action, check if the current `playstyle` exists in the new role's options. If not, set `playstyle: null`.
**Warning signs:** Test by rapidly switching roles and verifying playstyle resets.

### Pitfall 2: HeroPicker Dropdown Z-Index Collision
**What goes wrong:** Multiple HeroPicker dropdowns in the ally/opponent rows overlap each other or get clipped by the sidebar overflow.
**Why it happens:** Absolute-positioned dropdown within `overflow-y-auto` sidebar container.
**How to avoid:** Only one HeroPicker dropdown should be open at a time. When a slot's picker opens, close any other open picker. Consider using a portal (`createPortal`) if z-index issues persist, but try the simpler approach first of coordinating open state.
**Warning signs:** Click ally slot 1, then ally slot 2 -- first dropdown should close.

### Pitfall 3: Excluded Hero IDs Not Updating Reactively
**What goes wrong:** User picks Anti-Mage as their hero, then searches for heroes in ally slot -- Anti-Mage still appears as selectable.
**Why it happens:** `excludedHeroIds` is computed once and not reactive to store changes.
**How to avoid:** Compute `excludedIds` as a `useMemo` that depends on all hero selection fields from the store. Each HeroPicker instance receives the latest set.
**Warning signs:** Select heroes in various slots and verify they disappear from other pickers.

### Pitfall 4: Compact Portrait Row Overflow
**What goes wrong:** 5 opponent slots don't fit in the 80-unit (320px) sidebar width.
**Why it happens:** 5 circular slots at 32px each = 160px + gaps + borders + padding can exceed available width.
**How to avoid:** Use `flex-wrap` or ensure slots are truly compact. At 32px per slot with 4px gap: (32 * 5) + (4 * 4) = 176px fits comfortably in ~280px content area (320px sidebar minus padding).
**Warning signs:** Test with all 5 opponent slots filled; check for horizontal scrollbar or clipping.

### Pitfall 5: Lane Opponent Picker Confusion
**What goes wrong:** Users try to pick lane opponents before picking regular opponents, or the lane opponent picker shows an empty list.
**Why it happens:** Lane opponent picker filters from already-picked enemies. If no enemies are picked, nothing to show.
**How to avoid:** Disable/hide lane opponent section until at least 1 opponent is picked. Show clear messaging like "Pick opponents first".
**Warning signs:** Open the app fresh and try to interact with lane opponent section immediately.

### Pitfall 6: CTA Button Enabled Prematurely
**What goes wrong:** "Get Item Build" button is clickable when insufficient data is provided.
**Why it happens:** Missing validation logic for minimum required fields.
**How to avoid:** CTA is disabled unless `selectedHero !== null && role !== null` (the minimum specified in CONTEXT.md). Visually distinguish disabled (muted) from enabled (glowing spectral cyan).
**Warning signs:** Clear hero selection and verify button becomes disabled.

## Code Examples

### Zustand Store Extension
```typescript
// Source: Zustand v5 flat store pattern (https://github.com/pmndrs/zustand)
import { create } from "zustand";
import type { Hero } from "../types/hero";

// Playstyle options per role (from CONTEXT.md decisions)
const PLAYSTYLE_OPTIONS: Record<number, string[]> = {
  1: ["Farm-first", "Aggressive", "Split-push", "Fighting"],
  2: ["Tempo", "Ganker", "Greedy", "Space-maker"],
  3: ["Frontline", "Aura-carrier", "Initiator", "Greedy"],
  4: ["Roamer", "Lane-dominator", "Greedy", "Save"],
  5: ["Lane-protector", "Roamer", "Greedy", "Save"],
};

interface GameStore {
  selectedHero: Hero | null;
  allies: (Hero | null)[];
  opponents: (Hero | null)[];
  role: number | null;
  playstyle: string | null;
  side: "radiant" | "dire" | null;
  lane: "safe" | "mid" | "off" | null;
  laneOpponents: Hero[];

  selectHero: (hero: Hero) => void;
  clearHero: () => void;
  setAlly: (index: number, hero: Hero) => void;
  clearAlly: (index: number) => void;
  setOpponent: (index: number, hero: Hero) => void;
  clearOpponent: (index: number) => void;
  setRole: (role: number) => void;
  setPlaystyle: (playstyle: string) => void;
  setSide: (side: "radiant" | "dire") => void;
  setLane: (lane: "safe" | "mid" | "off") => void;
  toggleLaneOpponent: (hero: Hero) => void;
  clearLaneOpponents: () => void;
}

export const useGameStore = create<GameStore>()((set) => ({
  selectedHero: null,
  allies: [null, null, null, null],
  opponents: [null, null, null, null, null],
  role: null,
  playstyle: null,
  side: null,
  lane: null,
  laneOpponents: [],

  selectHero: (hero) => set({ selectedHero: hero }),
  clearHero: () => set({ selectedHero: null }),

  setAlly: (index, hero) =>
    set((state) => {
      const allies = [...state.allies];
      allies[index] = hero;
      return { allies };
    }),
  clearAlly: (index) =>
    set((state) => {
      const allies = [...state.allies];
      allies[index] = null;
      return { allies };
    }),

  setOpponent: (index, hero) =>
    set((state) => {
      const opponents = [...state.opponents];
      opponents[index] = hero;
      return { opponents };
    }),
  clearOpponent: (index) =>
    set((state) => {
      const opponents = [...state.opponents];
      opponents[index] = null;
      // Also remove from laneOpponents if present
      const laneOpponents = state.laneOpponents.filter(
        (lo) => lo.id !== opponents[index]?.id
      );
      return { opponents, laneOpponents };
    }),

  setRole: (role) =>
    set((state) => {
      const validPlaystyles = PLAYSTYLE_OPTIONS[role] ?? [];
      const playstyle = validPlaystyles.includes(state.playstyle ?? "")
        ? state.playstyle
        : null;
      return { role, playstyle };
    }),
  setPlaystyle: (playstyle) => set({ playstyle }),
  setSide: (side) => set({ side }),
  setLane: (lane) => set({ lane }),

  toggleLaneOpponent: (hero) =>
    set((state) => {
      const exists = state.laneOpponents.some((lo) => lo.id === hero.id);
      if (exists) {
        return {
          laneOpponents: state.laneOpponents.filter((lo) => lo.id !== hero.id),
        };
      }
      if (state.laneOpponents.length >= 2) return state; // Max 2
      return { laneOpponents: [...state.laneOpponents, hero] };
    }),
  clearLaneOpponents: () => set({ laneOpponents: [] }),
}));
```

### Toggle Button Group (Reusable Pattern)
```typescript
// Source: WAI-ARIA Radio Group pattern
interface ToggleOption<T extends string | number> {
  value: T;
  label: string;
}

interface ToggleGroupProps<T extends string | number> {
  options: ToggleOption<T>[];
  value: T | null;
  onChange: (value: T) => void;
  label: string;
  getButtonClass?: (isActive: boolean, option: ToggleOption<T>) => string;
}

function ToggleGroup<T extends string | number>({
  options,
  value,
  onChange,
  label,
  getButtonClass,
}: ToggleGroupProps<T>) {
  const defaultClass = (active: boolean) =>
    active
      ? "bg-cyan-accent/20 text-cyan-accent border-cyan-accent"
      : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200";

  return (
    <div role="radiogroup" aria-label={label} className="flex flex-wrap gap-1.5">
      {options.map((opt) => {
        const isActive = value === opt.value;
        const cls = getButtonClass
          ? getButtonClass(isActive, opt)
          : defaultClass(isActive);
        return (
          <button
            key={String(opt.value)}
            role="radio"
            aria-checked={isActive}
            onClick={() => onChange(opt.value)}
            className={`px-3 py-1.5 text-xs font-medium rounded-md border transition-colors ${cls}`}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
```

### Compact Hero Slot
```typescript
// Single slot in ally/opponent row
interface HeroSlotProps {
  hero: Hero | null;
  onClickEmpty: () => void;
  onClear: () => void;
  borderColor: string; // "border-radiant" or "border-dire"
}

function HeroSlot({ hero, onClickEmpty, onClear, borderColor }: HeroSlotProps) {
  if (hero) {
    const slug = heroSlugFromInternal(hero.internal_name);
    return (
      <div
        className={`relative group w-8 h-8 rounded-full overflow-hidden border-2 ${borderColor}`}
      >
        <img
          src={heroIconUrl(slug)}
          alt={hero.localized_name}
          className="w-full h-full object-cover"
          title={hero.localized_name}
        />
        <button
          onClick={onClear}
          className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
          aria-label={`Remove ${hero.localized_name}`}
        >
          <span className="text-white text-xs">x</span>
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={onClickEmpty}
      className={`w-8 h-8 rounded-full border-2 border-dashed ${borderColor} flex items-center justify-center text-gray-500 hover:text-gray-300 hover:border-gray-400 transition-colors`}
      aria-label="Add hero"
    >
      <span className="text-sm">+</span>
    </button>
  );
}
```

### SideSelector with Theme Colors
```typescript
// Uses existing OKLCH radiant/dire colors from globals.css
function SideSelector() {
  const side = useGameStore((s) => s.side);
  const setSide = useGameStore((s) => s.setSide);

  return (
    <div role="radiogroup" aria-label="Side" className="flex gap-2">
      <button
        role="radio"
        aria-checked={side === "radiant"}
        onClick={() => setSide("radiant")}
        className={`flex-1 py-1.5 text-xs font-medium rounded-md border transition-colors ${
          side === "radiant"
            ? "bg-radiant/20 text-radiant border-radiant"
            : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
        }`}
      >
        Radiant
      </button>
      <button
        role="radio"
        aria-checked={side === "dire"}
        onClick={() => setSide("dire")}
        className={`flex-1 py-1.5 text-xs font-medium rounded-md border transition-colors ${
          side === "dire"
            ? "bg-dire/20 text-dire border-dire"
            : "bg-bg-elevated text-gray-400 border-bg-elevated hover:text-gray-200"
        }`}
      >
        Dire
      </button>
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind config.js | Tailwind v4 CSS-first @theme | Jan 2025 | Already using @theme in globals.css -- no migration needed |
| Zustand v4 create() | Zustand v5 create()() (double invoke) | Dec 2024 | Already using v5 pattern in gameStore.ts |
| React class components | React 19 functional + hooks | Established | Already using functional components throughout |
| Framer Motion for simple animations | CSS transitions + Tailwind utilities | 2024-2025 | Avoid adding Framer Motion; CSS transitions sufficient for reveal animations |

**Deprecated/outdated:**
- `@starting-style` / `starting:` variant in Tailwind v4: Available but browser support is still maturing. Safe for progressive enhancement but not reliable as the only animation mechanism for critical UI. Use conditional CSS classes (max-height + opacity transition) as the primary approach.

## Open Questions

1. **Hero icon vs hero portrait for compact slots**
   - What we know: `heroIconUrl()` returns the mini icon (used in-game minimap). `heroImageUrl()` returns the larger rectangular portrait.
   - What's unclear: At 32px circular, the rectangular portrait may look odd when cropped to a circle. The icon is square and purpose-built for small sizes.
   - Recommendation: Use `heroIconUrl()` for compact 32px circular slots. Use `heroImageUrl()` for the main "Your Hero" large display (already working in Phase 1).

2. **Single open picker coordination**
   - What we know: With 10 hero slots each potentially opening a dropdown, only one should be open at a time.
   - What's unclear: Whether to lift "which picker is open" state into Zustand or manage it locally in the parent component.
   - Recommendation: Manage the "active picker ID" as local state in Sidebar.tsx (or in the AllyPicker/OpponentPicker wrappers). This is transient UI state, not app state -- it should not go in Zustand.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.0 + @testing-library/react 16.3.2 |
| Config file | `prismlab/frontend/vitest.config.ts` |
| Quick run command | `cd prismlab/frontend && npx vitest run` |
| Full suite command | `cd prismlab/frontend && npx vitest run` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DRFT-02 | Select/clear ally heroes in 4 slots | unit | `cd prismlab/frontend && npx vitest run src/stores/gameStore.test.ts -t "ally"` | No -- Wave 0 |
| DRFT-03 | Select/clear opponent heroes in 5 slots | unit | `cd prismlab/frontend && npx vitest run src/stores/gameStore.test.ts -t "opponent"` | No -- Wave 0 |
| DRFT-04 | Select role (Pos 1-5) | unit | `cd prismlab/frontend && npx vitest run src/stores/gameStore.test.ts -t "role"` | No -- Wave 0 |
| DRFT-05 | Role-dependent playstyle selection + reset on role change | unit | `cd prismlab/frontend && npx vitest run src/stores/gameStore.test.ts -t "playstyle"` | No -- Wave 0 |
| DRFT-06 | Select Radiant/Dire side | unit | `cd prismlab/frontend && npx vitest run src/stores/gameStore.test.ts -t "side"` | No -- Wave 0 |
| DRFT-07 | Select lane assignment | unit | `cd prismlab/frontend && npx vitest run src/stores/gameStore.test.ts -t "lane"` | No -- Wave 0 |

### Sampling Rate
- **Per task commit:** `cd prismlab/frontend && npx vitest run`
- **Per wave merge:** `cd prismlab/frontend && npx vitest run`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `prismlab/frontend/src/stores/gameStore.test.ts` -- covers DRFT-02 through DRFT-07 (store logic: setAlly, clearAlly, setOpponent, clearOpponent, setRole + playstyle invalidation, setSide, setLane, toggleLaneOpponent)
- [ ] Existing `heroSearch.test.ts` already covers search logic -- no new search tests needed

## Sources

### Primary (HIGH confidence)
- Existing codebase: `gameStore.ts`, `HeroPicker.tsx`, `HeroPortrait.tsx`, `Sidebar.tsx`, `constants.ts`, `globals.css` -- directly read and analyzed
- Zustand v5 GitHub README (https://github.com/pmndrs/zustand) -- confirmed create()() pattern and flat store approach
- Tailwind CSS v4 official docs (https://tailwindcss.com/docs/animation, https://tailwindcss.com/docs/transition-behavior) -- confirmed transition utilities and `starting:` variant

### Secondary (MEDIUM confidence)
- Tailwind CSS v4 blog post (https://tailwindcss.com/blog/tailwindcss-v4) -- confirmed `starting:` variant for `@starting-style`
- WAI-ARIA Radio Group pattern -- standard accessibility pattern for toggle button groups

### Tertiary (LOW confidence)
- None -- all findings verified against primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already installed and verified at latest versions; no new dependencies
- Architecture: HIGH -- patterns derived directly from existing Phase 1 code and Zustand/React conventions
- Pitfalls: HIGH -- derived from concrete analysis of existing component structure and CONTEXT.md specifications

**Research date:** 2026-03-21
**Valid until:** 2026-04-21 (stable -- no library upgrades or API changes expected)

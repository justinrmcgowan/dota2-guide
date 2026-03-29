---
phase: 17-design-system-migration
verified: 2026-03-26T00:00:00Z
status: human_needed
score: 8/8 must-haves verified
human_verification:
  - test: "Visual inspection of running app"
    expected: "All surfaces match Tactical Relic Editorial spec: obsidian hierarchy, gold/crimson accents, Newsreader headers, 0px corners, no cyan anywhere"
    why_human: "Code audit passes completely; visual rendering of parchment noise texture, blood-glass blur, and font rendering cannot be verified programmatically"
  - test: "Functional exceptions audit"
    expected: "rounded-full on checkmarks, status dots, hero avatars, badges, spinners are all intentional and visually appropriate"
    why_human: "Requires visual confirmation that circular affordances are correct in context"
---

# Phase 17: Design System Migration Verification Report

**Phase Goal:** Every visual surface in Prismlab matches the "Tactical Relic Editorial" spec in DESIGN.md -- obsidian surfaces, crimson/gold accents, Newsreader/Manrope typography, 0px corners
**Verified:** 2026-03-26
**Status:** human_needed (all automated checks pass)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | App renders with Newsreader (display/headline) and Manrope (body/label), self-hosted, no CDN | VERIFIED | `main.tsx` imports `@fontsource-variable/newsreader` and `@fontsource-variable/manrope`; `package.json` confirms both installed, old fonts removed; `globals.css` maps `--font-display` to "Newsreader Variable" and `--font-body` to "Manrope Variable" |
| 2 | All surfaces use obsidian tonal hierarchy with no 1px borders or rounded corners (except documented exceptions) | VERIFIED | `globals.css` has `--radius-*: 0px` for all sizes; grep for `rounded-lg`, `rounded-md`, `rounded-xl` returns zero matches; grep for `border-b border-bg`, `border-r border-bg`, `border-t border-bg` returns zero matches; surface hierarchy applied across all layout files |
| 3 | Floating elements show ambient crimson glow shadows and blood-glass backdrop-blur | VERIFIED | `SettingsPanel.tsx` uses `bg-primary-container/25 backdrop-blur-md` + `shadow-glow`; `ScreenshotParser.tsx` uses `bg-primary-container/30 backdrop-blur-md` + `shadow-glow`; `AutoRefreshToast.tsx` uses `shadow-glow` without `backdrop-blur` (correct per Pitfall 13) |
| 4 | Hero/legendary item cards show gold left-accent strips; base background has parchment noise texture | VERIFIED | `ItemCard.tsx` PRIORITY_BORDER map: `core` and `luxury` both map to `"border-l-secondary-fixed"` (gold #FFE16D); `globals.css` contains `.noise-overlay::before` with `feTurbulence` SVG data URI; `App.tsx` root div has `noise-overlay relative` class |
| 5 | Visual audit finds zero old tokens across all ~30 components | VERIFIED | See DESIGN-08 section below; all token classes confirmed zero-count |

**Score:** 5/5 success criteria verified (8/8 requirement IDs covered)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `prismlab/frontend/src/styles/globals.css` | Complete @theme with DESIGN.md tokens + noise-overlay CSS | VERIFIED | Contains full surface hierarchy, crimson/gold palette, 0px radius tokens, Newsreader/Manrope font vars, shadow-glow tokens, feTurbulence noise overlay; deprecated aliases removed |
| `prismlab/frontend/src/main.tsx` | Variable font imports, old fonts removed | VERIFIED | Imports `@fontsource-variable/newsreader` and `@fontsource-variable/manrope`; no `@fontsource/inter` or `@fontsource/jetbrains-mono` |
| `prismlab/frontend/src/App.tsx` | noise-overlay class on root | VERIFIED | Root div has `className="h-screen flex flex-col bg-surface text-on-surface font-body noise-overlay relative"` |
| `prismlab/frontend/src/components/layout/Sidebar.tsx` | `bg-surface-container-lowest` | VERIFIED | `<aside className="w-80 bg-surface-container-lowest ...">` |
| `prismlab/frontend/src/components/layout/Header.tsx` | `bg-surface-container-low`, no `border-b` | VERIFIED | `<header className="h-14 bg-surface-container-low ...">`, no border-b present |
| `prismlab/frontend/src/components/layout/MainPanel.tsx` | `bg-surface` | VERIFIED | `<main className="flex-1 bg-surface ...">` |
| `prismlab/frontend/src/components/timeline/ItemCard.tsx` | Gold accent strip on core/luxury | VERIFIED | PRIORITY_BORDER: `core: "border-l-secondary-fixed"`, `luxury: "border-l-secondary-fixed"`; purchased checkmark retains `rounded-full bg-radiant` |
| `prismlab/frontend/src/components/timeline/PhaseCard.tsx` | `bg-surface-container-low`, no `rounded-lg`, `font-display` | VERIFIED | `<div className="bg-surface-container-low p-[1.75rem]">`, phase h3 has `font-display` class |
| `prismlab/frontend/src/components/settings/SettingsPanel.tsx` | Blood-glass backdrop + `shadow-glow` | VERIFIED | Backdrop `bg-primary-container/25 backdrop-blur-md`; panel `bg-surface-container-highest shadow-glow`; inputs follow Sacrificial Table pattern |
| `prismlab/frontend/src/components/screenshot/ScreenshotParser.tsx` | Blood-glass backdrop + `shadow-glow`, no `rounded-lg` | VERIFIED | Backdrop `bg-primary-container/30 backdrop-blur-md`; modal `bg-surface-container-highest shadow-glow`; no `rounded-lg` anywhere |
| `prismlab/frontend/src/components/toast/AutoRefreshToast.tsx` | `bg-surface-container-highest shadow-glow`, no `backdrop-blur` | VERIFIED | Uses `bg-surface-container-highest ... shadow-glow`; no backdrop-blur (Pitfall 13 respected) |
| `prismlab/frontend/src/components/timeline/ErrorBanner.tsx` | Crimson tonal for errors, gold for fallbacks | VERIFIED | Error: `bg-primary-container/15 ... text-primary`; fallback: `bg-secondary/10 ... text-secondary/80` |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `main.tsx` | `node_modules/@fontsource-variable/newsreader` | CSS import | WIRED | Import present; package exists in node_modules |
| `globals.css` | Tailwind utility generation | @theme directive | WIRED | `--color-surface: #131313` and all tokens present in @theme block |
| `App.tsx` | `globals.css` | noise-overlay class | WIRED | `noise-overlay` class applied to root div; `.noise-overlay::before` defined in globals.css |
| `ItemCard.tsx` | DESIGN.md Monolith card | gold left-accent strip | WIRED | `border-l-secondary-fixed` pattern resolves to `--color-secondary-fixed: #FFE16D` |
| `SettingsPanel.tsx` | `globals.css` shadow tokens | shadow-glow class | WIRED | `shadow-glow` class resolves to `--shadow-glow: 0 0 32px rgb(255 180 172 / 0.05)` |
| `ScreenshotParser.tsx` | `globals.css` shadow tokens | shadow-glow class | WIRED | Same as above |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| DESIGN-01 | 17-01 | Tailwind @theme block replaced with DESIGN.md tokens | SATISFIED | Full token set in globals.css; deprecated aliases removed in Plan 05 |
| DESIGN-02 | 17-01 | Newsreader + Manrope self-hosted via @fontsource-variable | SATISFIED | Both variable fonts in package.json; `main.tsx` imports; no CDN calls |
| DESIGN-03 | 17-02, 17-03 | All components updated to surface hierarchy, no 1px borders, tonal layering | SATISFIED | All layout, draft, timeline, and game components use surface-container-* tokens; border-bg patterns removed |
| DESIGN-04 | 17-04 | Ambient crimson glow shadows on floating elements | SATISFIED | `shadow-glow` on SettingsPanel, ScreenshotParser, AutoRefreshToast, ItemEditPicker |
| DESIGN-05 | 17-03 | Gold left-accent strips on hero/legendary item cards | SATISFIED | `border-l-secondary-fixed` on `core` and `luxury` priorities in ItemCard.tsx |
| DESIGN-06 | 17-04 | Blood-glass backdrop-blur overlays on modals and settings panel | SATISFIED | `bg-primary-container/25 backdrop-blur-md` on SettingsPanel; `bg-primary-container/30 backdrop-blur-md` on ScreenshotParser |
| DESIGN-07 | 17-05 | Parchment noise texture overlay on base background | SATISFIED | `.noise-overlay::before` with feTurbulence SVG in globals.css; `noise-overlay` class on App root |
| DESIGN-08 | 17-05 | All components pass visual audit (no rounded corners, no blue links, no #FFFFFF) | SATISFIED (with warnings) | grep for all old tokens returns zero matches; see Anti-Patterns section for minor fallback warnings |

---

## DESIGN-08 Detailed Token Audit

The following grep patterns were run against all `.tsx` and `.ts` files in `prismlab/frontend/src/`:

| Pattern | Matches | Status |
|---------|---------|--------|
| `cyan-accent` | 0 | CLEAN |
| `#00d4ff` / `#00D4FF` | 0 | CLEAN |
| `#FFFFFF` / `#ffffff` | 0 | CLEAN |
| `text-white` | 0 | CLEAN |
| `rounded-lg` | 0 | CLEAN |
| `rounded-md` | 0 | CLEAN |
| `rounded-xl` / `rounded-2xl` | 0 | CLEAN |
| `font-mono` | 0 | CLEAN |
| `text-blue` / `text-sky` / `text-indigo` | 0 | CLEAN |
| `bg-bg-primary` / `bg-bg-secondary` / `bg-bg-elevated` | 0 | CLEAN |
| `text-text-muted` | 0 | CLEAN |
| `border-b border-bg` / `border-r border-bg` / `border-t border-bg` | 0 | CLEAN |

Deprecated token aliases (`--color-cyan-accent`, `--color-bg-primary`, `--color-bg-secondary`, `--color-bg-elevated`, `--color-text-muted`) confirmed removed from `globals.css`.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `components/timeline/NeutralItemSection.tsx` | 83 | `?? "bg-gray-700 text-gray-300"` | Warning | Fallback for `RANK_COLORS[pick.rank]` when rank > 3. Only reached with invalid data (valid ranks 1-3 are all mapped to new tokens). Never renders in normal operation. |
| `components/timeline/PhaseCard.tsx` | 32 | `?? "text-gray-400"` | Warning | Fallback for `PHASE_COLORS[phase.phase]` when phase key is unknown. Valid phases (starting, laning, core, late_game, situational) all mapped. Never renders with valid backend data. |
| `components/draft/HeroPortrait.tsx` | 22 | `?? "bg-gray-400"` | Warning | Fallback for `ATTR_BG_COLORS[hero.primary_attr]` when attr is unknown. Valid attrs (str, agi, int, all) are all mapped to `bg-attr-*` tokens. Never renders with valid hero data. |
| `components/layout/GsiStatusIndicator.tsx` | 8 | `bg-gray-500` for idle dot color | Warning | The idle (disconnected) GSI status dot uses `bg-gray-500`. Radiant (connected) and Dire (lost) are correct game colors. `bg-gray-500` for idle is not a DESIGN.md token, though it is semantically neutral. Could be `bg-on-surface-variant/30` for palette purity. |

**Classification note:** All four are warnings, not blockers. The three `??` fallback patterns are defensive error guards that never render under normal conditions. The `bg-gray-500` idle dot is the only production-path gray token and represents a minor palette escape.

---

## Behavioral Spot-Checks

Step 7b: SKIPPED for font import and CSS token verification (no runnable entry points in CI). Font package existence verified via `node_modules/@fontsource-variable/` directory listing (both `newsreader` and `manrope` present).

---

## Human Verification Required

### 1. Complete Visual Inspection

**Test:** Start the dev server (`cd prismlab/frontend && npm run dev`), open http://localhost:5173, and verify the following visually:

- Sidebar is the darkest surface (near-black #0E0E0E)
- Main panel is slightly lighter (#131313)
- Header is a distinct middle tone (#1C1B1B)
- "Prismlab" title is gold, serif/editorial font (Newsreader)
- Game clock shows in gold when GSI is connected
- All toggle buttons (Role, Lane, Playstyle, Side) use crimson accent when active — no cyan anywhere
- "Get Item Build" button is deep crimson (#B22222) with sharp corners
- No visible 1px borders on layout dividers
- All corners are sharp (0px) except checkmarks, status dots, avatar circles, and confidence badges

**Expected:** App matches Tactical Relic Editorial spec with obsidian surfaces, crimson/gold accents, editorial serif headlines
**Why human:** Font rendering, tonal depth perception, and subtle texture overlay cannot be confirmed programmatically

### 2. Parchment Noise Texture

**Test:** Look closely at the base background (#131313) area with no overlaid content
**Expected:** Subtle film grain / noise texture visible at close inspection (opacity 3.5% — very subtle)
**Why human:** SVG feTurbulence in CSS is confirmed present in code; actual browser rendering of the texture requires visual inspection

### 3. Blood-Glass Overlay

**Test:** Click the Settings gear icon; also paste a screenshot (Ctrl+V with any image in clipboard)
**Expected:** Settings panel backdrop has a slightly red-tinted blur; screenshot modal backdrop has red-tinted blur with stronger opacity. Panels have sharp corners and no visible outer borders.
**Why human:** `backdrop-filter: blur()` requires GPU compositing; correct visual appearance requires browser verification

### 4. Functional Roundedness Exceptions

**Test:** Inspect the following UI elements:
- Purchased item checkmark circles (ItemCard)
- GSI status dot in header
- Hero portrait attribute dots
- Rank badges in NeutralItemSection (rank 1 gold, etc.)
- Loading spinner in ScreenshotParser
- Confidence badges (orange ?) in ParsedHeroRow
**Expected:** All are `rounded-full` circles — intentional for their function
**Why human:** Requires confirming these are visually appropriate circular affordances, not accidental roundness

### 5. `bg-gray-500` Idle GSI Dot

**Test:** With GSI disconnected (initial app load), inspect the GSI status dot in the Header
**Expected:** A neutral/muted gray dot indicating idle status — visually unobtrusive
**Why human:** Verify whether this gray feels "outside" the palette or acceptably neutral. If it looks wrong, replace with `bg-on-surface-variant/30` for palette purity.

---

## Gaps Summary

No structural gaps. All 8 requirements have implementation evidence. All critical token classes are at zero violations.

The four "warning" anti-patterns are all defensive fallback values that require invalid data to render. They do not represent design regressions in normal operation. The `bg-gray-500` idle dot is the only active production-path non-DESIGN.md token; it is semantically correct (neutral gray = neutral/idle state) but does escape the obsidian palette.

**Recommendation:** The three `?? gray` fallback strings should be updated to DESIGN.md equivalents in a follow-up cleanup, and `bg-gray-500` should be considered for replacement with `bg-on-surface-variant/30`. These are not blockers for phase completion.

---

*Verified: 2026-03-26*
*Verifier: Claude (gsd-verifier)*

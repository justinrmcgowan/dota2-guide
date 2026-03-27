# Phase 17: Design System Migration - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 17 migrates every visual surface in Prismlab to the "Tactical Relic Editorial" design system defined in DESIGN.md. This includes the @theme token swap (colors, fonts, corners), per-component surface hierarchy updates, ambient glow shadows, gold accent strips, blood-glass overlays, and parchment texture. After this phase, zero instances of old tokens (cyan accent, #FFFFFF, rounded corners, blue links) remain.

</domain>

<decisions>
## Implementation Decisions

### Migration Strategy
- **D-01:** Two-step migration: (1) Token swap in globals.css @theme block + font installation — covers ~60% of visual change in one file. (2) Per-component audit pass — update classes, remove borders, adjust surfaces, add effects.
- **D-02:** Hard cutover, not gradual. Adding new tokens alongside old ones first, then removing old tokens after verified zero references. No half-migrated state.
- **D-03:** Font installation via `@fontsource-variable/newsreader` and `@fontsource-variable/manrope` npm packages. Self-hosted, no CDN dependency. Variable fonts for optical sizing axis.

### Functional Exceptions
- **D-04:** Purchased-item checkmarks (`rounded-full`) are EXEMPT from the 0px corner mandate. Circles are universally understood as "done" indicators and are the most-used interaction during live gameplay.
- **D-05:** Claude has discretion to identify and document other functional roundedness exceptions (e.g., avatar/portrait images, status indicator dots) during implementation.

### Surface Hierarchy Mapping
- **D-06:** Sidebar → `surface-container-lowest` (#0E0E0E) — recessed into the "obsidian void" per DESIGN.md sidebar guidance.
- **D-07:** Main panel (item timeline) → `surface` (#131313) — the base layer.
- **D-08:** Header → `surface-container-low` (#1C1B1B) — secondary information area.
- **D-09:** Floating elements (modals, settings panel, screenshot parser) → `surface-container-highest` (#353534) with ambient crimson glow and blood-glass overlay.
- **D-10:** Item timeline cards → Monolith card pattern: `surface-container-low` fill, no internal dividers, 1.75rem spacing, 2px gold (`secondary_fixed` #FFE16D) left-accent strip on core/luxury priority items.

### Typography
- **D-11:** Newsreader for display/headline text (hero names, section headers, phase labels). Tight letter-spacing (-0.02em).
- **D-12:** Manrope for body/label text (stats, reasoning, descriptions, buttons). High readability.
- **D-13:** Gold (`secondary` #FFDB3C) reserved for headlines and label-md highlights only. Never for long-form body text.
- **D-14:** Secondary body text uses `on_surface_variant` (#E2BEBA) for parchment-like legibility.

### Effects
- **D-15:** Ambient crimson glow: `primary` (#FFB4AC) at 5% opacity, 32px blur on floating elements.
- **D-16:** Ghost border: `outline_variant` (#5A403E) at 15% opacity for containers needing perimeter. Felt, not seen.
- **D-17:** Blood-glass: `primary_container` (#B22222) at 20-40% opacity with `backdrop-blur: 12px` on tactical overlays.
- **D-18:** Parchment texture: low-opacity noise/grain overlay on base background (#131313).

### Claude's Discretion
- Exact noise texture implementation (CSS background-image, pseudo-element, SVG filter)
- Which item priority levels get gold accent strips (core + luxury? all? just core?)
- Button hover/active states per DESIGN.md "Blade" pattern
- Input field styling per "Sacrificial Table" pattern
- Tactical HUD sections using `tertiary_container` (#4E5E6D)
- Additional functional roundedness exceptions beyond checkmarks
- Font preloading strategy and metric-matching fallback fonts

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Spec (CANONICAL)
- `DESIGN.md` — THE authoritative design system spec. Every decision here derives from it. Agents MUST read this file.

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — DESIGN-01 through DESIGN-08
- `.planning/ROADMAP.md` — Phase 17 success criteria (5 criteria that must be TRUE)

### Research
- `.planning/research/STACK.md` — Font packages, Tailwind @theme mechanics
- `.planning/research/FEATURES.md` — Migration strategy analysis
- `.planning/research/PITFALLS.md` — Font layout shift, token removal order, WCAG contrast, checkmark exception

### Frontend Files (all need updating)
- `prismlab/frontend/src/globals.css` — Current @theme block to replace
- `prismlab/frontend/src/components/layout/Header.tsx` — Header component
- `prismlab/frontend/src/components/layout/Sidebar.tsx` — Sidebar component
- `prismlab/frontend/src/components/layout/MainPanel.tsx` — Main panel
- `prismlab/frontend/src/components/timeline/ItemCard.tsx` — Item cards (Monolith pattern)
- `prismlab/frontend/src/components/timeline/PhaseCard.tsx` — Phase section headers
- `prismlab/frontend/src/components/settings/SettingsPanel.tsx` — Settings slide-over (blood-glass)
- `prismlab/frontend/src/components/screenshot/ScreenshotParser.tsx` — Screenshot modal (blood-glass)
- All other component files in src/components/

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `globals.css` @theme block — Already uses Tailwind v4 @theme pattern. Token swap is a value replacement, not architecture change.
- All existing Tailwind utility classes — Many will "just work" after token swap (bg-bg-primary, text-text-muted, etc.)

### Established Patterns
- Tailwind v4 with @theme CSS custom properties
- Component-level className strings with Tailwind utilities
- Dark theme tokens referenced via custom property names

### Integration Points
- `package.json` — Install @fontsource-variable packages
- `globals.css` — @theme block + font imports
- Every component file in src/components/ — Class name updates
- `tailwind.config.ts` or equivalent — Font family configuration

</code_context>

<specifics>
## Specific Ideas

- Sidebar recessed into obsidian void (#0E0E0E) — deepest surface level
- Item cards use Monolith pattern with gold left-accent strips
- Checkmarks exempt from 0px corners
- Blood-glass effect on all floating overlays (modals, panels)
- Parchment noise texture on base background

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 17-design-system-migration*
*Context gathered: 2026-03-26*

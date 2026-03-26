# Design System Specification: Tactical Relic Editorial

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Digital Monolith."** 

This system moves away from the "flatness" of modern SaaS and instead embraces the weight, history, and lethal precision of an ancient battlefield. We are not building a simple interface; we are chiseling a tactical artifact. By blending high-end editorial typography with a brooding, high-contrast color palette, we create an environment that feels both authoritative and atmospheric. 

To break the "template" look, designers must lean into **Intentional Asymmetry**. Key information should not always be centered; use the `Spacing Scale` to create wide, cinematic gutters and overlapping elements where a `surface-container-high` element might bleed over a `surface-dim` background, mimicking the way stone slabs overlap in ancient architecture.

---

## 2. Colors & Surface Philosophy
The palette is a clash between the divine and the demonic—Radiant Gold and Dire Crimson—set against an infinite obsidian void.

### The "No-Line" Rule
**Strict Prohibition:** Do not use 1px solid borders to define sections. 
In this system, boundaries are earned, not drawn. Separate content blocks using background shifts:
- Use `surface-container-low` (#1C1B1B) for secondary information.
- Use `surface-container-lowest` (#0E0E0E) for deep, recessed areas like sidebars or footers.
- Use `surface-bright` (#3A3939) sparingly for high-action callouts.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of stone and light. 
*   **Base:** `surface` (#131313)
*   **The Inset:** Use `surface-container-lowest` to create "carved" areas for data entry.
*   **The Float:** Use `surface-container-highest` (#353534) for floating modals, creating a sense of a heavy slab hovering over the abyss.

### The "Glass & Glow" Rule
To elevate the "Dire" aesthetic, use `primary_container` (#B22222) with a 20-40% opacity and a `backdrop-blur` of 12px for tactical overlays. This creates a "blood-glass" effect. For "Radiant" elements, use `secondary_container` (#FFDB3C) with a subtle linear gradient (from `secondary` to `secondary_fixed_dim`) to simulate the shimmer of gold leaf.

---

## 3. Typography: The Chiseled Word
We pair the ancient weight of **Newsreader** (Display/Headline) with the surgical precision of **Manrope** (Body/Label).

*   **Display & Headlines (Newsreader):** These are your "engravings." Use `display-lg` for hero moments. The high-contrast serifs should feel like they were carved into the screen. Maintain tight letter-spacing (-0.02em) to emphasize the "stone block" feel.
*   **Body & Technical Data (Manrope):** All tactical data—stats, descriptions, and logs—must use Manrope. It provides the necessary "high-readability" contrast against the decorative headlines. 
*   **Hierarchy Tip:** Never use Gold (`secondary`) for long-form body text; keep it reserved for Headlines or `label-md` highlights. Use `on_surface_variant` (#E2BEBA) for secondary body text to ensure a soft, parchment-like legibility.

---

## 4. Elevation & Depth: Tonal Layering
Traditional drop shadows are forbidden. We use **Ambient Shadows** and **Tonal Stacking**.

*   **The Layering Principle:** Depth is achieved by placing a `surface-container-highest` card atop a `surface-dim` background. The contrast in hex value provides the lift.
*   **Ambient Glows:** When an element must "float," use a shadow tinted with `primary` (#FFB4AC) at 5% opacity with a blur of 32px. This mimics a magical "crimson aura" rather than a physical shadow.
*   **The Ghost Border:** If a container needs a perimeter (e.g., a high-stakes button), use the `outline_variant` (#5A403E) at 15% opacity. It should be felt, not seen.
*   **Angular Geometry:** All containers must adhere to the `0px` Roundedness Scale. Sharp corners are non-negotiable; they reflect the jagged architecture of the Dire.

---

## 5. Components

### Buttons: The "Blade" Pattern
*   **Primary:** Background of `primary_container` (#B22222) with a subtle "gold leaf" `outline` (#AA8986) on hover. Sharp corners.
*   **Secondary:** Background of `surface-container-high`, text in `secondary` (Gold).
*   **States:** On `Active`, apply a `surface_tint` glow. The button should feel like it is "charging" with energy.

### Cards: The "Monolith"
Forbid dividers. Use `Spacing Scale 8` (1.75rem) to separate internal card content. Use a `surface-container-low` fill. If the card represents a "Hero" or "Legendary" item, apply a 2px left-side accent strip of `secondary_fixed` (#FFE16D).

### Inputs: The "Sacrificial Table"
Text inputs are recessed. Use `surface-container-lowest` with an `outline-variant` bottom border only. This creates an editorial "underline" feel rather than a modern "box" feel.

### Tactical HUD (Custom Component)
For dense data visualizations, use `tertiary_container` (#4E5E6D) for "Slate Blue" backgrounds. This differentiates "Lore/Marketing" sections (Crimson/Gold) from "Tactical/Utility" sections (Slate/Gray).

---

## 6. Do’s and Don’ts

### Do:
*   **Do** use extreme typographic scale. A `display-lg` headline next to a `body-sm` caption creates a high-end editorial rhythm.
*   **Do** use "Parchment Textures." Apply a low-opacity noise overlay or a subtle grain texture to `background` (#131313) to prevent the UI from feeling "sterile."
*   **Do** utilize white space as a structural element. Let the obsidian backgrounds breathe.

### Don't:
*   **Don't** use rounded corners. Even a 2px radius can soften the "lethal" intent of the system. Keep it at `0px`.
*   **Don't** use standard blue for links. Use `secondary_fixed_dim` (Gold) or `tertiary` (Slate).
*   **Don't** use 100% white (#FFFFFF). Use `on_surface` (#E5E2E1) for a slightly warmer, more premium ivory feel.
*   **Don't** use "Card Shadows." If an element needs to stand out, use a color shift or a thin "Ghost Border."
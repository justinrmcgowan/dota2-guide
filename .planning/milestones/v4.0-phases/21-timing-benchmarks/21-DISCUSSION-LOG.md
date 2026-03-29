# Phase 21: Timing Benchmarks - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 21-timing-benchmarks
**Areas discussed:** Timing Display in Item Cards, Claude Timing Reasoning, GSI Live Timing Comparison
**Mode:** Smart discuss (autonomous)

---

## Timing Display in Item Cards

| Option | Description | Selected |
|--------|-------------|----------|
| Compact bar below item | Horizontal bar with good/on-track/late zones, win rate on hover | ✓ |
| Full timing table | Detailed table per item | |
| Text-only annotation | No visual bar, just text | |

| Option | Description | Selected |
|--------|-------------|----------|
| Pulsing accent border | Animated crimson border for urgent items | ✓ |
| Icon badge | Small icon indicator | |
| Text label "URGENT" | Text-only urgency | |

| Option | Description | Selected |
|--------|-------------|----------|
| Tooltip only | Confidence on hover | ✓ |
| Inline label | Always visible | |
| Opacity variation | Bar opacity reflects confidence | |

| Option | Description | Selected |
|--------|-------------|----------|
| All items with data | Per D-07, no data hidden. Weak confidence muted. | ✓ |
| Only strong/moderate | Hide weak data | |

**User's choice:** Accept all recommended
**Notes:** All 4 questions accepted as recommended.

---

## Claude Timing Reasoning

| Option | Description | Selected |
|--------|-------------|----------|
| Per-item timing section | New _build_timing_section() in context builder, ~200 tokens | ✓ |
| Inline with item catalog | Timing data mixed into catalog | |
| Separate timing-only prompt | Separate prompt section | |

| Option | Description | Selected |
|--------|-------------|----------|
| Hero's popular items only | Filtered to hero-specific timing data | ✓ |
| All items in catalog | Unfiltered | |
| Top 10 by popularity | Limited to most popular | |

| Option | Description | Selected |
|--------|-------------|----------|
| Natural language with numbers | Claude cites specific percentages naturally | ✓ |
| Structured timing field | Forced format per item | |

**User's choice:** Accept all recommended
**Notes:** All 3 questions accepted as recommended.

---

## GSI Live Timing Comparison

| Option | Description | Selected |
|--------|-------------|----------|
| Progress marker on timing bar | "You are here" marker based on game clock, "X gold away" below | ✓ |
| Separate timing dashboard | Dedicated panel | |
| Countdown timer | Timer until timing window closes | |

| Option | Description | Selected |
|--------|-------------|----------|
| Muted styling + "window passed" | Grey out bar, show label, keep item | ✓ |
| Remove from recommendations | Drop the item | |
| Red warning banner | Aggressive alert | |

| Option | Description | Selected |
|--------|-------------|----------|
| All unpurchased items | Show timing on all items not yet purchased | ✓ |
| Only next item | Just the immediate next purchase | |
| Only current phase items | Limited to current game phase | |

**User's choice:** Accept all recommended
**Notes:** All 3 questions accepted as recommended.

---

## Claude's Discretion

- Good/on-track/late range derivation from TimingBucket data
- Steep win-rate falloff threshold for urgency classification
- TimingBar component structure and animation
- GSI marker update mechanism
- API response schema extension for timing data

## Deferred Ideas

- Per-match timing comparison (requires Steam login)
- Prescriptive exact-minute targets (false precision)
- Timing-aware re-evaluation weighting (ADVINT-02)

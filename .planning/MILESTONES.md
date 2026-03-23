# Milestones

## v1.1 Allied Synergy & Neutral Items (Shipped: 2026-03-23)

**Phases completed:** 3 phases, 6 plans, 12 tasks

**Key accomplishments:**

- Removed 3 dead API methods, wired /admin/ through Nginx proxy, added auto-dismiss error toasts and concise empty state text
- 32 unit tests added for recommendationStore (Zustand) and context_builder (Python) covering all store actions, toggle behaviors, midgame formatting, and full prompt assembly
- Allied hero names and popular item builds wired into Claude user message via _build_ally_lines() with OpenDota popularity data
- Team Coordination section with aura dedup, combo awareness, and gap filling rules added to Claude system prompt with ally-aware reasoning example
- Neutral item data pipeline wired end-to-end: seed fix, tier query, schema extension, context catalog, system prompt rules, and recommender passthrough with 14 new tests
- NeutralItemSection component rendering all 5 tiers with ranked picks, per-item reasoning, and Steam CDN images below the purchasable item timeline

---

## v1.0 MVP (Shipped: 2026-03-21)

**Phases completed:** 6 phases, 14 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---

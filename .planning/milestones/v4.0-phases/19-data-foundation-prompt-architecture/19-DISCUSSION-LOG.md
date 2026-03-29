# Phase 19: Data Foundation & Prompt Architecture - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-27
**Phase:** 19-data-foundation-prompt-architecture
**Areas discussed:** Timing data refresh, Prompt architecture, Data quality filters

---

## Timing Data Refresh

| Option | Description | Selected |
|--------|-------------|----------|
| Daily batch refresh | Fetch all 124 heroes during APScheduler pipeline. ~3,700 API calls/month (7.4% of free tier). All data ready upfront, ~2.5 min at 60 req/min. | |
| Stale-while-revalidate | Fetch per-hero on first request, cache in DB, background refresh when stale (24h). Matches uncommitted matchup_service pattern. Only fetches queried heroes. | ✓ |
| You decide | Let Claude pick based on architecture constraints | |

**User's choice:** Stale-while-revalidate
**Notes:** Consistent with existing matchup_service pattern and uncommitted HeroItemPopularity changes.

### Follow-up: Ability Data Refresh

| Option | Description | Selected |
|--------|-------------|----------|
| Daily batch (Recommended) | Add to existing APScheduler pipeline alongside heroes/items. Only 2 extra API calls/day. | ✓ |
| Startup-only | Fetch once at app startup, never refresh until restart. | |
| You decide | Let Claude pick based on architecture fit | |

**User's choice:** Daily batch (Recommended)
**Notes:** Ability data is global (2 endpoints, not per-hero), changes only on Dota patches.

---

## Prompt Architecture

| Option | Description | Selected |
|--------|-------------|----------|
| Directives only | System prompt = identity + reasoning rules + output format + examples. ALL dynamic data in user message. | |
| Directives + static knowledge | Keep domain knowledge in system prompt alongside directives. Only truly per-request data in user message. | |
| You decide | Let Claude determine the optimal split based on token budget and caching | ✓ |

**User's choice:** You decide (Claude's discretion)
**Notes:** Goal is system prompt under ~5K tokens, cache-friendly. Claude determines optimal split.

---

## Data Quality Filters

| Option | Description | Selected |
|--------|-------------|----------|
| Show with confidence | Always show, annotate: strong (1000+), moderate (200-999), weak (<200). No data hidden. | ✓ |
| Hard threshold | Only show with 500+ games. Silently omit weak data. | |
| You decide | Let Claude pick a threshold based on statistical significance | |

**User's choice:** Show with confidence
**Notes:** Always show timing data with confidence annotation. Downstream phases can display confidence visually.

---

## Claude's Discretion

- Prompt split strategy (system vs user message boundary)
- DataCache internal data structures for ability data
- Timing data cache structure
- Rate limiting / semaphore strategy for background refreshes
- Three-cache coherence extension

## Deferred Ideas

None — discussion stayed within phase scope.

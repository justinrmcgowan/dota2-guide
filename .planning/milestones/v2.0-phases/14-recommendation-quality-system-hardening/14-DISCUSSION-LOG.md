# Phase 14: Recommendation Quality & System Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-26
**Phase:** 14-recommendation-quality-system-hardening
**Areas discussed:** Rules engine expansion, Rate limiting & request dedup, Error transparency, Validation gaps

---

## Rules Engine Expansion

### Hero ID Source

| Option | Description | Selected |
|--------|-------------|----------|
| DB lookups (Recommended) | Rules query Hero table by name at startup, cache mapping. Never desyncs. | ✓ |
| Keep hardcoded | Current approach. Simple, no DB dependency. Risk: new heroes break rules silently. | |
| You decide | Claude picks the approach. | |

**User's choice:** DB lookups
**Notes:** None

### Rule Coverage Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Targeted additions (Recommended) | Add 5-10 high-value rules: boots by role, Raindrops, BKB timing, Mek/Pipe, Orchid. | ✓ |
| Comprehensive ruleset | Expand to 30+ rules. More items without API calls. Risk: maintenance, conflict with Claude. | |
| No expansion | Keep 12 rules, just fix hero IDs. | |

**User's choice:** Targeted additions
**Notes:** None

### Item ID Source

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, DB lookups for both (Recommended) | Both hero AND item IDs from DB by internal_name. Fully data-driven. | ✓ |
| Just hero IDs | Item IDs more stable. Keep hardcoded for simplicity. | |
| You decide | Claude picks based on stability. | |

**User's choice:** DB lookups for both
**Notes:** None

---

## Rate Limiting & Request Dedup

### Rate Limit Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Per-IP cooldown (Recommended) | 1 req/10s per IP. 429 with Retry-After. In-memory dict. | ✓ |
| Global token bucket | 5 req/min globally with burst. Overkill for single-user. | |
| Frontend-only debounce | Disable button for 10s. No backend enforcement. Bypassable. | |

**User's choice:** Per-IP cooldown
**Notes:** None

### Request Deduplication

| Option | Description | Selected |
|--------|-------------|----------|
| Short-TTL in-memory cache (Recommended) | Hash payload, cache 5 min. Python dict with TTL. No Redis. | ✓ |
| No caching | Every request calls Claude. Simpler. Relies on rate limiting alone. | |
| You decide | Claude picks best caching for single-user. | |

**User's choice:** Short-TTL in-memory cache
**Notes:** None

---

## Error Transparency

### Error Detail Level

| Option | Description | Selected |
|--------|-------------|----------|
| Reason category + retry hint (Recommended) | Show failure type + actionable hint. E.g., "AI timed out — showing rules-based build." | ✓ |
| Minimal (current) | Keep "Rules-based only" message. Fallback is the feature. | |
| Full technical detail | Show error class, status code, raw message. Helpful for debugging. | |

**User's choice:** Reason category + retry hint
**Notes:** None

### Fallback Notice Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Toast + strategy text (Recommended) | Auto-dismiss toast AND updated overall_strategy text. Two signals. | ✓ |
| Strategy text only | Just update overall_strategy. Quieter. | |
| You decide | Claude picks best UX. | |

**User's choice:** Toast + strategy text
**Notes:** None

---

## Validation Gaps

### Damage Profile Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Frontend + backend validation (Recommended) | Frontend auto-adjusts sliders to sum 100%. Backend rejects != 100% with 422. | ✓ |
| Frontend only | Frontend enforces. Backend trusts it. | |
| You decide | Claude picks. | |

**User's choice:** Frontend + backend validation
**Notes:** None

### Invalid Item ID Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Pre-filter + post-validate (Recommended) | Stronger prompt instruction + keep post-LLM validation. Log filtered items. | ✓ |
| Post-validate only (current) | Invalid items silently removed. Simple but invisible. | |
| Reject and retry | Retry API call on invalid items. More expensive. | |

**User's choice:** Pre-filter + post-validate
**Notes:** None

### Playstyle Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Backend validation (Recommended) | Backend maintains role→playstyle mapping. Rejects invalid combos with 422. | ✓ |
| Trust frontend | Frontend already enforces. Backend accepts anything. | |
| You decide | Claude picks. | |

**User's choice:** Backend validation
**Notes:** None

---

## Claude's Discretion

- Exact wording of fallback toast messages
- Specific new rules to add (within 5-10 targeted scope)
- Cache implementation details (LRU vs TTL dict)
- Damage profile slider rebalancing UX (proportional vs sequential)
- Whether to add /api/playstyles endpoint or keep as backend constant

## Deferred Ideas

- localStorage persistence for game state across refreshes
- Frontend loading timeout for long /recommend calls
- Structured logging (JSON to stdout)
- Stratz API integration
- Redis-backed request dedup for multi-instance

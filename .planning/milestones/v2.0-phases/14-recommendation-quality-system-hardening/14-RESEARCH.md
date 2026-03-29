# Phase 14: Recommendation Quality & System Hardening - Research

**Researched:** 2026-03-26
**Domain:** Backend engine hardening, rate limiting, validation, error transparency
**Confidence:** HIGH

## Summary

Phase 14 is a hardening-only phase -- no new features, only improving the reliability, accuracy, and error transparency of existing systems. The four pillars are: (1) replacing hardcoded hero/item IDs in the rules engine with DB-backed lookups, (2) adding per-IP rate limiting and response caching to `/api/recommend`, (3) making Claude API failures transparent to users with actionable fallback messages, and (4) closing validation gaps in damage profile enforcement, playstyle-role validation, and system prompt item ID guidance.

The codebase is well-structured for these changes. The rules engine (`rules.py`) has a clear 74-entry `HERO_NAMES` dict and hardcoded item IDs across 12 rules that need DB migration. The recommender orchestrator already has a `fallback` boolean but no reason categorization. The existing `_fetch_locks` pattern in `matchup_service.py` provides a proven in-memory dict pattern that rate limiting and response caching can follow. The frontend already has `ErrorBanner.tsx` with `"error" | "fallback"` type support that needs extension for reason-specific messages.

**Primary recommendation:** Implement all four pillars as backend-first changes. The rules engine DB migration is the riskiest change (touches every rule); rate limiting and caching are isolated middleware; error transparency threads through backend response schema to frontend display; validation gaps are targeted fixes across both layers.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Replace all hardcoded hero IDs (74-entry HERO_NAMES dict) with DB lookups. Rules query Hero table by `localized_name` at startup, cache the name->ID mapping. Never desyncs with OpenDota data.
- **D-02:** Replace hardcoded item IDs in rules with DB lookups by `internal_name`. Both hero and item references are fully data-driven.
- **D-03:** Add 5-10 targeted high-value rules beyond the existing 12. Focus on obvious/deterministic cases: role-default boots, Raindrops vs magic harass, BKB timing by role, Mekansm/Pipe for support/offlane, Orchid vs escape heroes. Keep rules for fast/obvious decisions -- Claude handles nuance.
- **D-04:** Per-IP cooldown on `/api/recommend`: 1 request per 10 seconds per IP. Returns HTTP 429 with `Retry-After` header. In-memory dict, no external dependency (suitable for single-user Unraid deployment).
- **D-05:** Short-TTL in-memory response cache: hash the request payload, cache the full response for 5 minutes. Identical inputs return cached response instantly. Python dict with TTL expiry, no Redis needed. Covers double-clicks and repeated queries.
- **D-06:** When Claude fails, show the failure reason category + retry hint. Examples: "AI timed out -- showing rules-based build. Try again in a moment." or "AI response was malformed -- showing rules-based build." Actionable without being technical.
- **D-07:** Fallback notification uses both toast banner (Phase 7 auto-dismiss pattern) AND updated `overall_strategy` text. Two signals, neither blocking -- toast for immediate notice, strategy text for persistent context in the timeline.
- **D-08:** Backend returns a `fallback_reason` field in the response so the frontend can display the appropriate message. Enum: `timeout | parse_error | api_error | rate_limited`.
- **D-09:** Damage profile enforced on both frontend and backend. Frontend auto-adjusts sliders so physical + magical + pure always sum to 100% (drag one, others rebalance proportionally). Backend rejects requests where sum != 100% with 422.
- **D-10:** Backend validates playstyle against role using the same role->playstyle mapping as frontend. Rejects invalid combos with 422. Backend is single source of truth -- frontend constants.ts should ideally fetch from backend in the future.
- **D-11:** Strengthen item ID guidance in system prompt: "ONLY use IDs from Available Items -- any other ID is discarded." Keep post-LLM validation as safety net. Log filtered items with warning so prompt quality can be monitored.

### Claude's Discretion
- Exact wording of fallback toast messages
- Specific new rules to add (within the 5-10 targeted scope)
- Cache eviction strategy details (LRU vs TTL dict implementation)
- How the damage profile slider rebalancing works in the frontend (proportional vs sequential)
- Whether to add a `/api/playstyles` endpoint or keep the mapping as a backend constant

### Deferred Ideas (OUT OF SCOPE)
- **localStorage persistence** -- saving game state across page refreshes. Useful but UX feature, not hardening.
- **Frontend loading timeout** -- showing error if /recommend takes >45s. Related to error transparency but frontend-specific.
- **Structured logging** -- JSON logs to stdout. Operational improvement, separate phase.
- **Stratz API integration** -- config wired but never used. Data enrichment, separate phase.
- **Request dedup across sessions** -- Redis-backed cache for multi-instance. Overkill for single-user Unraid.
</user_constraints>

## Project Constraints (from CLAUDE.md)

- **Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy + SQLite (backend), React 18 + Vite + TypeScript + Tailwind CSS + Zustand (frontend)
- **Hybrid engine architecture:** Rules fire first (instant, no API call). Claude API second. Always have a fallback if LLM fails.
- **Structured JSON output** from Claude API -- parse and validate before returning to frontend.
- **Code Style:** Type hints throughout, async endpoints, Pydantic models for request/response validation (backend); TypeScript strict mode, functional components, hooks (frontend).
- **Dark theme** with spectral cyan (#00d4ff) primary accent, Radiant teal (#6aff97), Dire red (#ff5555).
- **Deployment:** Docker Compose on Unraid server. Backend port 8420, frontend port 8421. Single-user deployment.

## Architecture Patterns

### Recommended Changes by Module

```
prismlab/backend/
  engine/
    rules.py           # DB-backed hero/item lookups, 5-10 new rules
    recommender.py      # fallback_reason threading, response caching
    llm.py              # Error category returns (not just None)
    schemas.py          # fallback_reason enum field on RecommendResponse
    prompts/
      system_prompt.py  # Stronger item ID instruction
    context_builder.py  # No changes needed
  api/
    routes/
      recommend.py      # Rate limiting decorator/middleware
  middleware/
    rate_limiter.py     # NEW: Per-IP cooldown module
  config.py             # NEW env var: RESPONSE_CACHE_TTL_SECONDS
  data/
    models.py           # No schema changes needed
prismlab/frontend/
  src/
    types/
      recommendation.ts # Add fallback_reason field
    components/
      game/
        DamageProfileInput.tsx  # Slider rebalancing logic
      timeline/
        ErrorBanner.tsx         # Reason-specific fallback messages
      layout/
        MainPanel.tsx           # Toast + strategy text dual signal
    utils/
      constants.ts              # No changes (backend validates against its own copy)
```

### Pattern 1: DB-Backed Rules Engine Initialization

**What:** Replace `HERO_NAMES` dict and all hardcoded item/hero IDs with DB lookups at startup time.
**When to use:** Once at application startup (in `lifespan` or at module import time), cached in memory, refreshed when the 6h data refresh runs.

```python
# rules.py -- new pattern
class RulesEngine:
    """Priority-ordered deterministic rules for item recommendations.

    Hero and item references are loaded from DB at startup and cached.
    Call refresh_lookups() after data refresh to stay in sync.
    """

    def __init__(self) -> None:
        # Populated by init_lookups() at startup
        self._hero_name_to_id: dict[str, int] = {}
        self._hero_id_to_name: dict[int, str] = {}
        self._item_name_to_id: dict[str, int] = {}

    async def init_lookups(self, db: AsyncSession) -> None:
        """Load hero/item mappings from DB. Call at startup and after data refresh."""
        heroes = (await db.execute(select(Hero))).scalars().all()
        self._hero_name_to_id = {h.localized_name: h.id for h in heroes}
        self._hero_id_to_name = {h.id: h.localized_name for h in heroes}

        items = (await db.execute(select(Item))).scalars().all()
        self._item_name_to_id = {i.internal_name: i.id for i in items}

    def _hero_id(self, name: str) -> int:
        """Lookup hero ID by localized_name. KeyError if not found."""
        return self._hero_name_to_id[name]

    def _item_id(self, internal_name: str) -> int:
        """Lookup item ID by internal_name. KeyError if not found."""
        return self._item_name_to_id[internal_name]

    def _hero_name(self, hero_id: int) -> str:
        """Lookup hero localized_name by ID."""
        return self._hero_id_to_name.get(hero_id, "the enemy")
```

### Pattern 2: LLM Error Category Returns

**What:** Instead of returning `None` for all failures, the LLM engine returns a tuple `(result, error_category)` so the recommender can thread the reason to the response.
**When to use:** In `llm.py` generate method.

```python
# llm.py -- new pattern
from enum import Enum

class FallbackReason(str, Enum):
    timeout = "timeout"
    parse_error = "parse_error"
    api_error = "api_error"
    rate_limited = "rate_limited"

async def generate(self, user_message: str) -> tuple[LLMRecommendation | None, FallbackReason | None]:
    """Returns (result, None) on success, (None, reason) on failure."""
    try:
        # ... existing call logic ...
        return (LLMRecommendation.model_validate(data), None)
    except APITimeoutError:
        return (None, FallbackReason.timeout)
    except APIStatusError as e:
        if e.status_code == 429:
            return (None, FallbackReason.rate_limited)
        return (None, FallbackReason.api_error)
    except (json.JSONDecodeError, ValueError):
        return (None, FallbackReason.parse_error)
    except Exception:
        return (None, FallbackReason.api_error)
```

### Pattern 3: In-Memory Rate Limiting

**What:** Per-IP request cooldown using a simple dict with timestamp tracking.
**When to use:** As a FastAPI dependency on the `/api/recommend` endpoint.

```python
# middleware/rate_limiter.py
import time
from fastapi import Request, HTTPException

class InMemoryRateLimiter:
    """Per-IP request cooldown. In-memory, no external dependencies."""

    def __init__(self, cooldown_seconds: float = 10.0):
        self.cooldown = cooldown_seconds
        self._last_request: dict[str, float] = {}

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, respecting X-Forwarded-For for proxy setups."""
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def check(self, request: Request) -> None:
        """Raise 429 if client is within cooldown period."""
        ip = self._get_client_ip(request)
        now = time.monotonic()
        last = self._last_request.get(ip, 0)
        remaining = self.cooldown - (now - last)

        if remaining > 0:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Try again shortly.",
                headers={"Retry-After": str(int(remaining) + 1)},
            )

        self._last_request[ip] = now

    def cleanup(self, max_age: float = 300.0) -> None:
        """Evict expired entries to prevent unbounded memory growth."""
        cutoff = time.monotonic() - max_age
        expired = [ip for ip, ts in self._last_request.items() if ts < cutoff]
        for ip in expired:
            del self._last_request[ip]
```

### Pattern 4: Response Cache with TTL

**What:** Hash-based response caching using a dict with TTL expiry.
**When to use:** In the recommender or as a wrapper around the recommend endpoint.

```python
# In recommender.py or a separate cache module
import hashlib
import json
import time

class ResponseCache:
    """In-memory response cache with TTL. Hash request -> cached response."""

    def __init__(self, ttl_seconds: float = 300.0):
        self.ttl = ttl_seconds
        self._cache: dict[str, tuple[RecommendResponse, float]] = {}

    def _hash_request(self, request: RecommendRequest) -> str:
        """Deterministic hash of request payload."""
        payload = request.model_dump_json(exclude_none=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, request: RecommendRequest) -> RecommendResponse | None:
        """Return cached response if exists and not expired."""
        key = self._hash_request(request)
        entry = self._cache.get(key)
        if entry is None:
            return None
        response, timestamp = entry
        if time.monotonic() - timestamp > self.ttl:
            del self._cache[key]
            return None
        return response

    def set(self, request: RecommendRequest, response: RecommendResponse) -> None:
        """Cache a response."""
        key = self._hash_request(request)
        self._cache[key] = (response, time.monotonic())

    def cleanup(self) -> None:
        """Evict expired entries."""
        now = time.monotonic()
        expired = [k for k, (_, ts) in self._cache.items() if now - ts > self.ttl]
        for k in expired:
            del self._cache[k]
```

### Pattern 5: Damage Profile Slider Rebalancing (Frontend)

**What:** When one slider moves, the other two adjust proportionally to maintain a 100% sum.
**When to use:** In `DamageProfileInput.tsx` handleSliderChange.

```typescript
const handleSliderChange = (
  key: "physical" | "magical" | "pure",
  newValue: number,
) => {
  const others = SLIDER_CONFIG
    .map((s) => s.key)
    .filter((k) => k !== key) as ("physical" | "magical" | "pure")[];

  const remaining = 100 - newValue;
  const otherSum = others.reduce((sum, k) => sum + current[k], 0);

  const updated = { ...current, [key]: newValue };

  if (otherSum === 0) {
    // Split remaining equally if others are both 0
    updated[others[0]] = Math.round(remaining / 2);
    updated[others[1]] = remaining - updated[others[0]];
  } else {
    // Proportional redistribution
    let allocated = 0;
    for (let i = 0; i < others.length; i++) {
      const k = others[i];
      if (i === others.length - 1) {
        updated[k] = remaining - allocated; // Last one gets remainder
      } else {
        updated[k] = Math.round((current[k] / otherSum) * remaining);
        allocated += updated[k];
      }
    }
  }

  setDamageProfile(updated);
};
```

### Anti-Patterns to Avoid

- **External dependency for rate limiting:** No Redis, no slowapi. In-memory dict is correct for single-user Unraid deployment per D-04.
- **Global middleware for rate limiting:** Only `/api/recommend` needs rate limiting. Other endpoints (heroes, items, health) should remain unrestricted.
- **Returning None from LLM for all failures:** Currently all error paths return `None` with no category. Must differentiate timeout vs parse error vs API error.
- **Frontend-only validation:** Backend MUST enforce damage profile sum = 100% and playstyle-role mapping. Frontend validation is UX convenience, not security.
- **Blocking cache cleanup:** Use periodic background task (piggyback on existing scheduler) or lazy eviction, not blocking cleanup on every request.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Request payload hashing | Custom string concatenation | `hashlib.sha256(model.model_dump_json())` | Pydantic's `model_dump_json` is deterministic with `exclude_none=True`; sha256 avoids collisions |
| IP extraction from proxy | Manual header parsing | `request.client.host` + `X-Forwarded-For` split | Standard pattern, but keep it simple since Nginx/Cloudflare is the only proxy |
| Rate limit timer | `datetime.now()` arithmetic | `time.monotonic()` | Monotonic clock is immune to system clock drift/NTP jumps |
| JSON schema enum | Raw string literals | Python `Enum(str, Enum)` | Pydantic serializes string enums automatically; catches typos at define-time |

**Key insight:** Every component in this phase is intentionally simple (in-memory dict, monotonic clock, Pydantic model hash) because the deployment is single-process, single-user Unraid. Over-engineering for multi-instance is explicitly deferred.

## Common Pitfalls

### Pitfall 1: Rules Engine Initialization Timing

**What goes wrong:** Rules engine is instantiated at module import time in `recommend.py` (line 27: `_rules = RulesEngine()`). DB-backed lookups require an async session, which isn't available at import time.
**Why it happens:** Python module-level code runs synchronously at import. SQLAlchemy async sessions need an event loop.
**How to avoid:** Either (a) lazy-init the lookups on first request with a `_initialized` flag, or (b) call `_rules.init_lookups(db)` in the FastAPI `lifespan` startup handler where async is available. Option (b) is cleaner -- it matches the existing `seed_if_empty()` startup pattern.
**Warning signs:** `KeyError` on hero/item lookups, empty `_hero_name_to_id` dict.

### Pitfall 2: Cache Key Determinism

**What goes wrong:** Two identical requests produce different cache keys because of field ordering or default values in JSON serialization.
**Why it happens:** Python dicts preserve insertion order, but Pydantic's `model_dump_json()` is deterministic by field definition order. However, `exclude_none=True` changes the key if optional fields are `None` vs absent.
**How to avoid:** Always use `model_dump_json(exclude_none=True)` for hashing. Alternatively, use `model_dump_json()` without exclusion to be consistent.
**Warning signs:** Cache misses for identical user inputs.

### Pitfall 3: Rate Limiter Memory Growth

**What goes wrong:** `_last_request` dict grows unbounded if many different IPs hit the server (unlikely for single-user Unraid, but defensive coding matters).
**Why it happens:** Entries are only added, never cleaned up.
**How to avoid:** Periodic cleanup via `scheduler.add_job()` (same APScheduler already used for data refresh) or lazy eviction on each check call when dict exceeds a size threshold (e.g., 1000 entries).
**Warning signs:** Gradual memory increase in long-running container.

### Pitfall 4: Frontend 429 Handling

**What goes wrong:** The frontend `postJson` helper throws a generic "API error: 429" message that doesn't match the user-friendly intent of D-06.
**Why it happens:** `client.ts` line 27: `throw new Error('API error: ${response.status} ${response.statusText}')`. No special handling for 429.
**How to avoid:** Parse the response body for 429 responses to extract the `Retry-After` header and show a specific message like "Please wait a moment before requesting again."
**Warning signs:** User sees raw "API error: 429 Too Many Requests" instead of friendly message.

### Pitfall 5: Slider Rounding Errors

**What goes wrong:** Proportional redistribution of damage profile values produces floating point results that don't sum to exactly 100 after `Math.round()`.
**Why it happens:** `Math.round(33.33)` = 33, `Math.round(33.33)` = 33, but 100 - 34 - 33 - 33 = 0, not balanced.
**How to avoid:** Always compute the last slider as `remaining - sum_of_others` instead of rounding independently. This is the "remainder assignment" pattern shown in the code example.
**Warning signs:** Damage profile values that sum to 99 or 101, causing backend 422 rejection.

### Pitfall 6: Stale Test Assertions After DB Migration

**What goes wrong:** Existing test_rules.py tests use hardcoded item IDs (e.g., `r.item_id == 36` for Magic Stick). After DB migration, the rules engine returns DB-looked-up IDs that must match.
**Why it happens:** Tests assume specific numeric IDs that are seeded in conftest.py.
**How to avoid:** Ensure conftest.py seeds match the IDs the rules engine will look up. Since rules will query by `internal_name`, the seeded items in conftest.py must have correct `internal_name` values. The current conftest.py already seeds items with correct internal_names and IDs.
**Warning signs:** All rules engine tests break after DB migration despite correct logic.

## Code Examples

### Existing Error Banner Extension

The current `ErrorBanner.tsx` supports `type: "error" | "fallback"`. For Phase 14, extend to use the `fallback_reason` from the response:

```typescript
// recommendation.ts -- add to RecommendResponse
export interface RecommendResponse {
  // ... existing fields ...
  fallback_reason: "timeout" | "parse_error" | "api_error" | "rate_limited" | null;
}

// Fallback message mapping
const FALLBACK_MESSAGES: Record<string, string> = {
  timeout: "AI timed out -- showing rules-based build. Try again in a moment.",
  parse_error: "AI response was malformed -- showing rules-based build.",
  api_error: "AI service unavailable -- showing rules-based build. Try again shortly.",
  rate_limited: "AI rate limited -- showing rules-based build. Try again in a moment.",
};
```

### Backend Playstyle-Role Validation

```python
# In schemas.py or a new validation module
VALID_PLAYSTYLES: dict[int, set[str]] = {
    1: {"Farm-first", "Aggressive", "Split-push", "Fighting"},
    2: {"Tempo", "Ganker", "Greedy", "Space-maker"},
    3: {"Frontline", "Aura-carrier", "Initiator", "Greedy"},
    4: {"Roamer", "Lane-dominator", "Greedy", "Save"},
    5: {"Lane-protector", "Roamer", "Greedy", "Save"},
}

# In RecommendRequest validator
@field_validator("playstyle")
@classmethod
def validate_playstyle(cls, v: str, info) -> str:
    role = info.data.get("role")
    if role and v not in VALID_PLAYSTYLES.get(role, set()):
        raise ValueError(f"Playstyle '{v}' is not valid for role {role}")
    return v
```

### Backend Damage Profile Validation

```python
# In RecommendRequest model validator
@model_validator(mode="after")
def validate_damage_profile_sum(self) -> "RecommendRequest":
    if self.damage_profile is not None:
        total = sum(self.damage_profile.values())
        if total != 100:
            raise ValueError(
                f"Damage profile must sum to 100%, got {total}%"
            )
    return self
```

### System Prompt Item ID Strengthening

```python
# Addition to system prompt
"- Use ONLY item_ids from the \"Available Items\" list. The number before the colon is the id.\n"
"- CRITICAL: Any item_id NOT in the Available Items list will be silently discarded. "
"Do not guess or invent IDs. If unsure, omit the item.\n"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded HERO_NAMES dict (74 entries) | DB-backed lookup cached at startup | Phase 14 | Rules never desync with OpenDota data refresh |
| `fallback: bool` only | `fallback_reason: enum` with categorized errors | Phase 14 | Users understand why AI failed and when to retry |
| No rate limiting on /api/recommend | Per-IP 10s cooldown | Phase 14 | Prevents accidental API cost spikes from double-clicks |
| Damage profile sliders independent (can sum > 100%) | Auto-rebalancing to 100% + backend enforcement | Phase 14 | Invalid inputs impossible to submit |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (Backend) | pytest + pytest-asyncio |
| Framework (Frontend) | Vitest + @testing-library/react + jsdom |
| Config file (Backend) | `prismlab/backend/tests/conftest.py` (shared fixtures) |
| Config file (Frontend) | `prismlab/frontend/vitest.config.ts` |
| Quick run (Backend) | `cd prismlab/backend && python -m pytest tests/ -x -q` |
| Quick run (Frontend) | `cd prismlab/frontend && npx vitest run --reporter=verbose` |
| Full suite | Both commands above |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-01 | Hero ID lookup from DB, not hardcoded | unit | `pytest tests/test_rules.py -x -k "db_lookup or init_lookups"` | Wave 0 |
| D-02 | Item ID lookup from DB, not hardcoded | unit | `pytest tests/test_rules.py -x -k "item_lookup"` | Wave 0 |
| D-03 | 5-10 new rules fire correctly | unit | `pytest tests/test_rules.py -x -k "new_rule or raindrops or orchid or mek or pipe"` | Wave 0 |
| D-04 | Rate limiting returns 429 with Retry-After | unit | `pytest tests/test_rate_limiter.py -x` | Wave 0 |
| D-05 | Response cache returns cached response within TTL | unit | `pytest tests/test_response_cache.py -x` | Wave 0 |
| D-06/D-08 | fallback_reason in response with correct category | unit | `pytest tests/test_recommender.py -x -k "fallback_reason"` | Wave 0 |
| D-09 (backend) | Damage profile sum != 100 returns 422 | unit | `pytest tests/test_api.py -x -k "damage_profile"` | Wave 0 |
| D-09 (frontend) | Sliders auto-rebalance to 100% | unit | `npx vitest run src/components/game/DamageProfileInput.test.tsx` | Wave 0 |
| D-10 | Invalid playstyle-role combo returns 422 | unit | `pytest tests/test_api.py -x -k "playstyle_validation"` | Wave 0 |
| D-11 | System prompt contains stronger item ID instruction | unit | `pytest tests/test_rules.py -x -k "system_prompt or item_id_instruction"` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd prismlab/backend && python -m pytest tests/ -x -q`
- **Per wave merge:** Full suite (backend + frontend)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_rate_limiter.py` -- covers D-04 (rate limiting 429, Retry-After, cleanup)
- [ ] `tests/test_response_cache.py` -- covers D-05 (TTL cache hit/miss/expiry/hash determinism)
- [ ] Extend `tests/test_recommender.py` -- covers D-06/D-08 (fallback_reason categories)
- [ ] Extend `tests/test_rules.py` -- covers D-01, D-02, D-03 (DB lookups + new rules)
- [ ] Extend `tests/test_api.py` -- covers D-09, D-10 (validation 422s)
- [ ] `src/components/game/DamageProfileInput.test.tsx` -- covers D-09 frontend (slider rebalancing)
- [ ] Extend conftest.py with any new heroes/items needed for new rules

## Open Questions

1. **Rules engine initialization on data refresh**
   - What we know: The 6h scheduler calls `refresh_all_data()`. The rules engine needs its lookup cache refreshed after this runs.
   - What's unclear: Whether to pass the rules engine instance to the refresh function or use a global signal/event pattern.
   - Recommendation: Add a `refresh_lookups()` call at the end of `refresh_all_data()` or have the scheduler call it separately. The `_rules` singleton in `recommend.py` is the instance that needs refreshing.

2. **Playstyle endpoint vs constant**
   - What we know: CONTEXT.md gives discretion on whether to add `/api/playstyles` or keep as backend constant.
   - What's unclear: Whether future phases will need to fetch this mapping.
   - Recommendation: Keep as a backend constant (`VALID_PLAYSTYLES` dict) for now. It changes only when the game changes roles, which is extremely rare. A `@field_validator` on `RecommendRequest` is sufficient.

3. **Response cache TTL configurability**
   - What we know: CONTEXT.md mentions TTL should be configurable via env var.
   - What's unclear: Default value is 300s (5 min). Whether to also cap max cache size.
   - Recommendation: Add `RESPONSE_CACHE_TTL_SECONDS: int = 300` to `Settings` in `config.py`. Cap cache size at 100 entries (single-user deployment won't need more).

## Sources

### Primary (HIGH confidence)
- Direct code inspection of all 14 canonical reference files listed in CONTEXT.md
- `prismlab/backend/engine/rules.py` -- 527 lines, 12 rules, 74-entry HERO_NAMES dict
- `prismlab/backend/engine/recommender.py` -- 249 lines, existing fallback boolean
- `prismlab/backend/engine/llm.py` -- 153 lines, all error paths return None
- `prismlab/backend/engine/schemas.py` -- 230 lines, RecommendResponse without fallback_reason
- `prismlab/frontend/src/components/game/DamageProfileInput.tsx` -- 91 lines, no rebalancing
- `prismlab/frontend/src/components/timeline/ErrorBanner.tsx` -- 53 lines, error|fallback types
- `prismlab/backend/tests/conftest.py` -- shared test fixtures with seeded heroes/items
- `prismlab/backend/tests/test_rules.py` -- 210 lines, 12 test classes for existing rules

### Secondary (MEDIUM confidence)
- [FastAPI Rate Limiting Guide](https://patrykgolabek.dev/guides/fastapi-production/rate-limiting/) -- per-IP in-memory pattern
- [FastAPI Response Caching Patterns](https://www.fastapiinteractive.com/fastapi-advanced-patterns/07-caching-patterns/) -- TTL dict caching with hashlib
- [FastAPI Throttle (no-dependency rate limiter)](https://github.com/AliYmn/fastapi-throttle) -- confirms in-memory approach is standard for single-instance

### Tertiary (LOW confidence)
- None -- all findings verified against codebase and official documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries needed, all changes use existing FastAPI/Pydantic/SQLAlchemy patterns
- Architecture: HIGH -- all four pillars map cleanly to existing module structure
- Pitfalls: HIGH -- identified from direct code inspection of timing, serialization, and test fixture patterns

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable domain, no external dependency changes)

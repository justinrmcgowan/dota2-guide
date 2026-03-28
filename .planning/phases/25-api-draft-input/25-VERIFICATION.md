---
phase: 25-api-draft-input
verified: 2026-03-28T18:30:00Z
status: gaps_found
score: 6/8 must-haves verified
re_verification: false
gaps:
  - truth: "Frontend TypeScript compiles without errors introduced by this phase"
    status: failed
    reason: "App.tsx line 19 triggers TS6198 — fetchDraft and isPolling are destructured from useLiveDraft but never used anywhere in the component, causing 'All destructured elements are unused' error in strict mode"
    artifacts:
      - path: "prismlab/frontend/src/App.tsx"
        issue: "const { fetchDraft, isPolling } = useLiveDraft(heroes); — both return values are unused, strict TypeScript flags TS6198"
    missing:
      - "Either prefix unused destructured variables with underscore (_fetchDraft, _isPolling) to suppress the error, or wire them to a visible element (e.g., a Refresh Draft button or polling indicator). The plan noted D-05 refresh button was deferred; the variable naming must still satisfy the compiler."
  - truth: "Backend tests cover the new /api/live-match/{account_id} and /api/settings/defaults endpoints"
    status: failed
    reason: "No test file covers either new endpoint. test_api.py has no tests for /api/live-match or /api/settings/defaults. test_config.py does not assert steam_id default."
    artifacts:
      - path: "prismlab/backend/tests/test_api.py"
        issue: "No test for GET /api/live-match/{account_id} or GET /api/settings/defaults"
      - path: "prismlab/backend/tests/test_config.py"
        issue: "steam_id field added to Settings but not asserted in test_settings_defaults"
    missing:
      - "Add test for GET /api/settings/defaults returning {steam_id: None} when not configured"
      - "Add test for GET /api/live-match/{account_id} with mocked StratzClient and OpenDotaClient returning None (no live match found)"
      - "Optionally add test for steam_id default in test_config.py: assert s.steam_id is None"
human_verification:
  - test: "Open Settings panel and verify Steam ID field renders with placeholder 76561198353796011, accepts input, persists to localStorage on valid 17-digit ID, and shows red error text on invalid input"
    expected: "Field labeled 'Your Steam ID (64-bit)' with validation indicator and localStorage persistence"
    why_human: "UI rendering and validation UX cannot be verified programmatically"
  - test: "With GSI connected in-game during hero pick phase, verify useLiveDraft auto-populates ally/opponent hero slots without any user action"
    expected: "Ally and opponent pickers fill automatically within 10s of GSI connect; hero/role/side pre-set from API data"
    why_human: "Requires live Dota 2 match + GSI stream + Stratz API returning real data"
  - test: "With STEAM_ID set in .env, open Settings panel before entering a Steam ID — verify the field pre-fills from the backend default"
    expected: "Steam ID field populated from /api/settings/defaults on first open when localStorage is empty"
    why_human: "Requires specific env configuration to test the pre-fill path"
---

# Phase 25: API-Driven Draft Input Verification Report

**Phase Goal:** Auto-populate allies and opponents from OpenDota/Stratz live match API using Steam ID, replacing manual hero selection during active games
**Verified:** 2026-03-28T18:30:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Stratz GraphQL client exists with two-step lookup | VERIFIED | `prismlab/backend/data/stratz_client.py` — 159 lines, `fetch_player_last_match_id`, `fetch_live_match`, `fetch_live_match_for_player` all implemented with proper error handling |
| 2 | OpenDota live fallback exists | VERIFIED | `opendota_client.py` lines 103-145 — `fetch_live_match_for_player` scans `/live` endpoint, handles HTTP errors and timeouts |
| 3 | `/api/live-match/{account_id}` endpoint registered and returns normalized data | VERIFIED | `live_match.py` — Stratz-first architecture, both `_normalize_stratz` and `_normalize_opendota` helpers, registered in `main.py` line 98 via `live_match_router` |
| 4 | `/api/settings/defaults` returns `steam_id` from config | VERIFIED | `settings.py` lines 39-47 — endpoint returns `{"steam_id": settings.steam_id}`, config has `steam_id: str | None = None` |
| 5 | Steam ID stored in Settings panel with localStorage persistence | VERIFIED | `SettingsPanel.tsx` lines 13-14, 60-71 — `prismlab_steam_id` key, real-time validation via `isValidSteamId`, localStorage read on init |
| 6 | `useLiveDraft` hook polls on GSI connect and auto-fills gameStore | VERIFIED | `useLiveDraft.ts` — `useGsiStore.subscribe` watches `gsiStatus`, immediate fetch on connect, `setInterval` every 10s, calls `gameStore.setSide`, `setAlly`, `setOpponent`, `selectHero`, `setRole` |
| 7 | Frontend TypeScript compiles without errors introduced by this phase | FAILED | `App.tsx:19` — TS6198: `fetchDraft` and `isPolling` destructured but never used in component body |
| 8 | Backend tests cover new endpoints | FAILED | No tests exist for `/api/live-match/{account_id}` or `/api/settings/defaults` |

**Score:** 6/8 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `prismlab/backend/data/stratz_client.py` | Stratz GraphQL client, two-step lookup | VERIFIED | 159 lines, three async methods, proper httpx error handling |
| `prismlab/backend/data/opendota_client.py` | `fetch_live_match_for_player` fallback | VERIFIED | Lines 103-145, scans `/live`, handles errors |
| `prismlab/backend/api/routes/live_match.py` | Unified endpoint with normalization | VERIFIED | Full implementation, Pydantic models, dual-source fallback |
| `prismlab/backend/api/routes/settings.py` | `GET /settings/defaults` endpoint | VERIFIED | Lines 39-47 added to existing file |
| `prismlab/backend/config.py` | `steam_id: str | None = None` field | VERIFIED | Line 13 |
| `prismlab/backend/main.py` | Router registration | VERIFIED | Line 98: `live_match_router` registered with `/api` prefix |
| `prismlab/frontend/src/utils/steamId.ts` | 64-bit to 32-bit conversion + validation | VERIFIED | BigInt arithmetic, 17-digit regex validation |
| `prismlab/frontend/src/types/livematch.ts` | TS types matching backend Pydantic models | VERIFIED | `LiveMatchPlayer` and `LiveMatchResponse` interfaces match backend exactly |
| `prismlab/frontend/src/api/client.ts` | `getLiveMatch` and `getSettingsDefaults` | VERIFIED | Lines 63-67 added, correct URL patterns |
| `prismlab/frontend/src/components/settings/SettingsPanel.tsx` | Steam ID input with localStorage + pre-fill | VERIFIED | Lines 13-31, 60-71, 193-227 — full implementation |
| `prismlab/frontend/src/hooks/useLiveDraft.ts` | Polling hook with GSI subscription | VERIFIED | 151 lines, full implementation per decisions D-03, D-04, D-06, D-08 |
| `prismlab/frontend/src/App.tsx` | `useLiveDraft` integrated at app level | STUB | Hook called, but destructured return values unused — TS6198 error |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `useLiveDraft` | `gsiStore` | `useGsiStore.subscribe` | WIRED | Lines 121-148 — subscribes to `gsiStatus` changes |
| `useLiveDraft` | `api.getLiveMatch` | `fetchDraft` callback | WIRED | Line 111 — `api.getLiveMatch(accountId)` called |
| `useLiveDraft` | `gameStore` | `setSide`, `setAlly`, `setOpponent`, `selectHero`, `setRole` | WIRED | Lines 44-86 — all five store setters confirmed present in gameStore |
| `App.tsx` | `useLiveDraft` | Hook call + destructure | PARTIAL | Hook called and runs, but `fetchDraft`/`isPolling` unused — polling side-effect fires, manual refresh not yet wired |
| `SettingsPanel` | `api.getSettingsDefaults` | `useEffect` on mount | WIRED | Lines 19-31 — fetches on mount if localStorage empty |
| `live_match router` | `main.py` | `app.include_router` | WIRED | Line 98 in main.py |
| `StratzClient` | `OpenDotaClient` | Fallback in `get_live_match` | WIRED | Lines 150-165 of live_match.py |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `useLiveDraft.ts` | `match` (LiveMatchResponse) | `api.getLiveMatch` → `GET /api/live-match/{id}` → Stratz GraphQL or OpenDota `/live` | Real API data (external, not hardcoded) | FLOWING |
| `SettingsPanel.tsx` | `steamId` | `localStorage.getItem("prismlab_steam_id")` or `/api/settings/defaults` | Real config value from env | FLOWING |
| `live_match.py` | `LiveMatchResponse` | `StratzClient.fetch_live_match_for_player` or `OpenDotaClient.fetch_live_match_for_player` | Real external API | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend tests pass | `python -m pytest tests/ -x -q` | 257 passed, 2 skipped, 7 warnings | PASS |
| TypeScript no new errors (phase 25 files) | `npx tsc -b --noEmit` | TS6198 at App.tsx:19 from phase 25 | FAIL |
| `steamId64ToAccountId` arithmetic correct | Module-level check | `76561198353796011 - 76561197960265728 = 393530283` (matches user Steam ID3 in context) | PASS |
| `useLiveDraft` exported correctly | `grep "export function useLiveDraft"` | Found in `useLiveDraft.ts:17` | PASS |
| `live_match_router` registered | `grep "live_match_router" main.py` | Line 98 confirmed | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DRAFT-01 | 25-01 | Stratz GraphQL as primary data source | SATISFIED | `stratz_client.py` with two-step lookup |
| DRAFT-02 | 25-01 | OpenDota fallback when Stratz unavailable | SATISFIED | `opendota_client.fetch_live_match_for_player` + fallback logic in endpoint |
| DRAFT-03 | 25-01 | `/api/live-match/{account_id}` unified endpoint | SATISFIED | Full implementation with Pydantic models |
| DRAFT-04 | 25-02 | Steam ID in Settings with localStorage, backend pre-fill | SATISFIED | SettingsPanel lines 13-31 |
| DRAFT-05 | 25-02 | `useLiveDraft` hook with GSI-triggered polling | SATISFIED (functional) | Hook implemented and integrated; manual refresh button deferred per plan |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `prismlab/frontend/src/App.tsx` | 19 | `const { fetchDraft, isPolling } = useLiveDraft(heroes);` — both values unused | Blocker | TypeScript TS6198 error in strict mode — build fails type check |

**Note on pre-existing errors:** The TypeScript errors in `GameClock.test.tsx`, `LiveStatsBar.test.tsx`, `GsiStatusIndicator.test.tsx`, `useGameIntelligence.test.ts`, and `gsiStore.test.ts` (missing `has_aghanims_shard`/`has_aghanims_scepter` in test fixtures) are pre-existing and introduced by commit `2dea083` (after phase 25 commits). These are not attributable to phase 25.

---

### Human Verification Required

#### 1. Steam ID Settings UI

**Test:** Open Settings panel in the browser. Verify the Steam ID section renders with label "Your Steam ID (64-bit)", placeholder "e.g. 76561198353796011", and a help text link. Enter an invalid value and confirm red error text "Enter a valid 17-digit Steam ID" appears. Enter a valid 17-digit ID, close and reopen the panel — confirm the value persists.
**Expected:** Field renders, validates in real time, persists to localStorage
**Why human:** UI rendering, real-time validation feedback, and localStorage round-trip require browser interaction

#### 2. Live Auto-Draft Population (Full Flow)

**Test:** With the backend running and a Stratz/OpenDota API token configured, start a Dota 2 match with GSI active and the user's Steam ID set. Observe the ally/opponent pickers in Prismlab during the hero selection phase.
**Expected:** Within 10s of GSI connect, ally heroes (same team, excluding self) and opponent heroes auto-fill into the pickers without any button click. Hero, role, and side also pre-fill.
**Why human:** Requires a live Dota 2 game, GSI connection, and external API keys returning real data

#### 3. Backend .env Pre-fill

**Test:** Set `STEAM_ID=76561198353796011` in the backend `.env`, clear `prismlab_steam_id` from localStorage, open the Settings panel.
**Expected:** Steam ID field pre-fills with the value from `.env` via `/api/settings/defaults` without user action
**Why human:** Requires specific env configuration; the pre-fill path only runs when localStorage is empty

---

### Gaps Summary

Two gaps block full goal achievement:

**Gap 1 — TypeScript TS6198 (blocker):** The `fetchDraft` and `isPolling` values returned from `useLiveDraft` are destructured in `App.tsx` but never consumed. In TypeScript strict mode this raises `TS6198: All destructured elements are unused`. The D-05 manual refresh button was intentionally deferred, but the unused destructure must still satisfy the compiler. Fix: prefix with underscores (`_fetchDraft`, `_isPolling`) to signal intentional non-use, or suppress via an `eslint-disable` comment if the project convention allows it. The hook itself works correctly — this is purely a naming/binding issue.

**Gap 2 — No endpoint tests (incomplete):** Neither `/api/live-match/{account_id}` nor `/api/settings/defaults` has test coverage. The two new routes are substantive and wired, but the test suite does not verify them. This means a regression in the normalization logic or router registration would go undetected. Minimum viable tests: (a) `GET /api/settings/defaults` returns `{"steam_id": None}` by default; (b) `GET /api/live-match/12345` with both external clients mocked to return `None` returns HTTP 200 with `null` body.

Gap 1 can be fixed in a single-line edit. Gap 2 requires adding ~20 lines of test code. Neither requires architectural changes.

---

_Verified: 2026-03-28T18:30:00Z_
_Verifier: Claude (gsd-verifier)_

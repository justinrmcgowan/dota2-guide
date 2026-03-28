# Phase 25: API-Driven Draft Input - Research

**Researched:** 2026-03-28
**Domain:** Live match API integration (Stratz GraphQL + OpenDota REST), Steam ID conversion, frontend auto-population
**Confidence:** MEDIUM-HIGH

## Summary

This phase adds automatic draft population from live match APIs. The player's Steam ID is configured once in Settings, and when GSI detects an active game, the backend fetches the full 10-hero draft from Stratz GraphQL (primary) or OpenDota REST (fallback), then auto-fills allies and opponents in the gameStore.

The Stratz GraphQL API provides live match data via `{ live { matches(...) { ... } } }` but critically has **no direct filter by steamAccountId** on the live matches query. The implementation must either: (a) fetch a batch of live matches and client-side filter for the player's account_id, or (b) use the player's recent matches to find the active match_id, then query by that ID. OpenDota's `/live` endpoint similarly returns top live games without player-specific filtering, but returns account_id and hero_id per player, making client-side matching straightforward.

**Primary recommendation:** Use a two-step approach for Stratz: first query `player(steamAccountId).matches` for the most recent match_id, then query `live.match(id)` for full live data including all 10 players with hero_id and position. For OpenDota fallback: fetch `/live`, scan all games for the player's account_id. Cache results aggressively -- live match data changes slowly (6-9s update cadence from Valve).

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use Stratz GraphQL as primary data source for live match draft data (real-time, faster). Fall back to OpenDota API if Stratz is unavailable or times out.
- **D-02:** OpenDota client already exists (`opendota_client.py`). Add Stratz GraphQL client as a new module. Both API tokens already configured in `config.py`.
- **D-03:** Auto-fetch draft on GSI connect (game detection). No user action needed to start.
- **D-04:** During hero pick phase, poll every 10s until draft is complete.
- **D-05:** Provide a manual "Refresh Draft" button for re-fetching if auto-detection is wrong or draft changes (late swaps).
- **D-06:** Auto-fill allies and opponents silently -- no confirmation dialog, no toast.
- **D-07:** Manual override preserved -- existing AllyPicker/OpponentPicker allow clearing and re-selecting heroes. API-fetched heroes are treated the same as manually entered ones.
- **D-08:** If user manually entered heroes before API data arrives, API data overwrites them.
- **D-09:** Add Steam ID field to the Settings panel in the frontend. Saves to localStorage.
- **D-10:** Pre-fill from backend .env (`STEAM_ID` or similar) as default value.
- **D-11:** Any user can enter their own Steam ID -- supports multi-user deployments.

### Claude's Discretion
- Error handling strategy (retry logic, timeout thresholds)
- Stratz GraphQL query structure
- Polling interval optimization
- Lane assignment inference from API data (if available)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Project Constraints (from CLAUDE.md)

- Backend: Python 3.12 + FastAPI + async endpoints + Pydantic models
- Frontend: React 18 + TypeScript strict + Zustand + Tailwind CSS
- httpx for HTTP calls (already in requirements.txt at v0.28.1)
- Hero/item images from Steam CDN, not self-hosted
- Dark theme with spectral cyan (#00d4ff), Radiant teal (#6aff97), Dire red (#ff5555)
- All code under `prismlab/` subdirectory
- Type hints throughout backend, meaningful Dota-referencing variable names
- Docker Compose deployment on Unraid (backend port 8420, frontend port 8421)

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| httpx | 0.28.1 | Async HTTP for both Stratz GraphQL and OpenDota REST | Already in requirements.txt, async-native, used by existing OpenDotaClient |
| FastAPI | 0.135.1 | New `/api/live-match/{steam_id}` endpoint | Already the backend framework |
| Zustand | (existing) | Store draft data from API in gameStore | Already manages allies/opponents state |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.12.5 | Validate Stratz/OpenDota API responses and backend endpoint schemas | Already in stack -- use for all request/response models |

### No New Dependencies Required
The entire feature can be built with httpx (for GraphQL POST to Stratz + REST GET to OpenDota) and existing frontend stack. No `gql`, `graphql-core`, or other GraphQL client libraries needed -- raw httpx POST with JSON payload is simpler and avoids dependency bloat.

## Architecture Patterns

### Recommended Project Structure
```
prismlab/backend/
  data/
    stratz_client.py          # NEW: Stratz GraphQL client
    opendota_client.py        # EXTEND: add fetch_live_games() method
  api/routes/
    live_match.py             # NEW: GET /api/live-match/{account_id}

prismlab/frontend/src/
  hooks/
    useGameIntelligence.ts    # EXTEND: add auto-draft trigger on GSI connect
    useLiveDraft.ts           # NEW: polling logic + API call + gameStore population
  components/settings/
    SettingsPanel.tsx          # EXTEND: add Steam ID input field
  stores/
    gameStore.ts              # EXTEND: add setAllAllies/setAllOpponents batch methods
  utils/
    steamId.ts                # NEW: Steam ID 64-bit <-> 32-bit conversion
```

### Pattern 1: Stratz GraphQL via httpx (No Library Needed)
**What:** Use raw httpx POST to send GraphQL queries as JSON, no `gql` dependency
**When to use:** Always -- matches existing codebase pattern of httpx-based API clients
**Example:**
```python
# Source: Verified against Stratz API schema (STRATZ_Models C# repo)
import httpx

class StratzClient:
    GRAPHQL_URL = "https://api.stratz.com/graphql"

    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Prismlab/1.0",
            "Content-Type": "application/json",
        }

    async def fetch_live_match(self, match_id: int) -> dict | None:
        """Fetch a specific live match by ID with full player data."""
        query = """
        query($matchId: Long!) {
            live {
                match(id: $matchId) {
                    matchId
                    gameState
                    gameTime
                    radiantScore
                    direScore
                    players {
                        steamAccountId
                        heroId
                        isRadiant
                        playerSlot
                        position
                        name
                        numKills
                        numDeaths
                        numAssists
                        level
                        networth
                    }
                }
            }
        }
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.GRAPHQL_URL,
                headers=self.headers,
                json={"query": query, "variables": {"matchId": match_id}},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", {}).get("live", {}).get("match")

    async def fetch_player_last_match_id(self, account_id: int) -> int | None:
        """Get the most recent match_id for a player to use with live query."""
        query = """
        query($steamAccountId: Long!) {
            player(steamAccountId: $steamAccountId) {
                matches(request: { take: 1 }) {
                    id
                }
            }
        }
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.GRAPHQL_URL,
                headers=self.headers,
                json={"query": query, "variables": {"steamAccountId": account_id}},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()
            matches = data.get("data", {}).get("player", {}).get("matches", [])
            return matches[0]["id"] if matches else None
```

### Pattern 2: OpenDota /live Fallback
**What:** Fetch all top live games, scan for player's account_id
**When to use:** When Stratz is unavailable or times out
**Example:**
```python
# Source: Verified via live curl of https://api.opendota.com/api/live
async def fetch_live_match_for_player(self, account_id: int) -> dict | None:
    """Scan OpenDota /live endpoint for a specific player's game."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{self.BASE_URL}/live",
            params=self.params,
            timeout=15.0,
        )
        resp.raise_for_status()
        games = resp.json()

    for game in games:
        for player in game.get("players", []):
            if player.get("account_id") == account_id:
                return game
    return None
```

### Pattern 3: Steam ID Conversion (Frontend)
**What:** Convert between Steam ID 64-bit (profile URL format) and 32-bit account_id (API format)
**When to use:** User enters Steam ID in any format; APIs need 32-bit account_id
**Example:**
```typescript
// Source: Valve Developer Community wiki - SteamID documentation
const STEAM_ID_64_BASE = 76561197960265728n;

export function steamId64ToAccountId(steamId64: string): number {
  const id64 = BigInt(steamId64);
  return Number(id64 - STEAM_ID_64_BASE);
}

export function accountIdToSteamId64(accountId: number): string {
  return String(STEAM_ID_64_BASE + BigInt(accountId));
}

// Validate: must be a positive integer after conversion
export function isValidSteamId(input: string): boolean {
  try {
    const accountId = steamId64ToAccountId(input);
    return accountId > 0 && accountId < 2 ** 32;
  } catch {
    return false;
  }
}
```

### Pattern 4: Auto-Draft Trigger in useGameIntelligence
**What:** Detect GSI connect + hero selection phase, trigger live draft fetch
**When to use:** Extends existing GSI subscription in useGameIntelligence hook
**Example:**
```typescript
// Inside the gsiStore.subscribe callback in useGameIntelligence:
// After hero auto-detection block, add draft auto-fetch

// --- Draft auto-fetch on GSI connect ---
if (prevStatus !== "connected" && state.gsiStatus === "connected") {
  // GSI just connected -- trigger live draft fetch
  const steamId = localStorage.getItem("prismlab_steam_id");
  if (steamId) {
    fetchAndPopulateDraft(steamId, heroesRef.current);
  }
}
```

### Anti-Patterns to Avoid
- **Polling the full /live endpoint every 10s:** OpenDota /live returns ALL top games (hundreds). This wastes bandwidth. Only poll during hero selection phase, stop after draft is complete.
- **Blocking on Stratz failure:** Never let a Stratz timeout block the user. Fire Stratz and OpenDota in parallel if Stratz is slow, use whichever responds first.
- **Creating a new httpx.AsyncClient per request:** The existing pattern does this (see opendota_client.py), but for polling every 10s during draft, consider reusing a client instance within StratzClient.
- **GraphQL library for simple queries:** Adding `gql` or `graphql-core` for 2-3 simple queries adds unnecessary complexity. httpx POST with JSON body is sufficient.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Steam ID format conversion | Custom parsing with regex | Simple BigInt arithmetic (subtract constant) | Valve's formula is trivial: `accountId = steamId64 - 76561197960265728` |
| GraphQL query execution | Full GraphQL client with schema validation | httpx.post() with JSON payload | Only 2-3 queries needed; no subscriptions, no fragments, no caching |
| Retry logic with backoff | Custom retry loops | httpx built-in retry or simple try/except with fallback | Stratz failure should immediately try OpenDota, not retry |
| Hero ID to Hero object mapping | Linear scan of heroes array | Pre-built Map/dict lookup from existing hero cache | Both DataCache (backend) and useHeroes (frontend) already have this |

**Key insight:** This feature is a thin integration layer, not a new system. The hard work (hero pickers, gameStore, GSI detection) already exists. The new code is: fetch draft -> map hero IDs -> call existing setAlly/setOpponent.

## Common Pitfalls

### Pitfall 1: OpenDota /live Only Returns Top/Popular Games
**What goes wrong:** The `/live` endpoint returns live games sorted by `sort_score` (spectator count + MMR). Low-MMR or unranked games may not appear at all.
**Why it happens:** OpenDota's `/live` comes from Valve's GetTopLiveGame API, which only surfaces "top" games. A random ranked game at 3K MMR is unlikely to be in this list.
**How to avoid:** Use Stratz as primary (it has broader live match coverage). For OpenDota fallback, document this limitation clearly. If the player's game isn't found in `/live`, return a specific "game not found" status rather than failing silently.
**Warning signs:** During testing, if you only test with high-MMR accounts, you'll miss this. Test with a regular account too.

### Pitfall 2: Draft Data Not Available During Pick Phase
**What goes wrong:** Querying for live match data during the hero selection phase may return heroes as `0` (not yet picked).
**Why it happens:** Stratz and OpenDota update every 6-9 seconds. During the pick phase, heroes are revealed one at a time. The `heroId` for unpicked slots will be 0.
**How to avoid:** Poll every 10s during HERO_SELECTION game state (D-04). Only populate allies/opponents for slots where heroId > 0. Keep polling until all 10 heroes are picked (all heroId > 0) or game state transitions to STRATEGY_TIME/PRE_GAME/GAME_IN_PROGRESS.
**Warning signs:** Seeing heroId=0 in the response -- that's an unpicked slot, not an error.

### Pitfall 3: Stratz Live Match Not Found for Player
**What goes wrong:** The player's game exists but Stratz `live.matches` doesn't surface it because the `MatchLiveRequestType` has no `steamAccountId` filter.
**Why it happens:** Stratz live query filters by leagueId, gameStates, tiers -- but not by player. You need either: (a) know the match_id already, or (b) get it from player's recent matches.
**How to avoid:** Two-step approach: (1) Query `player(steamAccountId).matches(take:1)` to get the most recent match_id. (2) Query `live.match(id: matchId)` with that ID. If the match isn't live, the second query returns null -- that's expected for non-live matches.
**Warning signs:** Player's last match in Stratz may be a completed game, not the current one. Check if the match's gameState indicates it's actually live.

### Pitfall 4: Identifying "My Team" vs "Enemy Team"
**What goes wrong:** The API returns 10 players with `isRadiant` (Stratz) or `team: 0/1` (OpenDota), but you need to know which team the user is on to separate allies from opponents.
**Why it happens:** The live match API doesn't tell you "this is the requesting player." You need to match the user's account_id in the players list to determine their team.
**How to avoid:** Find the user's account_id in the players array. Their `isRadiant`/`team` value determines their team. All players on the same team are allies; the other team is opponents. Also set `side` in gameStore based on this.
**Warning signs:** If account_id isn't found in the players list (wrong ID, lobby type mismatch), the entire ally/opponent split fails. Handle this gracefully.

### Pitfall 5: Position/Role Inference Reliability
**What goes wrong:** Stratz provides `position` (POSITION_1 through POSITION_5) during live matches, but this is a prediction, not a declared role. It can be wrong or unavailable early in the game.
**Why it happens:** Stratz infers positions from laning patterns. During pick phase or very early game, positions may be UNKNOWN.
**How to avoid:** Use Stratz position data as a suggestion, not authoritative. If position data is available and matches a valid role (1-5), auto-suggest it but don't override a manually set role. OpenDota live data includes `team_slot` but this is connection order, NOT role.
**Warning signs:** Position = UNKNOWN or FILTERED in early game.

### Pitfall 6: Steam ID Format Confusion
**What goes wrong:** User enters Steam ID in wrong format (profile URL, Steam3 ID, vanity URL instead of numeric ID).
**Why it happens:** Steam has multiple ID formats: 64-bit (76561198353796011), 32-bit/accountId (393530283), Steam3 ([U:1:393530283]), profile URL.
**How to avoid:** Accept the 64-bit Steam ID (the one in profile URLs). Validate it's a 17-digit number starting with 7656. Convert to 32-bit for API calls. Show a helper text: "Find your Steam ID at steamid.io" or parse it from the profile URL.
**Warning signs:** Conversion producing negative or impossibly large account IDs.

## Code Examples

### Backend Endpoint: GET /api/live-match/{account_id}
```python
# Source: Pattern matches existing backend route structure
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LiveMatchPlayer(BaseModel):
    account_id: int
    hero_id: int
    is_radiant: bool
    player_slot: int
    position: int | None = None  # 1-5 from Stratz, None from OpenDota

class LiveMatchResponse(BaseModel):
    match_id: int
    game_state: str  # "HERO_SELECTION", "STRATEGY_TIME", "PRE_GAME", "GAME_IN_PROGRESS"
    game_time: int
    players: list[LiveMatchPlayer]
    source: str  # "stratz" or "opendota"
    radiant_score: int = 0
    dire_score: int = 0

@router.get("/live-match/{account_id}", response_model=LiveMatchResponse | None)
async def get_live_match(account_id: int):
    """Fetch current live match for a player. Tries Stratz first, falls back to OpenDota."""
    # Try Stratz
    try:
        result = await stratz_client.fetch_live_match_for_player(account_id)
        if result:
            return result
    except Exception:
        pass  # Fall through to OpenDota

    # Fallback: OpenDota
    try:
        result = await opendota_client.fetch_live_match_for_player(account_id)
        if result:
            return result
    except Exception:
        pass

    return None  # No live match found
```

### Frontend: useLiveDraft Hook
```typescript
// Source: Extends existing patterns from useGameIntelligence
import { useCallback, useEffect, useRef } from "react";
import { useGameStore } from "../stores/gameStore";
import { useGsiStore } from "../stores/gsiStore";
import { api } from "../api/client";
import type { Hero } from "../types/hero";

export function useLiveDraft(heroes: Hero[]) {
  const pollRef = useRef<NodeJS.Timeout | null>(null);
  const draftCompleteRef = useRef(false);

  const fetchDraft = useCallback(async () => {
    const steamId = localStorage.getItem("prismlab_steam_id");
    if (!steamId) return;

    const accountId = steamId64ToAccountId(steamId);
    const match = await api.getLiveMatch(accountId);
    if (!match) return;

    // Find the user's team
    const me = match.players.find(p => p.account_id === accountId);
    if (!me) return;

    const myTeamIsRadiant = me.is_radiant;
    const allies = match.players
      .filter(p => p.is_radiant === myTeamIsRadiant && p.account_id !== accountId)
      .map(p => heroes.find(h => h.id === p.hero_id))
      .filter(Boolean);
    const opponents = match.players
      .filter(p => p.is_radiant !== myTeamIsRadiant)
      .map(p => heroes.find(h => h.id === p.hero_id))
      .filter(Boolean);

    // Auto-fill gameStore (D-06, D-08)
    const gameStore = useGameStore.getState();
    allies.forEach((hero, i) => { if (hero) gameStore.setAlly(i, hero); });
    opponents.forEach((hero, i) => { if (hero) gameStore.setOpponent(i, hero); });

    // Auto-set side (D-06)
    gameStore.setSide(myTeamIsRadiant ? "radiant" : "dire");

    // Check if draft is complete (all 10 heroes picked)
    const allPicked = match.players.every(p => p.hero_id > 0);
    if (allPicked) {
      draftCompleteRef.current = true;
      if (pollRef.current) clearInterval(pollRef.current);
    }
  }, [heroes]);

  // Trigger on GSI connect
  useEffect(() => {
    const unsub = useGsiStore.subscribe((state, prev) => {
      if (prev.gsiStatus !== "connected" && state.gsiStatus === "connected") {
        draftCompleteRef.current = false;
        fetchDraft(); // Immediate fetch
        // Start polling every 10s during pick phase (D-04)
        pollRef.current = setInterval(() => {
          if (!draftCompleteRef.current) fetchDraft();
        }, 10_000);
      }
      if (state.gsiStatus !== "connected" && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    });
    return () => { unsub(); if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchDraft]);
}
```

### Frontend: Settings Panel Steam ID Field
```typescript
// Extends existing SettingsPanel.tsx pattern
// Uses localStorage with key "prismlab_steam_id"
const [steamId, setSteamId] = useState(
  () => localStorage.getItem("prismlab_steam_id") ?? ""
);

const handleSteamIdChange = (value: string) => {
  setSteamId(value);
  if (isValidSteamId(value)) {
    localStorage.setItem("prismlab_steam_id", value);
  }
};

// JSX: Same input pattern as existing GSI host input
<input
  type="text"
  value={steamId}
  onChange={(e) => handleSteamIdChange(e.target.value)}
  placeholder="e.g. 76561198353796011"
  className="w-full px-3 py-2 bg-surface-container-lowest border-b border-outline-variant/15 ..."
/>
```

## API Reference: Verified Response Schemas

### OpenDota /live Response (Verified via live curl)
```json
[{
  "match_id": "8747526504",
  "game_time": 2296,
  "game_mode": 22,
  "average_mmr": 7733,
  "radiant_score": 35,
  "dire_score": 32,
  "radiant_lead": -6134,
  "spectators": 51,
  "players": [
    {
      "account_id": 859258244,
      "hero_id": 102,
      "team_slot": 1,
      "team": 0
    }
  ]
}]
```
**Key fields:** `team: 0` = Radiant, `team: 1` = Dire. `team_slot` is connection order (1-5), NOT role/position. `hero_id: 0` means not yet picked.

**Limitation:** Only returns top/popular games sorted by spectator count + MMR. Low-MMR games may not appear.

### Stratz GraphQL Schema (Verified via STRATZ_Models C# repo)

**Endpoint:** `https://api.stratz.com/graphql`
**Auth:** `Authorization: Bearer {STRATZ_API_TOKEN}`

**MatchLiveType fields (34 total):** matchId, leagueId, lobbyId, serverSteamId, radiantScore, direScore, radiantLead, gameTime, gameMinute, delay, spectators, radiantTeamId, direTeamId, numHumanPlayers, averageRank, gameMode, gameState, completed, isUpdating, isParsing, buildingState, parseBeginGameTime, createdDateTime, modifiedDateTime, winRateValues, durationValues, + nested: players, radiantTeam, direTeam, league, playbackData, insight, liveWinRateValues

**MatchLivePlayerType fields (42 total):** matchId, heroId, hero, name, playerSlot, steamAccountId, steamAccount, isRadiant, numKills, numDeaths, numAssists, leaverStatus, numLastHits, numDenies, goldPerMinute, experiencePerMinute, gold, goldSpent, networth, heroDamage, towerDamage, level, itemId0-5, backpackId0-2, ultimateCooldown, ultimateState, respawnTimer, gameVersionId, playbackData, baseWinRateValue, position, impPerMinute

**MatchLivePickBanType fields:** isPick, heroId, bannedHeroId, order, isRadiant, baseWinRate, adjustedWinRate, letter, position, positionValues, winRateValues, durationValues

**MatchLiveGameState enum:** INIT, WAIT_FOR_PLAYERS_TO_LOAD, HERO_SELECTION, STRATEGY_TIME, PRE_GAME, GAME_IN_PROGRESS, POST_GAME, DISCONNECT, TEAM_SHOWCASE, CUSTOM_GAME_SETUP, WAIT_FOR_MAP_TO_LOAD, SCENARIO_SETUP, PLAYER_DRAFT, LAST

**MatchLiveRequestType filters (NO steamAccountId filter!):** heroId, leagueId, isParsing, isCompleted, leagueIds, gameStates, tiers, lastPlaybackEventOnly, orderBy, isLeague, take, skip

**MatchPlayerPositionType enum:** POSITION_1, POSITION_2, POSITION_3, POSITION_4, POSITION_5, UNKNOWN, FILTERED, ALL

**Top-level query access pattern:**
```graphql
# Get specific live match by ID
{ live { match(id: $matchId) { ... } } }

# Get filtered list of live matches
{ live { matches(request: { gameStates: [HERO_SELECTION, GAME_IN_PROGRESS], take: 100 }) { ... } } }

# Get player's recent match IDs
{ player(steamAccountId: $accountId) { matches(request: { take: 1 }) { id } } }
```

### Steam ID Conversion Formula
```
32-bit account_id = 64-bit Steam ID - 76561197960265728
```
The constant `76561197960265728` is the base value for individual Steam accounts (universe=1, type=1, instance=1).

**User's example:** `76561198353796011 - 76561197960265728 = 393530283` (confirmed from CONTEXT.md)

## API Rate Limits

### Stratz GraphQL
| Tier | Per Second | Per Minute | Per Hour | Per Day |
|------|-----------|------------|----------|---------|
| Default Token | 20 | 250 | 2,000 | 10,000 |
| Individual Token | 20 | 250 | 4,000 | 20,000 |

**Impact on polling:** At 1 query every 10s during draft (D-04), that's 6/min. Well within all limits. Even with 2 queries per poll (player lookup + live match), 12/min is fine.

### OpenDota REST
| Tier | Per Minute | Per Month |
|------|-----------|-----------|
| No API Key | 60 | 50,000 |
| With API Key | 60 | Higher (unspecified) |

**Impact on polling:** 6 requests/min during draft is 10% of per-minute budget. Acceptable. The `/live` endpoint returns large payloads (all top games), so minimize calls.

## Stratz Query Strategy (Claude's Discretion)

Given that `MatchLiveRequestType` has **no steamAccountId filter**, here are the viable approaches ranked:

### Recommended: Two-Step Match ID Approach
1. Query `player(steamAccountId).matches(take: 1)` to get the most recent match_id
2. Query `live.match(id: matchId)` with that match_id
3. If the match is live, you get full player data with heroIds
4. If null (match isn't live), the player's game isn't in Stratz's live feed yet

**Pros:** Precise, efficient (2 small queries), no scanning large result sets
**Cons:** Recent match may be a completed game, not current one. Need to verify gameState.

### Alternative: Batch Scan
1. Query `live.matches(request: { take: 100, gameStates: [HERO_SELECTION, STRATEGY_TIME, PRE_GAME, GAME_IN_PROGRESS] })`
2. Scan all players arrays for the target steamAccountId
3. If found, return that match

**Pros:** Single query, gets the actual live match
**Cons:** Returns up to 100 matches (large payload), O(n*10) scan, may not include the player's game if it's not in the top 100

### Recommendation
Use the two-step approach as primary. If step 1 returns a match_id and step 2 returns null (not live), fall back to batch scan. If batch scan also fails, fall back to OpenDota.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Stratz REST API v1 | Stratz GraphQL API | 2019 (Dota 7.23 era) | REST deprecated, GraphQL is the only supported path |
| OpenDota /live with full player data | OpenDota /live with minimal player data | Ongoing | Live endpoint shows top games only; low-MMR games may be absent |
| Manual hero selection only | GSI + API auto-population | This phase | Eliminates manual input for draft during live games |

## Open Questions

1. **Stratz live match coverage for non-league games**
   - What we know: Stratz live match UI shows ranked games, not just pro/league matches
   - What's unclear: Whether the API returns ALL live matches or only a subset (like OpenDota's "top games")
   - Recommendation: Test with the user's actual Steam ID during implementation. If Stratz doesn't surface the game, OpenDota fallback handles it. LOW confidence on Stratz coverage depth.

2. **Stratz `player.matches(take:1)` during an active game**
   - What we know: This returns the most recent match. If a game is in progress, it MIGHT appear here with the current match_id.
   - What's unclear: Does Stratz create the match record during hero selection, or only after the game starts?
   - Recommendation: Test empirically. If the match_id isn't available until post-draft, the two-step approach needs adjustment -- may need to use batch scan during pick phase.

3. **Default Steam ID from backend .env (D-10)**
   - What we know: config.py needs a new `steam_id` setting, frontend needs an endpoint to fetch it
   - What's unclear: Whether to expose it via a dedicated `/api/settings/defaults` endpoint or piggyback on an existing endpoint
   - Recommendation: Add `GET /api/settings/defaults` returning `{ steam_id: "..." }`. Frontend fetches on first load and uses as default if localStorage is empty. Keep it simple.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| httpx | Stratz/OpenDota API calls | Yes | 0.28.1 | -- |
| Stratz API Token | Primary live match source | Configured in .env | -- | OpenDota fallback |
| OpenDota API Key | Fallback live match source | Configured in .env (optional) | -- | Works without key (lower rate limit) |
| GSI WebSocket | Trigger auto-draft on game detection | Yes | Existing | Manual "Refresh Draft" button |
| localStorage | Steam ID persistence | Yes | Browser API | -- |

**Missing dependencies with no fallback:** None
**Missing dependencies with fallback:** None -- all dependencies are already in the project

## Sources

### Primary (HIGH confidence)
- OpenDota `/live` endpoint -- verified via direct curl to `https://api.opendota.com/api/live` (actual response inspected)
- Stratz GraphQL schema -- verified via [STRATZ_Models C# repository](https://github.com/TheAmazingLooser/STRATZ_Models) (auto-generated from live schema, updated daily)
- Stratz API rate limits -- verified via [STRATZ knowledge base](https://stratz.com/knowledge-base/API/Are%20there%20any%20rate%20limits)
- Steam ID conversion -- verified via [Valve Developer Community wiki](https://developer.valvesoftware.com/wiki/SteamID)
- Existing codebase patterns -- verified via direct file reads of opendota_client.py, config.py, gameStore.ts, useGameIntelligence.ts, SettingsPanel.tsx, gsiStore.ts

### Secondary (MEDIUM confidence)
- Stratz live match update frequency (6-9 seconds) -- from [STRATZ Medium blog post](https://medium.com/stratz/dota-2-live-matches-639021bede36)
- OpenDota rate limits (60/min, 50K/month free) -- from multiple community sources and [OpenDota blog](https://blog.opendota.com/2018/04/17/changes-to-the-api/)
- Stratz GraphQL endpoint URL (`api.stratz.com/graphql`) -- from [STRATZ Medium blog](https://medium.com/stratz/dota-7-23-graphql-631ea1d5f173) and C# models

### Tertiary (LOW confidence)
- Stratz live match coverage for non-league games -- not verified with official docs
- Stratz `player.matches` behavior during active games -- not empirically tested
- OpenDota /live coverage for low-MMR games -- anecdotal, needs testing

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, extends existing patterns
- Architecture: HIGH - clear integration points identified, existing code inspected
- API schemas: MEDIUM-HIGH - Stratz verified via auto-generated C# models (not direct schema introspection due to Cloudflare), OpenDota verified via live curl
- Pitfalls: MEDIUM - based on schema analysis and API behavior; some pitfalls (live match coverage) need empirical validation
- Query strategy: MEDIUM - two-step approach is theoretically sound but untested against live Stratz API due to auth requirement

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (Stratz schema updates daily; OpenDota API is stable)

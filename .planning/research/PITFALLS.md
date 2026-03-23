# Pitfalls Research

**Domain:** Live game intelligence for Dota 2 item advisor (GSI, screenshot parsing, WebSocket, auto-refresh)
**Researched:** 2026-03-23
**Confidence:** HIGH (official Valve GSI docs, Claude Vision API docs, FastAPI WebSocket docs, community issue reports)

## Critical Pitfalls

### Pitfall 1: GSI Cannot See Enemy Items -- The Core Data Gap

**What goes wrong:**
The entire v2.0 vision assumes live game data can replace manual inputs. But Dota 2 GSI deliberately restricts data when playing (not spectating) to prevent cheating. Critically: **you cannot see enemy hero items, abilities, cooldowns, or positions through GSI when playing your own match.** GSI only exposes your own hero data (inventory, gold, stats) and your own team. The "enemy items spotted" feature -- which is central to mid-game re-evaluation -- gets ZERO data from GSI. Developers discover this after building the entire GSI pipeline and realize they still need manual input for enemy items.

**Why it happens:**
Valve intentionally limits GSI player-mode data to prevent third-party tools from providing unfair information advantages. The GSI documentation buries this distinction. Libraries like Dota2GSI (C#) and dota2gsipy (Python) document spectator-mode fields prominently, making developers assume all fields are available during play.

**How to avoid:**
- Accept this limitation upfront and design the architecture around it. GSI provides YOUR data (gold, items, hero state, map time). Enemy data requires a separate channel (screenshot parsing or manual input).
- Do NOT build a unified "game state from GSI" model that tries to include enemy data. Build two separate data flows: (1) GSI for player data, automatically populated, (2) Screenshot parsing or manual input for enemy data.
- The screenshot parsing feature for enemy items is not just a "nice to have" -- it is the ONLY automated way to get enemy build data in v2.0. Prioritize it accordingly.
- Document clearly in the UI what data is auto-detected vs what requires user input.

**Warning signs:**
- Architecture diagrams showing "GSI provides full game state" without distinguishing player vs enemy data
- Models that have fields for enemy items sourced from GSI
- Confusion during testing: "why isn't enemy data coming through?"

**Phase to address:**
Phase 1 (GSI Foundation). Must be understood before any code is written. The entire architecture depends on this data boundary.

---

### Pitfall 2: Docker Container Cannot Receive GSI Localhost Posts

**What goes wrong:**
Dota 2 GSI sends HTTP POST requests to a URI configured in the .cfg file, typically `http://localhost:PORT/`. The Prismlab backend runs inside a Docker container on Unraid. Docker containers have their own network namespace -- `localhost` inside the container is NOT the host machine's localhost. Dota 2 (running on a separate gaming PC) sends POSTs to the host machine, but the container never receives them. Even if Dota 2 ran on the same machine, `localhost` in the GSI config would target the host, not the container.

**Why it happens:**
The standard GSI setup guides all assume the listener runs directly on the same machine as Dota 2. Docker introduces a network boundary that breaks this assumption. The Prismlab deployment runs on Unraid (a server), while Dota 2 runs on a gaming PC -- they are separate machines entirely. The GSI config must point to the Unraid server's LAN IP, and the Docker port mapping must expose the GSI endpoint.

**How to avoid:**
- The GSI .cfg file URI must point to the Unraid server's LAN IP, NOT localhost: `"uri" "http://192.168.X.X:8420/api/gsi"`.
- Expose the GSI endpoint through the existing Docker port mapping (8420 maps to backend:8000). Add a `/api/gsi` POST endpoint to FastAPI.
- The Nginx reverse proxy in the frontend container must also forward `/api/gsi` to the backend, or GSI posts must go directly to port 8420 (backend).
- If using Cloudflare Tunnel or Nginx Proxy Manager, ensure the GSI endpoint is accessible on the LAN without going through external DNS/proxy (GSI posts from the local network should hit the server directly).
- Include the `.cfg` file generation as part of the setup flow. Do NOT make users hand-edit config files -- provide a downloadable .cfg with the correct URI pre-filled based on the server's detected IP.

**Warning signs:**
- GSI endpoint receiving zero requests during testing
- Dota 2 timeout/retry behavior (GSI waits for HTTP 2XX, retries on failure)
- Works in local dev (no Docker) but fails in production deployment

**Phase to address:**
Phase 1 (GSI Foundation). Must be validated end-to-end with actual Docker deployment on Unraid early. Do not defer this to a later phase -- the entire GSI feature depends on network connectivity working.

---

### Pitfall 3: GSI Data Flood Triggering Uncontrolled Claude API Calls

**What goes wrong:**
GSI sends HTTP POST updates to your server continuously during a game. With a typical throttle of 1-5 seconds, that is 360-1800 requests per 30-minute game. Each update contains changed game state (new gold amount, items purchased, hero level, etc.). If the auto-refresh logic naively triggers a Claude API recommendation call on every "significant" state change, you burn through API budget ($0.004-0.01 per call) and hit rate limits. A single game could generate 50+ Claude API calls without rate limiting -- costing $0.20-0.50 per game and potentially exhausting API quota.

**Why it happens:**
Game state changes are continuous and granular. Gold increments every second. Items are purchased. Hero levels up. Each of these is a "change" that could trigger a refresh. Without explicit rate limiting and change significance thresholds, the system fires Claude API calls far too often. The "max 1 per 2 min" constraint in the project spec is correct but easy to violate if the debounce logic has bugs or edge cases.

**How to avoid:**
- Implement a **three-layer rate control**: (1) Backend-side hard cooldown timer (minimum 2 minutes between Claude API calls, no exceptions), (2) Change significance filter (only trigger on meaningful changes: item purchased, death, level milestone, gold threshold crossed), (3) Token bucket limiter on the Claude API client.
- Define the exact "trigger events" explicitly: item purchase detected, hero death (respawn timer starts), game clock hitting 10:00/20:00/30:00 minute marks, lane result determination (gold delta at 10 min). Everything else is informational -- update the UI but do NOT trigger re-recommendation.
- Show a "next refresh available in X:XX" countdown in the UI so the user understands the rate limit.
- Track Claude API call count per game session. Alert if it exceeds 15 calls per game (budget protection).
- Consider cheaper models (Haiku) for rapid low-stakes updates and Sonnet only for full re-evaluations.

**Warning signs:**
- Claude API call count exceeding 10 per game in logs
- "Rate limit exceeded" errors from Anthropic API during games
- Monthly API costs increasing 10x after enabling auto-refresh
- Backend latency spikes as Claude API calls queue up

**Phase to address:**
Phase 3 (Auto-Refresh Engine). The rate limiter must be the FIRST thing built before any auto-trigger logic. Design it so auto-refresh cannot physically call Claude more than once per 2 minutes, even if the trigger logic has bugs.

---

### Pitfall 4: Screenshot Parsing Unreliability for Enemy Items

**What goes wrong:**
Claude Vision API is used to parse Dota 2 scoreboard screenshots to extract enemy item builds. But Dota 2 item icons are small (roughly 30x30 pixels on a 1080p scoreboard), visually similar items exist (Ogre Axe vs Mithril Hammer vs Broadsword are all simple brown/gray rectangles), and screenshot quality varies (JPEG compression, different resolutions, UI scaling). Claude Vision hallucinates or misidentifies items, reporting items the enemy does not have. The recommendation engine then generates advice countering items that don't exist.

**Why it happens:**
Claude Vision's spatial reasoning and small-object recognition have documented limitations. The official docs state: "Claude may hallucinate or make mistakes when interpreting low-quality, rotated, or very small images under 200 pixels" and "Claude's spatial reasoning abilities are limited." Dota 2 item icons on a scoreboard are well under 200 pixels each. Additionally, item icons change with patches and some items share visual elements (all Blade items look similar, all Staff items look similar).

**How to avoid:**
- **Crop the scoreboard region before sending to Claude.** A full 1920x1080 screenshot wastes tokens on irrelevant UI. Crop to just the item grid area for each hero. This increases effective resolution for the items and reduces token cost (~1334 tokens for a 1000x1000 image vs ~1590 for full resolution).
- **Provide Claude with the complete item icon reference in the prompt.** Include the full list of purchasable items with their internal names. Ask Claude to match what it sees against this known list rather than free-associating item names.
- **Use structured output with constrained item names.** Claude should only return item identifiers from a predefined enum, not freetext item descriptions. Validate every returned item name against the items database.
- **Show parsed results to the user for confirmation.** Never auto-apply screenshot parsing results without user review. Display "We detected: BKB, Blink, Manta -- is this correct?" with edit capability.
- **Track confidence per item.** If Claude is uncertain about an item icon, mark it as "uncertain" and let the user confirm. Low-confidence items should not influence recommendations.
- **Image preparation:** require PNG screenshots (not JPEG -- compression artifacts destroy small icons), and instruct users to take screenshots at native resolution without UI scaling.

**Warning signs:**
- Items being detected that the enemy cannot possibly have at that game time (e.g., Radiance at 5 minutes)
- Same screenshot producing different results on repeated parsing
- Gold-cost validation failing (detected items cost more than enemy's visible net worth)
- User complaints about wrong items being detected

**Phase to address:**
Phase 2 (Screenshot Parsing). Build a validation layer that cross-references detected items against game time and enemy net worth (from OpenDota live data or estimation). Include human-in-the-loop confirmation before any parsed data affects recommendations.

---

### Pitfall 5: WebSocket Connection Dies Silently, Frontend Shows Stale Data

**What goes wrong:**
The WebSocket connection between backend and frontend drops silently (network hiccup, Cloudflare Tunnel reconnection, Nginx proxy timeout, user's laptop goes to sleep). The frontend continues displaying the last received game state as if it is current. The user thinks they are seeing live data but the gold counter stopped updating 3 minutes ago. Worse, the UI shows no indication that the connection is lost. The user makes item decisions based on stale information.

**Why it happens:**
WebSocket connections can die without sending a close frame. Unlike HTTP requests that fail visibly with error codes, a dead WebSocket just stops receiving messages. The frontend has no way to distinguish "no new data because game state has not changed" from "no new data because connection is dead." FastAPI WebSocket handlers in particular have a known pattern where background tasks leak if the client disconnects without proper cleanup (one of the most common FastAPI WebSocket bugs).

**How to avoid:**
- **Heartbeat/ping-pong protocol.** Backend sends a ping every 10 seconds. Frontend expects a pong response. If no heartbeat received for 30 seconds, frontend shows a "Connection lost -- reconnecting..." banner. This is non-negotiable for any real-time system.
- **Connection state indicator in the UI.** A small green/yellow/red dot in the corner showing: green = connected and receiving data, yellow = connected but no data in 30s (game may be paused), red = disconnected, attempting reconnection.
- **Exponential backoff reconnection on the frontend.** When connection drops: retry immediately, then 1s, 2s, 4s, 8s, max 30s. Reset backoff on successful connection.
- **State reconciliation on reconnect.** When WebSocket reconnects, backend must send the FULL current game state, not just the delta. The frontend must replace its entire GSI state, not merge incrementally. This prevents stale partial state.
- **Nginx WebSocket configuration.** The existing Nginx config does NOT support WebSocket proxying. Must add `proxy_http_version 1.1;`, `proxy_set_header Upgrade $http_upgrade;`, `proxy_set_header Connection "upgrade";` and increase `proxy_read_timeout` (default 60s is too short for WebSocket -- use 3600s or higher).
- **Task cleanup on disconnect.** In FastAPI, use `try/finally` in the WebSocket handler. When the connection closes, cancel any background tasks (like GSI data forwarding) associated with that connection using `task.cancel()`.

**Warning signs:**
- Frontend gold counter frozen while game is ongoing
- "last updated" timestamp not changing
- Memory leak in backend (orphaned background tasks per dead connection)
- Nginx 504 errors in logs after 60 seconds of WebSocket inactivity

**Phase to address:**
Phase 1 (WebSocket Foundation). The heartbeat protocol and reconnection logic must be built into the initial WebSocket implementation, not added retroactively. The Nginx configuration change is a prerequisite.

---

### Pitfall 6: Manual Inputs and Automated GSI Data Conflicting

**What goes wrong:**
The existing v1.0 system uses manual inputs for everything: hero selection, role, lane, opponents, gold, items purchased. V2.0 introduces GSI auto-detection for some of these (hero, gold, items purchased). But both input methods coexist -- the user can still manually adjust. Conflicts arise: GSI says hero is level 12, user manually set lane result to "lost" but gold data shows they are ahead. GSI auto-marks items as purchased but user already marked different items. The recommendation engine receives contradictory signals and produces confused advice.

**Why it happens:**
The dual-input system creates a "source of truth" ambiguity. The v1.0 Zustand stores (`gameStore` and `recommendationStore`) assume a single source of truth: user input. Adding GSI as a second input source creates merge conflicts that are not modeled in the existing state architecture. The `purchasedItems` Set in `recommendationStore` tracks user-clicked purchases; GSI detects items in inventory. These can diverge.

**How to avoid:**
- **Explicit priority hierarchy:** GSI data is the default truth for fields it provides (hero, gold, inventory, game clock). Manual input is the override. If the user explicitly changes something GSI auto-set, the manual value wins and a "manual override" flag is set for that field.
- **Add a `source` field to each game state property.** `{value: "won", source: "manual"}` vs `{value: 14500, source: "gsi"}`. The UI shows which fields are auto-detected (subtle GSI icon) vs manually entered.
- **Reconcile purchasedItems from GSI inventory data.** When GSI reports items in inventory, cross-reference against the recommendation list and auto-mark matches as purchased. But do NOT un-mark items the user manually purchased -- they may have sold and rebought, or the GSI data may be delayed.
- **Gold tracking from GSI replaces the manual estimation.** Remove the need for user gold input entirely. Show real-time gold in the UI with GSI source indicator. But keep a "gold override" option for edge cases where GSI data is delayed.
- **Lane result auto-detection from gold differential at 10 minutes** should populate the laneResult field but show a confirmation: "GSI detected lane as WON (gold advantage +1200 at 10:00). Correct?" Let user override.

**Warning signs:**
- Recommendation output contradicting visible game state
- Items flickering between purchased/unpurchased as GSI and manual inputs fight
- User confusion: "I set my lane to lost but the app says I won?"
- State management bugs where GSI overwrites a manual override on next update tick

**Phase to address:**
Phase 1 (GSI Foundation). The state management architecture must be redesigned BEFORE building any GSI features. The existing Zustand stores need a `source` concept added to every auto-detectable field. This is an architectural change, not a feature addition.

---

### Pitfall 7: Screenshot Parsing Cost Explosion

**What goes wrong:**
Each Claude Vision API call for screenshot parsing costs ~$0.004 for a 1000x1000px image (~1334 input tokens at $3/1M tokens for Sonnet 4.6). If a user pastes a screenshot every 2-3 minutes during a 40-minute game, that is 13-20 Vision API calls per game. Combined with regular recommendation API calls, total per-game cost reaches $0.15-0.30. For a tool used daily across multiple games, monthly costs can reach $10-30 just on Vision API -- on top of existing text recommendation costs. This is unsustainable for a personal project.

**Why it happens:**
Vision API costs are per-image, calculated by pixel count (tokens = width * height / 750). A full 1920x1080 Dota 2 screenshot is ~2,764 tokens (~$0.008 per image). Even cropped screenshots add up quickly with frequent use. Developers underestimate vision costs because text API costs are familiar, but image token counts are much higher per request.

**How to avoid:**
- **Aggressive image preprocessing.** Crop to ONLY the scoreboard item grid. A 400x200px crop is ~107 tokens (~$0.0003) vs ~2,764 tokens for full screenshot. This is a 25x cost reduction.
- **Rate limit screenshot parsing.** Maximum 1 parse per 3 minutes. Show cooldown timer.
- **Cache results.** If the user pastes the same screenshot (or near-identical based on perceptual hash), return cached results. Enemy items do not change between 10-second scoreboard checks.
- **Batch enemy heroes.** Parse all 5 enemy heroes from ONE screenshot in a single Claude call rather than 5 separate calls. Send one cropped scoreboard image and ask Claude to identify items for all visible enemy heroes.
- **Cost tracking per session.** Show the user how many API calls have been made this session. Consider a daily budget cap.
- **Consider OCR alternatives for simpler cases.** Some items (BKB, Blink Dagger, etc.) have distinctive visual profiles. A lightweight local classifier could handle common items without Claude API, reserving Vision API for ambiguous cases only. This is an optimization for later, not v2.0.

**Warning signs:**
- Monthly Claude API costs doubling or tripling after enabling screenshot parsing
- Users sending full-resolution screenshots instead of cropped regions
- Same screenshot being parsed multiple times (cache miss or no caching)

**Phase to address:**
Phase 2 (Screenshot Parsing). Image preprocessing (crop, resize) must be implemented before any Vision API calls are made. The cost monitoring should be built into the same phase.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Polling instead of WebSocket for GSI data relay | Simpler frontend, no WebSocket setup | Higher latency (1-3s polling delay), unnecessary HTTP overhead, missed rapid events | Never for live game data -- WebSocket is the correct pattern for sub-second updates |
| Storing GSI state in the same Zustand store as manual inputs | No store refactoring needed | Source-of-truth conflicts, impossible to distinguish auto vs manual data, bugs on every edge case | Never -- separate GSI state from manual state, merge with explicit priority |
| Sending full screenshots to Vision API without cropping | Faster implementation, no image processing | 25x higher per-image cost, more hallucination due to irrelevant visual context, slower response | Early prototyping only, must crop before any repeated use |
| Single WebSocket endpoint for all real-time data | Simpler routing, one connection | Message types get tangled, hard to add new data streams, hard to debug | Acceptable in v2.0 with message type discriminators. Separate channels only needed at scale. |
| Hardcoding GSI .cfg file contents | Works on your setup | Breaks for any user with different network config, different Dota install path | Never -- generate the .cfg dynamically based on server IP |
| Skipping heartbeat protocol on WebSocket | Fewer moving parts | Silent disconnections, stale data without user awareness | Never for any production WebSocket |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Dota 2 GSI | Assuming enemy data is available during play | GSI only exposes YOUR hero, items, gold, and team data. Enemy data requires screenshot parsing or manual input. Design two separate data flows. |
| Dota 2 GSI | Using existing Python GSI libraries (dota2gsipy) without checking maintenance status | dota2gsipy has 0.1 release on PyPI, minimal maintenance. Write a lightweight FastAPI POST endpoint yourself -- GSI is just JSON POSTs. You already have FastAPI. |
| Dota 2 GSI | Not handling GSI data structure variability | GSI JSON structure differs between playing, spectating, and menu states. Not all fields exist in all states. Null-check everything. Use Pydantic models with all Optional fields. |
| Dota 2 GSI | Listening on port 80 or 443 (common HTTP ports) | These ports may conflict with existing services. Use a dedicated port or your existing backend port with a distinct endpoint path (`/api/gsi`). |
| Dota 2 GSI | Not returning HTTP 2XX quickly enough | Dota 2 waits for 2XX response. If your handler does heavy processing synchronously, GSI times out and retries, causing duplicate events. Return 200 immediately, process asynchronously. |
| Claude Vision | Sending base64-encoded images in every request | Base64 increases payload by ~33%. For repeated use, consider the Files API (upload once, reference by file_id). For one-shot screenshots, base64 is fine. |
| Claude Vision | Not specifying the item vocabulary in the prompt | Claude will hallucinate item names. Always include the full list of valid Dota 2 item names and tell Claude to ONLY use names from that list. |
| FastAPI WebSocket | Using HTTPException in WebSocket handlers | HTTPException does not work in WebSocket routes -- it crashes the handler instead of returning an error. Close the WebSocket with a custom close code (4000-4999 range) instead. |
| FastAPI WebSocket | Not canceling background tasks on disconnect | If you spawn asyncio tasks per connection (e.g., forwarding GSI data), you must cancel them when the client disconnects. Otherwise tasks leak memory indefinitely. Use try/finally with task.cancel(). |
| Nginx reverse proxy | Using existing Nginx config for WebSocket | The current nginx.conf does NOT support WebSocket. Must add `proxy_http_version 1.1`, Upgrade headers, and increase `proxy_read_timeout` from default 60s to 3600s+. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Processing every GSI update synchronously | Backend latency spikes during games, blocked event loop | Return HTTP 200 to GSI immediately. Process state diff asynchronously. Only forward meaningful changes to WebSocket clients. | Immediately -- GSI sends updates every 1-5 seconds |
| Broadcasting full game state on every GSI tick | WebSocket messages are large (full JSON), frontend re-renders constantly | Send only changed fields (JSON Patch or delta). Frontend applies diffs to local state. | With multiple concurrent sessions or complex game states |
| No debounce on auto-refresh trigger | Claude API called on every gold change, item purchase, level up | Implement 2-minute hard cooldown. Define specific trigger events (item purchase, death, time milestones). Ignore incremental changes. | First game with auto-refresh enabled |
| Full screenshot sent to Vision API | Each parse costs ~$0.008, takes 3-5 seconds | Crop to item grid region (~400x200px), reducing cost to ~$0.0003 and latency to 1-2 seconds | First session with frequent screenshot use |
| WebSocket per-message JSON serialization overhead | CPU spike on backend with frequent GSI updates | Use msgpack or a binary protocol for WebSocket messages if performance becomes an issue. JSON is fine for v2.0 initial implementation. | Only at very high message frequency (unlikely for single-user) |
| Frontend re-rendering entire recommendation panel on every GSI update | UI jank, laggy gold counter | Separate GSI display state (gold, items, game clock) from recommendation state. Use Zustand selectors to prevent cross-store re-renders. | Immediately visible during gameplay |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| GSI endpoint accessible without auth token | Anyone on LAN can POST fake game state data, corrupting recommendations | Include an `auth` token in the GSI .cfg file. Validate the token on every POST to `/api/gsi`. Reject requests without valid token. |
| GSI auth token hardcoded in source code | Token visible in public repos or Docker image layers | Generate a random token during setup. Store in .env file. Reference via `settings.gsi_auth_token`. |
| WebSocket endpoint open without authentication | Anyone can connect and receive live game data | Authenticate WebSocket connections. Use a query parameter token or first-message auth pattern (browser WebSocket API does not support custom headers). |
| Screenshot upload endpoint with no size/type validation | Upload of malicious files, memory exhaustion from huge images | Validate Content-Type (only image/png, image/jpeg). Limit file size to 5MB. Validate image dimensions. Reject non-image content. |
| CORS allowing all origins for WebSocket | Cross-site WebSocket hijacking | Restrict WebSocket CORS to the same origins as HTTP CORS (localhost:5173 and localhost:8421). Validate Origin header in the WebSocket handshake. |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Auto-updating recommendations without user consent | Jarring -- user is reading a recommendation and it changes mid-sentence | Show "New recommendations available" notification. Let user click to apply. Never auto-replace visible recommendations. |
| No visual distinction between GSI-detected and manual data | User cannot trust the data -- "did I set this or did the app detect it?" | Add subtle GSI icon (antenna/signal icon) next to auto-detected fields. Different visual treatment for manual vs automated data. |
| Hiding the manual input fallback when GSI is active | If GSI disconnects or misdetects, user has no way to correct data | Always keep manual override accessible. Show a toggle: "Auto (GSI)" / "Manual" for each field. Manual override persists until GSI reconnects. |
| Screenshot paste workflow requiring too many clicks | During a live game, every second matters. Three-click workflows are abandoned. | Single paste action: Ctrl+V on the app, immediate processing, results shown in 2 seconds with one-click confirm. Minimal friction. |
| Gold counter updating faster than human can read | Distracting, seizure-risk for rapid number changes | Smooth gold counter transitions (CSS transition on number change). Update at most once per second even if GSI sends faster. Round to nearest 50g for display. |
| No indication of when next auto-refresh will happen | User mashes re-evaluate button not knowing it is rate-limited | Show countdown timer: "Next refresh in 1:45" after an auto-refresh triggers. Make it clear that manual re-evaluate still works (bypasses auto-refresh cooldown). |

## "Looks Done But Isn't" Checklist

- [ ] **GSI Endpoint:** Often missing authentication -- verify the auth token from .cfg is validated on every POST, not just checked once
- [ ] **GSI Endpoint:** Often missing immediate 200 response -- verify the handler returns 200 before any processing. Dota 2 retries on timeout, causing duplicate events.
- [ ] **GSI .cfg file:** Often missing all required data fields -- verify `hero`, `items`, `player`, `map`, and `abilities` are all set to `"1"` in the data section
- [ ] **WebSocket:** Often missing heartbeat -- verify ping/pong runs every 10s and frontend shows disconnection state after 30s silence
- [ ] **WebSocket:** Often missing Nginx configuration -- verify nginx.conf has `proxy_http_version 1.1`, Upgrade headers, and increased `proxy_read_timeout`
- [ ] **Screenshot Parsing:** Often missing image cropping -- verify screenshots are cropped to item grid before being sent to Claude Vision API
- [ ] **Screenshot Parsing:** Often missing result confirmation -- verify parsed items are shown to user for approval before affecting recommendations
- [ ] **Auto-Refresh:** Often missing hard cooldown enforcement -- verify even if trigger logic fires rapidly, Claude API is never called more than once per 2 minutes
- [ ] **State Management:** Often missing source tracking -- verify every auto-detectable field in Zustand stores has a `source` property ("gsi" | "manual" | "screenshot")
- [ ] **Lane Result Detection:** Often missing user confirmation -- verify auto-detected lane result shows a confirmation prompt, not silent auto-apply
- [ ] **Cost Tracking:** Often missing -- verify there is a per-session counter for Claude API calls (both text and vision) visible somewhere in the UI or logs
- [ ] **Reconnection:** Often missing state reconciliation -- verify that after WebSocket reconnect, the frontend receives FULL current state and replaces local state entirely

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| GSI cannot see enemy items | LOW | Already planned: screenshot parsing as the enemy data channel. No architecture change needed if this was designed in from the start. If not, requires adding a second data pipeline. |
| Docker networking blocks GSI | LOW | Change GSI .cfg URI to server LAN IP. Update Docker port mapping if needed. No code changes, just config. But requires testing with actual deployment. |
| Claude API call flood | MEDIUM | Add rate limiter middleware. Requires defining trigger events and cooldown timers. Can be added retroactively but risks budget damage before it is caught. |
| Screenshot parsing hallucinations | MEDIUM | Add validation layer: cross-reference detected items vs game time and estimated net worth. Add user confirmation step. Requires UI work but no architecture change. |
| WebSocket silent disconnect | MEDIUM | Implement heartbeat protocol. Requires changes to both backend handler and frontend hook. Can be retrofitted but should be built in from the start. |
| Manual/GSI state conflicts | HIGH | Requires refactoring Zustand stores to add source tracking on every field. If built without this, every field interaction has potential bugs. Retrofitting is expensive -- build it in from Phase 1. |
| Screenshot cost explosion | LOW | Add image cropping. Can be added at any time with minimal code change. The sooner the better to avoid budget waste. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| GSI enemy data limitation | Phase 1 (GSI Foundation) | Architecture diagram explicitly shows two data flows: GSI (player data) and screenshot/manual (enemy data). No GSI model fields for enemy data. |
| Docker GSI networking | Phase 1 (GSI Foundation) | End-to-end test: Dota 2 on gaming PC sends GSI POST to Unraid Docker container. Backend receives and parses the data. Test with actual deployment, not local dev. |
| Claude API call flood | Phase 3 (Auto-Refresh) | Run a simulated 30-minute game with GSI data replay. Count Claude API calls in logs. Must be 15 or fewer per game. |
| Screenshot parsing reliability | Phase 2 (Screenshot Parsing) | Test with 10 diverse scoreboard screenshots (different resolutions, different game times). Measure item identification accuracy. Target >85% per-item accuracy with user confirmation. |
| WebSocket silent disconnect | Phase 1 (WebSocket Foundation) | Simulate network disconnect (kill WebSocket connection). Frontend must show "disconnected" indicator within 30 seconds. Reconnection must restore full state. |
| Manual/GSI state conflicts | Phase 1 (GSI Foundation) | Zustand store code review: every auto-detectable field has `source` property. Manual override test: set field manually, verify GSI update does NOT overwrite. |
| Screenshot cost control | Phase 2 (Screenshot Parsing) | Measure token count per screenshot parse. Must be under 200 tokens (cropped image). Full screenshot token count as a regression test (must NOT be used). |
| Lane result auto-detection | Phase 3 (Auto-Refresh) | At 10:00 game time in simulated data, verify lane result is auto-detected and shown with confirmation prompt. Verify user can override to a different result. |
| Nginx WebSocket support | Phase 1 (WebSocket Foundation) | WebSocket connection test through Nginx proxy. Verify connection stays alive for 5+ minutes without timeout. Verify Upgrade headers are present in Nginx config. |
| GSI .cfg generation | Phase 1 (GSI Foundation) | Setup flow generates a .cfg file. File contents include correct server IP, auth token, and all required data fields. User can download and place in Dota 2 cfg directory. |

## Sources

- [Dota 2 GSI - antonpup/Dota2GSI](https://github.com/antonpup/Dota2GSI) - C# library, most comprehensive GSI data field documentation. Confirms player-only data restriction during gameplay.
- [Dota 2 GSI Issue 1023 - Intermittent connectivity](https://github.com/ValveSoftware/Dota-2/issues/1023) - Known intermittent connection issues, Linux containerization problems, delayed event transmission.
- [Game State Integration Intro - auo.nu](https://auo.nu/posts/game-state-integration-intro/) - GSI .cfg configuration, data fields, observer vs player distinction, authentication.
- [dota2gsipy - Python GSI Library](https://github.com/Daniel-EST/dota2gsipy) - Python GSI implementation, minimal maintenance (v0.1), basic HTTP POST listener pattern.
- [Claude Vision API Documentation](https://platform.claude.com/docs/en/build-with-claude/vision) - Image size limits (5MB API), token calculation (width*height/750), cost tables, supported formats, known limitations.
- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/) - WebSocket endpoint patterns, connection management.
- [FastAPI WebSocket Scaling Techniques - hexshift](https://hexshift.medium.com/top-ten-advanced-techniques-for-scaling-websocket-applications-with-fastapi-a5af1e5e901f) - Task cleanup on disconnect, background task leaks, Redis pub/sub for multi-worker.
- [FastAPI WebSocket Auth - peterbraden](https://peterbraden.co.uk/article/websocket-auth-fastapi/) - WebSocket authentication patterns, query parameter tokens, custom close codes.
- [WebSocket Best Practices - websocket.org](https://websocket.org/guides/best-practices/) - Heartbeat protocol, reconnection with backoff, state recovery.
- [React WebSocket Best Practices - maybe.works](https://maybe.works/blogs/react-websocket) - useRef for connection, singleton pattern, cleanup in useEffect, exponential backoff reconnection.
- [Claude API Rate Limits](https://platform.claude.com/docs/en/api/rate-limits) - Token bucket algorithm, RPM/TPM/daily limits, tier system.
- [Dota 2 GSI - xzion/dota2-gsi (Node.js)](https://github.com/xzion/dota2-gsi) - GSI data structure, event handling patterns, JSON variability between play/spectate modes.

---
*Pitfalls research for: Live game intelligence for Dota 2 item advisor (v2.0)*
*Researched: 2026-03-23*

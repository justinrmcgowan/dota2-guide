# Feature Research: v2.0 Live Game Intelligence

**Domain:** Dota 2 real-time game integration (GSI, screenshot parsing, auto gold tracking, WebSocket)
**Researched:** 2026-03-23
**Confidence:** HIGH (GSI well-documented, vision API verified, WebSocket patterns mature)

## Feature Landscape

### Table Stakes (Users Expect These)

Features that any GSI-powered Dota 2 tool must have. Dotabuff App and Dota Plus already set user expectations here.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| GSI endpoint receives game state | Valve official mechanism; Dotabuff App, Dota Plus, Overwolf all use it | MEDIUM | FastAPI POST endpoint at /api/gsi. Dota 2 POSTs JSON to a configurable URI every 0.1-5s depending on throttle settings. Must validate auth token from cfg file |
| Auto-detect own hero from GSI | GSI provides hero.name in console format (e.g., npc_dota_hero_antimage). Every GSI tool auto-populates the hero | LOW | Map console name to hero_id in DB. Fires during DOTA_GAMERULES_STATE_PRE_GAME or DOTA_GAMERULES_STATE_GAME_IN_PROGRESS |
| Auto-detect own items/inventory | GSI provides items.slot0-slot5.name, items.stash0-stash5.name, items.backpack0-backpack2.name. Dotabuff App tracks gold progress toward next item | LOW | Parse item names from console format. Cross-reference with purchased items in recommendationStore. Auto-mark items as purchased |
| Auto-track gold/net worth | GSI exposes player.gold, player.gold_reliable, player.gold_unreliable, player.gpm, player.net_worth. Core to any real-time advisor | LOW | Direct field reads from GSI payload. Update gameStore with current gold. Display gold progress toward next recommended item |
| Game clock sync | GSI exposes map.clock_time and map.game_time. Users expect the app to know what phase of the game they are in | LOW | Use clock_time for phase detection: 0-10 min = laning, 10-25 min = midgame, 25+ = lategame. Current phase already exists in gameStore |
| WebSocket push to frontend | GSI data arrives at backend; frontend needs real-time updates without polling. All modern game overlays use push-based updates | MEDIUM | FastAPI WebSocket endpoint /ws/game-state. Backend receives GSI POST, processes, pushes to connected frontend clients. Single connection per browser tab |
| GSI connection status indicator | Users need to know if the Dota client is actually sending data. Dotabuff App shows connection status prominently | LOW | Heartbeat-based: GSI config supports heartbeat field. Display connected/disconnected in frontend header. Timeout after 2x heartbeat interval |

### Differentiators (Competitive Advantage)

Features that set Prismlab apart from Dotabuff App and Dota Plus. These leverage the existing hybrid recommendation engine.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Auto-determine lane result from gold data | At ~10 min, compare own GPM/net worth against expected benchmarks for role+hero. Auto-set lane_result (won/even/lost) instead of manual toggle. No other tool does this for item recommendations | MEDIUM | Algorithm: track gold at game start and at 10 min mark. Compare against role-specific benchmarks (Pos 1 carry: 5000+ gold at 10 min = won lane; 3500-5000 = even; below 3500 = lost). GPM thresholds from OpenDota hero averages. Trigger re-evaluation automatically |
| Screenshot parsing for enemy items via Claude Vision | User pastes scoreboard screenshot (Tab screen), Claude Vision extracts enemy hero items and maps them to enemyItemsSpotted. No manual item-by-item entry. Unique to Prismlab because the app already has Claude API integration | HIGH | Send screenshot as base64 to Claude API with structured output schema. Identify all items for each enemy hero. ~1600 tokens per 1MP screenshot at ~$0.005/image. Must handle: scoreboard layout variations, item icon recognition at small sizes, mapping to internal item names. Rate-limit: max 1 screenshot parse per 60s |
| Auto-refresh recommendations on key events | When GSI detects: (a) new item purchased, (b) 10-min mark crossed, (c) significant gold milestone reached, (d) death -- auto-queue a re-evaluation instead of requiring manual Re-Evaluate click. Rate-limited to max 1 per 2 minutes | HIGH | Event detection from GSI diff (compare previous vs current state). Queue system with 2-min cooldown. Claude API call is expensive so batching events is critical. Must not disrupt user if they are mid-action |
| Gold progress bar toward next item | Visual progress (e.g., 2100/4150 gold toward BKB) using real-time gold from GSI. Dotabuff App does this but Prismlab ties it to the hybrid engine specific recommendation with reasoning | LOW | Calculate: current_gold / next_recommended_item_cost. Account for reliable vs unreliable gold. Component cost breakdown |
| Draft auto-detection from GSI | GSI exposes draft.team2.pick0_id through pick4_id and draft.team3.pick0_id through pick4_id. Auto-populate all 10 hero slots during the draft phase without manual entry | MEDIUM | GSI sends draft data during DOTA_GAMERULES_STATE_HERO_SELECTION. Map pick IDs to heroes. Auto-fill allies[] and opponents[] in gameStore. Challenge: draft data only fully available to spectators; player mode may only see own pick plus already-revealed picks |
| Automatic game phase progression | Instead of user manually managing phases, detect phase transitions from GSI clock + events: pre-game to laning to mid-game to late game. Collapse/expand timeline phases automatically | LOW | Clock thresholds + event triggers. Already have phase concept in UI; wire to GSI clock data |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time enemy item tracking via GSI | Just read enemy items from game data | GSI in player mode (not spectator) only exposes YOUR OWN data. Enemy items are NOT available through GSI. Anti-cheat restriction by Valve. Reading game memory is bannable | Screenshot parsing via Claude Vision. User opens scoreboard (Tab), takes screenshot, pastes into app. Slower but VAC-safe |
| Clipboard monitoring / auto-capture screenshots | Auto-detect when I open scoreboard and capture it | Requires OS-level hooks, raises anti-cheat concerns, platform-specific. Too invasive | Manual paste only for v2.0. User presses PrtScn, Ctrl+V into app. Clean, explicit, cross-platform |
| In-game overlay via GSI | Display item recommendations as overlay on top of game | Requires injecting into game rendering pipeline or overlay SDK (Overwolf). VAC risk, heavy development, platform-specific | Prismlab stays as second-monitor/alt-tab web app. Updates real-time via WebSocket |
| Auto-detect enemy heroes from GSI during game | Fill in opponent heroes automatically | Player-mode GSI does not reliably expose all 10 heroes. Only your own pick and revealed enemy picks visible. Full enemy team only guaranteed for spectators | Hybrid: auto-detect what GSI reveals, let user fill gaps manually |
| Re-evaluate on every GSI tick | Update recommendations constantly | GSI sends every 0.1-1s. Claude API calls take 3-10s and cost ~$0.01 each. Would cost $6/hour and create poor UX with constantly shifting recommendations | Rate-limit to max 1 per 2 minutes. Batch events. Only trigger on meaningful state changes |
| Voice coaching / TTS callouts | Tell me what to buy next via audio | Significant scope expansion. Not core to v2.0 goal | Text-only for v2.0. Voice is v3.0 feature |

## Feature Dependencies

\`\`\`
[GSI Endpoint (backend)]
    +-- requires --> [GSI Config File Setup (user action)]
    +-- enables --> [WebSocket Push to Frontend]
    |                   +-- enables --> [GSI Connection Status Indicator]
    |                   +-- enables --> [Real-time Gold/Item Display]
    |                   +-- enables --> [Auto Game Phase Progression]
    +-- enables --> [Auto-detect Own Hero]
    |                   +-- enables --> [Draft Auto-detection]
    |                                       +-- enables --> [Auto-fill Allies/Opponents]
    +-- enables --> [Auto-detect Own Items]
    |                   +-- enables --> [Auto-mark Purchased Items]
    |                   +-- enables --> [Gold Progress Bar]
    |                   +-- enables --> [Auto-refresh on Key Events]
    |                                       +-- requires --> [Rate Limiter (2-min cooldown)]
    +-- enables --> [Auto-track Gold/Net Worth]
    |                   +-- enables --> [Auto-determine Lane Result]
    +-- enables --> [Game Clock Sync]
                        +-- enables --> [Auto Game Phase Progression]
                        +-- enables --> [Auto-determine Lane Result (at 10 min)]

[Screenshot Parsing (Claude Vision)]
    +-- requires --> [Paste/Upload UI Component]
    +-- requires --> [Claude Vision API Integration (backend)]
    +-- requires --> [Item Name Mapping (console name -> DB)]
    +-- enables --> [Auto-fill Enemy Items Spotted]
    +-- independent of GSI (works without GSI enabled)

[Existing Manual Controls]
    +-- remain as fallback for everything GSI automates
    +-- user can override any auto-detected value
\`\`\`

### Dependency Notes

- **GSI Endpoint requires GSI Config File:** User must place a .cfg file in their Dota 2 installation directory and add -gamestateintegration to launch options.
- **WebSocket requires GSI Endpoint:** WebSocket only has data to push if GSI is actively sending. Connect on page load but display no-game-data until GSI connects.
- **Screenshot Parsing is independent of GSI:** Even without GSI, users can paste screenshots. Standalone feature feeding enemyItemsSpotted.
- **Auto-refresh requires Rate Limiter:** 2-minute cooldown is a hard requirement to avoid Claude API cost explosion.
- **Draft Auto-detection has data limitations:** Player mode may not expose all enemy picks. Handle partial data gracefully, allow manual overrides.
- **Auto-determine Lane Result requires Gold Baseline:** Need role+hero-specific GPM benchmarks at 10 minutes from OpenDota.

## MVP Definition

### Launch With (v2.0 Core)

- [ ] GSI endpoint (/api/gsi) receiving and parsing Dota 2 game state -- foundation for everything
- [ ] GSI config file generation/instructions -- user must be able to set this up easily
- [ ] WebSocket endpoint (/ws/game-state) pushing processed game state to frontend
- [ ] Frontend WebSocket hook with reconnection -- receives and applies game state updates to Zustand stores
- [ ] GSI connection status indicator in header
- [ ] Auto-detect own hero from GSI -- eliminates first manual step
- [ ] Auto-detect own items and auto-mark purchased -- biggest time-saver during live games
- [ ] Auto-track gold/net worth -- enables gold progress toward next item
- [ ] Game clock sync and auto-phase progression -- removes manual phase management
- [ ] Screenshot paste for enemy items via Claude Vision -- killer feature for enemy intel
- [ ] Manual controls remain as overrides and fallbacks -- nothing breaks if GSI is not enabled

### Add After Validation (v2.x)

- [ ] Auto-determine lane result from gold data at 10 min -- requires tuning benchmarks
- [ ] Gold progress bar toward next recommended item with component breakdown
- [ ] Auto-refresh recommendations on key events with 2-min rate limit
- [ ] Draft auto-detection from GSI draft data -- complex due to player-mode limitations

### Future Consideration (v3+)

- [ ] Docker networking optimization for remote Dota clients
- [ ] Multiple simultaneous game tracking -- party/coaching mode
- [ ] Voice coaching / TTS callouts for item timing reminders
- [ ] Hotkey-triggered screenshot capture (OS-level integration)
- [ ] Match history saving with GSI game data for post-game review

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| GSI endpoint + config setup | HIGH | MEDIUM | P1 |
| WebSocket push to frontend | HIGH | MEDIUM | P1 |
| GSI connection status indicator | MEDIUM | LOW | P1 |
| Auto-detect own hero | HIGH | LOW | P1 |
| Auto-detect own items / auto-mark purchased | HIGH | LOW | P1 |
| Auto-track gold/net worth | HIGH | LOW | P1 |
| Game clock sync + auto-phase progression | MEDIUM | LOW | P1 |
| Screenshot parsing for enemy items (Claude Vision) | HIGH | HIGH | P1 |
| Manual controls remain as fallback | HIGH | LOW | P1 |
| Auto-determine lane result | MEDIUM | MEDIUM | P2 |
| Gold progress bar toward next item | MEDIUM | LOW | P2 |
| Auto-refresh on key events | HIGH | HIGH | P2 |
| Draft auto-detection | MEDIUM | HIGH | P2 |
| Docker networking for remote Dota | LOW | MEDIUM | P3 |
| Voice coaching | LOW | HIGH | P3 |

## Competitor Feature Analysis

| Feature | Dotabuff App | Dota Plus (Valve) | Prismlab v2.0 |
|---------|-------------|-------------------|---------------|
| GSI data integration | Yes -- reads hero, items, gold | Yes -- native integration | Yes -- same GSI mechanism |
| Item suggestions | Static builds from win-rate data | Three suggested builds, lane-specific | Hybrid engine: rules + Claude reasoning with per-item matchup explanations |
| Gold progress tracking | Shows gold toward next item | Shows item completion progress | Gold progress + component breakdown + reliable/unreliable split |
| Enemy item detection | No | No -- in-game only (Tab screen) | Claude Vision screenshot parsing -- unique differentiator |
| Natural language reasoning | No -- data only | No -- percentages only | Yes -- contextual explanations referencing hero abilities and matchup dynamics |
| Adaptive re-evaluation | Limited -- adjusts to draft | Adjusts to purchased items | Full re-evaluation with lane result, damage profile, enemy items, gold state |
| Lane result detection | Post-game analytics only | No | Auto-detect at 10 min from gold data |
| Setup friction | Desktop app install + Steam login | Built into game client | Config file in Dota folder + launch option flag + open web app |

**Key competitive insight:** Dotabuff App and Dota Plus provide data-driven suggestions but neither explains why. Prismlab differentiator is the hybrid reasoning engine. GSI integration means the reasoning engine gets better inputs automatically. Screenshot parsing for enemy items is genuinely unique.

## GSI Technical Details (Research Findings)

### What GSI Exposes in Player Mode

When playing (not spectating), Dota 2 GSI exposes ONLY the local player data.

**Available to players (HIGH confidence -- verified across multiple GSI libraries):**
- hero.name -- own hero, console format (e.g., npc_dota_hero_antimage)
- hero.level, hero.health, hero.max_health, hero.mana, hero.max_mana
- hero.alive, hero.respawn_seconds, hero.buyback_cost, hero.buyback_cooldown
- hero.xpos, hero.ypos -- map coordinates (usable for lane detection)
- player.gold, player.gold_reliable, player.gold_unreliable
- player.gpm, player.xpm, player.net_worth
- player.kills, player.deaths, player.assists, player.last_hits, player.denies
- items.slot0-slot5.name, items.stash0-stash5.name, items.backpack0-backpack2.name
- items.slot0-slot5.cooldown, items.slot0-slot5.charges
- abilities.ability0-abilityN.name, level, cooldown
- map.clock_time, map.game_time, map.daytime, map.game_state, map.matchid

**NOT available to players (anti-cheat restriction):**
- Other players hero data, items, gold, position
- Enemy team draft picks (only revealed picks visible during pick phase)
- Building health for enemy structures (unconfirmed)

**Game state values (HIGH confidence):**
- DOTA_GAMERULES_STATE_WAIT_FOR_PLAYERS_TO_LOAD
- DOTA_GAMERULES_STATE_HERO_SELECTION
- DOTA_GAMERULES_STATE_STRATEGY_TIME
- DOTA_GAMERULES_STATE_PRE_GAME
- DOTA_GAMERULES_STATE_GAME_IN_PROGRESS
- DOTA_GAMERULES_STATE_POST_GAME

### GSI Configuration

\`\`\`
"prismlab Configuration"
{
    "uri"           "http://localhost:8420/api/gsi"
    "timeout"       "5.0"
    "buffer"        "0.5"
    "throttle"      "1.0"
    "heartbeat"     "30.0"
    "data"
    {
        "provider"      "1"
        "map"           "1"
        "player"        "1"
        "hero"          "1"
        "abilities"     "1"
        "items"         "1"
        "draft"         "1"
    }
    "auth"
    {
        "token"         "prismlab_gsi_token"
    }
}
\`\`\`

**Key settings:** buffer 0.5 (aggregate events over 0.5s), throttle 1.0 (max 1 update/sec), heartbeat 30.0 (ping every 30s when idle).

### Docker Networking

Dota 2 runs on the gaming PC. Prismlab runs in Docker on Unraid. The GSI config uri must point to the Unraid server IP, not localhost:
- Config file URI: http://UNRAID_IP:8420/api/gsi
- Backend must accept POSTs from external IPs
- CORS/firewall must allow Dota client to reach the backend

### VAC Safety

GSI is Valve official API. It does NOT read game memory, inject code, or interact with the game process. Multiple community applications (Dotabuff App, Overwolf apps, casting overlays) use GSI without VAC issues. The -gamestateintegration launch option is officially supported. **Using GSI is safe.** (MEDIUM confidence -- no explicit Valve statement, but wide community usage without bans is strong evidence.)

## Screenshot Parsing Technical Details

### Claude Vision API for Enemy Items

**Approach:** User opens scoreboard (Tab key), takes screenshot (PrtScn or Win+Shift+S), pastes into Prismlab. Backend sends base64 image to Claude Vision API with structured output request.

**Cost:** ~1600 tokens per 1MP image at $3/M input tokens = ~$0.005 per parse. Negligible.

**Accuracy considerations (MEDIUM confidence):**
- Dota 2 scoreboard item icons are ~32x32 pixels in a 1920x1080 screenshot
- Claude Vision accuracy diminishes with small icons and dense layouts
- Mitigation: crop scoreboard region, provide reference list of valid item names, use structured output
- Scoreboard layout is consistent (same structure every game), aiding reliable extraction

**Extraction strategy:**
- Include reference list of all valid Dota 2 item names from items DB
- Ask Claude to identify each enemy hero items by scoreboard row
- Structured output schema: {heroes: [{name: string, items: string[]}]}
- Validate returned item names against DB before applying

**Limitations:**
- Items in backpack/stash not visible in scoreboard
- Screenshot must be clear and unobstructed
- Works best at 1080p+ resolution
- Captures a moment in time only

**Recommendation: Use Claude Vision over template matching.** Cost is negligible, accuracy is sufficient, and it leverages existing API integration. Template matching (OpenCV) breaks on patch icon changes and resolution variations.

## Lane Result Auto-Detection Algorithm

Use GPM at the 10-minute mark vs role-specific benchmarks from OpenDota.

| Role | Won Lane GPM | Even Lane GPM | Lost Lane GPM |
|------|-------------|---------------|---------------|
| Pos 1 (Carry) | >550 | 400-550 | below 400 |
| Pos 2 (Mid) | >550 | 400-550 | below 400 |
| Pos 3 (Offlane) | >450 | 300-450 | below 300 |
| Pos 4 (Soft Support) | >300 | 200-300 | below 200 |
| Pos 5 (Hard Support) | >250 | 150-250 | below 150 |

**Why GPM not net worth:** Net worth includes starting gold, less normalized. GPM at 10 min reflects actual farm efficiency.

**Implementation:** Record gold at game start. At map.clock_time >= 600, calculate GPM. Compare against thresholds. Auto-set laneResult. Trigger re-evaluation if cooldown permits. User can always override.

## Sources

### GSI Documentation and Libraries
- [Dota2GSI C# Library](https://github.com/antonpup/Dota2GSI) -- most comprehensive field docs
- [dota2-gsi Node.js Library](https://github.com/xzion/dota2-gsi) -- event-driven interface
- [dota2gsipy Python Library](https://github.com/Daniel-EST/dota2gsipy) -- Python implementation
- [dota2-gsi JVM Library](https://mrbean355.github.io/dota2-gsi/) -- typed data model
- [GSI Intro](https://auo.nu/posts/game-state-integration-intro/) -- configuration walkthrough

### Claude Vision API
- [Claude Vision Documentation](https://platform.claude.com/docs/en/build-with-claude/vision) -- official
- [Claude Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

### Competitor Analysis
- [Dotabuff App Adaptive Items](https://www.dotabuff.com/blog/2021-06-23-announcing-the-dotabuff-apps-new-adaptive-items-module)
- [Dota Plus](https://www.dota2.com/plus)

### WebSocket Patterns
- [FastAPI WebSocket Docs](https://fastapi.tiangolo.com/advanced/websockets/)

### Game Analytics
- [STRATZ Lane Outcomes](https://stratz.com/knowledge-base/General/How%20are%20lane%20outcomes%20calculated)
- [Dotabuff Laning Analysis](https://www.dotabuff.com/blog/2017-10-09-analyze-your-laning-stage)

---
*Feature research for: Dota 2 Live Game Intelligence (v2.0)*
*Researched: 2026-03-23*

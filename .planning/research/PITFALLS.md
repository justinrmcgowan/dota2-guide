# Pitfalls Research

**Domain:** Dota 2 adaptive item advisor with hybrid rules+LLM engine
**Researched:** 2026-03-21
**Confidence:** HIGH (multiple authoritative sources cross-referenced)

## Critical Pitfalls

### Pitfall 1: LLM Hallucinating Item Names, Abilities, and Interactions

**What goes wrong:**
Claude invents item names that do not exist in Dota 2, confuses items that have been renamed across patches (e.g., "Poor Man's Shield" removed in 7.20, "Vanguard" renamed components), or describes ability interactions that are factually incorrect. Research shows LLMs hallucinate named entities at alarming rates -- up to 26% of tasks with one-character name similarity, and structured output compliance does NOT prevent semantic hallucination. Anthropic explicitly states: "We guarantee that the model's output will adhere to a specified format, not that any output will be 100% accurate."

**Why it happens:**
Claude's training data contains Dota 2 information from multiple patches spanning years. Items get added, removed, renamed, and reworked constantly (Patch 7.39 alone removed 12+ neutral items and added 8 new ones, Patch 7.40 reworked Ethereal Blade, Guardian Greaves, and Radiance). The LLM has no way to distinguish current-patch item data from historical data without explicit grounding.

**How to avoid:**
- Pass a **complete item ID-to-name mapping** in every prompt context. The LLM should only reference items from this list.
- Use structured outputs with an `item_id` integer field referencing your database, NOT a freetext `item_name` string. Validate that every `item_id` in the response exists in your items table before returning to frontend.
- Include a constraint in the system prompt: "You may ONLY recommend items from the provided item list. If an item is not in the list, it does not exist in this patch."
- Post-process every Claude response to verify item IDs resolve to real items. Reject and retry (or fall back to rules) if validation fails.

**Warning signs:**
- Items appearing in recommendations that return 404 from your items endpoint
- Recommendations mentioning items by old names (e.g., "Ring of Aquila" which was removed years ago)
- Ability descriptions that don't match current hero data (e.g., referencing a pre-rework ability)

**Phase to address:**
Phase 3 (Recommendation Engine). The context builder and response validator are the defense layers. This must be solved before any user-facing recommendation is displayed.

---

### Pitfall 2: Post-Patch Data Staleness Window

**What goes wrong:**
A major Dota 2 patch drops (7.39, 7.40, etc.) and the app's cached hero stats, item data, matchup win rates, and item build popularity are now wrong. Items get added/removed, heroes get reworked, stats change. Win rate data from OpenDota/Stratz takes days to weeks to become statistically meaningful after a patch -- early post-patch data has tiny sample sizes and is dominated by players experimenting, not playing optimally.

**Why it happens:**
Dota 2 ships 2-4 major patches per year with sweeping changes. Patch 7.39 (May 2025) reworked the entire Facet system and rotated the neutral item pool. Patch 7.40 (December 2025) reworked Lone Druid, Slark, and Treant Protector entirely. OpenDota constants data (hero list, item list) updates relatively quickly after a patch, but win rate and item popularity data requires thousands of games to stabilize -- typically 1-2 weeks minimum.

**How to avoid:**
- Separate "constants data" (hero names, item names, stats) from "statistical data" (win rates, item popularity). Constants should refresh within hours of a patch. Statistical data should carry a `patch_version` tag and a `games_sampled` count.
- Display a visible warning when `games_sampled < 1000` for a matchup: "Limited data for this matchup in current patch."
- When statistical data is stale, lean harder on the rules engine and Claude's general game knowledge rather than data-driven recommendations. The prompt should say: "Note: matchup statistics may reflect the previous patch. Weight your game knowledge more heavily than the provided win rates."
- Track the current Dota 2 patch version (scrape from the Dota 2 blog or use OpenDota's constants endpoint) and compare against your stored data's patch version.

**Warning signs:**
- Win rate data showing heroes as strong/weak that the community consensus disagrees with
- Items in your database that no longer exist in-game
- Heroes missing from your database after a new hero release (Largo added in 7.40)
- `updated_at` timestamps on matchup data older than the latest patch date

**Phase to address:**
Phase 1 (Foundation) for the data model design that supports patch versioning. Phase 6 (Polish + Data Pipeline) for the automated refresh and staleness detection system. But the data model must be designed correctly from the start.

---

### Pitfall 3: Generic "Good Advice" Instead of Matchup-Specific Reasoning

**What goes wrong:**
The LLM recommends items that are generically good on the hero regardless of the matchup, opponent, or game state. Example: always recommending BKB on carry heroes because it's "always good" rather than explaining "BKB is critical here because Lina and Lion have 4 combined single-target disables and 3 magic nukes, and you need to survive their burst window to get your Phantom Strike off." Community feedback on Dota Plus (Valve's built-in recommendation system) is overwhelmingly negative precisely because of this -- it suggests items without matchup reasoning.

**Why it happens:**
- The prompt context doesn't include enough specific matchup information (opponent abilities, damage types, disable durations)
- The system prompt doesn't enforce the specificity requirement strongly enough
- The LLM defaults to safe, generic advice because it's technically correct
- No feedback loop or quality check on reasoning specificity

**How to avoid:**
- The context builder must assemble rich matchup data: opponent hero abilities (names and effects), damage types the opponents deal, disable types and durations, the specific items commonly built against this matchup. This is NOT optional context -- it's the core value of the product.
- System prompt must include explicit constraints: "Every reasoning field MUST mention at least one enemy hero by name AND at least one specific ability or mechanic. Generic reasoning like 'provides good stats' is unacceptable."
- Include few-shot examples in the system prompt showing the DIFFERENCE between generic and specific reasoning. Show a bad example and a good example side by side.
- Post-process reasoning text: if no enemy hero name appears in the reasoning string, flag it for regeneration or supplement with rules-engine commentary.

**Warning signs:**
- Reasoning text that could apply to any game (no hero names, no ability references)
- Same items recommended regardless of opponent changes
- User feedback that advice "sounds like a guide, not a coach"

**Phase to address:**
Phase 3 (Recommendation Engine). The system prompt and context builder are the primary defense. The few-shot examples in the system prompt are especially critical -- invest real time crafting 3-4 high-quality examples.

---

### Pitfall 4: Claude API Latency Killing Mid-Game Usability

**What goes wrong:**
During a live Dota 2 game, the player has approximately 10-30 seconds of downtime (death timer, walking to lane, brief pause). If the Claude API takes 5-15 seconds to respond, the recommendation arrives too late to be useful. The player either doesn't use the tool mid-game or learns to not trust it for timely advice.

**Why it happens:**
Claude Sonnet API calls with 2K+ input tokens and structured output can take 3-8 seconds in normal conditions, and 10-15+ seconds under API load or with larger context windows. Network latency to Anthropic's API adds 100-500ms. If the prompt includes extensive hero data, item lists, and matchup context, input tokens balloon and latency increases proportionally.

**How to avoid:**
- **10-second hard timeout** on Claude API calls. If it doesn't respond in time, immediately return rules-only recommendations with a note: "Quick recommendations (detailed analysis loading...)". Then optionally complete the LLM call in the background and push updated results.
- **Minimize input token count.** Don't dump the entire hero/item database into every prompt. Only include the relevant heroes (your hero + lane opponents), their key abilities, and the specific items already being considered by the rules engine. Target under 1500 input tokens.
- **Cache system prompt context.** Hero ability descriptions, item stats, and other static data should be in the system prompt (which Anthropic caches across calls), not in the user message.
- **Pre-compute during draft phase.** When the user selects their hero and opponents, immediately fire the first Claude API call. Don't wait for them to click "Get Recommendations."
- **Use streaming** for the initial recommendation (show items as they're generated). For re-evaluation, use non-streaming with timeout + fallback.

**Warning signs:**
- Average API response time exceeding 5 seconds in logs
- Users clicking "Re-Evaluate" and then alt-tabbing back to the game before results load
- Input token counts growing beyond 2000 tokens per request

**Phase to address:**
Phase 3 (Recommendation Engine) for the timeout/fallback architecture. Phase 5 (Mid-Game Adaptation) for the re-evaluation speed optimization. Phase 6 for performance monitoring and optimization.

---

### Pitfall 5: OpenDota and Stratz API Rate Limits Exhausted During Data Seeding

**What goes wrong:**
The initial data seeding process (fetching all heroes, all items, all matchup data for every hero pair) requires thousands of API calls. With 124+ heroes, fetching matchup data for every hero pair is 124 x 123 = 15,252 matchup combinations. OpenDota's free tier allows 50,000 calls/month and 60/minute. Stratz allows 10,000 calls/day on a default token. A naive seeding script blows through these limits in minutes, gets rate-limited, and the seeding process fails or takes hours.

**Why it happens:**
Developers underestimate the combinatorial explosion of hero matchup data. 124 heroes means ~15K matchup pairs. Each pair might need multiple API calls (win rates by bracket, common items). Without rate limiting on the client side, you hit the API rate limit wall immediately.

**How to avoid:**
- **Batch and throttle.** Implement a request queue with configurable delay (minimum 1 second between calls for OpenDota, respect Stratz's 20/second limit). Use asyncio with a semaphore to limit concurrent requests.
- **Prioritize data.** Don't fetch ALL matchup pairs on first seed. Fetch hero and item constants first (2 API calls). Then fetch matchup data lazily -- when a user queries a specific matchup, fetch and cache it on-demand. Pre-populate only the top 20 most popular heroes' matchups.
- **Use bulk endpoints.** OpenDota's `/heroStats` endpoint returns aggregated data for all heroes in a single call. Use it instead of individual hero endpoints. The `/heroes/{hero_id}/matchups` endpoint returns all matchup data for one hero in a single call.
- **Cache aggressively.** Matchup data doesn't change between patches. Cache everything in SQLite with `patch_version` tracking. Only refresh when a new patch is detected.
- **Stratz GraphQL advantage.** Stratz's GraphQL API lets you request exactly the fields you need and can batch multiple hero queries into a single request, drastically reducing call count.

**Warning signs:**
- HTTP 429 responses from OpenDota/Stratz during seeding
- Seeding script taking longer than 30 minutes
- Incomplete matchup data in the database after seeding completes
- Monthly API call budget exhausted in the first week

**Phase to address:**
Phase 1 (Foundation) for the API client design with built-in rate limiting. Phase 3 for matchup data ingestion strategy. Phase 6 for the automated refresh pipeline.

---

### Pitfall 6: SQLite Locking Under Docker on Unraid with Mounted Volumes

**What goes wrong:**
SQLite uses file-level locking. When the database file lives on a Docker volume mounted from the Unraid host (potentially on an array or cache drive), file locking behavior can be unreliable. WAL mode -- which is critical for concurrent read/write access -- requires shared memory between processes, and this can fail on network filesystems. The symptom is intermittent "database is locked" errors, especially when the data refresh script runs while a user is requesting recommendations.

**Why it happens:**
Unraid's storage system uses FUSE-based filesystems for array drives, and some cache drive configurations use btrfs or XFS. SQLite's WAL mode requires that the filesystem properly support `mmap` and POSIX advisory locking. Docker bind mounts from FUSE filesystems can violate these assumptions. This is a known issue documented in multiple Docker/SQLite issue trackers.

**How to avoid:**
- **Store the SQLite database on a cache drive, NOT the array.** Unraid cache drives (typically SSD/NVMe with ext4/XFS) have proper filesystem support for SQLite WAL mode. Array drives (FUSE-based) do not.
- **Enable WAL mode explicitly** in the SQLAlchemy engine configuration: `engine = create_engine("sqlite:///./data/prismlab.db", connect_args={"check_same_thread": False})` and execute `PRAGMA journal_mode=WAL` on connection.
- **Set PUID/PGID environment variables** in the Docker Compose file to match the Unraid user's UID/GID, preventing permission mismatches on the mounted volume.
- **Use connection pooling with NullPool or StaticPool** for SQLite in async FastAPI to avoid connection contention. Or use a single writer pattern where all writes go through a dedicated background task.
- **Document the volume mount requirement clearly** in the deployment instructions.

**Warning signs:**
- "database is locked" errors in backend logs
- Intermittent 500 errors on API endpoints that write to the database
- Data refresh script failing silently or partially completing
- WAL file (-wal) growing without bound (checkpoint starvation)

**Phase to address:**
Phase 1 (Foundation) for database configuration and Docker Compose setup. Must be validated early with actual Unraid deployment, not just local Docker.

---

### Pitfall 7: Structured Output Schema Rigidity vs. Recommendation Flexibility

**What goes wrong:**
The recommendation response schema is designed with fixed phases (starting, early_laning, laning_complete, first_core, situational). But real Dota 2 games don't follow a rigid phase structure. Some games need a "survive the lane" emergency phase. Some heroes skip early items entirely and rush a key item. The rigid schema forces Claude to fill every phase with recommendations even when the optimal advice is "skip this phase and rush X." Alternatively, Claude wants to recommend conditional branches ("if they have BKB, get Y; otherwise get Z") but the schema doesn't support it cleanly.

**Why it happens:**
Designing a JSON schema upfront based on the "average game" rather than the full range of game states. The temptation is to model the happy path and force every game into that structure. But Dota 2 is a game of exceptions -- the best advice is often situational, conditional, and non-linear.

**How to avoid:**
- Make phases **optional** in the schema. Not every recommendation needs every phase populated. Use `"required": false` on phase objects or allow null values.
- Include a `skip_reason` field: "Skip early laning items -- rush Midas before 8:00 for this build."
- The `situational` phase with `decision_trees` (already in the blueprint) is the right pattern. Extend it -- allow decision trees within ANY phase, not just the final one. "If lane is going well, buy X. If lane is contested, buy Y instead."
- Use Claude's structured outputs with a schema that supports an array of phases with a `phase_type` enum rather than fixed named phases. This lets Claude add or omit phases as needed.
- Test the schema with 10+ diverse hero/matchup scenarios before locking it down. Include edge cases: support heroes (fewer items, lower gold), late-game carries (item progression matters), turbo game timings.

**Warning signs:**
- Claude recommending filler items in phases where the real advice would be "skip this"
- All recommendations looking structurally identical regardless of hero role (carry vs support)
- Support heroes getting 6+ item recommendations when they'll realistically afford 3-4
- Users reporting that the advice "doesn't match how this hero actually plays"

**Phase to address:**
Phase 3 (Recommendation Engine) for schema design. Phase 4 (Item Timeline UI) for flexible rendering. Must be iterated on during Phase 5 (Mid-Game Adaptation) as more game states are tested.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoding hero/item IDs anywhere in rules engine | Faster rules implementation | Breaks every patch when IDs change or items are added/removed | Never -- always reference by internal_name or query from DB |
| Embedding full hero data in every Claude prompt | Simple context building | Token costs balloon, latency increases, prompt exceeds optimal size | Never -- use the system prompt cache for static data, user message for game-specific context only |
| Skipping Claude response validation | Faster iteration during dev | Hallucinated items, malformed data, or schema violations reach the frontend and confuse users | Only in local dev with mock data, never in production |
| Using OpenDota without an API key | Avoids signup friction | 50K calls/month limit, 60/min cap; will block data refresh and development iteration | Early development only, get a key before Phase 3 |
| Storing matchup data without patch version | Simpler data model | Cannot distinguish stale vs current data, cannot clear old data on patch day | Never -- always include patch version in matchup records |
| Synchronous Claude API calls in FastAPI | Simpler code | Blocks the event loop, one slow API call blocks ALL concurrent requests | Never -- always use async httpx or the async Anthropic client |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenDota API | Using individual hero endpoints for bulk data | Use `/heroStats` (all heroes, one call) and `/heroes/{id}/matchups` (all matchups for one hero, one call). Never loop over individual endpoints. |
| OpenDota API | Not handling 429 (rate limit) responses | Implement exponential backoff with jitter. OpenDota returns 429 with no Retry-After header -- start at 3s, double each retry, max 60s. |
| Stratz API | Using REST endpoints instead of GraphQL | Stratz's REST API is legacy. Their GraphQL API lets you fetch exactly the fields you need and batch queries. One GraphQL call can replace 10+ REST calls. |
| Stratz API | Ignoring bracket filtering | Stratz data defaults to all brackets. High-MMR item builds differ significantly from all-bracket averages. Always filter by Legend+ or Divine+ for recommendation quality. |
| Steam CDN | Constructing image URLs with display names instead of internal names | CDN uses internal short names (e.g., `antimage`, `bfury`). The OpenDota constants data provides the mapping. Heroes use `npc_dota_hero_` prefix in the API but CDN strips it. |
| Steam CDN | Assuming CDN URLs never break | New heroes and renamed items occasionally have missing or different CDN paths. Always include a fallback/placeholder image and check for 404s on hero portraits. |
| Claude API | Using the synchronous Python client in async FastAPI | Use `anthropic.AsyncAnthropic()` for async calls. The sync client will block the event loop and destroy throughput under any concurrent load. |
| Claude API | Not using structured outputs (parsing JSON from freetext) | Use `output_config.format` with a JSON schema. Structured outputs guarantee valid JSON since late 2025. Freetext JSON parsing is fragile and unnecessary. |
| Claude API | Prefilling responses with `{` for JSON | Prefilling is deprecated and not supported on Claude Sonnet 4.5+. Use structured outputs instead -- the feature exists specifically to replace prefill-based JSON hacks. |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading all heroes + items on frontend mount | Initial page load takes 2-3 seconds, visible FOUC or loading spinners | Pre-cache hero/item data with SWR or React Query with staleTime of 24h. Data changes only on patch days. | Immediately visible on first load |
| Re-fetching hero/item lists on every navigation | Unnecessary network requests, UI flicker | Use Zustand store or React Query cache. Hero/item data is essentially static between patches. | Noticeable with slow connections |
| Sending full item database in Claude prompt context | Token count exceeds 4000, latency doubles, cost triples | Only include items relevant to the hero's role and the matchup. A carry doesn't need support items in context. Filter to ~50 relevant items max. | First production use with real prompts |
| Not debouncing the hero search filter | Fires on every keystroke, 10+ filter operations per search | Debounce by 200-300ms. Hero list is ~124 items, filtering is fast, but rapid re-renders hurt perceived performance. | Noticeable on slower devices |
| Storing recommendations in Zustand without memoization | Timeline component re-renders on every store update | Memoize recommendation data with `useMemo` or Zustand selectors. Only re-render when recommendations actually change. | Noticeable when mid-game state toggles trigger re-renders |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Exposing ANTHROPIC_API_KEY in frontend code or client-side requests | API key theft, unauthorized usage charges, potential abuse | API key stays in backend .env only. Frontend calls your FastAPI backend, which calls Claude. Never expose the key in any client-facing code or network response. |
| No rate limiting on /api/recommend endpoint | Abuse vector: automated scripts hammering Claude API, running up costs | Implement rate limiting per IP (e.g., 10 requests/minute per IP) using FastAPI middleware. Each /recommend call costs real money. |
| Admin endpoints (data refresh, data status) accessible without authentication | Anyone can trigger data refreshes, potentially causing API rate limit exhaustion or data corruption | Protect /api/admin/* endpoints with at minimum a shared secret token in the Authorization header. |
| SQLite database file accessible via Nginx misconfiguration | Database download exposes cached matchup data (low risk, but bad practice) | Ensure Nginx only serves the built frontend assets, not the data volume. Docker network isolation helps -- frontend container shouldn't have access to backend's data volume. |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing a full-page loading spinner during Claude API calls | User can't reference current recommendations while waiting for re-evaluation results | Show loading state ONLY on the recommendation panel. Keep sidebar inputs interactive. Show a subtle progress indicator, not a blocker. |
| Requiring all inputs before generating any recommendations | User has to fill out hero + role + playstyle + side + lane + opponents before seeing anything | Generate partial recommendations as soon as a hero is selected. Each additional input refines the results. Progressive enhancement, not gate-keeping. |
| Using Dota 2 internal item names in the UI (e.g., "item_black_king_bar") | Confusing, non-human-readable text in the interface | Always map to display names ("Black King Bar"). Store internal names for API/CDN use only. |
| Not showing item cost alongside recommendations | Player can't assess gold feasibility at a glance | Always display gold cost next to each item. For supports (Pos 4/5), this is critical -- they need to know if they can afford the recommendation. |
| Damage profile inputs (physical/magical/pure %) showing before laning phase | Overwhelming the user with inputs they can't answer yet | Only reveal damage profile inputs after lane result is set (midgame transition). Progressive disclosure matching the actual game flow. |
| Tiny or unrecognizable item icons | User can't quickly identify items during a live game | Item icons should be at minimum 40x40px, ideally 48x48px. Use the higher-resolution CDN images. Add item name as both tooltip and visible text. |

## "Looks Done But Isn't" Checklist

- [ ] **Hero Picker:** Often missing attribute-based filtering (STR/AGI/INT/Universal) -- verify all four attribute filters work, including Universal heroes (added in 7.33)
- [ ] **Item recommendations:** Often missing component breakdown -- verify each recommended item shows its build-up components and intermediate items to buy
- [ ] **Structured output validation:** Often missing server-side validation -- verify that every item_id in Claude's response resolves to a real item in the database BEFORE returning to frontend
- [ ] **Error states:** Often missing fallback UI -- verify what the user sees when Claude API is down, when OpenDota is down, when a hero has no matchup data
- [ ] **Re-evaluate flow:** Often missing "locked items" persistence -- verify that items marked as purchased survive a re-evaluation and don't reappear as recommendations
- [ ] **Mobile viewport:** Often missing scroll handling -- verify the sidebar doesn't overflow on 768px-wide screens, even though mobile isn't a V1 priority
- [ ] **Favicon:** Often forgotten entirely -- verify favicon.ico AND favicon.svg exist, are themed (prism/refraction), and render in browser tabs (per CLAUDE.md requirements)
- [ ] **Docker health checks:** Often missing -- verify both containers have health check endpoints and Docker restart policies actually work on Unraid
- [ ] **Empty state:** Often missing -- verify what the user sees before selecting any hero (should be an inviting prompt, not a blank panel)
- [ ] **Patch version display:** Often missing -- verify the app shows which Dota 2 patch the data corresponds to, so users know if data is current

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| LLM hallucinating items | LOW | Add item_id validation layer. Filter invalid items from response. Return partial results + rules-engine fallback for filtered items. Can be added without schema changes. |
| Post-patch stale data | MEDIUM | Add `patch_version` column to matchup_data table. Write a migration script. Implement a data refresh triggered by patch detection. Requires data pipeline work but no architecture change. |
| Generic recommendations | MEDIUM | Rewrite system prompt with few-shot examples. Enrich context builder with opponent ability data. Add post-processing validation. Iterative prompt engineering -- budget 2-3 days. |
| Claude API latency | LOW | Add timeout middleware to FastAPI. Implement rules-engine fallback. These are additive changes that don't require refactoring existing code. |
| OpenDota rate limit exhaustion | MEDIUM | Redesign seeding to be lazy/on-demand. Add request queue with rate limiting. Requires refactoring the data client but not the API or frontend. |
| SQLite locking on Unraid | HIGH | If WAL mode doesn't work on the host filesystem, must either change the volume mount configuration (cache drive), switch to PostgreSQL (Docker container), or use an in-memory write buffer. The PostgreSQL switch is the nuclear option but solves it permanently. |
| Rigid schema limiting recommendations | HIGH | Schema change requires coordinated updates: backend response model, Claude prompt, frontend rendering. Must be done carefully to avoid breaking the existing flow. Design the schema flexibly from the start to avoid this. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| LLM hallucinating items | Phase 3 | Write a test that sends 20 diverse matchups to Claude and validates every item_id in responses against the items table. Zero invalid IDs = pass. |
| Post-patch data staleness | Phase 1 (model) + Phase 6 (pipeline) | Check that matchup_data table has a `patch_version` column. Run data refresh script after a simulated patch and verify old data is flagged/replaced. |
| Generic recommendations | Phase 3 | Review 10 recommendation outputs manually. Every reasoning field must mention at least one enemy hero name and one specific ability. |
| Claude API latency | Phase 3 + Phase 5 | Add a test that simulates a 15-second Claude API delay. Verify the endpoint returns rules-only results within 10 seconds. |
| OpenDota/Stratz rate limits | Phase 1 | Run the full seeding script against real APIs. Monitor for 429 responses. Verify seeding completes without errors. |
| SQLite locking on Unraid | Phase 1 | Deploy to actual Unraid with Docker Compose. Run concurrent read+write operations (recommendations while data refresh runs). Check for "database is locked" errors in logs. |
| Rigid recommendation schema | Phase 3 | Test schema with: a Pos 5 support (few items), a Pos 1 carry rushing an item (skip early phase), a hero needing conditional branches. All three should produce sensible output without filler. |

## Sources

- [OpenDota API Documentation](https://docs.opendota.com/) - Rate limits: 50K calls/month free, 60/min
- [OpenDota API Changes Blog Post](https://blog.opendota.com/2018/04/17/changes-to-the-api/) - Rate limit policy history
- [Stratz API Rate Limits](https://stratz.com/knowledge-base/API/Are%20there%20any%20rate%20limits) - Default: 2K/hour, Individual: 4K/hour, 20/sec
- [Stratz API Knowledge Base](https://stratz.com/knowledge-base/API) - GraphQL API structure and authentication
- [Claude Structured Outputs Documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) - JSON schema limitations, model support, migration notes
- [Claude Prefill Deprecation](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prefill-claudes-response) - Prefilling incompatible with newer models
- [Claude Prompting Best Practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) - Few-shot examples, XML tags, structure
- [LLM Hallucination Research - Named Entity Sensitivity](https://arxiv.org/pdf/2509.22202) - 26% hallucination rate with one-character name similarity
- [Dota 2 Patch 7.39 Spring Forward](https://www.dota2.com/springforward2025) - Neutral item rotation, Facet reworks
- [Dota 2 Patch 7.40 Changes](https://blix.gg/news/dota-2/dota-2-patch-7-40-overview/) - Hero reworks, item changes
- [SQLite Concurrent Writes and Database Locking](https://tenthousandmeters.com/blog/sqlite-concurrent-writes-and-database-is-locked-errors/) - WAL mode limitations, Docker filesystem issues
- [SQLite WAL Mode Documentation](https://sqlite.org/wal.html) - Network filesystem limitations, checkpoint starvation
- [Jellyfin Docker SQLite Issues on Unraid](https://forums.unraid.net/topic/190813-jellyfin-docker-sqlite-unable-to-open-database-file-aka-help-with-general-file-permission-in-unraid/) - Real-world Unraid SQLite permission problems
- [Docker Compose Named Volume Permissions](https://www.codegenes.net/blog/docker-compose-and-named-volume-permission-denied/) - PUID/PGID configuration for Docker
- [Dota 2 Community Discussion on Item Guides](https://steamcommunity.com/app/570/discussions/0/4628107223585858742/?ctp=3) - Community frustration with generic recommendations
- [Dota Plus Suggestions Criticism](https://steamcommunity.com/app/570/discussions/0/1697169163407568828/) - Community feedback on Valve's recommendation system
- [Sequential Item Recommendation in Dota 2 (arXiv)](https://arxiv.org/abs/2201.08724) - Academic research on item recommendation challenges
- [FastAPI Timeout Middleware](https://www.compilenrun.com/docs/framework/fastapi/fastapi-middleware/fastapi-timeout-middleware/) - Request-level timeout patterns
- [FastAPI Best Practices (async)](https://github.com/zhanymkanov/fastapi-best-practices) - Async route patterns, blocking call prevention

---
*Pitfalls research for: Dota 2 adaptive item advisor with hybrid rules+LLM engine*
*Researched: 2026-03-21*

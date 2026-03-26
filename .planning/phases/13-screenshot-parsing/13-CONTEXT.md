# Phase 13: Screenshot Parsing - Context

**Gathered:** 2026-03-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 13 delivers scoreboard screenshot parsing: the player pastes (Ctrl+V) or uploads a Dota 2 scoreboard screenshot, the backend parses it via Claude Vision to extract enemy heroes, item builds, KDA, and levels, a confirmation modal lets the user review and edit results before applying, and confirmed data feeds into the recommendation system (enemy items, opponent heroes, game state). After this phase, the player can capture full enemy team state from a single screenshot instead of manually entering items.

</domain>

<decisions>
## Implementation Decisions

### Input Method & UX
- **D-01:** Primary input: global Ctrl+V paste listener on the page. User takes screenshot (Win+Shift+S or PrtScn), alt-tabs to Prismlab, pastes anywhere. Only triggers when clipboard contains an image.
- **D-02:** Fallback: upload button with drag-and-drop support for file browse.
- **D-03:** Pasting an image anywhere on the page auto-opens the screenshot parser modal with the image loaded and parsing initiated automatically. No extra click needed.
- **D-04:** "Parse Screenshot" button in the sidebar near the Enemy Items Spotted section opens the modal manually (for upload/drag-drop flow).

### Confirmation UI
- **D-05:** Modal overlay displays: screenshot thumbnail at top, parsed results below as hero rows. Each row shows hero portrait + name + KDA + level on the left, detected item icons on the right.
- **D-06:** Item icons use Steam CDN images (consistent with rest of app).
- **D-07:** Full edit capability: user can both remove incorrect items (click to X/strikethrough) AND add missing items via a search/picker. Enables correction of Vision errors before applying.
- **D-08:** "Apply to Build" and "Cancel" buttons at the bottom. Apply closes modal and triggers data integration + recommendation refresh.

### Vision Parsing Scope
- **D-09:** Extract all four data categories: enemy heroes (names), enemy items (6 inventory slots per hero), KDA (kills/deaths/assists per hero), and hero levels.
- **D-10:** Backend returns per-item confidence level (high/medium/low). Frontend flags low-confidence items with a visual indicator (orange border, question mark icon). User decides whether to keep or remove in confirmation UI.
- **D-11:** Use the same Claude model as the recommendation engine (currently Haiku 4.5). Single Anthropic client, single API key. Can upgrade to Sonnet for vision later if accuracy is insufficient.
- **D-12:** New backend endpoint (e.g., `POST /api/parse-screenshot`) accepts image data (base64 or multipart), calls Claude Vision, returns structured JSON with parsed results.

### Data Integration
- **D-13:** Applying parsed results replaces `enemy_items_spotted` in gameStore with the full set of parsed enemy items (all items from all 5 enemies). The manual EnemyItemTracker grid auto-highlights items present in parsed data.
- **D-14:** Parsed enemy heroes auto-fill all 5 opponent slots in the draft section of gameStore. Overwrites existing manual entries (same GSI-wins pattern from Phase 11).
- **D-15:** Parsed KDA and levels feed into game state assessment — stored in gameStore or passed to the recommendation request for context.
- **D-16:** Applying parsed results immediately triggers a recommendation refresh (bypasses the Phase 12 auto-refresh cooldown since it's user-initiated). Toast: "Enemy builds applied — updating recommendations."
- **D-17:** After applying, user can still manually toggle items in the EnemyItemTracker or change opponents in the draft. Manual changes persist until next screenshot parse.

### Claude's Discretion
- Vision prompt engineering (how to instruct Claude to extract scoreboard data reliably)
- Image preprocessing (resize, crop, format before sending to Vision API)
- Item name matching strategy (Vision returns display names → map to internal_name in DB)
- Hero name matching strategy (Vision returns localized names → match to hero DB)
- Error handling for unparseable screenshots (wrong image, partial scoreboard, etc.)
- Confidence scoring algorithm (how Vision output is translated to high/medium/low)
- File size limits and image format handling
- Backend endpoint design (base64 vs multipart upload)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — SCREEN-01, SCREEN-02, SCREEN-03, SCREEN-04 requirement definitions
- `.planning/ROADMAP.md` — Phase 13 success criteria (5 criteria that must be TRUE)

### Upstream Phase Context
- `.planning/phases/11-live-game-dashboard/11-CONTEXT.md` — GSI-wins pattern for overwriting manual inputs (D-03/D-04)
- `.planning/phases/12-auto-refresh-lane-detection/12-CONTEXT.md` — Auto-refresh cooldown system (D-07/D-09), toast notifications (D-15/D-16)

### Existing Code — Frontend
- `prismlab/frontend/src/components/game/EnemyItemTracker.tsx` — Manual enemy item toggle grid using ENEMY_COUNTER_ITEMS. Phase 13 auto-highlights items from parsed data.
- `prismlab/frontend/src/stores/gameStore.ts` — `enemyItemsSpotted` array, `toggleEnemyItem` action, `opponents` array, `setOpponent` action. Phase 13 writes parsed data here.
- `prismlab/frontend/src/hooks/useRecommendation.ts` — `recommend()` function that reads gameStore and calls API. Phase 13 triggers this after applying parsed results.
- `prismlab/frontend/src/utils/imageUrls.ts` — `itemImageUrl()` helper for Steam CDN item images. Reuse for parsed item display.

### Existing Code — Backend
- `prismlab/backend/engine/llm.py` — LLMEngine with AsyncAnthropic client. Phase 13 adds a Vision-capable method or new class using the same client.
- `prismlab/backend/engine/schemas.py` — Pydantic models for request/response. Phase 13 adds new schemas for screenshot parse request/response.
- `prismlab/backend/data/models.py` — Hero model (localized_name for matching), Item model (internal_name for matching). Used to validate Vision output.
- `prismlab/backend/main.py` — FastAPI app. New `/api/parse-screenshot` endpoint goes here.
- `prismlab/backend/config.py` — Settings. Same ANTHROPIC_API_KEY used for Vision calls.

### Project Spec
- `PRISMLAB_BLUEPRINT.md` — Original spec with data models, API patterns, Steam CDN URL formats

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `LLMEngine` (llm.py) — AsyncAnthropic client already initialized. Vision calls can use the same client instance with `messages.create()` and image content blocks.
- `EnemyItemTracker.tsx` — Grid of counter items with toggle. After parse, items in the tracker grid that match parsed data should auto-highlight.
- `itemImageUrl()` — Steam CDN URL builder. Reuse for item icons in the confirmation modal.
- `gameStore.ts` — Already has `opponents` array (5 slots), `enemyItemsSpotted` array, and `setOpponent`/`toggleEnemyItem` actions. Phase 13 writes parsed data through these existing actions.
- `ENEMY_COUNTER_ITEMS` constant — Curated list of counter items (BKB, Blink, MKB, etc.). Parsed items can be cross-referenced against this for the tracker grid.

### Established Patterns
- Pydantic schemas for all API request/response contracts
- AsyncAnthropic client with timeout and error handling
- Zustand stores with action methods
- Modal pattern: Settings slide-over already exists (from Phase 10). Screenshot parser modal is similar but centered overlay.

### Integration Points
- New `POST /api/parse-screenshot` endpoint in `main.py`
- New Pydantic schemas for parse request (image data) and response (parsed heroes/items/KDA)
- New frontend component: `ScreenshotParser.tsx` modal
- Global paste event listener (likely in App.tsx or a dedicated hook)
- `gameStore` actions for bulk-setting opponents and enemy items from parsed data

</code_context>

<specifics>
## Specific Ideas

- User chose full edit capability (add + remove) in the confirmation modal — they want to correct Vision errors before applying, not just remove items
- User wants ALL four data categories extracted (heroes, items, KDA, levels) — maximum information from each screenshot
- Auto-open modal on paste is critical for the fast path during live gameplay (alt-tab, paste, review, apply)
- Parsed enemy heroes should auto-fill opponent draft slots — gives the recommendation engine full enemy team composition context

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 13-screenshot-parsing*
*Context gathered: 2026-03-26*

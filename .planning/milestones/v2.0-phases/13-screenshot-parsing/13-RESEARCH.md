# Phase 13: Screenshot Parsing - Research

**Researched:** 2026-03-26
**Domain:** Claude Vision API, image processing, multimodal AI, FastAPI file uploads, React clipboard/paste handling
**Confidence:** HIGH

## Summary

Phase 13 adds scoreboard screenshot parsing: the user pastes or uploads a Dota 2 scoreboard screenshot, the backend sends it to Claude Vision (Haiku 4.5) to extract enemy heroes, items, KDA, and levels, and a confirmation modal lets the user review/edit before applying the parsed data to the recommendation engine.

The core technical challenge is well-supported: Claude Haiku 4.5 has full vision/multimodal support, the existing `LLMEngine` uses the same `AsyncAnthropic` client that supports image content blocks natively, and the Anthropic Python SDK (v0.86.0 installed) has the `messages.create()` API with image blocks built in. No new SDK is needed. The frontend needs a global paste listener, a new modal component, and new gameStore actions for bulk-setting parsed data.

The key risk is accuracy of small item icon recognition (~30x30px icons on a 1920x1080 scoreboard). This was already flagged in STATE.md as MEDIUM confidence. The mitigation is the confirmation UI with per-item confidence levels and full edit capability, plus careful prompt engineering that gives Claude the complete list of valid item names to match against.

**Primary recommendation:** Use base64 image upload via a new `POST /api/parse-screenshot` endpoint. Frontend sends base64-encoded image data as JSON (not multipart). Backend passes it directly to Claude Vision with a structured extraction prompt. Return structured JSON with per-hero/per-item confidence scores. No `python-multipart` dependency needed if using base64 JSON body.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Primary input: global Ctrl+V paste listener on the page. User takes screenshot (Win+Shift+S or PrtScn), alt-tabs to Prismlab, pastes anywhere. Only triggers when clipboard contains an image.
- **D-02:** Fallback: upload button with drag-and-drop support for file browse.
- **D-03:** Pasting an image anywhere on the page auto-opens the screenshot parser modal with the image loaded and parsing initiated automatically. No extra click needed.
- **D-04:** "Parse Screenshot" button in the sidebar near the Enemy Items Spotted section opens the modal manually (for upload/drag-drop flow).
- **D-05:** Modal overlay displays: screenshot thumbnail at top, parsed results below as hero rows. Each row shows hero portrait + name + KDA + level on the left, detected item icons on the right.
- **D-06:** Item icons use Steam CDN images (consistent with rest of app).
- **D-07:** Full edit capability: user can both remove incorrect items (click to X/strikethrough) AND add missing items via a search/picker. Enables correction of Vision errors before applying.
- **D-08:** "Apply to Build" and "Cancel" buttons at the bottom. Apply closes modal and triggers data integration + recommendation refresh.
- **D-09:** Extract all four data categories: enemy heroes (names), enemy items (6 inventory slots per hero), KDA (kills/deaths/assists per hero), and hero levels.
- **D-10:** Backend returns per-item confidence level (high/medium/low). Frontend flags low-confidence items with a visual indicator (orange border, question mark icon). User decides whether to keep or remove in confirmation UI.
- **D-11:** Use the same Claude model as the recommendation engine (currently Haiku 4.5). Single Anthropic client, single API key. Can upgrade to Sonnet for vision later if accuracy is insufficient.
- **D-12:** New backend endpoint (e.g., `POST /api/parse-screenshot`) accepts image data (base64 or multipart), calls Claude Vision, returns structured JSON with parsed results.
- **D-13:** Applying parsed results replaces `enemy_items_spotted` in gameStore with the full set of parsed enemy items (all items from all 5 enemies). The manual EnemyItemTracker grid auto-highlights items present in parsed data.
- **D-14:** Parsed enemy heroes auto-fill all 5 opponent slots in the draft section of gameStore. Overwrites existing manual entries (same GSI-wins pattern from Phase 11).
- **D-15:** Parsed KDA and levels feed into game state assessment -- stored in gameStore or passed to the recommendation request for context.
- **D-16:** Applying parsed results immediately triggers a recommendation refresh (bypasses the Phase 12 auto-refresh cooldown since it's user-initiated). Toast: "Enemy builds applied -- updating recommendations."
- **D-17:** After applying, user can still manually toggle items in the EnemyItemTracker or change opponents in the draft. Manual changes persist until next screenshot parse.

### Claude's Discretion
- Vision prompt engineering (how to instruct Claude to extract scoreboard data reliably)
- Image preprocessing (resize, crop, format before sending to Vision API)
- Item name matching strategy (Vision returns display names -> map to internal_name in DB)
- Hero name matching strategy (Vision returns localized names -> match to hero DB)
- Error handling for unparseable screenshots (wrong image, partial scoreboard, etc.)
- Confidence scoring algorithm (how Vision output is translated to high/medium/low)
- File size limits and image format handling
- Backend endpoint design (base64 vs multipart upload)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCREEN-01 | User can paste/upload a scoreboard screenshot and backend parses it via Claude Vision | Claude Vision API with base64 image blocks in messages.create(); global paste listener via ClipboardEvent; new POST /api/parse-screenshot endpoint |
| SCREEN-02 | Parsed results show enemy item builds (all 5 enemies) with confirmation UI before applying | Structured JSON response schema with per-hero item arrays; React modal component with hero rows and Steam CDN item icons |
| SCREEN-03 | Enemy hero identification extracted from scoreboard screenshot | Vision prompt instructs Claude to identify heroes by portrait/name; fuzzy match against Hero.localized_name in DB |
| SCREEN-04 | Kill/death scores extracted from scoreboard screenshot for game state assessment | Vision prompt extracts K/D/A numbers per hero row; returned in structured JSON response alongside items |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Hero/item images from Steam CDN** -- item icons in confirmation modal must use `itemImageUrl()` helper, hero portraits use `heroImageUrl()`
- **Structured JSON output from Claude API** -- parse and validate before returning to frontend (Pydantic schemas)
- **Dark theme** with spectral cyan (#00d4ff) primary accent, Radiant teal (#6aff97), Dire red (#ff5555)
- **TypeScript strict mode, functional components, hooks** on frontend
- **Type hints throughout, async endpoints, Pydantic models** on backend
- **Docker Compose deployment** -- nginx proxy needs body size config for image uploads

## Standard Stack

### Core (Already Installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic (Python SDK) | 0.86.0 | Claude Vision API calls with image content blocks | Already installed, same client as recommendation engine |
| FastAPI | 0.135.1 | New `/api/parse-screenshot` endpoint | Already installed, async endpoint |
| Pydantic | 2.12.5 | Request/response schemas for screenshot parsing | Already installed, project pattern |
| React | 19.2.4 | Modal component, paste listener | Already installed |
| Zustand | (installed) | gameStore for applying parsed data | Already installed, project pattern |

### Supporting (New Dependencies)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | 0.0.22 | Required by FastAPI for `UploadFile` if using multipart | ONLY needed if using multipart upload; NOT needed if using base64 JSON body |

### Decision: base64 JSON Body vs Multipart Upload

**Use base64 JSON body.** Rationale:
1. Frontend clipboard API gives base64 data directly from `canvas.toDataURL()` or `FileReader.readAsDataURL()`
2. No new dependency (`python-multipart` not needed)
3. Simpler endpoint -- standard Pydantic model, not `UploadFile`
4. Consistent with how Anthropic API itself accepts images (base64 in content blocks)
5. Screenshot PNGs from 1920x1080 are typically 0.5-2MB, well under the 5MB Anthropic limit

**Installation:** No new packages required. All dependencies are already installed.

## Architecture Patterns

### Recommended Project Structure
```
prismlab/backend/
  engine/
    llm.py              # Add parse_screenshot() method to LLMEngine
    schemas.py          # Add ScreenshotParseRequest, ScreenshotParseResponse
    prompts/
      vision_prompt.py  # NEW: Vision system prompt for scoreboard parsing
  api/routes/
    screenshot.py       # NEW: POST /api/parse-screenshot route
  main.py               # Register screenshot router

prismlab/frontend/src/
  components/
    screenshot/
      ScreenshotParser.tsx    # NEW: Modal overlay component
      ParsedHeroRow.tsx       # NEW: Single hero row in results
      ItemEditPicker.tsx      # NEW: Add-item search/picker for editing
  hooks/
    useScreenshotPaste.ts     # NEW: Global paste listener hook
  stores/
    screenshotStore.ts        # NEW: Screenshot parsing state (modal open, parsed data, loading)
```

### Pattern 1: Base64 Image to Claude Vision API
**What:** Send base64-encoded scoreboard image as a content block in Claude messages.create()
**When to use:** Every screenshot parse request
**Example:**
```python
# Source: https://platform.claude.com/docs/en/build-with-claude/vision
async def parse_screenshot(self, image_base64: str, media_type: str) -> dict | None:
    response = await self.client.with_options(
        timeout=30.0,
        max_retries=0,
    ).messages.create(
        model=self.MODEL,
        max_tokens=4096,
        temperature=0.1,  # Lower temp for structured extraction
        system=VISION_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64,
                    },
                },
                {"type": "text", "text": VISION_USER_PROMPT},
            ],
        }],
    )
```

### Pattern 2: Global Paste Listener
**What:** Listen for Ctrl+V with image data in clipboard, auto-open modal
**When to use:** App-level hook, always active
**Example:**
```typescript
// useScreenshotPaste.ts
function useScreenshotPaste(onPaste: (imageData: string, mimeType: string) => void) {
  useEffect(() => {
    const handler = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      for (const item of items) {
        if (item.type.startsWith("image/")) {
          const blob = item.getAsFile();
          if (!blob) continue;
          const reader = new FileReader();
          reader.onload = () => {
            const dataUrl = reader.result as string;
            // dataUrl format: "data:image/png;base64,iVBOR..."
            const [header, base64] = dataUrl.split(",");
            const mimeType = header.match(/data:(.*?);/)?.[1] ?? "image/png";
            onPaste(base64, mimeType);
          };
          reader.readAsDataURL(blob);
          e.preventDefault();
          break;
        }
      }
    };
    document.addEventListener("paste", handler);
    return () => document.removeEventListener("paste", handler);
  }, [onPaste]);
}
```

### Pattern 3: Name Matching Strategy
**What:** Map Claude Vision's extracted names to database records via fuzzy matching
**When to use:** Backend post-processing of Vision output
**Example:**
```python
# Backend: match Vision output to DB records
from difflib import SequenceMatcher

def match_hero_name(vision_name: str, heroes: list[Hero]) -> Hero | None:
    """Match Vision-extracted hero name to DB hero by localized_name."""
    # Try exact match first (case-insensitive)
    lower = vision_name.lower().strip()
    for hero in heroes:
        if hero.localized_name.lower() == lower:
            return hero
    # Fuzzy match fallback
    best_match = None
    best_ratio = 0.0
    for hero in heroes:
        ratio = SequenceMatcher(None, lower, hero.localized_name.lower()).ratio()
        if ratio > best_ratio and ratio > 0.7:
            best_ratio = ratio
            best_match = hero
    return best_match

def match_item_name(vision_name: str, items: list[Item]) -> Item | None:
    """Match Vision-extracted item name to DB item by display name."""
    lower = vision_name.lower().strip()
    for item in items:
        if item.name.lower() == lower:
            return item
    # Fuzzy match fallback
    best_match = None
    best_ratio = 0.0
    for item in items:
        if not item.name:
            continue
        ratio = SequenceMatcher(None, lower, item.name.lower()).ratio()
        if ratio > best_ratio and ratio > 0.7:
            best_ratio = ratio
            best_match = item
    return best_match
```

### Pattern 4: Confidence Scoring
**What:** Assign high/medium/low confidence based on Vision output certainty signals
**When to use:** Backend post-processing
**Approach:**
- **High confidence:** Exact name match to DB + item is commonly seen in Dota 2
- **Medium confidence:** Fuzzy match (ratio 0.85-0.99) or item name has minor differences
- **Low confidence:** Fuzzy match (ratio 0.7-0.84) or Vision explicitly expressed uncertainty
- **Rejected:** Match ratio below 0.7 -- not included in results

The Vision prompt should be engineered to output a confidence field for each item (e.g., "certain", "likely", "uncertain"). Backend translates:
- "certain" + exact DB match = high
- "likely" + any DB match = medium
- "uncertain" or weak DB match = low

### Anti-Patterns to Avoid
- **Multipart upload for simple image data:** Adds `python-multipart` dependency, more complex endpoint signature. Base64 JSON is simpler and sufficient for single-image uploads under 5MB.
- **Storing screenshots on disk/database:** Screenshots are ephemeral -- pass through to Claude API and discard. No storage needed.
- **Prompt without valid name list:** Without anchoring Claude to the actual hero/item name list, it may hallucinate plausible but incorrect Dota names. Always include the valid name set in the prompt.
- **Blocking UI during parse:** Parse can take 5-15 seconds. Show the image immediately and display a loading skeleton for results.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image-to-text extraction | Custom OCR pipeline (Tesseract, etc.) | Claude Vision API | Claude understands Dota context, icons, layout -- not just text. Vision handles the full scoreboard interpretation, not just character recognition. |
| Fuzzy string matching | Levenshtein distance from scratch | `difflib.SequenceMatcher` | Built into Python stdlib, well-tested, handles the hero/item name matching adequately |
| Image resizing | PIL/Pillow manual resize pipeline | Let Anthropic API handle it | API automatically resizes images >1568px. Only pre-resize if targeting latency optimization. |
| Clipboard handling | Manual event.preventDefault chains | ClipboardEvent API + FileReader | Browser-native APIs handle the image extraction cleanly |

**Key insight:** The entire OCR/extraction problem is delegated to Claude Vision. The backend code is mostly prompt engineering + name matching + validation. Do not build image processing pipelines.

## Common Pitfalls

### Pitfall 1: Nginx 1MB Default Body Size
**What goes wrong:** Scoreboard screenshots (1920x1080 PNG) can be 1-3MB raw, and base64 encoding adds ~33% overhead. A 2MB PNG becomes ~2.7MB base64. Nginx's default `client_max_body_size` is 1MB and will reject the request with 413 Entity Too Large.
**Why it happens:** The existing nginx.conf has no `client_max_body_size` directive.
**How to avoid:** Add `client_max_body_size 10m;` to the `/api/` location block in `nginx.conf`.
**Warning signs:** 413 error in browser console on paste.

### Pitfall 2: Anthropic 5MB Image Limit
**What goes wrong:** Claude API rejects images larger than 5MB with an error.
**Why it happens:** Very high-resolution monitors (4K) can produce 5MB+ screenshots.
**How to avoid:** Frontend should resize the image before sending if it exceeds ~4MB. Use canvas to downscale to max 1920px wide. This also reduces token cost.
**Warning signs:** 400 error from Claude API mentioning size limit.

### Pitfall 3: Base64 Data URL Prefix
**What goes wrong:** `FileReader.readAsDataURL()` returns `"data:image/png;base64,iVBOR..."` but Claude API expects raw base64 without the prefix.
**Why it happens:** Common confusion between data URLs and raw base64 strings.
**How to avoid:** Strip the `data:image/...;base64,` prefix before sending to backend. Backend passes only the raw base64 to Claude.
**Warning signs:** Claude API returns error about invalid image data.

### Pitfall 4: Empty Item Slots
**What goes wrong:** Not every hero has 6 items. Vision might hallucinate items for empty slots, or return "Empty" / "None" entries.
**Why it happens:** Scoreboard shows empty gray slots that Vision might misinterpret.
**How to avoid:** Prompt should explicitly instruct: "If an inventory slot is empty, do not include it. Only list items the hero actually has." Backend filters out any entries matching "empty", "none", or similar.
**Warning signs:** Parsed results show 6 items for a hero who clearly has fewer.

### Pitfall 5: Scoreboard vs Post-Game Screen
**What goes wrong:** User pastes a post-game stats screen instead of the in-game scoreboard. Layout is different.
**Why it happens:** Both show heroes and items but in different formats.
**How to avoid:** Vision prompt should handle both layouts gracefully. Include instructions for both common screen formats. If the image doesn't appear to be a Dota 2 scoreboard at all, return an error message.
**Warning signs:** All confidence scores are low, or Claude returns an error/refusal.

### Pitfall 6: Item Name Mismatches Between Display and Internal Names
**What goes wrong:** Claude returns "Black King Bar" but the `enemyItemsSpotted` array uses internal names like "bkb". The `ENEMY_COUNTER_ITEMS` in constants.ts uses `name: "bkb"` (internal) and `label: "Black King Bar"` (display).
**Why it happens:** The Item model has both `name` (display: "Black King Bar") and `internal_name` (slug: "bkb"). Vision outputs display names.
**How to avoid:** Backend resolves display names to `internal_name` during matching. The response to frontend includes `internal_name` for each item, which is what `enemyItemsSpotted` and `itemImageUrl()` expect.
**Warning signs:** Items don't highlight in EnemyItemTracker after applying, or Steam CDN URLs 404.

### Pitfall 7: Stale Closure in Paste Handler
**What goes wrong:** Paste listener captures stale callback references and doesn't trigger modal correctly.
**Why it happens:** useEffect dependency array missing the callback.
**How to avoid:** Use `useCallback` for the paste handler callback and include it in the useEffect dependency array. Or use a ref for the callback.
**Warning signs:** First paste works, subsequent pastes don't open modal or use stale data.

## Code Examples

### Backend: Vision Prompt Engineering
```python
# Source: Anthropic Vision docs + Dota 2 domain knowledge
VISION_SYSTEM_PROMPT = """You are a Dota 2 scoreboard parser. You analyze screenshots of the
Dota 2 in-game scoreboard or post-game screen and extract structured data about enemy heroes.

You MUST return valid JSON matching the required schema. Do not include any text outside the JSON.

For each enemy hero visible in the scoreboard, extract:
1. Hero name (use the official English name, e.g., "Anti-Mage", "Crystal Maiden")
2. Items in their inventory (only items they actually have -- skip empty slots)
3. Kills / Deaths / Assists
4. Hero level

For each item, also provide your confidence: "certain", "likely", or "uncertain".
- "certain": You can clearly read or identify the item
- "likely": You're fairly confident but the icon is small or partially obscured
- "uncertain": You're guessing based on partial visual information

Valid hero names: [full list injected at runtime from DB]
Valid item names: [full list injected at runtime from DB]

If the image is not a Dota 2 scoreboard, respond with:
{"error": "not_a_scoreboard", "message": "..."}
"""
```

### Backend: Pydantic Response Schemas
```python
from pydantic import BaseModel, Field

class ParsedItem(BaseModel):
    """Single item parsed from scoreboard."""
    display_name: str
    internal_name: str  # Resolved from DB
    confidence: str  # "high" | "medium" | "low"

class ParsedHero(BaseModel):
    """Single enemy hero parsed from scoreboard."""
    hero_name: str  # Localized display name
    hero_id: int | None = None  # Resolved from DB, None if unmatched
    internal_name: str | None = None  # For hero portrait URL
    items: list[ParsedItem] = Field(default_factory=list)
    kills: int | None = None
    deaths: int | None = None
    assists: int | None = None
    level: int | None = None

class ScreenshotParseRequest(BaseModel):
    """POST /api/parse-screenshot request."""
    image_base64: str  # Raw base64 (no data URL prefix)
    media_type: str = "image/png"  # "image/png" | "image/jpeg" | "image/webp"

class ScreenshotParseResponse(BaseModel):
    """POST /api/parse-screenshot response."""
    heroes: list[ParsedHero]
    error: str | None = None  # "not_a_scoreboard", "parse_failed", etc.
    message: str | None = None  # Human-readable error context
    latency_ms: int | None = None
```

### Frontend: Screenshot Store
```typescript
// screenshotStore.ts
interface ParsedItem {
  display_name: string;
  internal_name: string;
  confidence: "high" | "medium" | "low";
}

interface ParsedHero {
  hero_name: string;
  hero_id: number | null;
  internal_name: string | null;
  items: ParsedItem[];
  kills: number | null;
  deaths: number | null;
  assists: number | null;
  level: number | null;
}

interface ScreenshotStore {
  isOpen: boolean;
  imageData: string | null;  // base64
  mimeType: string | null;
  parsedHeroes: ParsedHero[];
  isLoading: boolean;
  error: string | null;

  openModal: (imageData: string, mimeType: string) => void;
  closeModal: () => void;
  setParsedHeroes: (heroes: ParsedHero[]) => void;
  updateHeroItem: (heroIdx: number, itemIdx: number, item: ParsedItem | null) => void;
  addHeroItem: (heroIdx: number, item: ParsedItem) => void;
  setLoading: (v: boolean) => void;
  setError: (msg: string | null) => void;
}
```

### Frontend: API Client Addition
```typescript
// Add to api/client.ts
export interface ScreenshotParseRequest {
  image_base64: string;
  media_type: string;
}

export interface ScreenshotParseResponse {
  heroes: ParsedHero[];
  error: string | null;
  message: string | null;
  latency_ms: number | null;
}

// In api object:
parseScreenshot: (req: ScreenshotParseRequest) =>
  postJson<ScreenshotParseRequest, ScreenshotParseResponse>("/parse-screenshot", req),
```

### Frontend: Apply Parsed Data to GameStore
```typescript
// When user clicks "Apply to Build":
const applyParsedData = (parsedHeroes: ParsedHero[], heroes: Hero[]) => {
  const gameStore = useGameStore.getState();

  // 1. Set opponents (D-14)
  parsedHeroes.forEach((parsed, idx) => {
    if (idx >= 5) return;
    const matchedHero = heroes.find(h => h.id === parsed.hero_id);
    if (matchedHero) {
      gameStore.setOpponent(idx, matchedHero);
    }
  });

  // 2. Set enemy items spotted (D-13)
  const allItems = parsedHeroes.flatMap(h => h.items.map(i => i.internal_name));
  const uniqueItems = [...new Set(allItems)];
  // Need a new action: setEnemyItemsSpotted(items: string[])
  gameStore.setEnemyItemsSpotted(uniqueItems);

  // 3. Show toast (D-16)
  useRefreshStore.getState().showToast("Enemy builds applied -- updating recommendations.");

  // 4. Trigger recommendation refresh bypassing cooldown (D-16)
  // Call recommend() directly (not through auto-refresh)
};
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| OCR + template matching | Multimodal LLM Vision | 2024-2025 | No need for Tesseract, OpenCV, or item icon template databases. Claude handles the full pipeline. |
| Multipart file upload | Base64 JSON body | Current best practice for single images | Simpler API, no extra dependencies, consistent with Anthropic API pattern |
| Image content `type: "image"` with `source.type: "base64"` | Same -- this is the current API | Since Claude 3 launch (2024) | Stable API, well-documented |

**Deprecated/outdated:**
- The Anthropic `beta.files` API exists but is overkill for single-use screenshot parsing (designed for repeated references in multi-turn conversations)

## Open Questions

1. **Vision accuracy for small item icons**
   - What we know: Item icons on scoreboard are approximately 30x30px at 1080p resolution. Claude Vision can struggle with very small images under 200px (per official docs). However, the icons appear alongside contextual information (hero portrait, hero name, KDA) that aids identification.
   - What's unclear: Real-world accuracy rate for Dota 2 item identification at scoreboard resolution. STATE.md flagged this as MEDIUM confidence.
   - Recommendation: Build it with Haiku 4.5, measure accuracy in practice. The confirmation UI with per-item confidence is the primary mitigation. If accuracy is poor, D-11 allows upgrading to Sonnet.

2. **Prompt token cost per parse**
   - What we know: A 1920x1080 image is approximately 1,600 tokens (~$0.001 per image with Haiku). The valid hero/item name list will add ~500-1000 tokens to the system prompt.
   - What's unclear: Exact output token count for a full 5-hero extraction.
   - Recommendation: Acceptable cost. Each parse is user-initiated, not automated.

3. **Dota 2 scoreboard layout variations**
   - What we know: The scoreboard layout can differ between in-game (Tab key) and post-game analysis screen. Both show heroes, items, and KDA but in different arrangements.
   - What's unclear: Whether recent Dota 2 patches have changed the scoreboard layout.
   - Recommendation: Design the prompt to handle both layouts. Claude Vision is flexible enough to parse tabular data in different arrangements.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (Backend) | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Framework (Frontend) | vitest 4.1.0 + @testing-library/react 16.3.2 |
| Config file (Backend) | pytest.ini or pyproject.toml (implicit) |
| Config file (Frontend) | vitest config in vite.config.ts |
| Quick run (Backend) | `cd prismlab/backend && python -m pytest tests/test_screenshot.py -x` |
| Quick run (Frontend) | `cd prismlab/frontend && npx vitest run src/stores/screenshotStore.test.ts` |
| Full suite (Backend) | `cd prismlab/backend && python -m pytest` |
| Full suite (Frontend) | `cd prismlab/frontend && npx vitest run` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCREEN-01 | Backend parses screenshot via Claude Vision | unit (mocked API) | `pytest tests/test_screenshot.py::test_parse_screenshot_success -x` | Wave 0 |
| SCREEN-01 | Frontend paste listener detects image | unit | `npx vitest run src/hooks/useScreenshotPaste.test.ts` | Wave 0 |
| SCREEN-02 | Parsed results rendered as hero rows | unit | `npx vitest run src/stores/screenshotStore.test.ts` | Wave 0 |
| SCREEN-03 | Hero name matched to DB record | unit | `pytest tests/test_screenshot.py::test_hero_name_matching -x` | Wave 0 |
| SCREEN-04 | KDA extracted in parse response | unit (mocked API) | `pytest tests/test_screenshot.py::test_kda_extraction -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** Quick run for affected test files
- **Per wave merge:** Full backend + frontend suite
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `prismlab/backend/tests/test_screenshot.py` -- covers SCREEN-01, SCREEN-03, SCREEN-04 (mocked Claude Vision)
- [ ] `prismlab/frontend/src/hooks/useScreenshotPaste.test.ts` -- covers SCREEN-01 paste behavior
- [ ] `prismlab/frontend/src/stores/screenshotStore.test.ts` -- covers SCREEN-02 state management

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| anthropic Python SDK | Vision API calls | Yes | 0.86.0 | -- |
| FastAPI | New endpoint | Yes | 0.135.1 | -- |
| Pydantic | Request/response schemas | Yes | 2.12.5 | -- |
| difflib (stdlib) | Fuzzy name matching | Yes | stdlib | -- |
| React | Modal component | Yes | 19.2.4 | -- |
| Zustand | Screenshot store | Yes | installed | -- |
| Nginx | Proxy with body size config | Yes | Docker image | -- |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** None

All required dependencies are already installed. No new packages needed (base64 JSON body avoids `python-multipart`).

## Sources

### Primary (HIGH confidence)
- [Anthropic Vision Docs](https://platform.claude.com/docs/en/build-with-claude/vision) -- Full Vision API reference, base64 image blocks, size limits (5MB per image, 8000px max dimension), supported formats (JPEG, PNG, GIF, WebP), token cost formula (width*height/750)
- Installed `anthropic==0.86.0` Python SDK -- verified supports image content blocks in `messages.create()`
- Existing `prismlab/backend/engine/llm.py` -- LLMEngine pattern with AsyncAnthropic client, error handling, JSON parsing

### Secondary (MEDIUM confidence)
- [Anthropic Claude Haiku 4.5 Capabilities](https://www.datastudios.org/post/anthropic-claude-haiku-4-5-capabilities-speed-context-size-coding-power-and-multimodal-use-in-2) -- Confirms Haiku 4.5 has full multimodal/vision support, 200k context, MMMU benchmark 73.2%
- [Dota 2 HUD/Scoreboard](https://liquipedia.net/dota2/Head-up_Display) -- Scoreboard shows K/D/A, items, levels; enemy info limited to last-seen state
- [FastAPI File Upload](https://fastapi.tiangolo.com/tutorial/request-forms-and-files/) -- UploadFile requires python-multipart; base64 JSON body is simpler alternative
- [Nginx client_max_body_size](https://nginx.org/en/docs/http/ngx_http_core_module.html) -- Default 1MB, must increase for image uploads

### Tertiary (LOW confidence)
- Vision accuracy for small Dota 2 item icons (~30x30px) -- flagged in STATE.md as MEDIUM confidence, needs real-world validation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - All libraries already installed, Vision API well-documented
- Architecture: HIGH - Clear patterns from existing LLMEngine, clipboard API is standard browser API
- Pitfalls: HIGH - Nginx body size, base64 prefix, 5MB limit are well-documented issues
- Vision accuracy: MEDIUM - Small icon recognition is the key uncertainty, mitigated by confirmation UI

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable -- Anthropic Vision API is GA, no breaking changes expected)

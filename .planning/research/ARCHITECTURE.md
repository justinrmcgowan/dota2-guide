# Architecture Patterns

**Domain:** Dota 2 adaptive item advisor (hybrid rules + LLM recommendation engine)
**Researched:** 2026-03-21

## Recommended Architecture

Prismlab follows a **layered hybrid architecture** with clear separation between data ingestion, recommendation logic, and presentation. The system uses a two-container Docker Compose deployment: a FastAPI backend that owns all data and recommendation logic, and a React frontend that manages progressive game state and renders item timelines.

The defining architectural characteristic is the **hybrid recommendation engine**: a fast, deterministic rules layer handles obvious item decisions (Magic Stick vs. spell-spammers, Quelling Blade for melee carries), while the Claude API provides nuanced reasoning that references specific hero abilities, matchup dynamics, and game state. The rules layer fires first and always; the LLM layer enriches and explains. If the LLM fails, rules-only output is the graceful fallback.

```
                          FRONTEND (React + Zustand)
   +------------------------------------------------------------------+
   |                                                                    |
   |  [Draft Inputs]  -->  [Zustand GameStore]  -->  [Item Timeline]    |
   |  (Hero, Role,         (Single source          (PhaseCards,         |
   |   Playstyle,           of truth for all        ItemRecommendation, |
   |   Side, Lane,          game state)             ReasoningTooltip)   |
   |   Opponents)                |                                      |
   |                             v                                      |
   |                    [API Client Layer]                              |
   |                     POST /api/recommend                            |
   +------------------------------------------------------------------+
                                |
                           HTTP (JSON)
                                |
                          BACKEND (FastAPI)
   +------------------------------------------------------------------+
   |                                                                    |
   |  [API Routes]  -->  [Hybrid Recommender]  -->  [Response Builder]  |
   |  (Pydantic            |            |                               |
   |   validation)         v            v                               |
   |               [Rules Engine]  [LLM Engine]                         |
   |               (Deterministic,  (Claude API,                        |
   |                instant)         structured JSON)                   |
   |                    |                |                               |
   |                    v                v                               |
   |              [Context Builder]                                     |
   |              (Assembles hero stats, matchup data,                  |
   |               game state into prompt context)                      |
   |                         |                                          |
   |                         v                                          |
   |              [Data Layer (SQLAlchemy + SQLite)]                    |
   |              (Heroes, Items, MatchupData)                          |
   |                         |                                          |
   |                         v                                          |
   |              [External API Clients]                                |
   |              (OpenDota REST, Stratz GraphQL)                       |
   +------------------------------------------------------------------+
```

### Component Boundaries

| Component | Responsibility | Communicates With | Build Phase |
|-----------|---------------|-------------------|-------------|
| **Zustand GameStore** | Single source of truth for all user input state, recommendations, loading states, purchased item tracking | All frontend components (read/write), API Client (read) | Phase 2 |
| **Draft Input Components** | Collect hero, role, playstyle, side, lane, opponents from user | GameStore (write) | Phase 1-2 |
| **Game State Components** | Collect mid-game updates: lane result, damage profile, enemy items | GameStore (write) | Phase 5 |
| **Item Timeline Components** | Render phased recommendations with reasoning, handle click-to-purchase | GameStore (read/write) | Phase 4 |
| **API Client** | HTTP layer between frontend and backend; serializes GameStore state to request, deserializes response | GameStore (read), FastAPI routes (HTTP) | Phase 3-4 |
| **FastAPI Routes** | Request validation (Pydantic), rate limiting, response formatting | Hybrid Recommender (delegates) | Phase 3 |
| **Hybrid Recommender** | Orchestrates rules layer and LLM layer; merges results; handles fallback | Rules Engine, LLM Engine, Context Builder | Phase 3 |
| **Rules Engine** | Fast, deterministic item recommendations for obvious cases | Data Layer (read hero/item data) | Phase 3 |
| **LLM Engine** | Claude API calls with structured JSON output for nuanced reasoning | Claude API (external), Context Builder (input) | Phase 3 |
| **Context Builder** | Assembles hero stats, matchup data, and game state into a structured prompt context for the LLM | Data Layer (read), Rules Engine output (read) | Phase 3 |
| **Data Layer** | SQLAlchemy models, database sessions, CRUD operations | SQLite database (persistent) | Phase 1 |
| **External API Clients** | Fetch and cache data from OpenDota REST API and Stratz GraphQL API | OpenDota (HTTP), Stratz (GraphQL), Data Layer (write) | Phase 1 |

### Data Flow

#### Primary Flow: Draft to Recommendations

```
1. User selects hero in HeroPicker
   --> GameStore.myHero = selectedHero

2. User selects role, playstyle, side, lane, opponents
   --> GameStore updates incrementally
   --> UI gates: playstyle disabled until role selected

3. User has enough context selected, triggers recommendation
   --> API Client reads GameStore snapshot
   --> POST /api/recommend with serialized game state

4. FastAPI route validates request body via Pydantic model
   --> Passes validated RecommendRequest to Hybrid Recommender

5. Hybrid Recommender orchestrates:
   a. Context Builder queries Data Layer for hero stats,
      item catalog, matchup win rates, common items
   b. Rules Engine evaluates deterministic rules:
      - Magic Stick if lane opponent spams spells
        (Bristleback, Zeus, etc.)
      - Quelling Blade for melee cores in lane
      - Starting item budget allocation
      - Counter-item triggers (BKB vs heavy magic, MKB vs evasion)
   c. Rules output becomes pre-filled recommendations
   d. Context Builder assembles LLM prompt with:
      - Hero stats + abilities summary
      - Matchup data (win rate, games played, common items)
      - Rules engine output (what was already decided and why)
      - Game state (role, playstyle, side, lane, phase)
      - Output JSON schema for structured response
   e. LLM Engine sends to Claude API with structured output
   f. Claude returns structured JSON matching recommendation schema
   g. Recommender merges rules output + LLM output:
      - Rules items keep their reasoning
      - LLM items add nuanced reasoning
      - LLM can override rules items with stronger reasoning
      - Conflicts resolved: rules win for budget constraints,
        LLM wins for reasoning

6. Response validated against Pydantic response model
   --> Returned to frontend as JSON

7. API Client deserializes response
   --> GameStore.recommendations = parsed response
   --> GameStore.isLoading = false

8. Timeline components render from GameStore.recommendations
   --> PhaseCards display items grouped by game phase
   --> ItemRecommendation shows icon + reasoning tooltip
```

#### Re-Evaluation Flow (Mid-Game)

```
1. User updates game state:
   - Marks items as purchased (click in timeline)
     --> GameStore.purchasedItems tracks which items are bought
   - Sets lane result (Won/Even/Lost)
   - Enters damage profile (Physical/Magical/Pure %)
   - Adds spotted enemy items

2. User clicks Re-Evaluate
   --> GameStore.isLoading = true
   --> API Client sends updated POST /api/recommend with:
     - All original draft info
     - current_phase: midgame or lategame
     - purchased_items: list of already-bought item IDs
     - lane_result: won | even | lost
     - damage_profile: { physical: N, magical: N, pure: N }
     - enemy_items_spotted: per-hero item lists

3. Backend Hybrid Recommender runs again with updated context:
   - Rules Engine re-evaluates with new information
     (e.g., losing lane --> defensive item priority increases)
   - Context Builder includes damage profile and enemy items
     in LLM prompt
   - LLM generates new forward-looking recommendations only
   - Past purchased items are locked -- not re-recommended

4. Response replaces only current + future phases
   --> Past phase cards remain in UI but dimmed/collapsed
   --> Current phase card expands with fresh recommendations
```

## Component Deep-Dives

### 1. Zustand GameStore (Frontend State)

**Pattern:** Single store with logical slices via the slices pattern. Use Immer middleware for immutable updates on the complex nested game state. Use devtools middleware in development.

**Confidence:** HIGH (Zustand slices pattern is well-documented and widely used for medium-complexity apps)

```typescript
// Store structure with slices pattern
interface DraftSlice {
  myHero: Hero | null;
  role: 1 | 2 | 3 | 4 | 5 | null;
  playstyle: string | null;
  side: 'radiant' | 'dire' | null;
  lane: 'safe' | 'off' | 'mid' | null;
  laneOpponents: [Hero | null, Hero | null];
  setMyHero: (hero: Hero) => void;
  setRole: (role: number) => void;
  // ... actions per field
}

interface GameStateSlice {
  currentPhase: 'draft' | 'laning' | 'midgame' | 'lategame';
  laneResult: 'won' | 'even' | 'lost' | null;
  damageProfile: {
    physical: number;
    magical: number;
    pure: number;
  } | null;
  enemyItems: Map<number, string[]>;
  purchasedItems: Set<number>;
  markItemPurchased: (itemId: number) => void;
  // ... actions
}

interface RecommendationSlice {
  recommendations: Recommendation | null;
  isLoading: boolean;
  error: string | null;
  fetchRecommendations: () => Promise<void>;
}

// Combined store
type GameStore = DraftSlice & GameStateSlice & RecommendationSlice;
```

**Key decisions:**
- Single store, not multiple stores. The draft, game state, and recommendations are deeply coupled -- a role change affects playstyle options which affects recommendations. One store keeps this coherent.
- Immer middleware for nested state updates (damage profile, enemy items map). Without Immer, updating enemyItems requires tedious spread syntax.
- Selectors for derived state: useGameStore(state => state.isReadyToRecommend) computes from hero + role + lane selections being filled.

### 2. Hybrid Recommendation Engine (Backend Core)

**Pattern:** Pipeline architecture. Rules fire first (deterministic, instant). Output feeds into the LLM context. LLM enriches, reasons, and fills gaps. Merger combines both.

**Confidence:** HIGH (this pattern is validated by academic research on hybrid recommendation systems and aligns with the RAG-style pattern where the LLM uses deterministic retrieval as a tool)

```python
# engine/recommender.py - The orchestrator
class HybridRecommender:
    def __init__(
        self,
        rules_engine: RulesEngine,
        llm_engine: LLMEngine,
        context_builder: ContextBuilder,
    ):
        self.rules = rules_engine
        self.llm = llm_engine
        self.context = context_builder

    async def recommend(
        self, request: RecommendRequest
    ) -> Recommendation:
        # 1. Build context from database
        context = self.context.build(request)

        # 2. Rules layer (instant, always succeeds)
        rules_output = self.rules.evaluate(request, context)

        # 3. LLM layer (may fail, has timeout)
        try:
            llm_output = await asyncio.wait_for(
                self.llm.reason(request, context, rules_output),
                timeout=10.0
            )
        except (asyncio.TimeoutError, Exception):
            # Fallback: return rules-only output
            return self._rules_only_response(rules_output, context)

        # 4. Merge: LLM output is primary, rules output fills gaps
        return self._merge(rules_output, llm_output)
```

**Rules Engine categories (deterministic, no API call):**

| Rule Category | Example | When |
|---------------|---------|------|
| **Counter items** | Magic Stick vs. spell-spammers (Bristleback, Batrider, Zeus) | Hero matchup check |
| **Starting items** | Budget allocation: 600g starting gold | Always for starting phase |
| **Role-gated items** | Quelling Blade for melee cores only, not supports | Role + attack type check |
| **Lane-specific** | More regen for offlane, Stout Shield for melee vs ranged | Lane + matchup check |
| **Obvious counter** | BKB when >50% magic damage in damage profile | Damage profile available |
| **Anti-evasion** | MKB/Bloodthorn when enemy has evasion items or heroes | Enemy items spotted |

**LLM Engine responsibilities (nuanced reasoning):**

- Item timing rationale (why 14-min BKB, not 22-min BKB)
- Opportunity cost articulation (BKB means delaying damage item)
- Playstyle integration (aggressive build vs. farming build for same hero)
- Situational decision trees (if X happens, build Y instead of Z)
- Overall strategy narrative (2-3 sentence game plan)

### 3. Context Builder (Backend)

**Pattern:** Builder/assembler that constructs the LLM prompt context from multiple data sources.

```python
# engine/context_builder.py
class ContextBuilder:
    def __init__(self, db: Session):
        self.db = db

    def build(self, request: RecommendRequest) -> MatchContext:
        # Synchronous SQLite queries (sub-millisecond)
        hero = self._get_hero(request.hero_id)
        opponents = self._get_opponents(request.lane_opponents)
        matchup_data = self._get_matchup_data(
            request.hero_id, request.lane_opponents
        )
        item_catalog = self._get_relevant_items(
            request.role, request.phase
        )

        return MatchContext(
            hero=hero,
            opponents=opponents,
            matchup_data=matchup_data,
            item_catalog=item_catalog,
            role=request.role,
            playstyle=request.playstyle,
            side=request.side,
            lane=request.lane,
            phase=request.phase,
            lane_result=request.lane_result,
            damage_profile=request.damage_profile,
            enemy_items=request.enemy_items_spotted,
            purchased_items=request.previous_recommendations,
        )
```

The context builder is the translation layer between database models and LLM prompt context. It queries the local SQLite database (fast, sub-millisecond) and structures the data into a format that the prompt templates consume.

### 4. Claude API Integration (LLM Engine)

**Pattern:** Structured JSON output via output_config parameter with Pydantic model validation. The official Anthropic SDK supports direct Pydantic model integration.

**Confidence:** HIGH (verified from official Anthropic documentation, GA since late 2025)

```python
# engine/llm.py
from anthropic import AsyncAnthropic
from pydantic import BaseModel

class ItemRecommendation(BaseModel):
    item_id: int
    item_name: str
    quantity: int = 1
    priority: str  # core | situational | luxury
    reasoning: str  # 1-3 sentences, matchup-specific

class PhaseRecommendation(BaseModel):
    phase: str
    items: list[ItemRecommendation]
    timing: str | None = None
    gold_budget: int | None = None

class LLMRecommendation(BaseModel):
    phases: list[PhaseRecommendation]
    overall_strategy: str
    meta_context: str | None = None

class LLMEngine:
    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514"
    ):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def reason(
        self,
        request: RecommendRequest,
        context: MatchContext,
        rules_output: RulesOutput,
    ) -> LLMRecommendation:
        prompt = self._build_prompt(context, rules_output)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": LLMRecommendation.model_json_schema(),
                }
            },
        )

        return LLMRecommendation.model_validate_json(
            response.content[0].text
        )
```

**Key implementation decisions:**

- Use output_config with json_schema (GA, no beta header needed). This guarantees the LLM returns valid JSON matching the schema. Eliminates parsing errors entirely.
- Use AsyncAnthropic client for non-blocking calls in FastAPI async event loop.
- Temperature 0.3 for consistency across recommendations for the same inputs.
- 10-second timeout at the orchestrator level, not the API client level, so the timeout is controlled by application logic.
- System prompt is static and cached. Only the user message changes per request. This keeps token usage efficient.

### 5. Data Layer

**Pattern:** SQLAlchemy 2.0 with synchronous SQLite. SQLite does not benefit from async drivers (it is file-based, not network-based), so use standard synchronous Session with FastAPI dependency injection.

**Confidence:** HIGH (SQLite with async wrappers adds complexity without benefit; the official FastAPI docs use sync SQLAlchemy for SQLite)

```python
# data/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/prismlab.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Important note on SQLite + async:** The blueprint specifies SQLAlchemy + SQLite. SQLite does not have a true async driver (aiosqlite wraps sync calls in a thread, providing no real concurrency benefit). Use synchronous SQLAlchemy sessions with FastAPI Depends(get_db). The only async operations are the Claude API call and external API fetches (OpenDota, Stratz), which genuinely benefit from async. This is not a limitation -- SQLite queries for hero/item lookups are sub-millisecond.

### 6. External Data Clients

**Pattern:** Async HTTP clients (httpx) for OpenDota REST API and Stratz GraphQL API. Data is fetched periodically and cached in SQLite, not queried live per request.

**Confidence:** MEDIUM (OpenDota endpoint paths verified via MCP server project and pyopendota docs; Stratz GraphQL schema not directly verified)

**OpenDota API endpoints used:**

| Endpoint | Purpose | Prismlab Usage |
|----------|---------|---------------|
| GET /heroes | All heroes with attributes | Seed hero table |
| GET /heroStats | Hero performance stats | Hero win rates, pick rates |
| GET /heroes/{id}/matchups | Hero vs. hero win rates | MatchupData table |
| GET /heroes/{id}/itemPopularity | Popular items by game phase | Common items per hero |
| GET /heroes/{id}/durations | Performance by match duration | Timing context |
| GET /constants/items | All item data | Seed items table |

**Stratz GraphQL API:**

| Query | Purpose | Prismlab Usage |
|-------|---------|---------------|
| Hero matchup queries | Win rate by bracket, with item builds | Supplement OpenDota matchup data |
| Item win rate queries | Item performance per hero per matchup | Common items in matchup context |

**Data refresh strategy:**
- Seed on first run (pull all heroes, items, matchup data)
- Refresh daily via cron-triggered endpoint POST /api/admin/refresh-data
- Patch detection: compare hero/item count; if changed, full refresh
- Rate limit awareness: OpenDota allows 60 req/min free tier; batch requests with delays

### 7. Frontend Component Architecture

**Pattern:** Container/presenter split. Container components connect to Zustand store; presenter components receive props and render.

```
App.tsx
  |
  +-- Header.tsx (logo, version)
  |
  +-- Sidebar.tsx (left panel - all inputs)
  |     |
  |     +-- HeroPicker.tsx (searchable dropdown, Steam CDN images)
  |     +-- RoleSelector.tsx (Pos 1-5 buttons)
  |     +-- PlaystyleSelector.tsx (dynamic options based on role)
  |     +-- SideSelector.tsx (Radiant/Dire toggle)
  |     +-- LaneSelector.tsx (Safe/Off/Mid)
  |     +-- OpponentPicker.tsx (1-2 slots, same HeroPicker component)
  |     |
  |     +-- [Divider: Game State - visible after recs exist]
  |     |
  |     +-- GameStatePanel.tsx
  |           +-- LaneResultSelector.tsx (Won/Even/Lost)
  |           +-- DamageProfileInput.tsx (P%/M%/U% with auto-sum)
  |           +-- EnemyItemTracker.tsx (per-hero item lists)
  |           +-- ReEvaluateButton.tsx
  |
  +-- MainPanel.tsx (right panel - recommendations)
        |
        +-- Timeline.tsx (vertical, scrollable)
              +-- PhaseCard.tsx (one per game phase)
                    +-- ItemRecommendation.tsx (icon + name + priority)
                          +-- ItemIcon.tsx (Steam CDN image)
                          +-- ReasoningTooltip.tsx (expandable why)
```

**Key UI state patterns:**
- Progressive disclosure: Game State panel hidden until first recommendation is received
- Phase gating: PlaystyleSelector disabled until role is selected; Opponent picker appears after lane is selected
- Loading isolation: Loading spinner only on MainPanel during recommendation fetch, never full-page
- Optimistic UI: Click-to-purchase immediately dims the item; if re-evaluate fails, item stays dimmed (no rollback needed since purchase tracking is local-only)

## Patterns to Follow

### Pattern 1: Dependency Injection via FastAPI Depends

**What:** Use FastAPI Depends() to inject database sessions, configuration, and service instances into route handlers. Chain dependencies so routes get fully-assembled service objects.

**When:** Every route handler. Never instantiate services directly in routes.

**Confidence:** HIGH

```python
# Dependency chain
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_context_builder(
    db: Session = Depends(get_db)
) -> ContextBuilder:
    return ContextBuilder(db)

def get_rules_engine() -> RulesEngine:
    return RulesEngine()

def get_llm_engine() -> LLMEngine:
    return LLMEngine(api_key=settings.anthropic_api_key)

def get_recommender(
    rules: RulesEngine = Depends(get_rules_engine),
    llm: LLMEngine = Depends(get_llm_engine),
    context: ContextBuilder = Depends(get_context_builder),
) -> HybridRecommender:
    return HybridRecommender(rules, llm, context)

# Route handler
@router.post("/recommend")
async def recommend(
    request: RecommendRequest,
    recommender: HybridRecommender = Depends(get_recommender),
) -> RecommendResponse:
    return await recommender.recommend(request)
```

### Pattern 2: Pydantic Models as API Contract

**What:** Define request and response schemas as Pydantic models. FastAPI validates automatically. Same models used for Claude structured output schema.

**When:** Every API endpoint and LLM interaction.

**Confidence:** HIGH

```python
from pydantic import BaseModel, Field, field_validator

class RecommendRequest(BaseModel):
    hero_id: int
    role: int = Field(ge=1, le=5)
    playstyle: str
    side: str
    lane: str
    lane_opponents: list[int | None] = Field(max_length=2)
    phase: str = "laning"
    lane_result: str | None = None
    damage_profile: DamageProfile | None = None
    enemy_items_spotted: list[EnemyItemEntry] = []
    purchased_items: list[int] = []

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str) -> str:
        if v not in ("radiant", "dire"):
            raise ValueError("side must be radiant or dire")
        return v
```

### Pattern 3: Rules-First, LLM-Second

**What:** The rules engine runs before the LLM and its output is fed into the LLM context. The LLM can endorse, enhance, or override rules recommendations, but must acknowledge them.

**When:** Every recommendation request.

**Why:** This prevents the LLM from forgetting obvious decisions (like Magic Stick vs. Bristleback) while still allowing it to provide nuanced reasoning. It also means the LLM prompt is more focused -- it does not need to figure out the basics, only reason about the nuance.

**Confidence:** HIGH (this is the retrieval-augmented pattern adapted for recommendation systems)

### Pattern 4: Progressive State Model

**What:** The Zustand store tracks a currentPhase that gates which UI components are visible and which data is sent to the backend. State transitions are explicit actions, not implicit side effects.

**When:** User progresses through draft -> laning -> midgame -> lategame.

```typescript
// Phase transitions in the store
advancePhase: () => set((state) => {
    const phaseOrder = ['draft', 'laning', 'midgame', 'lategame'];
    const currentIndex = phaseOrder.indexOf(state.currentPhase);
    if (currentIndex < phaseOrder.length - 1) {
        return { currentPhase: phaseOrder[currentIndex + 1] };
    }
    return state;
}),
```

### Pattern 5: Graceful Degradation

**What:** Every path that depends on an external service (Claude API, OpenDota, Stratz) has a fallback. The app should never show an error state for a degraded but functional recommendation.

**When:** Always.

| Service Down | Fallback | User Impact |
|-------------|----------|-------------|
| Claude API timeout | Rules-only recommendations (no reasoning text) | Items still recommended, just without why explanations |
| Claude API error | Same as timeout | Same |
| OpenDota API down | Use cached data from SQLite | Data may be stale (show last updated timestamp) |
| Stratz API down | OpenDota data only | Slightly less matchup detail; not noticeable |

## Anti-Patterns to Avoid

### Anti-Pattern 1: Live External API Calls Per Request

**What:** Calling OpenDota or Stratz APIs during a recommendation request to get matchup data.

**Why bad:** Adds 500ms-2s latency per request, rate limit risk (50K/month free), and the data does not change between requests. A user running 10 re-evaluations in a game would make 10x the external API calls for identical data.

**Instead:** Pre-fetch and cache all hero, item, and matchup data in SQLite. Refresh daily. The recommendation endpoint reads only from the local database.

### Anti-Pattern 2: Monolithic Zustand Store Without Selectors

**What:** Components subscribing to the entire store and re-rendering on every state change.

**Why bad:** Changing the damage profile slider would re-render the hero picker, the timeline, the sidebar, and every other component. With ~20 components connected to the store, this creates visible jank.

**Instead:** Use granular selectors: const hero = useGameStore(s => s.myHero). Each component subscribes only to the slice it needs. Zustand built-in shallow comparison prevents unnecessary re-renders.

### Anti-Pattern 3: Stuffing Full Item Catalog into LLM Prompt

**What:** Sending all 200+ Dota items to the Claude API in every prompt.

**Why bad:** Wastes tokens (cost), increases latency, and dilutes the LLM attention. Most items are irrelevant for any given hero/role/matchup.

**Instead:** Context Builder filters items to a relevant subset (~30-50 items) based on:
- Hero commonly built items (from OpenDota item popularity data)
- Role-appropriate items (no carry items for Pos 5)
- Counter items relevant to the matchup (armor items if facing physical damage)
- Phase-appropriate items (no 6K gold items in starting phase)

### Anti-Pattern 4: Synchronous Claude API Calls

**What:** Using the synchronous anthropic.Anthropic() client in an async FastAPI route.

**Why bad:** Blocks the entire FastAPI event loop for 2-10 seconds during the Claude API call. Other requests cannot be served.

**Instead:** Use anthropic.AsyncAnthropic() with await. FastAPI can serve other requests while waiting for the Claude API response. Note: the database calls can remain synchronous (SQLite is file-based and fast), but the Claude API call must be async.

### Anti-Pattern 5: Bidirectional Data Flow Between Frontend Components

**What:** Components passing callbacks to siblings or parents to coordinate state changes.

**Why bad:** Creates spaghetti dependencies. When the user changes the role, the PlaystyleSelector, the HeroPicker, and the Timeline all need to respond. If they communicate via props/callbacks, the logic is scattered.

**Instead:** All state flows through Zustand. Components write to the store, other components react to store changes. The store is the single coordination point.

## Scalability Considerations

| Concern | Single User (V1) | 10+ Concurrent Users (V1.x) | 100+ Users (V2) |
|---------|-------------------|-------------------------------|-------------------|
| Claude API cost | ~0.003-0.01 per rec | Rate limit middleware (10 req/min per IP) | Response caching for identical combos |
| Claude API latency | 2-5s acceptable | Same; async handles concurrency | Pre-compute common matchup recs |
| SQLite concurrency | No concern | WAL mode for concurrent reads | Migrate to PostgreSQL if write contention |
| Data freshness | Daily refresh is fine | Same | Webhook-triggered refresh on Dota patches |
| Frontend bundle | Single SPA, no code splitting needed | Same | Lazy-load GameStatePanel and admin components |

For V1 (single user on Unraid), scalability is not a concern. The architecture is designed to be simple and correct first. The only proactive measure worth taking is WAL mode on SQLite (PRAGMA journal_mode=WAL) to prevent database locked errors if the daily data refresh runs while the user is making requests.

## Suggested Build Order (Dependency Analysis)

The build order is constrained by data dependencies. Each phase depends on artifacts from the previous phase.

```
Phase 1: Foundation
  |- SQLite + SQLAlchemy models (Heroes, Items, MatchupData)
  |- OpenDota client + data seeding script
  |- FastAPI app shell + data endpoints (GET /heroes, GET /items)
  |- React + Vite scaffold + layout shell (Sidebar, MainPanel)
  |- HeroPicker component (needs hero data from backend)
  |- Favicon, theme, typography setup
  |
  v
Phase 2: Draft Input UI (depends on Phase 1 hero/item data)
  |- Zustand GameStore with draft slice
  |- RoleSelector, PlaystyleSelector, SideSelector, LaneSelector
  |- OpponentPicker (reuses HeroPicker component)
  |- Wire all inputs to GameStore
  |
  v
Phase 3: Recommendation Engine (depends on Phase 1 data layer)
  |- Rules Engine (deterministic item rules)
  |- Context Builder (database queries + prompt assembly)
  |- LLM Engine (Claude API integration + structured output)
  |- Hybrid Recommender (orchestrator)
  |- POST /api/recommend endpoint
  |- Matchup data ingestion (OpenDota /heroes/{id}/matchups)
  |
  v
Phase 4: Item Timeline UI (depends on Phase 2 store + Phase 3 engine)
  |- API Client (frontend HTTP layer)
  |- Timeline, PhaseCard, ItemRecommendation components
  |- Connect Generate Build action to /api/recommend
  |- Loading states and error handling
  |- End-to-end flow: select hero -> get recs -> see timeline
  |
  v
Phase 5: Mid-Game Adaptation (depends on Phase 4 working flow)
  |- GameStateSlice added to Zustand store
  |- LaneResultSelector, DamageProfileInput, EnemyItemTracker
  |- Click-to-purchase on timeline items
  |- Re-Evaluate button + updated recommendation flow
  |- Phase-specific prompt builders (midgame, lategame)
  |
  v
Phase 6: Polish (depends on Phase 5 complete flow)
  |- Data refresh pipeline (cron script, admin endpoints)
  |- Error handling throughout (network failures, invalid data)
  |- Loading skeletons, animations, transitions
  |- Performance optimization (debounce, caching)
  |- Responsive groundwork (don't break on resize)
```

**Critical path:** Phase 1 data layer -> Phase 3 engine -> Phase 4 timeline UI. This is the narrowest path to a working demo. Phases 1-2 (frontend scaffold) and Phase 3 (backend engine) can be developed in parallel by different developers, but converge at Phase 4.

**Phase 3 is the highest-risk phase.** It involves integrating with the Claude API, designing the system prompt, tuning rules, and getting structured output to parse reliably. Budget extra time here. The other phases are straightforward UI or data plumbing.

## Sources

- [OpenDota API Documentation](https://docs.opendota.com/) -- Endpoint reference for hero, item, and matchup data (MEDIUM confidence on specific endpoints; verified via pyopendota and MCP server projects)
- [Anthropic Structured Outputs Documentation](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) -- GA structured JSON output with output_config parameter (HIGH confidence; verified from official docs)
- [Anthropic Structured Outputs Blog](https://claude.com/blog/structured-outputs-on-the-claude-developer-platform) -- GA announcement for Claude Sonnet 4.5, Opus 4.5, Haiku 4.5
- [FastAPI SQL Databases Tutorial](https://fastapi.tiangolo.com/tutorial/sql-databases/) -- Official pattern for SQLAlchemy + SQLite (HIGH confidence)
- [FastAPI Dependency Injection](https://fastapi.tiangolo.com/tutorial/dependencies/) -- Built-in DI pattern (HIGH confidence)
- [Zustand Slices Pattern](https://github.com/pmndrs/zustand/blob/main/docs/learn/guides/slices-pattern.md) -- Official guide for store organization (HIGH confidence)
- [Zustand GitHub](https://github.com/pmndrs/zustand) -- Latest version and API reference
- [STRATZ API](https://stratz.com/api) -- GraphQL API for Dota 2 stats (LOW confidence on specific schema; documentation not directly verified)
- [OpenDota MCP Server](https://github.com/hkaanengin/opendota-mcp-server) -- Confirms available OpenDota endpoints including hero matchups and item popularity (MEDIUM confidence)
- [Layered Architecture and Dependency Injection in FastAPI](https://dev.to/markoulis/layered-architecture-dependency-injection-a-recipe-for-clean-and-testable-fastapi-code-3ioo) -- Service layer pattern reference
- [Sequential Item Recommendation in Dota 2](https://arxiv.org/abs/2201.08724) -- Academic research on item recommendation architectures for MOBAs
- [Dotabuff Adaptive Items](https://www.dotabuff.com/blog/2021-06-23-announcing-the-dotabuff-apps-new-adaptive-items-module) -- Competitor reference for draft-aware item suggestions
- [Improving Recommendation Systems in the Age of LLMs](https://eugeneyan.com/writing/recsys-llm/) -- Hybrid recommendation patterns with LLMs

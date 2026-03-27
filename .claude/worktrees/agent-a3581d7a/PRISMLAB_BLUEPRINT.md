# PRISMLAB — Dota 2 Adaptive Item Advisor
## Claude Code Project Blueprint

---

## Project Overview

Prismlab is a web-based Dota 2 item advisor that adapts in real-time to your game state. Unlike static guides, Prismlab evolves from draft through late game, providing contextual item recommendations with coaching-quality explanations.

**V1 Focus:** Win your lane. Pick your hero, define your role/playstyle, identify your lane opponent(s), and get a living item build that adapts as the game progresses.

---

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 18 + Vite | TypeScript, Tailwind CSS |
| Backend | Python 3.12 + FastAPI | Async, auto-generated API docs |
| Database | SQLite (via SQLAlchemy) | Hero/item data cache, user sessions |
| AI Engine | Claude API (Sonnet) | Reasoning layer for item recommendations |
| Data Sources | OpenDota API, Stratz API | Hero stats, item data, matchup win rates |
| Deployment | Docker Compose on Unraid | Two containers: frontend (Nginx) + backend (FastAPI) |
| Reverse Proxy | Cloudflare Tunnel or Nginx Proxy Manager | Already in Justin's Unraid stack |

---

## Project Structure

```
prismlab/
├── docker-compose.yml
├── .env.example                    # ANTHROPIC_API_KEY, OPENDOTA_API_KEY, etc.
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     # FastAPI app entry
│   ├── config.py                   # Settings, env vars
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── heroes.py           # GET /heroes, GET /heroes/{id}
│   │   │   ├── items.py            # GET /items, GET /items/{id}
│   │   │   ├── matchups.py         # GET /matchups/{hero_id}/{opponent_id}
│   │   │   ├── recommend.py        # POST /recommend (main recommendation endpoint)
│   │   │   └── data_refresh.py     # POST /admin/refresh-data (trigger data pull)
│   │   └── middleware/
│   │       └── rate_limit.py       # Rate limiting for Claude API calls
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── recommender.py          # Hybrid recommendation orchestrator
│   │   ├── rules.py                # Rule-based layer (fast, no API call)
│   │   ├── llm.py                  # Claude API reasoning layer
│   │   ├── prompts/
│   │   │   ├── system_prompt.py    # Master system prompt for Claude
│   │   │   ├── laning_prompt.py    # Phase-specific prompt builder
│   │   │   ├── midgame_prompt.py
│   │   │   └── lategame_prompt.py
│   │   └── context_builder.py      # Assembles game state into prompt context
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy models
│   │   ├── database.py             # DB connection, session management
│   │   ├── seed.py                 # Initial data population
│   │   ├── opendota_client.py      # OpenDota API wrapper
│   │   ├── stratz_client.py        # Stratz API wrapper
│   │   └── refresh.py              # Scheduled data refresh logic
│   │
│   └── tests/
│       ├── test_recommender.py
│       ├── test_rules.py
│       └── test_api.py
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── index.html                  # Must include favicon
│   │
│   ├── public/
│   │   ├── favicon.ico             # REQUIRED — Prismlab prism/refraction icon
│   │   └── favicon.svg
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts           # Axios/fetch wrapper for backend API
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Header.tsx       # Logo, app title
│   │   │   │   ├── Sidebar.tsx      # Input panel (left side)
│   │   │   │   └── MainPanel.tsx    # Recommendations (right side)
│   │   │   │
│   │   │   ├── draft/
│   │   │   │   ├── HeroPicker.tsx          # Searchable dropdown with hero portraits
│   │   │   │   ├── HeroPortrait.tsx        # Hero image + name + attribute icon
│   │   │   │   ├── RoleSelector.tsx        # Pos 1-5 selection
│   │   │   │   ├── PlaystyleSelector.tsx   # Context-dependent playstyle options
│   │   │   │   ├── SideSelector.tsx        # Radiant / Dire toggle
│   │   │   │   ├── LaneSelector.tsx        # Safe / Off / Mid
│   │   │   │   └── OpponentPicker.tsx      # 1-2 lane opponent slots
│   │   │   │
│   │   │   ├── game/
│   │   │   │   ├── GameStatePanel.tsx      # Mid-game update controls
│   │   │   │   ├── LaneResultSelector.tsx  # Won / Even / Lost
│   │   │   │   ├── DamageProfileInput.tsx  # Physical / Magical / Pure % inputs
│   │   │   │   ├── EnemyItemTracker.tsx    # Track spotted enemy items
│   │   │   │   └── ReEvaluateButton.tsx    # Triggers recommendation refresh
│   │   │   │
│   │   │   └── recommendations/
│   │   │       ├── Timeline.tsx            # Vertical timeline of item phases
│   │   │       ├── PhaseCard.tsx           # Individual phase (starting, laning, core, etc.)
│   │   │       ├── ItemRecommendation.tsx  # Single item with icon + reasoning
│   │   │       ├── ItemIcon.tsx            # Item image from CDN
│   │   │       └── ReasoningTooltip.tsx    # Expandable "why" explanation
│   │   │
│   │   ├── hooks/
│   │   │   ├── useHeroes.ts        # Fetch and cache hero list
│   │   │   ├── useItems.ts         # Fetch and cache item list
│   │   │   ├── useRecommendation.ts # Main recommendation state + API call
│   │   │   └── useGameState.ts     # Game state management
│   │   │
│   │   ├── stores/
│   │   │   └── gameStore.ts        # Zustand store for full game state
│   │   │
│   │   ├── types/
│   │   │   ├── hero.ts
│   │   │   ├── item.ts
│   │   │   ├── gameState.ts
│   │   │   └── recommendation.ts
│   │   │
│   │   ├── utils/
│   │   │   ├── heroFilters.ts      # Search/filter logic for hero picker
│   │   │   ├── imageUrls.ts        # CDN URL builders for hero/item images
│   │   │   └── constants.ts        # Role names, playstyle options, lane names
│   │   │
│   │   └── styles/
│   │       └── globals.css         # Tailwind imports, CSS variables, custom styles
│   │
│   └── tests/
│       └── components/
│           └── HeroPicker.test.tsx
│
└── scripts/
    ├── seed_data.sh                # One-time data population
    └── refresh_data.sh             # Cron-friendly data refresh
```

---

## Data Models

### Hero
```python
class Hero(Base):
    __tablename__ = "heroes"
    
    id = Column(Integer, primary_key=True)           # Dota 2 hero ID
    name = Column(String, nullable=False)              # "Anti-Mage"
    localized_name = Column(String, nullable=False)    # "Anti-Mage"
    internal_name = Column(String, nullable=False)     # "npc_dota_hero_antimage"
    primary_attr = Column(String)                      # "agi", "str", "int", "all"
    attack_type = Column(String)                       # "Melee", "Ranged"
    roles = Column(JSON)                               # ["Carry", "Escape", "Nuker"]
    
    # Base stats
    base_health = Column(Float)
    base_mana = Column(Float)
    base_armor = Column(Float)
    base_attack_min = Column(Integer)
    base_attack_max = Column(Integer)
    base_str = Column(Float)
    base_agi = Column(Float)
    base_int = Column(Float)
    str_gain = Column(Float)
    agi_gain = Column(Float)
    int_gain = Column(Float)
    attack_range = Column(Integer)
    move_speed = Column(Integer)
    
    # Metadata
    img_url = Column(String)                           # CDN portrait URL
    icon_url = Column(String)                          # CDN icon URL
    
    updated_at = Column(DateTime, default=func.now())
```

### Item
```python
class Item(Base):
    __tablename__ = "items"
    
    id = Column(Integer, primary_key=True)             # Dota 2 item ID
    name = Column(String, nullable=False)              # "Black King Bar"
    internal_name = Column(String, nullable=False)     # "item_black_king_bar"
    cost = Column(Integer)                             # Total gold cost
    
    # Item properties
    components = Column(JSON)                          # List of component item IDs
    is_recipe = Column(Boolean, default=False)
    is_neutral = Column(Boolean, default=False)        # V2: neutral items
    tier = Column(Integer, nullable=True)              # Neutral item tier (1-5)
    
    # Stat bonuses (JSON blob for flexibility)
    bonuses = Column(JSON)                             # {"strength": 10, "armor": 5, ...}
    
    # Active/passive descriptions
    active_desc = Column(Text, nullable=True)
    passive_desc = Column(Text, nullable=True)
    
    # Categorization
    category = Column(String)                          # "early_game", "mid_game", "late_game"
    tags = Column(JSON)                                # ["armor", "disable", "survivability"]
    
    img_url = Column(String)
    updated_at = Column(DateTime, default=func.now())
```

### MatchupData
```python
class MatchupData(Base):
    __tablename__ = "matchup_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    hero_id = Column(Integer, ForeignKey("heroes.id"))
    opponent_id = Column(Integer, ForeignKey("heroes.id"))
    
    # Stats from OpenDota/Stratz
    win_rate = Column(Float)                           # Hero's WR vs this opponent
    games_played = Column(Integer)                     # Sample size
    
    # Common item builds in this matchup (top 5)
    common_items = Column(JSON)                        # [{"item_id": 1, "win_rate": 0.55, "pick_rate": 0.3}, ...]
    common_starting_items = Column(JSON)               # Same format, starting items only
    
    # Bracket filter
    bracket = Column(String, default="high")           # "all", "high" (Legend+), "pro"
    
    updated_at = Column(DateTime, default=func.now())
```

### GameState (in-memory / Zustand, not persisted)
```typescript
interface GameState {
  // Draft phase
  myHero: Hero | null;
  role: 1 | 2 | 3 | 4 | 5 | null;
  playstyle: string | null;         // From PlaystyleSelector
  side: 'radiant' | 'dire' | null;
  lane: 'safe' | 'off' | 'mid' | null;
  laneOpponents: [Hero | null, Hero | null];  // Up to 2
  
  // Game phase
  currentPhase: 'draft' | 'laning' | 'midgame' | 'lategame';
  laneResult: 'won' | 'even' | 'lost' | null;
  
  // Damage profile (from in-game death screen)
  damageProfile: {
    physical: number;    // 0-100
    magical: number;     // 0-100
    pure: number;        // 0-100
  } | null;
  
  // Enemy items spotted
  enemyItems: {
    heroId: number;
    items: string[];     // item internal names
  }[];
  
  // Recommendations (from API)
  recommendations: Recommendation | null;
  isLoading: boolean;
}
```

---

## API Endpoints

### Data Endpoints
```
GET  /api/heroes                    → List all heroes (for picker dropdowns)
GET  /api/heroes/{id}               → Single hero full detail
GET  /api/items                     → List all items
GET  /api/items/{id}                → Single item full detail
GET  /api/matchups/{hero}/{opponent} → Matchup data + common items
```

### Recommendation Engine
```
POST /api/recommend
Body: {
  "hero_id": 1,
  "role": 1,
  "playstyle": "aggressive_laner",
  "side": "radiant",
  "lane": "safe",
  "lane_opponents": [102, null],
  "phase": "laning",
  "lane_result": null,
  "damage_profile": null,
  "enemy_items_spotted": [],
  "previous_recommendations": []    // What was already recommended
}
Response: {
  "phases": [
    {
      "phase": "starting",
      "gold_budget": 600,
      "items": [
        {
          "item_id": 44,
          "item_name": "Tango",
          "quantity": 1,
          "priority": "core",
          "reasoning": "..."
        }
      ],
      "total_cost": 600
    },
    {
      "phase": "early_laning",
      "items": [...],
      "timing": "0-5 min"
    },
    {
      "phase": "laning_complete",
      "items": [...],
      "timing": "5-12 min"
    },
    {
      "phase": "first_core",
      "items": [...],
      "timing": "12-20 min",
      "target_timing": "14:00"
    },
    {
      "phase": "situational",
      "decision_trees": [
        {
          "condition": "Enemy has heavy magic damage",
          "recommendation": {"item_id": 116, "item_name": "Black King Bar"},
          "reasoning": "..."
        },
        {
          "condition": "Enemy has evasion",
          "recommendation": {"item_id": 133, "item_name": "Monkey King Bar"},
          "reasoning": "..."
        }
      ]
    }
  ],
  "overall_strategy": "...",         // 2-3 sentence game plan
  "meta_context": "..."             // Any relevant patch/meta notes
}
```

### Admin
```
POST /api/admin/refresh-data        → Trigger OpenDota/Stratz data refresh
GET  /api/admin/data-status         → Last refresh time, data freshness
```

---

## Claude System Prompt Skeleton

This is the core of the reasoning engine. It lives in `backend/engine/prompts/system_prompt.py`.

```python
SYSTEM_PROMPT = """
You are Prismlab, an elite Dota 2 item advisor operating at 8K+ MMR coaching level.

## Your Role
You provide item build recommendations with specific, contextual reasoning.
You sound like a high-MMR coach talking to a teammate — direct, specific,
referencing actual hero abilities and item interactions. Never generic.

## Core Principles
1. EVERY item recommendation must have a "why" tied to the specific matchup
2. Item timings matter — a 14-min BKB is different from a 22-min BKB
3. Always consider the OPPORTUNITY COST — recommending BKB means NOT recommending
   something else. Acknowledge what you're giving up.
4. Lane-specific context matters — starting items for a solo offlane vs. a
   dual offlane are different even on the same hero
5. Gold efficiency vs. slot efficiency — early game favors gold efficiency,
   late game favors slot efficiency. Always frame recommendations in this context.

## Knowledge Base
You have access to current hero stats, item stats, and matchup data provided
in the user message. Use this data — do not rely on potentially outdated
training knowledge for specific numbers.

## Output Format
Always respond in valid JSON matching the schema provided. Include a
"reasoning" field for every item recommendation. The reasoning should be:
- 1-3 sentences
- Reference specific abilities, stats, or interactions
- Mention the enemy hero(es) by name
- Explain what problem the item solves in THIS game, not in general

## Damage Type Awareness
When damage profile percentages are provided:
- High physical (>50%): Prioritize armor items (Platemail, Shiva's, AC)
- High magical (>50%): Prioritize magic resist (Hood, Pipe, BKB)
- High pure (>20%): Pure damage ignores both — prioritize raw HP
- Mixed: Balanced approach, favor items with both HP and resist

## Playstyle Integration
The player has declared a playstyle preference. Respect it. If they say
"aggressive laner," don't recommend a farming build. If they say "split-push,"
factor in TP scroll usage and wave-clear items. The playstyle is their
INTENT — optimize for it.

## Side Awareness (Radiant vs Dire)
- Radiant safelane: Easy pull camp access, longer lane. Supports can secure
  farm passively. Carry can build slightly greedier.
- Dire safelane: Closer to Roshan. Triangle farming accessible earlier.
- Radiant offlane: Can contest pull camp. Harder camp access for farming.
- Dire offlane: Triangle adjacent. Can catch-up farm efficiently if lane is hard.
Factor these into early item decisions and farming item timings.
"""
```

---

## Playstyle Options by Role

```python
PLAYSTYLES = {
    1: {  # Pos 1 — Carry
        "aggressive_laner": "Wants to fight in lane, pressure opponents, secure kills",
        "afk_farmer": "Prioritizes farm speed, avoids fights until key item timing",
        "early_fighter": "Joins fights early with 1-2 items, snowball-oriented",
        "split_pusher": "Focuses on lane pressure and map control through pushing",
    },
    2: {  # Pos 2 — Mid
        "lane_dominator": "Aims to win lane hard, deny CS, zone opponent",
        "tempo_controller": "Rotates early to gank side lanes, creates space",
        "scaling_farmer": "Plays for late game, uses mid lane for fast farm",
        "playmaker": "Aggressive ganker, aims for kills from level 6+",
    },
    3: {  # Pos 3 — Offlane
        "aggressive_laner": "Cuts waves, trades aggressively, disrupts enemy carry",
        "teamfight_initiator": "Farms key initiation item (Blink, etc.), plays for fights",
        "aura_carrier": "Builds utility/aura items to buff team",
        "lane_bully": "Focuses on denying enemy carry farm, zoning, harassing",
    },
    4: {  # Pos 4 — Soft Support
        "aggressive_roamer": "Rotates frequently, smokes for ganks, tempo-oriented",
        "lane_support": "Stays in lane to win it, trades with enemy support",
        "stacker_puller": "Focuses on securing farm for core through stacking/pulling",
        "greedy_four": "Farms when possible, builds toward a key item timing",
    },
    5: {  # Pos 5 — Hard Support
        "lane_protector": "Stays with carry, zones offlaners, secures farm",
        "harass_focused": "Spends mana and HP to bully enemy laners",
        "save_oriented": "Prioritizes defensive items (Glimmer, Force, etc.)",
        "ward_centric": "Vision-focused, prioritizes map control and dewarding",
    },
}
```

---

## Image Asset URLs

Hero and item images come from the Dota 2 CDN via OpenDota:

```typescript
// Hero portrait (full)
const heroImageUrl = (heroName: string) =>
  `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/${heroName}.png`;

// Hero icon (small)
const heroIconUrl = (heroName: string) =>
  `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/icons/${heroName}.png`;

// Item image
const itemImageUrl = (itemName: string) =>
  `https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/items/${itemName}.png`;

// Note: heroName/itemName here is the short internal name like "antimage", "bfury"
// The API response will include the correct mapping
```

---

## Docker Compose

```yaml
version: "3.8"

services:
  prismlab-backend:
    build: ./backend
    container_name: prismlab-backend
    restart: unless-stopped
    ports:
      - "8420:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENDOTA_API_KEY=${OPENDOTA_API_KEY}
      - STRATZ_API_TOKEN=${STRATZ_API_TOKEN}
      - DATABASE_URL=sqlite:///./data/prismlab.db
    volumes:
      - ./data:/app/data    # Persistent SQLite DB
    networks:
      - prismlab-net

  prismlab-frontend:
    build: ./frontend
    container_name: prismlab-frontend
    restart: unless-stopped
    ports:
      - "8421:80"
    depends_on:
      - prismlab-backend
    networks:
      - prismlab-net

networks:
  prismlab-net:
    driver: bridge
```

---

## UI Design Direction

### Aesthetic
- **Dark theme** — Deep charcoal/slate background (#0f1117 primary, #1a1d28 secondary)
- **Prism-inspired accents** — Spectral cyan (#00d4ff) for primary highlights, Radiant teal (#6aff97) and Dire red (#ff5555) for side selection, prismatic gradient accents where appropriate
- **Typography** — Use a clean, gaming-adjacent font. Something like "Rajdhani" or "Chakra Petch" for headings, "JetBrains Mono" for stats/numbers, clean sans-serif for body text
- **Item icons** — Displayed with subtle gold borders, glow effect on hover
- **Hero portraits** — Cropped hero portraits in circular frames for the picker, full art for the selected hero display

### Layout (Desktop V1)
```
┌──────────────────────────────────────────────────────────────────┐
│  🔷 PRISMLAB                                            [v1.0]   │
├────────────────────┬─────────────────────────────────────────────┤
│                    │                                             │
│  YOUR HERO         │  ITEM TIMELINE                              │
│  [Hero Picker]     │                                             │
│                    │  ┌─ STARTING ITEMS (600g) ──────────────┐   │
│  ROLE: [1-5]       │  │ 🧪 Tango  🌿 Branch  ⚔️ Quelling   │   │
│  STYLE: [Dropdown] │  │ "You need sustain and last-hit dmg   │   │
│                    │  │  against Bristle's Quill harass"      │   │
│  SIDE: [R] [D]     │  └──────────────────────────────────────┘   │
│  LANE: [S] [O] [M] │                                             │
│                    │  ┌─ EARLY LANING (0-5 min) ─────────────┐   │
│  LANE OPPONENTS    │  │ 🪄 Magic Stick → Magic Wand           │   │
│  [Opponent 1]      │  │ "Bristle spams 3+ spells per trade.  │   │
│  [Opponent 2]      │  │  Wand will regularly sit at 10+       │   │
│                    │  │  charges."                             │   │
│  ─────────────     │  └──────────────────────────────────────┘   │
│                    │                                             │
│  GAME STATE        │  ┌─ CORE TIMING (12-20 min) ────────────┐   │
│  Lane: [W] [E] [L] │  │ ...                                    │   │
│  Dmg: [P%] [M%] [U%]│ └──────────────────────────────────────┘   │
│  Enemy Items: [+]  │                                             │
│                    │  ┌─ SITUATIONAL ─────────────────────────┐   │
│  [RE-EVALUATE]     │  │ Decision tree cards...                │   │
│                    │  └──────────────────────────────────────┘   │
│                    │                                             │
└────────────────────┴─────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Project scaffolding (React + Vite frontend, FastAPI backend)
- [ ] Docker Compose configuration
- [ ] Database models and SQLite setup
- [ ] OpenDota API client — fetch and cache all heroes + items
- [ ] Hero list endpoint + Hero picker component with search
- [ ] Item list endpoint + Item icon component
- [ ] Basic layout shell (sidebar + main panel)
- [ ] Favicon (Prismlab prism/refraction icon)

### Phase 2: Draft Phase UI (Week 2-3)
- [ ] Role selector (Pos 1-5)
- [ ] Playstyle selector (contextual to role)
- [ ] Side selector (Radiant/Dire)
- [ ] Lane selector (Safe/Off/Mid)
- [ ] Opponent picker (1-2 slots)
- [ ] Game state store (Zustand)
- [ ] Wire up all selectors to store

### Phase 3: Recommendation Engine (Week 3-4)
- [ ] Rule-based recommendation layer (starting items, obvious counters)
- [ ] Claude API integration — system prompt, context builder, response parser
- [ ] POST /recommend endpoint
- [ ] Matchup data ingestion from OpenDota (hero vs hero win rates)
- [ ] Matchup data ingestion from OpenDota (common items per matchup)
- [ ] Hybrid orchestrator (rules first, LLM for reasoning + edge cases)

### Phase 4: Item Timeline UI (Week 4-5)
- [ ] Timeline component (vertical, phase-based)
- [ ] Phase cards with item icons + reasoning text
- [ ] Situational items as decision tree cards
- [ ] Loading state during Claude API calls
- [ ] Connect frontend to /recommend endpoint
- [ ] Full draft → recommendation flow working end-to-end

### Phase 5: Mid-Game Adaptation (Week 5-6)
- [ ] Lane result selector (Won/Even/Lost)
- [ ] Damage profile input (Physical/Magical/Pure percentages)
- [ ] Enemy item tracker (add items spotted per enemy hero)
- [ ] Re-evaluate button triggering updated recommendations
- [ ] Phase progression (laning → midgame → lategame)
- [ ] Past phases collapse, current phase expands

### Phase 6: Polish + Data Pipeline (Week 6-7)
- [ ] Data refresh script (daily cron for matchup stats)
- [ ] Patch detection and data refresh trigger
- [ ] Error handling and edge cases throughout
- [ ] Loading skeletons and animations
- [ ] Mobile-responsive groundwork (not full mobile, but don't break on resize)
- [ ] Performance optimization (debounce searches, cache API responses)

---

## Key Implementation Notes

### Hero Picker Behavior
- Searchable by hero name (fuzzy match)
- Filterable by primary attribute (STR/AGI/INT/Universal)
- Filterable by attack type (Melee/Ranged)
- Shows hero portrait + name + attribute icon in dropdown
- Selected hero displays full portrait with base stats summary
- Same component used for your hero AND opponent slots

### Playstyle Selector Behavior
- Disabled until role is selected
- Options change dynamically based on selected role (see PLAYSTYLES dict above)
- Each option has a tooltip with a brief description
- Selection persists if role changes, clears if new role has different options

### Damage Profile Input
- Three number inputs: Physical %, Magical %, Pure %
- Must sum to 100 (auto-adjust or validation)
- Pre-filled with a balanced default (40/40/20) until user updates
- Tooltip: "Find this on your death screen in-game"
- Only visible after phase transitions past laning

### Re-Evaluate Flow
1. User updates game state inputs
2. Clicks "Re-Evaluate"
3. Loading spinner on recommendation panel only (not full page)
4. Backend builds new context including updated state
5. Hybrid engine runs: rules layer checks for obvious shifts, LLM reasons about nuance
6. New recommendations replace current phase and future phases
7. Past phases remain locked

### Claude API Call Optimization
- Cache hero/item static data in the system prompt (don't re-send every call)
- Use temperature 0.3 for consistency
- Target response in structured JSON — parse and validate before returning to frontend
- Timeout at 10 seconds, fallback to rule-based only if LLM fails
- Estimated cost per recommendation: ~$0.003-0.01 (Sonnet, ~2K input tokens + ~1K output)

---

## Environment Variables

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...
OPENDOTA_API_KEY=...           # Optional but recommended for higher rate limits

# Optional
STRATZ_API_TOKEN=...           # For Stratz data (needs free account)
DATA_REFRESH_INTERVAL=86400    # Seconds between auto-refresh (default: 24h)
CLAUDE_MODEL=claude-sonnet-4-20250514
CLAUDE_TEMPERATURE=0.3
CLAUDE_MAX_TOKENS=2000
LOG_LEVEL=INFO
```

---

## V2 Roadmap (Post-V1)

- [ ] Full 10-hero draft context (allied team heroes)
- [ ] Neutral item tier recommendations
- [ ] Team composition analysis ("your team lacks wave clear")
- [ ] GSI integration (Game State Integration — auto-read game data live)
- [ ] Build history / session saving
- [ ] Mobile-optimized layout
- [ ] Community build sharing
- [ ] Patch notes integration (highlight recent changes affecting recommendations)
- [ ] Voice callouts (TTS for item timing reminders)
- [ ] Dota Plus-style real-time overlay (stretch goal — requires different architecture)

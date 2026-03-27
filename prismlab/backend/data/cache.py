"""In-memory hero, item, ability, and timing data cache.

Preloads all hero, item, and ability data from the database at startup into
frozen dataclasses. Serves all lookups as synchronous dict reads with zero DB
queries. Refreshes atomically via reference swap on pipeline cycle. Timing
data uses stale-while-revalidate pattern (per-hero, fetched on demand).

Module-level singleton: `data_cache` is the single DataCache instance
used throughout the application.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from data.models import Hero, Item, HeroAbilityData, ItemTimingData

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HeroCached:
    """Immutable snapshot of a Hero row. All fields mirror Hero model columns
    except updated_at. Roles stored as tuple for immutability."""

    id: int
    name: str
    localized_name: str
    internal_name: str
    primary_attr: str | None
    attack_type: str | None
    roles: tuple[str, ...] | None
    base_health: float | None
    base_mana: float | None
    base_armor: float | None
    base_str: float | None
    base_agi: float | None
    base_int: float | None
    str_gain: float | None
    agi_gain: float | None
    int_gain: float | None
    base_attack_min: int | None
    base_attack_max: int | None
    attack_range: int | None
    move_speed: int | None
    img_url: str | None
    icon_url: str | None


@dataclass(frozen=True)
class ItemCached:
    """Immutable snapshot of an Item row. All fields mirror Item model columns
    except updated_at. Lists stored as tuples for immutability."""

    id: int
    name: str
    internal_name: str
    cost: int | None
    components: tuple | None
    is_recipe: bool
    is_neutral: bool
    tier: int | None
    bonuses: dict | None  # Read-only by convention; frozen prevents reassignment
    active_desc: str | None
    passive_desc: str | None
    category: str | None
    tags: tuple[str, ...] | None
    img_url: str | None


@dataclass(frozen=True)
class AbilityCached:
    """Counter-item-relevant fields for a hero ability."""

    key: str                      # e.g. "enigma_black_hole"
    dname: str                    # e.g. "Black Hole"
    behavior: tuple[str, ...]     # e.g. ("AOE", "Point Target", "Channeled")
    bkbpierce: bool               # True if raw value == "Yes"
    dispellable: str | None       # "Yes", "No", "Strong Dispels Only", None
    dmg_type: str | None          # "Magical", "Physical", "Pure", None

    @property
    def is_channeled(self) -> bool:
        return "Channeled" in self.behavior

    @property
    def is_passive(self) -> bool:
        return "Passive" in self.behavior


@dataclass(frozen=True)
class TimingBucket:
    """Single time bucket from OpenDota item timing data."""

    time: int          # seconds since game start
    games: int         # PARSED from string
    wins: int          # PARSED from string
    confidence: str    # "strong" | "moderate" | "weak" (D-07)

    @property
    def win_rate(self) -> float:
        return self.wins / self.games if self.games > 0 else 0.0


class DataCache:
    """In-memory cache of all hero, item, ability, and timing data.

    Loaded at startup after DB seeding, refreshed atomically on pipeline
    cycle. All lookup methods are synchronous pure dict reads -- zero DB
    queries on the hot path.

    Thread safety: single-threaded async (uvicorn single-worker). The atomic
    swap pattern (build new dicts, then replace references) is safe because
    no concurrent mutation occurs in a single-threaded event loop.
    """

    def __init__(self) -> None:
        self._heroes: dict[int, HeroCached] = {}
        self._items: dict[int, ItemCached] = {}
        self._hero_name_to_id: dict[str, int] = {}
        self._hero_internal_name_to_id: dict[str, int] = {}
        self._item_name_to_id: dict[str, int] = {}
        self._hero_abilities: dict[int, list[AbilityCached]] = {}
        self._timing_benchmarks: dict[int, dict[str, list[TimingBucket]]] = {}
        self._initialized: bool = False

    @property
    def initialized(self) -> bool:
        """Whether the cache has been loaded at least once."""
        return self._initialized

    async def load(self, db: AsyncSession) -> None:
        """Load all heroes and items from DB into frozen dataclasses.

        Builds new dicts first, then atomically swaps all references at once.
        Safe to call while reads are happening (single-threaded async).
        """
        # -- Build hero cache --
        hero_result = await db.execute(select(Hero))
        hero_rows = hero_result.scalars().all()

        new_heroes: dict[int, HeroCached] = {}
        new_hero_name_to_id: dict[str, int] = {}
        new_hero_internal_name_to_id: dict[str, int] = {}

        for h in hero_rows:
            roles = tuple(h.roles) if h.roles else None
            cached = HeroCached(
                id=h.id,
                name=h.name,
                localized_name=h.localized_name,
                internal_name=h.internal_name,
                primary_attr=h.primary_attr,
                attack_type=h.attack_type,
                roles=roles,
                base_health=h.base_health,
                base_mana=h.base_mana,
                base_armor=h.base_armor,
                base_str=h.base_str,
                base_agi=h.base_agi,
                base_int=h.base_int,
                str_gain=h.str_gain,
                agi_gain=h.agi_gain,
                int_gain=h.int_gain,
                base_attack_min=h.base_attack_min,
                base_attack_max=h.base_attack_max,
                attack_range=h.attack_range,
                move_speed=h.move_speed,
                img_url=h.img_url,
                icon_url=h.icon_url,
            )
            new_heroes[h.id] = cached
            new_hero_name_to_id[h.localized_name] = h.id
            new_hero_internal_name_to_id[h.internal_name] = h.id

        # -- Build item cache --
        item_result = await db.execute(select(Item))
        item_rows = item_result.scalars().all()

        new_items: dict[int, ItemCached] = {}
        new_item_name_to_id: dict[str, int] = {}

        for i in item_rows:
            components = tuple(i.components) if i.components else None
            tags = tuple(i.tags) if i.tags else None
            cached = ItemCached(
                id=i.id,
                name=i.name,
                internal_name=i.internal_name,
                cost=i.cost,
                components=components,
                is_recipe=i.is_recipe,
                is_neutral=i.is_neutral,
                tier=i.tier,
                bonuses=i.bonuses,
                active_desc=i.active_desc,
                passive_desc=i.passive_desc,
                category=i.category,
                tags=tags,
                img_url=i.img_url,
            )
            new_items[i.id] = cached
            new_item_name_to_id[i.internal_name] = i.id

        # -- Build ability cache --
        ability_result = await db.execute(select(HeroAbilityData))
        ability_rows = ability_result.scalars().all()

        new_hero_abilities: dict[int, list[AbilityCached]] = {}
        for row in ability_rows:
            if row.abilities_json:
                abilities = []
                for key, data in row.abilities_json.items():
                    behavior_raw = data.get("behavior", "")
                    if isinstance(behavior_raw, list):
                        behavior = tuple(behavior_raw)
                    elif isinstance(behavior_raw, str) and behavior_raw:
                        behavior = (behavior_raw,)
                    else:
                        behavior = ()

                    abilities.append(AbilityCached(
                        key=key,
                        dname=data.get("dname", key),
                        behavior=behavior,
                        bkbpierce=data.get("bkbpierce") == "Yes",
                        dispellable=data.get("dispellable"),
                        dmg_type=data.get("dmg_type"),
                    ))
                new_hero_abilities[row.hero_id] = abilities

        # -- Build timing cache --
        timing_result = await db.execute(select(ItemTimingData))
        timing_rows = timing_result.scalars().all()

        new_timing_benchmarks: dict[int, dict[str, list[TimingBucket]]] = {}
        for row in timing_rows:
            if row.timings_json:
                hero_timings: dict[str, list[TimingBucket]] = {}
                for item_name, buckets_raw in row.timings_json.items():
                    buckets = []
                    for bucket in buckets_raw:
                        games = int(bucket["games"])  # CRITICAL: cast from string (D-07, Pitfall 1)
                        wins = int(bucket["wins"])    # CRITICAL: cast from string
                        confidence = (
                            "strong" if games >= 1000
                            else "moderate" if games >= 200
                            else "weak"
                        )
                        buckets.append(TimingBucket(
                            time=bucket["time"],
                            games=games,
                            wins=wins,
                            confidence=confidence,
                        ))
                    hero_timings[item_name] = buckets
                new_timing_benchmarks[row.hero_id] = hero_timings

        # -- Atomic swap: replace all references at once --
        self._heroes = new_heroes
        self._items = new_items
        self._hero_name_to_id = new_hero_name_to_id
        self._hero_internal_name_to_id = new_hero_internal_name_to_id
        self._item_name_to_id = new_item_name_to_id
        self._hero_abilities = new_hero_abilities
        self._timing_benchmarks = new_timing_benchmarks
        self._initialized = True

        logger.info(
            "DataCache loaded: %d heroes, %d items, %d heroes with abilities, %d heroes with timings",
            len(new_heroes), len(new_items), len(new_hero_abilities), len(new_timing_benchmarks),
        )

    async def refresh(self, db: AsyncSession) -> None:
        """Refresh cache from DB. Alias for load() -- atomic swap is safe."""
        await self.load(db)

    # ------------------------------------------------------------------
    # Synchronous lookup methods (zero DB, pure dict reads)
    # ------------------------------------------------------------------

    def get_hero(self, hero_id: int) -> HeroCached | None:
        """Get a cached hero by ID. Returns None if not found."""
        return self._heroes.get(hero_id)

    def get_all_heroes(self) -> list[HeroCached]:
        """Get all cached heroes sorted by localized_name."""
        return sorted(self._heroes.values(), key=lambda h: h.localized_name)

    def get_all_items(self) -> list[ItemCached]:
        """Get all cached items sorted by name."""
        return sorted(self._items.values(), key=lambda i: i.name)

    def get_item(self, item_id: int) -> ItemCached | None:
        """Get a cached item by ID. Returns None if not found."""
        return self._items.get(item_id)

    def hero_name_to_id(self, name: str) -> int | None:
        """Lookup hero ID by localized_name. Returns None if not found."""
        return self._hero_name_to_id.get(name)

    def item_name_to_id(self, internal_name: str) -> int | None:
        """Lookup item ID by internal_name. Returns None if not found."""
        return self._item_name_to_id.get(internal_name)

    def hero_internal_name_to_id(self, internal_name: str) -> int | None:
        """Lookup hero ID by internal_name (e.g. 'npc_dota_hero_antimage' -> 1)."""
        return self._hero_internal_name_to_id.get(internal_name)

    def get_hero_abilities(self, hero_id: int) -> list[AbilityCached] | None:
        """Get cached abilities for a hero. Returns None if no ability data."""
        return self._hero_abilities.get(hero_id)

    def get_hero_timings(self, hero_id: int) -> dict[str, list[TimingBucket]] | None:
        """Get cached timing benchmarks for a hero. Returns None if no timing data.

        Returns dict of {item_internal_name: [TimingBucket, ...]} sorted by time.
        """
        return self._timing_benchmarks.get(hero_id)

    def set_hero_timings(self, hero_id: int, timings: dict[str, list[TimingBucket]]) -> None:
        """Update timing benchmarks for a single hero in the live cache.

        Called by the stale-while-revalidate timing service after a background
        refresh. Does NOT trigger ResponseCache clear (timing data changes slowly;
        5-min ResponseCache TTL is sufficient).
        """
        self._timing_benchmarks[hero_id] = timings

    def hero_id_to_name(self, hero_id: int) -> str:
        """Lookup hero localized_name by ID. Falls back to 'the enemy'."""
        hero = self._heroes.get(hero_id)
        return hero.localized_name if hero else "the enemy"

    def get_item_name_map(self) -> dict[int, str]:
        """Return {item_id: item.name} for all items.

        Used by context_builder._extract_top_items to resolve item IDs
        to display names without a DB query.
        """
        return {item_id: item.name for item_id, item in self._items.items()}

    def get_item_validation_map(self) -> dict[int, tuple[int | None, str]]:
        """Return {item_id: (cost, internal_name)} for all items.

        Used by recommender._validate_item_ids to verify item IDs and
        enrich recommendations with cost and slug data.
        """
        return {
            item_id: (item.cost, item.internal_name)
            for item_id, item in self._items.items()
        }

    def get_relevant_items(self, role: int) -> list[dict]:
        """Filter item catalog to ~40-50 items relevant to this role.

        Replicates matchup_service.get_relevant_items logic:
        - Excludes recipes, neutral items, zero-cost items
        - Applies role budget: max 10000g for cores (Pos 1-3), 5500g for
          supports (Pos 4-5)
        - Returns list of {"id", "name", "cost"} dicts sorted by cost,
          capped at 50

        Note: does not take hero_id -- the original function ignores it too.
        """
        max_cost = 10000 if role <= 3 else 5500
        filtered = [
            {"id": item.id, "name": item.name, "cost": item.cost}
            for item in self._items.values()
            if not item.is_recipe
            and not item.is_neutral
            and item.cost is not None
            and item.cost > 0
            and item.cost <= max_cost
        ]
        filtered.sort(key=lambda x: x["cost"])
        return filtered[:80]

    def get_neutral_items_by_tier(self) -> dict[int, list[dict]]:
        """Get all neutral items grouped by tier number.

        Replicates matchup_service.get_neutral_items_by_tier logic:
        - Filters is_neutral and tier is not None
        - Groups by tier
        - Returns {tier: [{id, name, internal_name, active_desc}]}
        """
        grouped: dict[int, list[dict]] = {}
        for item in self._items.values():
            if not item.is_neutral or item.tier is None:
                continue
            tier = item.tier
            if tier not in grouped:
                grouped[tier] = []
            grouped[tier].append({
                "id": item.id,
                "name": item.name,
                "internal_name": item.internal_name,
                "active_desc": item.active_desc or "",
            })
        return grouped


# Module-level singleton
data_cache = DataCache()

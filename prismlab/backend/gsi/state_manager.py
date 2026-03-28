"""In-memory singleton holding the latest parsed GSI game state.

The GsiStateManager receives raw GSI JSON dicts, parses them into a
normalized ParsedGsiState dataclass, and exposes the state for WebSocket
broadcast and connection status queries.
"""

import dataclasses
import time
from dataclasses import dataclass, field

from gsi.models import GsiBuilding, GsiPayload


@dataclass
class ParsedGsiState:
    """Normalized game state from GSI, ready for WebSocket broadcast."""

    hero_name: str = ""
    hero_id: int = 0
    hero_level: int = 0
    has_aghanims_shard: bool = False
    has_aghanims_scepter: bool = False
    gold: int = 0
    gpm: int = 0
    net_worth: int = 0
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    items_inventory: list[str] = field(default_factory=list)  # 6 slots
    items_backpack: list[str] = field(default_factory=list)  # 3 slots
    items_neutral: str = ""
    game_clock: int = 0
    game_state: str = ""
    match_id: str = ""
    team_side: str = ""
    is_alive: bool = True
    roshan_state: str = "alive"
    radiant_tower_count: int = 11
    dire_tower_count: int = 11
    timestamp: float = 0.0


def _normalize_item_name(raw_name: str) -> str:
    """Normalize GSI item name: strip 'item_' prefix, convert 'empty' to ''."""
    if raw_name == "empty":
        return ""
    if raw_name.startswith("item_"):
        return raw_name[5:]  # len("item_") == 5
    return raw_name


def _normalize_hero_name(raw_name: str) -> str:
    """Normalize GSI hero name: strip 'npc_dota_hero_' prefix."""
    prefix = "npc_dota_hero_"
    if raw_name.startswith(prefix):
        return raw_name[len(prefix):]
    return raw_name


def _count_alive_towers(buildings: dict[str, GsiBuilding]) -> int:
    """Count alive towers (health > 0) from a buildings dict, excluding rax/fort."""
    return sum(1 for key, b in buildings.items() if "tower" in key and b.health > 0)


class GsiStateManager:
    """Singleton managing the latest parsed GSI state."""

    def __init__(self) -> None:
        self._state: ParsedGsiState | None = None
        self._connected: bool = False
        self._last_update: float = 0.0

    @property
    def is_connected(self) -> bool:
        """True if we've received data recently (within 10s)."""
        return self._connected and (time.time() - self._last_update) < 10.0

    def update(self, raw: dict) -> None:
        """Parse raw GSI JSON dict and update internal state."""
        payload = GsiPayload.model_validate(raw)

        # Extract hero info
        hero_name = ""
        hero_id = 0
        hero_level = 0
        is_alive = True
        has_aghanims_shard = False
        has_aghanims_scepter = False
        if payload.hero:
            hero_name = _normalize_hero_name(payload.hero.name)
            hero_id = payload.hero.id
            hero_level = payload.hero.level
            is_alive = payload.hero.alive
            has_aghanims_shard = payload.hero.aghanims_shard
            has_aghanims_scepter = payload.hero.aghanims_scepter

        # Extract player info
        gold = 0
        gpm = 0
        net_worth = 0
        kills = 0
        deaths = 0
        assists = 0
        team_side = ""
        if payload.player:
            gold = payload.player.gold
            gpm = payload.player.gpm
            net_worth = payload.player.net_worth
            kills = payload.player.kills
            deaths = payload.player.deaths
            assists = payload.player.assists
            team_side = payload.player.team_name

        # Extract map info
        game_clock = 0
        game_state = ""
        match_id = ""
        roshan_state = "alive"
        if payload.map:
            game_clock = int(payload.map.clock_time)
            game_state = payload.map.game_state
            match_id = payload.map.matchid
            roshan_state = payload.map.roshan_state or "alive"

        # Extract buildings / tower counts
        radiant_tower_count = 11
        dire_tower_count = 11
        if payload.buildings is not None:
            radiant_tower_count = _count_alive_towers(payload.buildings.radiant)
            dire_tower_count = _count_alive_towers(payload.buildings.dire)

        # Extract items
        items_inventory: list[str] = []
        items_backpack: list[str] = []
        items_neutral = ""
        if payload.items:
            # Inventory: slot0-slot5
            for i in range(6):
                slot = getattr(payload.items, f"slot{i}")
                items_inventory.append(_normalize_item_name(slot.name))

            # Backpack: slot6-slot8
            for i in range(6, 9):
                slot = getattr(payload.items, f"slot{i}")
                items_backpack.append(_normalize_item_name(slot.name))

            # Neutral item
            items_neutral = _normalize_item_name(payload.items.neutral0.name)

        self._state = ParsedGsiState(
            hero_name=hero_name,
            hero_id=hero_id,
            hero_level=hero_level,
            has_aghanims_shard=has_aghanims_shard,
            has_aghanims_scepter=has_aghanims_scepter,
            gold=gold,
            gpm=gpm,
            net_worth=net_worth,
            kills=kills,
            deaths=deaths,
            assists=assists,
            items_inventory=items_inventory,
            items_backpack=items_backpack,
            items_neutral=items_neutral,
            game_clock=game_clock,
            game_state=game_state,
            match_id=match_id,
            team_side=team_side,
            is_alive=is_alive,
            roshan_state=roshan_state,
            radiant_tower_count=radiant_tower_count,
            dire_tower_count=dire_tower_count,
            timestamp=time.time(),
        )
        self._last_update = time.time()
        self._connected = True

    def get_state(self) -> ParsedGsiState | None:
        """Return the current parsed state, or None if no data received yet."""
        return self._state

    def get_connection_info(self) -> dict:
        """Connection metadata for status indicator."""
        return {
            "connected": self.is_connected,
            "last_update": self._last_update,
            "game_clock": self._state.game_clock if self._state else None,
            "game_state": self._state.game_state if self._state else None,
        }

    def to_broadcast_dict(self) -> dict | None:
        """Serialize current state for WebSocket broadcast, or None if no state."""
        if self._state is None:
            return None
        return dataclasses.asdict(self._state)


# Module-level singleton
gsi_state_manager = GsiStateManager()

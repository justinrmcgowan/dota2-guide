"""Pydantic v2 models for parsing Dota 2 GSI JSON payloads.

The GSI (Game State Integration) protocol sends HTTP POST requests with JSON
payloads describing the current game state. These models parse the player-mode
(flat, not spectator-nested) payload structure.
"""

from pydantic import BaseModel, ConfigDict, Field


class GsiItemSlot(BaseModel):
    """A single item slot in the GSI payload."""

    name: str = "empty"
    purchaser: int = 0
    can_cast: bool = False
    cooldown: float = 0
    passive: bool = False
    charges: int = 0


class GsiMap(BaseModel):
    """Map/game state information from GSI."""

    name: str = ""
    matchid: str = ""
    game_time: float = 0
    clock_time: float = 0
    daytime: bool = True
    game_state: str = ""
    paused: bool = False
    roshan_state: str = "alive"
    roshan_state_end_seconds: float = 0
    win_team: str = ""

    model_config = ConfigDict(extra="allow")


class GsiPlayer(BaseModel):
    """Player stats from GSI."""

    steamid: str = ""
    name: str = ""
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    last_hits: int = 0
    denies: int = 0
    gold: int = 0
    gold_reliable: int = 0
    gold_unreliable: int = 0
    gpm: int = 0
    xpm: int = 0
    net_worth: int = 0
    team_name: str = ""

    model_config = ConfigDict(extra="allow")


class GsiHero(BaseModel):
    """Hero state from GSI."""

    id: int = 0
    name: str = ""
    level: int = 0
    alive: bool = True
    health: int = 0
    max_health: int = 0
    mana: int = 0
    max_mana: int = 0
    aghanims_shard: bool = False
    aghanims_scepter: bool = False

    model_config = ConfigDict(extra="allow")


class GsiItems(BaseModel):
    """All item slots from GSI: inventory (0-5), backpack (6-8), stash, TP, neutral."""

    slot0: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot1: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot2: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot3: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot4: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot5: GsiItemSlot = Field(default_factory=GsiItemSlot)
    slot6: GsiItemSlot = Field(default_factory=GsiItemSlot)  # backpack
    slot7: GsiItemSlot = Field(default_factory=GsiItemSlot)  # backpack
    slot8: GsiItemSlot = Field(default_factory=GsiItemSlot)  # backpack
    stash0: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash1: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash2: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash3: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash4: GsiItemSlot = Field(default_factory=GsiItemSlot)
    stash5: GsiItemSlot = Field(default_factory=GsiItemSlot)
    teleport0: GsiItemSlot = Field(default_factory=GsiItemSlot)
    neutral0: GsiItemSlot = Field(default_factory=GsiItemSlot)


class GsiBuilding(BaseModel):
    """A single building (tower, rax, fort) in the GSI buildings payload."""

    health: int = 0
    max_health: int = 0


class GsiBuildings(BaseModel):
    """Buildings data from GSI, keyed by building name per team."""

    radiant: dict[str, GsiBuilding] = {}
    dire: dict[str, GsiBuilding] = {}

    model_config = ConfigDict(extra="allow")


class GsiPayload(BaseModel):
    """Top-level GSI JSON payload (player mode, flat structure).

    Uses extra="allow" to accept unknown top-level fields like
    provider, previously, added, etc.
    """

    map: GsiMap | None = None
    player: GsiPlayer | None = None
    hero: GsiHero | None = None
    items: GsiItems | None = None
    buildings: GsiBuildings | None = None
    auth: dict | None = None

    model_config = ConfigDict(extra="allow")

import httpx


class OpenDotaClient:
    """Async HTTP client for the OpenDota API."""

    BASE_URL = "https://api.opendota.com/api"

    def __init__(self, api_key: str | None = None):
        self.params: dict[str, str] = {"api_key": api_key} if api_key else {}

    async def fetch_heroes(self) -> dict:
        """Fetch all hero constants from OpenDota.

        Returns a dict keyed by hero ID strings, e.g. {"1": {...}, "2": {...}}.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/constants/heroes",
                params=self.params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def fetch_items(self) -> dict:
        """Fetch all item constants from OpenDota.

        Returns a dict keyed by item internal names, e.g. {"blink": {...}, "black_king_bar": {...}}.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/constants/items",
                params=self.params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def fetch_hero_matchups(self, hero_id: int) -> list[dict]:
        """Fetch matchup stats for a hero from /heroes/{hero_id}/matchups.

        Returns list of {"hero_id": int, "games_played": int, "wins": int}.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/heroes/{hero_id}/matchups",
                params=self.params,
                timeout=15.0,
            )
            response.raise_for_status()
            return response.json()

    async def fetch_hero_item_popularity(self, hero_id: int) -> dict:
        """Fetch item popularity for a hero from /heroes/{hero_id}/itemPopularity.

        Returns {"start_game_items": {item_id: count}, "early_game_items": {...},
                 "mid_game_items": {...}, "late_game_items": {...}}.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/heroes/{hero_id}/itemPopularity",
                params=self.params,
                timeout=15.0,
            )
            response.raise_for_status()
            return response.json()

    async def fetch_abilities(self) -> dict:
        """Fetch all ability constants from OpenDota.

        Returns a dict keyed by ability internal name, e.g.
        {"antimage_mana_break": {"dname": "Mana Break", "behavior": "Passive", ...}}.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/constants/abilities",
                params=self.params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def fetch_hero_abilities(self) -> dict:
        """Fetch hero-to-ability mapping from OpenDota.

        Returns a dict keyed by hero internal name, e.g.
        {"npc_dota_hero_antimage": {"abilities": ["antimage_mana_break", ...], "talents": [...]}}.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/constants/hero_abilities",
                params=self.params,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def fetch_item_timings(self, hero_id: int) -> list[dict]:
        """Fetch item timing benchmark data for a hero from OpenDota scenarios.

        Returns list of dicts with keys: hero_id (int), item (str),
        time (int), games (str), wins (str).
        NOTE: games and wins are strings from the API, not ints.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/scenarios/itemTimings",
                params={**self.params, "hero_id": str(hero_id)},
                timeout=15.0,
            )
            response.raise_for_status()
            return response.json()

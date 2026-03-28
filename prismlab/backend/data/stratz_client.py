"""Stratz GraphQL client for live match data.

Uses raw httpx POST requests (no GraphQL library) to query the Stratz
GraphQL API. Primary data source for live match draft fetching -- faster
and broader coverage than OpenDota /live.

Two-step approach:
1. Query player(steamAccountId).matches(take:1) for the most recent match_id
2. Query live.match(id) for full live match data with all 10 players
"""

import logging

import httpx

logger = logging.getLogger(__name__)


class StratzClient:
    """Async GraphQL client for the Stratz API."""

    GRAPHQL_URL = "https://api.stratz.com/graphql"

    def __init__(self, token: str):
        self.headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "Prismlab/1.0",
            "Content-Type": "application/json",
        }

    async def fetch_player_last_match_id(self, account_id: int) -> int | None:
        """Get the most recent match_id for a player.

        Used as step 1 of the two-step live match lookup: find the match_id,
        then query live.match(id) to see if it's currently live.

        Args:
            account_id: Player's 32-bit Steam account ID.

        Returns:
            The match_id of the player's most recent match, or None if not found.
        """
        query = """
        query($steamAccountId: Long!) {
            player(steamAccountId: $steamAccountId) {
                matches(request: { take: 1 }) {
                    id
                }
            }
        }
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.GRAPHQL_URL,
                headers=self.headers,
                json={"query": query, "variables": {"steamAccountId": account_id}},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

        matches = data.get("data", {}).get("player", {}).get("matches", [])
        if matches:
            return matches[0].get("id")
        return None

    async def fetch_live_match(self, match_id: int) -> dict | None:
        """Fetch a specific live match by ID with full player data.

        Args:
            match_id: The Dota 2 match ID to look up in the live feed.

        Returns:
            The live match data dict with players, scores, game state, etc.
            Returns None if the match is not currently live.
        """
        query = """
        query($matchId: Long!) {
            live {
                match(id: $matchId) {
                    matchId
                    gameState
                    gameTime
                    radiantScore
                    direScore
                    players {
                        steamAccountId
                        heroId
                        isRadiant
                        playerSlot
                        position
                        numKills
                        numDeaths
                        numAssists
                        level
                        networth
                    }
                }
            }
        }
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.GRAPHQL_URL,
                headers=self.headers,
                json={"query": query, "variables": {"matchId": match_id}},
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("data", {}).get("live", {}).get("match")

    async def fetch_live_match_for_player(self, account_id: int) -> dict | None:
        """Two-step live match lookup for a specific player.

        1. Get the player's most recent match_id via player.matches(take:1)
        2. Query live.match(id) with that match_id
        3. If the match is live and has players, return it
        4. Otherwise return None (player not in a live match)

        Args:
            account_id: Player's 32-bit Steam account ID.

        Returns:
            Live match data dict if the player is in a live match, None otherwise.
        """
        try:
            match_id = await self.fetch_player_last_match_id(account_id)
            if match_id is None:
                logger.debug("Stratz: no recent match found for account %d", account_id)
                return None

            live_data = await self.fetch_live_match(match_id)
            if live_data and live_data.get("players"):
                logger.info(
                    "Stratz: found live match %d for account %d (state: %s)",
                    match_id,
                    account_id,
                    live_data.get("gameState", "unknown"),
                )
                return live_data

            logger.debug(
                "Stratz: match %d exists but is not live for account %d",
                match_id,
                account_id,
            )
            return None

        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Stratz HTTP error for account %d: %s", account_id, exc.response.status_code
            )
            return None
        except httpx.TimeoutException:
            logger.warning("Stratz timeout for account %d", account_id)
            return None

"""Cache warming module for pre-computing rules-only recommendations.

On server startup and after data refresh, pre-computes rules-only (fast path)
recommendations for all viable hero+role combos from HERO_ROLE_VIABLE.
Results are stored in L1 cache tier for instant serving of first requests.

Key design decisions:
- Uses HybridRecommender._fast_path() -- rules-only, no LLM calls, no DB queries for recs
- Playstyle is deterministic: alphabetically first for each role (stable, cache-friendly)
- Rate-limited via asyncio.sleep(0) every 10 combos to yield to event loop
- Individual failures logged and skipped -- never crashes the warming loop
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from engine.schemas import RecommendRequest, RecommendResponse

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular / load-time issues
TYPE_CHECKING = False
if TYPE_CHECKING:
    from engine.recommender import HierarchicalCache, HybridRecommender


class CacheWarmer:
    """Pre-computes rules-only recommendations for popular hero+role combos.

    Runs on startup and after data refresh to populate L1 cache tier.
    Uses fast-mode (rules-only) path -- no LLM calls, no DB queries for recs.
    """

    ROLE_DEFAULT_LANE: dict[int, str] = {
        1: "safe",
        2: "mid",
        3: "off",
        4: "off",
        5: "safe",
    }

    def __init__(
        self,
        recommender: HybridRecommender,
        cache: HierarchicalCache,
    ) -> None:
        self.recommender = recommender
        self.cache = cache

    def get_warmable_combos(self) -> list[tuple[int, int, str]]:
        """Return list of (hero_id, role, lane) for all viable hero+role combos.

        Sources combos from HERO_ROLE_VIABLE (the static Python mirror of
        heroPlaystyles.ts). Sorted by hero_id within each role for determinism.
        """
        from engine.hero_selector import HERO_ROLE_VIABLE

        combos: list[tuple[int, int, str]] = []
        for role in sorted(HERO_ROLE_VIABLE.keys()):
            hero_ids = HERO_ROLE_VIABLE[role]
            lane = self.ROLE_DEFAULT_LANE[role]
            for hero_id in sorted(hero_ids):
                combos.append((hero_id, role, lane))
        return combos

    async def warm(self, db: AsyncSession) -> int:
        """Pre-compute rules-only recs for all viable combos. Returns count warmed.

        Iterates all hero+role combos, constructs a minimal RecommendRequest with
        deterministic playstyle (alphabetically first for the role), runs the fast
        path, and stores the result in L1 cache.

        Individual failures are logged and skipped. Yields to event loop every 10
        combos to avoid blocking startup.
        """
        from engine.schemas import VALID_PLAYSTYLES

        combos = self.get_warmable_combos()
        warmed = 0

        for hero_id, role, lane in combos:
            playstyle = sorted(VALID_PLAYSTYLES[role])[0]
            request = RecommendRequest(
                hero_id=hero_id,
                role=role,
                playstyle=playstyle,
                side="radiant",
                lane=lane,
                lane_opponents=[],
                allies=[],
                all_opponents=[],
                mode="fast",
            )
            try:
                response = await self.recommender._fast_path(request, db)
                self.cache.set_l1(hero_id, role, lane, response)
                warmed += 1
            except Exception as e:
                logger.warning(
                    "Cache warm failed for hero=%d role=%d: %s",
                    hero_id,
                    role,
                    e,
                )

            # Rate limit: yield control every 10 combos to keep event loop responsive
            if (warmed + 1) % 10 == 0:
                await asyncio.sleep(0)

        logger.info(
            "Cache warming complete: %d/%d combos warmed", warmed, len(combos)
        )
        return warmed

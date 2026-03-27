"""Win condition classifier for Dota 2 draft archetypes.

Maps hero role distributions to macro strategy archetypes.
Consumes DataCache for hero role lookups -- zero DB queries.

Minimum 3 heroes required for classification; returns None below threshold.
"""
from __future__ import annotations
from dataclasses import dataclass
from data.cache import DataCache

ARCHETYPE_WEIGHTS: dict[str, dict[str, float]] = {
    "teamfight":       {"Disabler": 2.0, "Nuker": 1.5, "Initiator": 2.0, "Support": 0.5},
    "split-push":      {"Pusher": 3.0, "Carry": 1.0, "Escape": 0.5},
    "pick-off":        {"Assassin": 3.0, "Ganker": 2.5, "Escape": 1.0},
    "deathball":       {"Pusher": 2.0, "Initiator": 1.5, "Nuker": 1.0},
    "late-game scale": {"Carry": 2.5, "Durable": 1.0, "Support": 0.5},
}

MIN_HEROES = 3


@dataclass
class WinConditionResult:
    archetype: str           # "teamfight" | "split-push" | "pick-off" | "deathball" | "late-game scale"
    confidence: str          # "high" | "medium" | "low"
    archetype_scores: dict[str, float]  # raw scores for all 5 archetypes


def classify_draft(hero_ids: list[int], cache: DataCache) -> WinConditionResult | None:
    """Classify a team's macro archetype from hero IDs.

    Returns None if fewer than MIN_HEROES (3) hero IDs provided, or if
    fewer than 3 heroes have role data (insufficient signal).
    """
    if len(hero_ids) < MIN_HEROES:
        return None

    # Collect roles for heroes that have data
    heroes_with_roles: list[tuple[str, ...]] = []
    for hid in hero_ids:
        hero = cache.get_hero(hid)
        if hero and hero.roles:
            heroes_with_roles.append(hero.roles)

    if len(heroes_with_roles) < MIN_HEROES:
        return None

    # Score each archetype by summing role weight contributions
    scores: dict[str, float] = {archetype: 0.0 for archetype in ARCHETYPE_WEIGHTS}
    for roles in heroes_with_roles:
        for archetype, role_weights in ARCHETYPE_WEIGHTS.items():
            for role in roles:
                if role in role_weights:
                    scores[archetype] += role_weights[role]

    total_score = sum(scores.values())
    top_archetype = max(scores, key=lambda a: scores[a])

    if total_score > 0:
        top_fraction = scores[top_archetype] / total_score
    else:
        top_fraction = 0.0

    if top_fraction >= 0.60:
        confidence = "high"
    elif top_fraction >= 0.40:
        confidence = "medium"
    else:
        confidence = "low"

    return WinConditionResult(
        archetype=top_archetype,
        confidence=confidence,
        archetype_scores=scores,
    )

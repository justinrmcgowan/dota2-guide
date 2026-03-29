"""Hero suggestion scoring engine for Phase 31.

Scores all role-viable hero candidates using synergy and counter matrices
from DataCache._matrices. Called by POST /api/suggest-hero.

Key design decisions:
- HERO_ROLE_VIABLE is a static Python mirror of heroPlaystyles.ts.
  SOURCE OF TRUTH: heroPlaystyles.ts — keep in sync when map is updated.
- hero_id_to_index keys are JSON strings; cast to int before lookup (Pitfall 2).
- Empty/placeholder matrices degrade gracefully to 0.0 scores (Pitfall 1).
- counter[a][b] is raw win rate; subtract 0.5 to center around 0 (Pitfall 4).
- Composite score: synergy * 0.4 + counter * 0.4 (no individual_wr in Phase 31).
"""
from __future__ import annotations

import logging

from engine.schemas import HeroSuggestion, SuggestHeroRequest, SuggestHeroResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# HERO_ROLE_VIABLE: dict[role_int, set[hero_id_int]]
# SOURCE OF TRUTH: heroPlaystyles.ts — keep in sync when map is updated.
# Derived by parsing all "{hero_id}-{role}" keys in HERO_PLAYSTYLE_MAP.
# ---------------------------------------------------------------------------

HERO_ROLE_VIABLE: dict[int, set[int]] = {
    1: set(),
    2: set(),
    3: set(),
    4: set(),
    5: set(),
}

# Parsed from heroPlaystyles.ts HERO_PLAYSTYLE_MAP — format: "hero_id-role": "playstyle"
_HERO_PLAYSTYLE_ENTRIES: list[str] = [
    # 1: Anti-Mage
    "1-1",
    # 2: Axe
    "2-3",
    # 3: Bane
    "3-5",
    # 5: Crystal Maiden
    "5-5",
    # 6: Drow Ranger
    "6-1",
    # 7: Earthshaker
    "7-4",
    # 8: Juggernaut
    "8-1",
    # 9: Mirana
    "9-2",
    "9-4",
    # 10: Morphling
    "10-1",
    # 11: Shadow Fiend
    "11-2",
    # 12: Phantom Lancer
    "12-1",
    # 13: Puck
    "13-2",
    # 14: Pudge
    "14-4",
    # 15: Razor
    "15-2",
    # 16: Sand King
    "16-3",
    "16-4",
    # 17: Storm Spirit
    "17-2",
    # 18: Sven
    "18-1",
    # 19: Tiny
    "19-2",
    "19-3",
    # 20: Vengeful Spirit
    "20-4",
    "20-5",
    # 21: Windranger
    "21-2",
    # 22: Zeus
    "22-2",
    "22-4",
    # 23: Kunkka
    "23-2",
    # 25: Lina
    "25-2",
    "25-4",
    # 26: Lion
    "26-4",
    "26-5",
    # 27: Shadow Shaman
    "27-5",
    # 28: Slardar
    "28-3",
    # 29: Tidehunter
    "29-3",
    # 30: Witch Doctor
    "30-5",
    # 31: Lich
    "31-5",
    # 32: Riki
    "32-1",
    "32-4",
    # 33: Enigma
    "33-3",
    # 35: Sniper
    "35-1",
    "35-2",
    # 36: Necrophos
    "36-2",
    "36-3",
    # 37: Warlock
    "37-5",
    # 38: Beastmaster
    "38-3",
    # 39: Queen of Pain
    "39-2",
    # 40: Venomancer
    "40-3",
    "40-4",
    # 41: Faceless Void
    "41-1",
    # 42: Wraith King
    "42-1",
    "42-3",
    # 43: Death Prophet
    "43-2",
    # 44: Phantom Assassin
    "44-1",
    # 45: Pugna
    "45-2",
    "45-5",
    # 46: Templar Assassin
    "46-2",
    # 47: Viper
    "47-2",
    "47-3",
    # 48: Luna
    "48-1",
    # 49: Dragon Knight
    "49-2",
    "49-3",
    # 50: Dazzle
    "50-5",
    # 51: Clockwerk
    "51-3",
    "51-4",
    # 52: Leshrac
    "52-2",
    # 53: Nature's Prophet
    "53-3",
    # 54: Lifestealer
    "54-1",
    # 55: Dark Seer
    "55-3",
    # 56: Clinkz
    "56-1",
    "56-2",
    # 57: Omniknight
    "57-3",
    "57-5",
    # 58: Enchantress
    "58-4",
    "58-5",
    # 59: Huskar
    "59-2",
    # 60: Night Stalker
    "60-3",
    # 61: Broodmother
    "61-2",
    "61-3",
    # 62: Bounty Hunter
    "62-4",
    # 63: Weaver
    "63-1",
    # 64: Jakiro
    "64-5",
    # 65: Batrider
    "65-3",
    # 66: Chen
    "66-4",
    "66-5",
    # 67: Spectre
    "67-1",
    # 68: Ancient Apparition
    "68-4",
    "68-5",
    # 69: Doom
    "69-3",
    # 70: Ursa
    "70-1",
    # 71: Spirit Breaker
    "71-4",
    # 72: Gyrocopter
    "72-1",
    "72-2",
    # 73: Alchemist
    "73-1",
    "73-2",
    # 74: Invoker
    "74-2",
    # 75: Silencer
    "75-4",
    "75-5",
    # 76: Outworld Destroyer
    "76-2",
    # 77: Lycan
    "77-1",
    "77-2",
    # 78: Brewmaster
    "78-3",
    # 79: Shadow Demon
    "79-4",
    "79-5",
    # 80: Lone Druid
    "80-1",
    # 81: Chaos Knight
    "81-1",
    # 82: Meepo
    "82-2",
    # 83: Treant Protector
    "83-4",
    "83-5",
    # 84: Ogre Magi
    "84-4",
    "84-5",
    # 86: Rubick
    "86-4",
    "86-5",
    # 87: Disruptor
    "87-4",
    "87-5",
    # 88: Nyx Assassin
    "88-4",
    # 89: Naga Siren
    "89-1",
    # 90: Keeper of the Light
    "90-4",
    "90-5",
    # 91: Io
    "91-4",
    "91-5",
    # 92: Visage
    "92-2",
    "92-4",
    # 93: Slark
    "93-1",
    # 94: Medusa
    "94-1",
    "94-2",
    # 95: Troll Warlord
    "95-1",
    # 96: Centaur Warrunner
    "96-3",
    # 97: Magnus
    "97-2",
    "97-3",
    # 98: Timbersaw
    "98-3",
    # 99: Bristleback
    "99-3",
    # 100: Tusk
    "100-4",
    # 101: Skywrath Mage
    "101-4",
    # 102: Abaddon
    "102-3",
    "102-5",
    # 103: Elder Titan
    "103-4",
    # 104: Legion Commander
    "104-3",
    # 106: Ember Spirit
    "106-2",
    # 107: Earth Spirit
    "107-4",
    # 108: Underlord
    "108-3",
    # 109: Terrorblade
    "109-1",
    # 110: Phoenix
    "110-3",
    "110-4",
    # 111: Oracle
    "111-5",
    # 112: Winter Wyvern
    "112-4",
    "112-5",
    # 113: Arc Warden
    "113-1",
    "113-2",
    # 114: Monkey King
    "114-1",
    "114-2",
    # 119: Dark Willow
    "119-4",
    # 120: Pangolier
    "120-3",
    # 121: Grimstroke
    "121-4",
    "121-5",
    # 123: Hoodwink
    "123-4",
    # 126: Void Spirit
    "126-2",
    # 128: Snapfire
    "128-4",
    "128-5",
    # 129: Mars
    "129-3",
    # 131: Ringmaster
    "131-4",
    # 135: Dawnbreaker
    "135-3",
    "135-5",
    # 136: Marci
    "136-3",
    "136-4",
    # 137: Primal Beast
    "137-3",
    # 138: Muerta
    "138-1",
    "138-2",
]

# Build HERO_ROLE_VIABLE from the entries list
for _entry in _HERO_PLAYSTYLE_ENTRIES:
    _hero_id_str, _role_str = _entry.split("-")
    _hero_id = int(_hero_id_str)
    _role = int(_role_str)
    HERO_ROLE_VIABLE[_role].add(_hero_id)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_bracket_matrices(
    cache: object, bracket: int
) -> tuple[list, list, dict[int, int]]:
    """Return (synergy, counter, hero_id_to_index) for the given bracket.

    hero_id_to_index keys are cast to int to handle JSON string keys (Pitfall 2).
    Returns empty structures when matrices are absent (placeholder scenario).
    """
    bracket_data = getattr(cache, "_matrices", {}).get(bracket, {})
    raw_mapping = bracket_data.get("hero_id_to_index", {})
    hero_id_to_index: dict[int, int] = {int(k): v for k, v in raw_mapping.items()}
    synergy: list = bracket_data.get("synergy", [])
    counter: list = bracket_data.get("counter", [])
    return synergy, counter, hero_id_to_index


def score_candidates(
    candidate_ids: list[int],
    ally_ids: list[int],
    enemy_ids: list[int],
    synergy: list,
    counter: list,
    hero_id_to_index: dict[int, int],
) -> dict[int, tuple[float, float, float]]:
    """Score each candidate hero using synergy + counter matrices.

    Returns dict mapping hero_id -> (composite, synergy_score, counter_score).

    Graceful degradation:
    - Empty synergy/counter arrays → all scores 0.0 (Pitfall 1).
    - Hero not in hero_id_to_index → score 0.0, no KeyError.
    - IndexError caught as final safety net (Pitfall 1).
    """
    if not synergy or not counter:
        return {hid: (0.0, 0.0, 0.0) for hid in candidate_ids}

    results: dict[int, tuple[float, float, float]] = {}

    for hid in candidate_ids:
        c_idx = hero_id_to_index.get(hid)
        if c_idx is None:
            results[hid] = (0.0, 0.0, 0.0)
            continue

        try:
            # Synergy with allies
            syn_vals: list[float] = []
            for a in ally_ids:
                a_idx = hero_id_to_index.get(a)
                if a_idx is not None:
                    cell = synergy[c_idx][a_idx]
                    if cell is not None:
                        syn_vals.append(float(cell))

            # Counter vs enemies (center raw win rate around 0)
            ctr_vals: list[float] = []
            for e in enemy_ids:
                e_idx = hero_id_to_index.get(e)
                if e_idx is not None:
                    cell = counter[c_idx][e_idx]
                    if cell is not None:
                        ctr_vals.append(float(cell) - 0.5)

            syn_score = sum(syn_vals) / len(syn_vals) if syn_vals else 0.0
            ctr_score = sum(ctr_vals) / len(ctr_vals) if ctr_vals else 0.0
            composite = syn_score * 0.4 + ctr_score * 0.4

        except IndexError:
            # Safety net: malformed matrix dimensions — treat as unavailable
            logger.debug(
                "score_candidates: IndexError for hero_id=%d, c_idx=%d", hid, c_idx
            )
            composite, syn_score, ctr_score = 0.0, 0.0, 0.0

        results[hid] = (composite, syn_score, ctr_score)

    return results


# ---------------------------------------------------------------------------
# HeroSelector class
# ---------------------------------------------------------------------------


class HeroSelector:
    """Scores hero candidates for role-based suggestions using DataCache matrices.

    Stateless — no instance state; all data comes from cache and request.
    """

    def get_suggestions(
        self, request: SuggestHeroRequest, cache: object
    ) -> SuggestHeroResponse:
        """Return top-N ranked hero suggestions for the given role and context.

        Steps:
        1. Get all heroes from cache.
        2. Filter by role viability (HERO_ROLE_VIABLE).
        3. Remove excluded hero IDs.
        4. Determine matrices_available from cache state.
        5. Score candidates using synergy/counter matrices.
        6. Sort descending by composite score, then ascending by name (stable tie-break).
        7. Return top_n as HeroSuggestion objects.
        """
        all_heroes = list(cache.get_all_heroes())

        # Role filter: use HERO_ROLE_VIABLE; fall back to all heroes if pool < 5
        viable_ids: set[int] = HERO_ROLE_VIABLE.get(request.role, set())
        if len(viable_ids) < 5:
            viable_ids = {h.id for h in all_heroes}

        # Build candidate list: viable and not excluded
        excluded: set[int] = set(request.excluded_hero_ids)
        candidates = [
            h for h in all_heroes if h.id in viable_ids and h.id not in excluded
        ]

        # Determine matrices_available
        matrices_dict = getattr(cache, "_matrices", {})
        bracket_data = matrices_dict.get(request.bracket, {})
        matrices_available: bool = bool(matrices_dict) and bool(
            bracket_data.get("synergy")
        )

        # Load matrices and score
        synergy, counter, hero_id_to_index = _get_bracket_matrices(
            cache, request.bracket
        )
        candidate_ids = [h.id for h in candidates]
        scores = score_candidates(
            candidate_ids=candidate_ids,
            ally_ids=request.ally_ids,
            enemy_ids=request.enemy_ids,
            synergy=synergy,
            counter=counter,
            hero_id_to_index=hero_id_to_index,
        )

        # Sort: descending by composite score, then ascending by localized_name
        sorted_candidates = sorted(
            candidates,
            key=lambda h: (-scores.get(h.id, (0.0, 0.0, 0.0))[0], h.localized_name),
        )

        # Build top_n HeroSuggestion objects
        suggestions: list[HeroSuggestion] = []
        for hero in sorted_candidates[: request.top_n]:
            composite, syn_score, ctr_score = scores.get(hero.id, (0.0, 0.0, 0.0))
            suggestions.append(
                HeroSuggestion(
                    hero_id=hero.id,
                    hero_name=hero.localized_name,
                    internal_name=hero.internal_name,
                    icon_url=hero.icon_url,
                    score=round(composite, 4),
                    synergy_score=round(syn_score, 4),
                    counter_score=round(ctr_score, 4),
                )
            )

        return SuggestHeroResponse(
            suggestions=suggestions,
            matrices_available=matrices_available,
        )

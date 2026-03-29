"""Tests for HeroSelector and HERO_ROLE_VIABLE (Phase 31).

TDD RED phase — tests written before implementation.
"""
import pytest
from unittest.mock import MagicMock


# ---------------------------------------------------------------------------
# HERO_ROLE_VIABLE tests
# ---------------------------------------------------------------------------


def test_hero_role_viable_has_all_five_roles():
    """HERO_ROLE_VIABLE must have keys 1, 2, 3, 4, 5."""
    from engine.hero_selector import HERO_ROLE_VIABLE

    assert set(HERO_ROLE_VIABLE.keys()) == {1, 2, 3, 4, 5}


def test_hero_role_viable_pos1_contains_anti_mage():
    """Anti-Mage (hero_id=1) must be in role 1 set."""
    from engine.hero_selector import HERO_ROLE_VIABLE

    assert 1 in HERO_ROLE_VIABLE[1], "Anti-Mage (id=1) should be viable Pos 1"


def test_hero_role_viable_pos5_contains_crystal_maiden():
    """Crystal Maiden (hero_id=5) must be in role 5 set."""
    from engine.hero_selector import HERO_ROLE_VIABLE

    assert 5 in HERO_ROLE_VIABLE[5], "Crystal Maiden (id=5) should be viable Pos 5"


def test_hero_role_viable_sets_are_non_empty():
    """Every role must have at least one hero viable."""
    from engine.hero_selector import HERO_ROLE_VIABLE

    for role, heroes in HERO_ROLE_VIABLE.items():
        assert len(heroes) > 0, f"Role {role} has no viable heroes"


def test_hero_role_viable_axe_is_pos3():
    """Axe (hero_id=2) must be in role 3 set."""
    from engine.hero_selector import HERO_ROLE_VIABLE

    assert 2 in HERO_ROLE_VIABLE[3], "Axe (id=2) should be viable Pos 3"


# ---------------------------------------------------------------------------
# score_candidates() tests
# ---------------------------------------------------------------------------


def test_score_candidates_empty_matrices_returns_zero():
    """When synergy/counter are empty, all scores should be 0.0."""
    from engine.hero_selector import score_candidates

    results = score_candidates(
        candidate_ids=[1, 2, 3],
        ally_ids=[],
        enemy_ids=[],
        synergy=[],
        counter=[],
        hero_id_to_index={},
    )
    assert results == {1: (0.0, 0.0, 0.0), 2: (0.0, 0.0, 0.0), 3: (0.0, 0.0, 0.0)}


def test_score_candidates_missing_hero_index_returns_zero():
    """Hero not in hero_id_to_index gets score 0.0 without error."""
    from engine.hero_selector import score_candidates

    # Provide non-empty matrices but hero_id_to_index doesn't contain candidate
    synergy = [[0.1, 0.2], [0.2, 0.1]]
    counter = [[0.55, 0.45], [0.60, 0.50]]
    hero_id_to_index = {1: 0, 2: 1}

    results = score_candidates(
        candidate_ids=[999],  # Not in hero_id_to_index
        ally_ids=[],
        enemy_ids=[],
        synergy=synergy,
        counter=counter,
        hero_id_to_index=hero_id_to_index,
    )
    assert results[999] == (0.0, 0.0, 0.0)


def test_score_candidates_with_allies_and_enemies():
    """Score includes synergy with allies and counter vs enemies."""
    from engine.hero_selector import score_candidates

    # Simple 3-hero matrices
    # synergy[c][a] for candidate 0 vs ally 1: 0.2
    synergy = [
        [0.0, 0.2, 0.1],
        [0.2, 0.0, 0.15],
        [0.1, 0.15, 0.0],
    ]
    # counter[c][e] — win rate (subtract 0.5 to center)
    # counter[0][2] = 0.6 -> centered = 0.1
    counter = [
        [0.5, 0.55, 0.6],
        [0.45, 0.5, 0.52],
        [0.4, 0.48, 0.5],
    ]
    hero_id_to_index = {1: 0, 2: 1, 3: 2}

    # Candidate 1 (idx=0), ally 2 (idx=1), enemy 3 (idx=2)
    results = score_candidates(
        candidate_ids=[1],
        ally_ids=[2],
        enemy_ids=[3],
        synergy=synergy,
        counter=counter,
        hero_id_to_index=hero_id_to_index,
    )
    composite, syn_score, ctr_score = results[1]
    # syn = 0.2 (synergy[0][1]), ctr = 0.6 - 0.5 = 0.1 (counter[0][2])
    assert abs(syn_score - 0.2) < 1e-6
    assert abs(ctr_score - 0.1) < 1e-6
    # composite = 0.2 * 0.4 + 0.1 * 0.4 = 0.08 + 0.04 = 0.12
    assert abs(composite - 0.12) < 1e-6


def test_score_candidates_no_allies_no_enemies():
    """No allies, no enemies → synergy and counter scores both 0.0."""
    from engine.hero_selector import score_candidates

    synergy = [[0.0, 0.3], [0.3, 0.0]]
    counter = [[0.5, 0.7], [0.3, 0.5]]
    hero_id_to_index = {1: 0, 2: 1}

    results = score_candidates(
        candidate_ids=[1],
        ally_ids=[],
        enemy_ids=[],
        synergy=synergy,
        counter=counter,
        hero_id_to_index=hero_id_to_index,
    )
    composite, syn_score, ctr_score = results[1]
    assert syn_score == 0.0
    assert ctr_score == 0.0
    assert composite == 0.0


def test_score_candidates_string_keys_in_hero_id_to_index():
    """score_candidates itself takes already-cast int keys (helper casts)."""
    from engine.hero_selector import score_candidates

    synergy = [[0.0, 0.25], [0.25, 0.0]]
    counter = [[0.5, 0.6], [0.4, 0.5]]
    # Keys already cast to int
    hero_id_to_index = {1: 0, 2: 1}

    results = score_candidates(
        candidate_ids=[1],
        ally_ids=[],
        enemy_ids=[2],
        synergy=synergy,
        counter=counter,
        hero_id_to_index=hero_id_to_index,
    )
    # counter[0][1] - 0.5 = 0.6 - 0.5 = 0.1
    _, _, ctr_score = results[1]
    assert abs(ctr_score - 0.1) < 1e-6


# ---------------------------------------------------------------------------
# HeroSelector.get_suggestions() tests
# ---------------------------------------------------------------------------


def _make_mock_hero(hero_id: int, name: str, internal: str) -> MagicMock:
    h = MagicMock()
    h.id = hero_id
    h.localized_name = name
    h.internal_name = internal
    h.icon_url = f"https://cdn.example/{internal}.png"
    return h


def _make_empty_cache() -> MagicMock:
    cache = MagicMock()
    cache._matrices = {}
    cache.get_all_heroes.return_value = []
    return cache


def test_get_suggestions_empty_cache_returns_empty():
    """Empty cache (no heroes, no matrices) returns empty suggestion list."""
    from engine.hero_selector import HeroSelector
    from engine.schemas import SuggestHeroRequest

    hs = HeroSelector()
    req = SuggestHeroRequest(role=1)
    cache = _make_empty_cache()

    resp = hs.get_suggestions(req, cache)
    assert resp.suggestions == []
    assert resp.matrices_available is False


def test_get_suggestions_matrices_available_false_when_empty():
    """matrices_available=False when cache._matrices is empty."""
    from engine.hero_selector import HeroSelector
    from engine.schemas import SuggestHeroRequest

    hs = HeroSelector()
    req = SuggestHeroRequest(role=1)
    cache = _make_empty_cache()

    resp = hs.get_suggestions(req, cache)
    assert resp.matrices_available is False


def test_get_suggestions_role_filters_heroes():
    """Only heroes viable for the requested role appear in suggestions."""
    from engine.hero_selector import HeroSelector, HERO_ROLE_VIABLE
    from engine.schemas import SuggestHeroRequest

    hs = HeroSelector()
    # Anti-Mage (1) is Pos 1; Axe (2) is Pos 3 — not Pos 1
    heroes = [
        _make_mock_hero(1, "Anti-Mage", "antimage"),
        _make_mock_hero(2, "Axe", "axe"),
    ]
    cache = MagicMock()
    cache._matrices = {}
    cache.get_all_heroes.return_value = heroes

    req = SuggestHeroRequest(role=1)
    resp = hs.get_suggestions(req, cache)

    result_ids = {s.hero_id for s in resp.suggestions}
    assert 1 in result_ids, "Anti-Mage should be in Pos 1 suggestions"
    assert 2 not in result_ids, "Axe should not be in Pos 1 suggestions"


def test_get_suggestions_excluded_hero_ids_removed():
    """excluded_hero_ids are not returned in suggestions."""
    from engine.hero_selector import HeroSelector
    from engine.schemas import SuggestHeroRequest

    hs = HeroSelector()
    heroes = [
        _make_mock_hero(1, "Anti-Mage", "antimage"),
        _make_mock_hero(6, "Drow Ranger", "drow_ranger"),
    ]
    cache = MagicMock()
    cache._matrices = {}
    cache.get_all_heroes.return_value = heroes

    req = SuggestHeroRequest(role=1, excluded_hero_ids=[1])
    resp = hs.get_suggestions(req, cache)

    result_ids = {s.hero_id for s in resp.suggestions}
    assert 1 not in result_ids, "Excluded hero (Anti-Mage) should not appear"


def test_get_suggestions_top_n_limits_results():
    """Only top_n results are returned."""
    from engine.hero_selector import HeroSelector
    from engine.schemas import SuggestHeroRequest

    # Give 10 Pos-1 viable heroes from HERO_ROLE_VIABLE
    from engine.hero_selector import HERO_ROLE_VIABLE
    pos1_ids = list(HERO_ROLE_VIABLE.get(1, set()))[:10]
    heroes = [_make_mock_hero(hid, f"Hero{hid}", f"hero{hid}") for hid in pos1_ids]

    cache = MagicMock()
    cache._matrices = {}
    cache.get_all_heroes.return_value = heroes

    hs = HeroSelector()
    req = SuggestHeroRequest(role=1, top_n=3)
    resp = hs.get_suggestions(req, cache)

    assert len(resp.suggestions) <= 3


def test_get_suggestions_alphabetical_order_when_no_matrices():
    """With empty matrices (all scores = 0), results are alphabetically sorted."""
    from engine.hero_selector import HeroSelector
    from engine.schemas import SuggestHeroRequest

    # Both heroes must be in HERO_ROLE_VIABLE[1]
    from engine.hero_selector import HERO_ROLE_VIABLE
    pos1_ids = sorted(HERO_ROLE_VIABLE.get(1, set()))

    # Use two heroes we know are in Pos 1 (Anti-Mage=1, Drow=6)
    heroes = [
        _make_mock_hero(6, "Drow Ranger", "drow_ranger"),
        _make_mock_hero(1, "Anti-Mage", "antimage"),
    ]

    cache = MagicMock()
    cache._matrices = {}
    cache.get_all_heroes.return_value = heroes

    hs = HeroSelector()
    req = SuggestHeroRequest(role=1)
    resp = hs.get_suggestions(req, cache)

    if len(resp.suggestions) >= 2:
        names = [s.hero_name for s in resp.suggestions]
        assert names == sorted(names), f"Expected alphabetical order, got {names}"


def test_get_suggestions_scores_rounded_to_4_decimals():
    """Scores are rounded to 4 decimal places."""
    from engine.hero_selector import HeroSelector
    from engine.schemas import SuggestHeroRequest

    from engine.hero_selector import HERO_ROLE_VIABLE
    pos1_ids = list(HERO_ROLE_VIABLE.get(1, set()))[:1]
    heroes = [_make_mock_hero(pos1_ids[0], "TestHero", "testhero")]

    cache = MagicMock()
    cache._matrices = {}
    cache.get_all_heroes.return_value = heroes

    hs = HeroSelector()
    req = SuggestHeroRequest(role=1)
    resp = hs.get_suggestions(req, cache)

    if resp.suggestions:
        s = resp.suggestions[0]
        # round(x, 4) should equal x for scores returned
        assert round(s.score, 4) == s.score
        assert round(s.synergy_score, 4) == s.synergy_score
        assert round(s.counter_score, 4) == s.counter_score


def test_get_suggestions_int_cast_applied_to_hero_id_to_index():
    """hero_id_to_index string keys from JSON are cast to int (no silent miss)."""
    from engine.hero_selector import HeroSelector, HERO_ROLE_VIABLE
    from engine.schemas import SuggestHeroRequest

    # Provide a matrix with string keys (as loaded from JSON)
    hero_id = list(HERO_ROLE_VIABLE.get(1, set()))[0]

    heroes = [_make_mock_hero(hero_id, f"Hero{hero_id}", f"hero{hero_id}")]
    # Use a small real matrix so scoring can run
    n = 5
    synergy = [[0.1 if i != j else 0.0 for j in range(n)] for i in range(n)]
    counter = [[0.55 if i != j else 0.5 for j in range(n)] for i in range(n)]
    hero_id_to_index_str_keys = {str(i): i for i in range(n)}
    # Overwrite with the actual hero_id
    hero_id_to_index_str_keys[str(hero_id)] = 0

    cache = MagicMock()
    cache._matrices = {
        2: {
            "hero_id_to_index": hero_id_to_index_str_keys,
            "synergy": synergy,
            "counter": counter,
        }
    }
    cache.get_all_heroes.return_value = heroes

    hs = HeroSelector()
    req = SuggestHeroRequest(role=1)
    resp = hs.get_suggestions(req, cache)

    # If int cast works, we should have suggestions (not empty)
    assert len(resp.suggestions) > 0
    assert resp.matrices_available is True

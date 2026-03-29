"""Tests for hero suggestion Pydantic schemas (Phase 31).

TDD RED phase — tests written before implementation.
"""
import pytest
from pydantic import ValidationError


def test_suggest_hero_request_defaults():
    """SuggestHeroRequest defaults: bracket=2, top_n=10, empty lists."""
    from engine.schemas import SuggestHeroRequest

    req = SuggestHeroRequest(role=1)
    assert req.bracket == 2
    assert req.top_n == 10
    assert req.ally_ids == []
    assert req.enemy_ids == []
    assert req.excluded_hero_ids == []


def test_suggest_hero_request_role_validation():
    """SuggestHeroRequest rejects role outside 1-5."""
    from engine.schemas import SuggestHeroRequest

    with pytest.raises(ValidationError):
        SuggestHeroRequest(role=0)
    with pytest.raises(ValidationError):
        SuggestHeroRequest(role=6)


def test_suggest_hero_request_ally_ids_max_length():
    """SuggestHeroRequest rejects ally_ids with more than 4 entries."""
    from engine.schemas import SuggestHeroRequest

    with pytest.raises(ValidationError):
        SuggestHeroRequest(role=1, ally_ids=[1, 2, 3, 4, 5])


def test_suggest_hero_request_enemy_ids_max_length():
    """SuggestHeroRequest rejects enemy_ids with more than 5 entries."""
    from engine.schemas import SuggestHeroRequest

    with pytest.raises(ValidationError):
        SuggestHeroRequest(role=1, enemy_ids=[1, 2, 3, 4, 5, 6])


def test_suggest_hero_request_top_n_bounds():
    """SuggestHeroRequest rejects top_n outside 1-30."""
    from engine.schemas import SuggestHeroRequest

    with pytest.raises(ValidationError):
        SuggestHeroRequest(role=1, top_n=0)
    with pytest.raises(ValidationError):
        SuggestHeroRequest(role=1, top_n=31)


def test_suggest_hero_request_bracket_bounds():
    """SuggestHeroRequest rejects bracket outside 1-4."""
    from engine.schemas import SuggestHeroRequest

    with pytest.raises(ValidationError):
        SuggestHeroRequest(role=1, bracket=0)
    with pytest.raises(ValidationError):
        SuggestHeroRequest(role=1, bracket=5)


def test_suggest_hero_request_all_fields():
    """SuggestHeroRequest accepts all valid fields."""
    from engine.schemas import SuggestHeroRequest

    req = SuggestHeroRequest(
        role=3,
        ally_ids=[1, 8],
        enemy_ids=[2, 6, 10],
        excluded_hero_ids=[1, 8, 2, 6, 10],
        top_n=15,
        bracket=3,
    )
    assert req.role == 3
    assert len(req.ally_ids) == 2
    assert len(req.enemy_ids) == 3
    assert req.top_n == 15
    assert req.bracket == 3


def test_hero_suggestion_model():
    """HeroSuggestion accepts all required fields."""
    from engine.schemas import HeroSuggestion

    s = HeroSuggestion(
        hero_id=1,
        hero_name="Anti-Mage",
        internal_name="antimage",
        icon_url="https://cdn.steam.example/antimage.png",
        score=0.1234,
        synergy_score=0.08,
        counter_score=0.05,
    )
    assert s.hero_id == 1
    assert s.hero_name == "Anti-Mage"
    assert s.icon_url is not None


def test_hero_suggestion_nullable_icon_url():
    """HeroSuggestion allows icon_url=None."""
    from engine.schemas import HeroSuggestion

    s = HeroSuggestion(
        hero_id=2,
        hero_name="Axe",
        internal_name="axe",
        icon_url=None,
        score=0.0,
        synergy_score=0.0,
        counter_score=0.0,
    )
    assert s.icon_url is None


def test_suggest_hero_response_model():
    """SuggestHeroResponse has suggestions list and matrices_available flag."""
    from engine.schemas import HeroSuggestion, SuggestHeroResponse

    resp = SuggestHeroResponse(
        suggestions=[
            HeroSuggestion(
                hero_id=1,
                hero_name="Anti-Mage",
                internal_name="antimage",
                icon_url=None,
                score=0.1,
                synergy_score=0.05,
                counter_score=0.05,
            )
        ],
        matrices_available=True,
    )
    assert len(resp.suggestions) == 1
    assert resp.matrices_available is True


def test_suggest_hero_response_empty():
    """SuggestHeroResponse accepts empty suggestions list."""
    from engine.schemas import SuggestHeroResponse

    resp = SuggestHeroResponse(suggestions=[], matrices_available=False)
    assert resp.suggestions == []
    assert resp.matrices_available is False

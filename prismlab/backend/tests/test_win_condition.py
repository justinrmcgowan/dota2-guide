"""Tests for WinConditionClassifier (WCON-01)."""
import pytest
from unittest.mock import MagicMock
from engine.win_condition import classify_draft, WinConditionResult
from data.cache import DataCache, HeroCached


def make_hero(id: int, roles: tuple[str, ...] | None) -> HeroCached:
    return HeroCached(
        id=id, name="", localized_name="Hero", internal_name="",
        primary_attr=None, attack_type=None, roles=roles,
        base_health=None, base_mana=None, base_armor=None,
        base_str=None, base_agi=None, base_int=None,
        str_gain=None, agi_gain=None, int_gain=None,
        base_attack_min=None, base_attack_max=None,
        attack_range=None, move_speed=None, img_url=None, icon_url=None,
    )


def make_cache(heroes: list[HeroCached]) -> DataCache:
    cache = MagicMock(spec=DataCache)
    hero_map = {h.id: h for h in heroes}
    cache.get_hero.side_effect = lambda hid: hero_map.get(hid)
    return cache


class TestClassifyDraft:
    def test_empty_returns_none(self):
        cache = make_cache([])
        assert classify_draft([], cache) is None

    def test_two_heroes_returns_none(self):
        heroes = [make_hero(1, ("Carry",)), make_hero(2, ("Support",))]
        cache = make_cache(heroes)
        assert classify_draft([1, 2], cache) is None

    def test_three_heroes_minimum(self):
        heroes = [make_hero(i, ("Disabler", "Nuker")) for i in range(1, 4)]
        cache = make_cache(heroes)
        result = classify_draft([1, 2, 3], cache)
        assert result is not None
        assert result.archetype in ("teamfight", "split-push", "pick-off", "deathball", "late-game scale")

    def test_teamfight_archetype(self):
        heroes = [
            make_hero(1, ("Disabler", "Initiator")),
            make_hero(2, ("Nuker", "Disabler")),
            make_hero(3, ("Initiator", "Nuker")),
        ]
        cache = make_cache(heroes)
        result = classify_draft([1, 2, 3], cache)
        assert result is not None
        assert result.archetype == "teamfight"

    def test_split_push_archetype(self):
        heroes = [
            make_hero(1, ("Pusher", "Carry")),
            make_hero(2, ("Pusher",)),
            make_hero(3, ("Pusher", "Escape")),
        ]
        cache = make_cache(heroes)
        result = classify_draft([1, 2, 3], cache)
        assert result is not None
        assert result.archetype == "split-push"

    def test_pick_off_archetype(self):
        heroes = [
            make_hero(1, ("Assassin", "Escape")),
            make_hero(2, ("Ganker", "Assassin")),
            make_hero(3, ("Ganker",)),
        ]
        cache = make_cache(heroes)
        result = classify_draft([1, 2, 3], cache)
        assert result is not None
        assert result.archetype == "pick-off"

    def test_late_game_scale_archetype(self):
        heroes = [
            make_hero(1, ("Carry", "Durable")),
            make_hero(2, ("Carry",)),
            make_hero(3, ("Carry", "Support")),
        ]
        cache = make_cache(heroes)
        result = classify_draft([1, 2, 3], cache)
        assert result is not None
        assert result.archetype == "late-game scale"

    def test_confidence_high(self):
        # All 3 heroes are pure teamfight -- should be high confidence
        heroes = [
            make_hero(i, ("Disabler", "Initiator", "Nuker")) for i in range(1, 4)
        ]
        cache = make_cache(heroes)
        result = classify_draft([1, 2, 3], cache)
        assert result is not None
        assert result.confidence == "high"

    def test_confidence_low_mixed(self):
        # Genuinely mixed: one of each archetype
        heroes = [
            make_hero(1, ("Pusher",)),   # split-push
            make_hero(2, ("Assassin",)), # pick-off
            make_hero(3, ("Disabler",)), # teamfight
        ]
        cache = make_cache(heroes)
        result = classify_draft([1, 2, 3], cache)
        assert result is not None
        assert result.confidence in ("low", "medium")

    def test_none_roles_skipped(self):
        heroes = [
            make_hero(1, None),
            make_hero(2, None),
            make_hero(3, ("Disabler", "Initiator")),
        ]
        cache = make_cache(heroes)
        # Should not crash; only 1 hero with roles means insufficient signal
        # We still return a result since 3 IDs were passed
        result = classify_draft([1, 2, 3], cache)
        # Either None or a result -- should not raise
        assert result is None or isinstance(result, WinConditionResult)

    def test_archetype_scores_present(self):
        heroes = [make_hero(i, ("Disabler",)) for i in range(1, 4)]
        cache = make_cache(heroes)
        result = classify_draft([1, 2, 3], cache)
        assert result is not None
        assert isinstance(result.archetype_scores, dict)
        assert len(result.archetype_scores) == 5  # all 5 archetypes scored

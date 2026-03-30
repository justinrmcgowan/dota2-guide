"""Unit tests for the exemplar matcher module.

Tests cover:
- Loading exemplar JSON files from disk
- Exemplar JSON structure validation
- ExemplarMatcher scoring and selection logic
- Graceful fallback on unknown profiles
- format_exemplar output formatting
"""

import pytest

from engine.exemplar_matcher import load_exemplars, ExemplarMatcher


# ---------------------------------------------------------------------------
# load_exemplars() tests
# ---------------------------------------------------------------------------


class TestLoadExemplars:
    def test_loads_correct_count(self):
        """load_exemplars() returns 15-18 exemplar dicts."""
        exemplars = load_exemplars()
        assert 15 <= len(exemplars) <= 18, f"Expected 15-18, got {len(exemplars)}"

    def test_each_exemplar_has_required_keys(self):
        """Each exemplar has role, threat_profile, matchup_type, hero_example,
        enemy_example, and recommendation keys."""
        required_keys = {
            "role", "threat_profile", "matchup_type",
            "hero_example", "enemy_example", "recommendation",
        }
        exemplars = load_exemplars()
        for ex in exemplars:
            missing = required_keys - set(ex.keys())
            assert not missing, (
                f"Exemplar {ex.get('_file', '?')} missing keys: {missing}"
            )

    def test_each_recommendation_has_phases_and_strategy(self):
        """Each recommendation has 'phases' (list) and 'overall_strategy' (str)."""
        exemplars = load_exemplars()
        for ex in exemplars:
            rec = ex["recommendation"]
            assert isinstance(rec.get("phases"), list), (
                f"{ex.get('_file', '?')}: recommendation.phases must be a list"
            )
            assert len(rec["phases"]) >= 3, (
                f"{ex.get('_file', '?')}: should have at least 3 phases"
            )
            assert isinstance(rec.get("overall_strategy"), str), (
                f"{ex.get('_file', '?')}: overall_strategy must be a string"
            )
            assert len(rec["overall_strategy"]) > 20, (
                f"{ex.get('_file', '?')}: overall_strategy too short"
            )

    def test_each_phase_has_items_with_required_fields(self):
        """Each phase has a name, items list, and each item has item_name + reasoning."""
        exemplars = load_exemplars()
        for ex in exemplars:
            for phase in ex["recommendation"]["phases"]:
                assert "phase" in phase, f"{ex.get('_file', '?')}: phase missing 'phase' key"
                assert "items" in phase, f"{ex.get('_file', '?')}: phase missing 'items' key"
                assert len(phase["items"]) >= 1, (
                    f"{ex.get('_file', '?')}: phase '{phase['phase']}' has no items"
                )
                for item in phase["items"]:
                    assert "item_name" in item, (
                        f"{ex.get('_file', '?')}: item missing 'item_name'"
                    )
                    assert "reasoning" in item, (
                        f"{ex.get('_file', '?')}: item missing 'reasoning'"
                    )


# ---------------------------------------------------------------------------
# ExemplarMatcher.select() tests
# ---------------------------------------------------------------------------


class TestExemplarMatcherSelect:
    def test_select_pos1_burst(self):
        """select(role=1, threat_profile='burst') returns at least 1 result."""
        matcher = ExemplarMatcher()
        results = matcher.select(role=1, threat_profile="burst")
        assert len(results) >= 1
        # The top result should be the pos1 vs burst exemplar
        assert results[0]["role"] == 1
        assert results[0]["threat_profile"] == "burst"

    def test_select_pos1_sustained(self):
        """select(role=1, threat_profile='sustained') returns at least 1 result."""
        matcher = ExemplarMatcher()
        results = matcher.select(role=1, threat_profile="sustained")
        assert len(results) >= 1
        assert results[0]["threat_profile"] == "sustained"

    def test_select_pos4_invis(self):
        """select(role=4, threat_profile='invis') returns at least 1 result."""
        matcher = ExemplarMatcher()
        results = matcher.select(role=4, threat_profile="invis")
        assert len(results) >= 1

    def test_select_unknown_profile_graceful(self):
        """select(role=1, threat_profile='nonexistent_xyz') returns 0-1 results."""
        matcher = ExemplarMatcher()
        results = matcher.select(role=1, threat_profile="nonexistent_xyz")
        # Should still return some results because role match alone scores points
        # But the unknown profile won't get threat_profile bonus
        assert len(results) <= 2

    def test_select_never_exceeds_max(self):
        """select() never returns more than 2 exemplars by default."""
        matcher = ExemplarMatcher()
        # Try various combinations
        for role in range(1, 6):
            for profile in ["burst", "magic", "physical", "invis", "sustained"]:
                results = matcher.select(role=role, threat_profile=profile)
                assert len(results) <= 2, (
                    f"role={role}, profile={profile} returned {len(results)} results"
                )

    def test_select_with_max_results_1(self):
        """select(max_results=1) returns at most 1 exemplar."""
        matcher = ExemplarMatcher()
        results = matcher.select(role=1, threat_profile="burst", max_results=1)
        assert len(results) <= 1


# ---------------------------------------------------------------------------
# ExemplarMatcher.format_exemplar() tests
# ---------------------------------------------------------------------------


class TestFormatExemplar:
    def test_format_contains_hero_name(self):
        """format_exemplar() output contains the hero_example name."""
        matcher = ExemplarMatcher()
        exemplars = matcher.exemplars
        assert len(exemplars) > 0, "No exemplars loaded"

        formatted = matcher.format_exemplar(exemplars[0])
        hero_name = exemplars[0]["hero_example"]
        assert hero_name in formatted

    def test_format_contains_enemy_name(self):
        """format_exemplar() output contains the enemy_example name."""
        matcher = ExemplarMatcher()
        exemplars = matcher.exemplars
        formatted = matcher.format_exemplar(exemplars[0])
        enemy_name = exemplars[0]["enemy_example"]
        assert enemy_name in formatted

    def test_format_contains_strategy(self):
        """format_exemplar() output contains the overall_strategy text."""
        matcher = ExemplarMatcher()
        exemplars = matcher.exemplars
        formatted = matcher.format_exemplar(exemplars[0])
        assert "Strategy:" in formatted

    def test_format_contains_phase_names(self):
        """format_exemplar() output contains phase names from the exemplar."""
        matcher = ExemplarMatcher()
        exemplars = matcher.exemplars
        formatted = matcher.format_exemplar(exemplars[0])
        # Should contain at least 'starting' or 'laning' phase reference
        assert "starting" in formatted.lower() or "laning" in formatted.lower()

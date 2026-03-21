"""Unit tests for the deterministic rules engine."""

import pytest

from engine.schemas import RecommendRequest
from engine.rules import RulesEngine, HERO_NAMES


def _make_request(
    hero_id: int = 1,
    role: int = 1,
    lane_opponents: list[int] | None = None,
    playstyle: str = "aggressive",
    side: str = "radiant",
    lane: str = "safe",
) -> RecommendRequest:
    """Create a minimal valid RecommendRequest for testing."""
    return RecommendRequest(
        hero_id=hero_id,
        role=role,
        playstyle=playstyle,
        side=side,
        lane=lane,
        lane_opponents=lane_opponents or [],
    )


@pytest.fixture
def engine() -> RulesEngine:
    return RulesEngine()


class TestMagicStickRule:
    def test_magic_stick_vs_spammer(self, engine: RulesEngine):
        """Magic Stick recommended against Bristleback (spell-spammer)."""
        req = _make_request(lane_opponents=[69])
        results = engine.evaluate(req)
        stick_results = [r for r in results if r.item_id == 36]
        assert len(stick_results) >= 1
        assert stick_results[0].item_name == "Magic Stick"
        assert stick_results[0].phase == "laning"
        assert stick_results[0].priority == "core"

    def test_magic_stick_vs_zeus(self, engine: RulesEngine):
        """Magic Stick recommended against Zeus."""
        req = _make_request(lane_opponents=[22])
        results = engine.evaluate(req)
        stick_results = [r for r in results if r.item_id == 36]
        assert len(stick_results) >= 1

    def test_magic_stick_vs_non_spammer(self, engine: RulesEngine):
        """Magic Stick NOT recommended against non-spell-spammer."""
        req = _make_request(lane_opponents=[1])  # Anti-Mage is not a spell-spammer
        results = engine.evaluate(req)
        stick_results = [r for r in results if r.item_id == 36]
        assert len(stick_results) == 0


class TestNoMatchReturnsEmpty:
    def test_no_match_returns_empty(self, engine: RulesEngine):
        """No opponent-specific rules fire when lane_opponents is empty."""
        req = _make_request(lane_opponents=[], role=1, hero_id=999)
        results = engine.evaluate(req)
        # Only role-based rules (boots, quelling blade) should fire
        # No opponent-dependent rules should produce results
        opponent_item_ids = {36, 116, 225, 235, 119, 102, 271, 40, 43, 249}
        opponent_results = [r for r in results if r.item_id in opponent_item_ids]
        assert len(opponent_results) == 0


class TestBkbRule:
    def test_bkb_vs_magic_heavy(self, engine: RulesEngine):
        """BKB recommended against Zeus (magic-heavy hero)."""
        req = _make_request(lane_opponents=[22], role=1)
        results = engine.evaluate(req)
        bkb_results = [r for r in results if r.item_id == 116]
        assert len(bkb_results) >= 1
        assert bkb_results[0].item_name == "Black King Bar"
        assert bkb_results[0].phase == "core"
        assert bkb_results[0].priority == "core"


class TestMkbRule:
    def test_mkb_vs_evasion(self, engine: RulesEngine):
        """MKB recommended against PA (evasion hero) for cores."""
        req = _make_request(lane_opponents=[12], role=1)
        results = engine.evaluate(req)
        mkb_results = [r for r in results if r.item_id == 225]
        assert len(mkb_results) >= 1
        assert mkb_results[0].item_name == "Monkey King Bar"
        assert mkb_results[0].phase == "core"
        assert mkb_results[0].priority == "situational"

    def test_mkb_not_for_supports(self, engine: RulesEngine):
        """MKB NOT recommended for supports (role 4-5)."""
        req = _make_request(lane_opponents=[12], role=5)
        results = engine.evaluate(req)
        mkb_results = [r for r in results if r.item_id == 225]
        assert len(mkb_results) == 0


class TestDustSentriesRule:
    def test_dust_for_support_vs_invis(self, engine: RulesEngine):
        """Dust/Sentries recommended for supports against Riki."""
        req = _make_request(lane_opponents=[32], role=5)
        results = engine.evaluate(req)
        detection_results = [r for r in results if r.item_id in (40, 43)]
        assert len(detection_results) >= 1
        detection_ids = {r.item_id for r in detection_results}
        # Should recommend both Dust and Sentries
        assert 40 in detection_ids or 43 in detection_ids

    def test_dust_not_for_cores(self, engine: RulesEngine):
        """Dust NOT recommended for cores (role 1-3) even against invis heroes."""
        req = _make_request(lane_opponents=[32], role=1)
        results = engine.evaluate(req)
        detection_results = [r for r in results if r.item_id in (40, 43)]
        assert len(detection_results) == 0


class TestBootsRule:
    def test_boots_by_role_carry(self, engine: RulesEngine):
        """Power Treads recommended for carries (role 1)."""
        req = _make_request(role=1)
        results = engine.evaluate(req)
        boots_results = [r for r in results if r.item_id == 48]
        assert len(boots_results) >= 1
        assert boots_results[0].item_name == "Power Treads"

    def test_boots_by_role_offlane(self, engine: RulesEngine):
        """Phase Boots recommended for offlaners (role 3)."""
        req = _make_request(role=3)
        results = engine.evaluate(req)
        boots_results = [r for r in results if r.item_id == 50]
        assert len(boots_results) >= 1
        assert boots_results[0].item_name == "Phase Boots"

    def test_boots_by_role_support(self, engine: RulesEngine):
        """Arcane Boots recommended for supports (role 4-5)."""
        req = _make_request(role=5)
        results = engine.evaluate(req)
        boots_results = [r for r in results if r.item_id == 180]
        assert len(boots_results) >= 1
        assert boots_results[0].item_name == "Arcane Boots"


class TestReasoningNamesEnemy:
    def test_reasoning_names_enemy(self, engine: RulesEngine):
        """Every opponent-triggered RuleResult reasoning names the enemy hero."""
        test_cases = [
            (69, 1, "Bristleback"),   # Magic Stick vs Bristleback
            (22, 1, "Zeus"),          # BKB vs Zeus
            (12, 1, "Phantom Assassin"),  # MKB vs PA
            (32, 5, "Riki"),          # Dust vs Riki
        ]
        for opponent_id, role, hero_name in test_cases:
            req = _make_request(lane_opponents=[opponent_id], role=role)
            results = engine.evaluate(req)
            # Find opponent-triggered results (exclude role-only results like boots)
            opponent_item_ids = {36, 116, 225, 235, 119, 102, 271, 40, 43, 249}
            opponent_results = [r for r in results if r.item_id in opponent_item_ids]
            for result in opponent_results:
                assert hero_name in result.reasoning, (
                    f"Reasoning for item {result.item_name} vs {hero_name} "
                    f"does not contain hero name. Got: {result.reasoning}"
                )


class TestSilverEdgeRule:
    def test_silver_edge_vs_bristleback(self, engine: RulesEngine):
        """Silver Edge recommended against Bristleback (critical passive)."""
        req = _make_request(lane_opponents=[69], role=1)
        results = engine.evaluate(req)
        se_results = [r for r in results if r.item_id == 249]
        assert len(se_results) >= 1
        assert "Bristleback" in se_results[0].reasoning


class TestSpiritVesselRule:
    def test_spirit_vessel_vs_alchemist(self, engine: RulesEngine):
        """Spirit Vessel recommended for offlaners against Alchemist."""
        req = _make_request(lane_opponents=[72], role=3)
        results = engine.evaluate(req)
        sv_results = [r for r in results if r.item_id == 271]
        assert len(sv_results) >= 1
        assert "Alchemist" in sv_results[0].reasoning


class TestQuellingBladeRule:
    def test_quelling_blade_for_melee_carry(self, engine: RulesEngine):
        """Quelling Blade recommended for Anti-Mage (melee carry, Pos 1)."""
        req = _make_request(hero_id=1, role=1)
        results = engine.evaluate(req)
        qb_results = [r for r in results if r.item_id == 29]
        assert len(qb_results) >= 1
        assert qb_results[0].phase == "starting"

    def test_quelling_blade_not_for_supports(self, engine: RulesEngine):
        """Quelling Blade NOT recommended for support role."""
        req = _make_request(hero_id=1, role=5)
        results = engine.evaluate(req)
        qb_results = [r for r in results if r.item_id == 29]
        assert len(qb_results) == 0


class TestRuleCount:
    def test_minimum_rule_count(self, engine: RulesEngine):
        """Engine has at least 10 rules registered."""
        assert len(engine._rules) >= 10

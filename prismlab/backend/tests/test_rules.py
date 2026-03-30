"""Unit tests for the deterministic rules engine."""

import pytest
import pytest_asyncio

from data.cache import data_cache
from engine.schemas import RecommendRequest, VALID_PLAYSTYLES, EnemyContext, compute_threat_level
from engine.rules import RulesEngine

pytestmark = pytest.mark.asyncio

# Default valid playstyle per role for test helpers
_DEFAULT_PLAYSTYLE: dict[int, str] = {
    1: "Aggressive",
    2: "Tempo",
    3: "Frontline",
    4: "Roamer",
    5: "Lane-protector",
}


def _make_request(
    hero_id: int = 1,
    role: int = 1,
    lane_opponents: list[int] | None = None,
    playstyle: str | None = None,
    side: str = "radiant",
    lane: str = "safe",
    enemy_context: list | None = None,
    all_opponents: list[int] | None = None,
    allies: list[int] | None = None,
) -> RecommendRequest:
    """Create a minimal valid RecommendRequest for testing."""
    if playstyle is None:
        playstyle = _DEFAULT_PLAYSTYLE.get(role, "Aggressive")
    return RecommendRequest(
        hero_id=hero_id,
        role=role,
        playstyle=playstyle,
        side=side,
        lane=lane,
        lane_opponents=lane_opponents or [],
        all_opponents=all_opponents or [],
        allies=allies or [],
        enemy_context=enemy_context or [],
    )


@pytest_asyncio.fixture
async def engine(test_db_session) -> RulesEngine:
    return RulesEngine(cache=data_cache)


class TestMagicStickRule:
    async def test_magic_stick_vs_spammer(self, engine: RulesEngine):
        """Magic Stick recommended against Bristleback (spell-spammer)."""
        req = _make_request(lane_opponents=[69])
        results = engine.evaluate(req)
        stick_results = [r for r in results if r.item_id == 36]
        assert len(stick_results) >= 1
        assert stick_results[0].item_name == "Magic Stick"
        assert stick_results[0].phase == "laning"
        assert stick_results[0].priority == "core"

    async def test_magic_stick_vs_zeus(self, engine: RulesEngine):
        """Magic Stick recommended against Zeus."""
        req = _make_request(lane_opponents=[22])
        results = engine.evaluate(req)
        stick_results = [r for r in results if r.item_id == 36]
        assert len(stick_results) >= 1

    async def test_magic_stick_vs_non_spammer(self, engine: RulesEngine):
        """Magic Stick NOT recommended against non-spell-spammer."""
        req = _make_request(lane_opponents=[1])  # Anti-Mage is not a spell-spammer
        results = engine.evaluate(req)
        stick_results = [r for r in results if r.item_id == 36]
        assert len(stick_results) == 0


class TestNoMatchReturnsEmpty:
    async def test_no_match_returns_empty(self, engine: RulesEngine):
        """No opponent-specific rules fire when lane_opponents is empty."""
        req = _make_request(lane_opponents=[], role=1, hero_id=999)
        results = engine.evaluate(req)
        # Only role-based rules (boots, quelling blade) should fire
        # No opponent-dependent rules should produce results
        opponent_item_ids = {
            36, 116, 225, 235, 119, 102, 271, 40, 43, 249,
            56, 190, 231, 168, 185,  # Phase 14 rule item IDs
            100, 226, 194, 250, 206,  # Phase 20 counter-item IDs
        }
        opponent_results = [r for r in results if r.item_id in opponent_item_ids]
        assert len(opponent_results) == 0


class TestBkbRule:
    async def test_bkb_vs_magic_heavy(self, engine: RulesEngine):
        """BKB recommended against Zeus (magic-heavy hero)."""
        req = _make_request(lane_opponents=[22], role=1)
        results = engine.evaluate(req)
        bkb_results = [r for r in results if r.item_id == 116]
        assert len(bkb_results) >= 1
        assert bkb_results[0].item_name == "Black King Bar"
        assert bkb_results[0].phase == "core"
        assert bkb_results[0].priority == "core"


class TestMkbRule:
    async def test_mkb_vs_evasion(self, engine: RulesEngine):
        """MKB recommended against PA (evasion hero) for cores."""
        req = _make_request(lane_opponents=[12], role=1)
        results = engine.evaluate(req)
        mkb_results = [r for r in results if r.item_id == 225]
        assert len(mkb_results) >= 1
        assert mkb_results[0].item_name == "Monkey King Bar"
        assert mkb_results[0].phase == "core"
        assert mkb_results[0].priority == "situational"

    async def test_mkb_not_for_supports(self, engine: RulesEngine):
        """MKB NOT recommended for supports (role 4-5)."""
        req = _make_request(lane_opponents=[12], role=5)
        results = engine.evaluate(req)
        mkb_results = [r for r in results if r.item_id == 225]
        assert len(mkb_results) == 0


class TestDustSentriesRule:
    async def test_dust_for_support_vs_invis(self, engine: RulesEngine):
        """Dust/Sentries recommended for supports against Riki."""
        req = _make_request(lane_opponents=[32], role=5)
        results = engine.evaluate(req)
        detection_results = [r for r in results if r.item_id in (40, 43)]
        assert len(detection_results) >= 1
        detection_ids = {r.item_id for r in detection_results}
        # Should recommend both Dust and Sentries
        assert 40 in detection_ids or 43 in detection_ids

    async def test_dust_not_for_cores(self, engine: RulesEngine):
        """Dust NOT recommended for cores (role 1-3) even against invis heroes."""
        req = _make_request(lane_opponents=[32], role=1)
        results = engine.evaluate(req)
        detection_results = [r for r in results if r.item_id in (40, 43)]
        assert len(detection_results) == 0


class TestBootsRule:
    async def test_boots_by_role_carry(self, engine: RulesEngine):
        """Power Treads recommended for carries (role 1)."""
        req = _make_request(role=1)
        results = engine.evaluate(req)
        boots_results = [r for r in results if r.item_id == 48]
        assert len(boots_results) >= 1
        assert boots_results[0].item_name == "Power Treads"

    async def test_boots_by_role_offlane(self, engine: RulesEngine):
        """Phase Boots recommended for offlaners (role 3)."""
        req = _make_request(role=3)
        results = engine.evaluate(req)
        boots_results = [r for r in results if r.item_id == 50]
        assert len(boots_results) >= 1
        assert boots_results[0].item_name == "Phase Boots"

    async def test_boots_by_role_support(self, engine: RulesEngine):
        """Arcane Boots recommended for supports (role 4-5)."""
        req = _make_request(role=5)
        results = engine.evaluate(req)
        boots_results = [r for r in results if r.item_id == 180]
        assert len(boots_results) >= 1
        assert boots_results[0].item_name == "Arcane Boots"


class TestReasoningNamesEnemy:
    async def test_reasoning_names_enemy(self, engine: RulesEngine):
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
            opponent_item_ids = {
                36, 116, 225, 235, 119, 102, 271, 40, 43, 249,
                56, 190, 231, 168, 185,  # Phase 14 rule item IDs
                100, 226, 194, 250, 206,  # Phase 20 counter-item IDs
            }
            opponent_results = [r for r in results if r.item_id in opponent_item_ids]
            for result in opponent_results:
                assert hero_name in result.reasoning, (
                    f"Reasoning for item {result.item_name} vs {hero_name} "
                    f"does not contain hero name. Got: {result.reasoning}"
                )


class TestSilverEdgeRule:
    async def test_silver_edge_vs_bristleback(self, engine: RulesEngine):
        """Silver Edge recommended against Bristleback (critical passive)."""
        req = _make_request(lane_opponents=[69], role=1)
        results = engine.evaluate(req)
        se_results = [r for r in results if r.item_id == 249]
        assert len(se_results) >= 1
        assert "Bristleback" in se_results[0].reasoning


class TestSpiritVesselRule:
    async def test_spirit_vessel_vs_alchemist(self, engine: RulesEngine):
        """Spirit Vessel recommended for offlaners against Alchemist."""
        req = _make_request(lane_opponents=[72], role=3)
        results = engine.evaluate(req)
        sv_results = [r for r in results if r.item_id == 271]
        assert len(sv_results) >= 1
        assert "Alchemist" in sv_results[0].reasoning


class TestQuellingBladeRule:
    async def test_quelling_blade_for_melee_carry(self, engine: RulesEngine):
        """Quelling Blade recommended for Anti-Mage (melee carry, Pos 1)."""
        req = _make_request(hero_id=1, role=1)
        results = engine.evaluate(req)
        qb_results = [r for r in results if r.item_id == 29]
        assert len(qb_results) >= 1
        assert qb_results[0].phase == "starting"

    async def test_quelling_blade_not_for_supports(self, engine: RulesEngine):
        """Quelling Blade NOT recommended for support role."""
        req = _make_request(hero_id=1, role=5)
        results = engine.evaluate(req)
        qb_results = [r for r in results if r.item_id == 29]
        assert len(qb_results) == 0


class TestRaindropsRule:
    async def test_raindrops_vs_zeus(self, engine: RulesEngine):
        """Infused Raindrops recommended against Zeus (magic harass)."""
        req = _make_request(lane_opponents=[22], role=1)
        results = engine.evaluate(req)
        raindrop = [r for r in results if r.item_name == "Infused Raindrops"]
        assert len(raindrop) >= 1
        assert raindrop[0].phase == "laning"


class TestOrchidRule:
    async def test_orchid_vs_slark(self, engine: RulesEngine):
        """Orchid recommended against Slark (escape hero) for cores."""
        req = _make_request(lane_opponents=[93], role=2)
        results = engine.evaluate(req)
        orchid = [r for r in results if r.item_name == "Orchid Malevolence"]
        assert len(orchid) >= 1
        assert orchid[0].phase == "core"

    async def test_orchid_not_for_supports(self, engine: RulesEngine):
        """Orchid NOT recommended for supports (role 4-5)."""
        req = _make_request(lane_opponents=[93], role=5)
        results = engine.evaluate(req)
        orchid = [r for r in results if r.item_name == "Orchid Malevolence"]
        assert len(orchid) == 0


class TestMekansmRule:
    async def test_mek_for_frontline_offlaner(self, engine: RulesEngine):
        """Mekansm recommended for Frontline offlaner."""
        req = _make_request(role=3, playstyle="Frontline")
        results = engine.evaluate(req)
        mek = [r for r in results if r.item_name == "Mekansm"]
        assert len(mek) >= 1


class TestPipeRule:
    async def test_pipe_vs_magic_lineup(self, engine: RulesEngine):
        """Pipe of Insight recommended vs magic-heavy enemy (Zeus) for offlaner."""
        req = _make_request(lane_opponents=[22], role=3)
        results = engine.evaluate(req)
        pipe = [r for r in results if r.item_name == "Pipe of Insight"]
        assert len(pipe) >= 1


class TestHalberdRule:
    async def test_halberd_vs_pa(self, engine: RulesEngine):
        """Heaven's Halberd recommended against PA for offlaner."""
        req = _make_request(lane_opponents=[12], role=3)
        results = engine.evaluate(req)
        halberd = [r for r in results if r.item_name == "Heaven's Halberd"]
        assert len(halberd) >= 1


class TestGhostScepterRule:
    async def test_ghost_vs_riki_support(self, engine: RulesEngine):
        """Ghost Scepter recommended for supports against Riki."""
        req = _make_request(lane_opponents=[32], role=5)
        results = engine.evaluate(req)
        ghost = [r for r in results if r.item_name == "Ghost Scepter"]
        assert len(ghost) >= 1


class TestRuleCount:
    async def test_minimum_rule_count(self, engine: RulesEngine):
        """Engine has at least 50 rules registered."""
        assert len(engine._rules) >= 50


class TestPatch741RuleAccuracy:
    """Verifies rules reflect 7.41 game data accurately."""

    async def test_shivas_reasoning_mentions_741(self, engine: RulesEngine):
        """Shiva's Guard reasoning references 7.41 cost (4500g)."""
        req = _make_request(lane_opponents=[12], role=3)  # PA is physical carry, offlaner
        results = engine.evaluate(req)
        shivas = [r for r in results if r.item_name == "Shiva's Guard"]
        assert len(shivas) >= 1, "Shiva's Guard not recommended vs PA for offlaner"
        assert "4500" in shivas[0].reasoning or "7.41" in shivas[0].reasoning, (
            f"Shiva's reasoning does not mention 7.41 cost. Got: {shivas[0].reasoning}"
        )

    async def test_no_cornucopia_in_rules(self, engine: RulesEngine):
        """No rule source code references Cornucopia (removed in 7.41)."""
        import inspect
        source = inspect.getsource(RulesEngine)
        assert "cornucopia" not in source.lower(), (
            "RulesEngine source contains 'cornucopia' -- item was removed in 7.41"
        )

    async def test_no_refresher_orb_rule(self, engine: RulesEngine):
        """No rule recommends Refresher Orb (behavior changed in 7.41)."""
        test_opponents = [22, 33]  # Zeus, Enigma
        for opp_id in test_opponents:
            req = _make_request(lane_opponents=[opp_id], role=1)
            results = engine.evaluate(req)
            refresher = [r for r in results if "Refresher" in r.item_name]
            assert len(refresher) == 0, (
                f"Rule recommends Refresher Orb vs opponent {opp_id}. "
                f"Refresher behavior changed in 7.41 -- should not be rule-driven."
            )


class TestPatch741PromptHints:
    """Verifies system prompt contains 7.41 meta hints."""

    def test_system_prompt_has_741_section(self):
        """System prompt contains Patch 7.41 Notes section."""
        from engine.prompts.system_prompt import SYSTEM_PROMPT
        assert "Patch 7.41" in SYSTEM_PROMPT

    def test_refresher_orb_hint(self):
        """System prompt mentions Refresher Orb abilities-only change."""
        from engine.prompts.system_prompt import SYSTEM_PROMPT
        assert "Refresher Orb" in SYSTEM_PROMPT
        assert "abilities only" in SYSTEM_PROMPT.lower() or "ABILITIES ONLY" in SYSTEM_PROMPT

    def test_bloodstone_hint(self):
        """System prompt mentions Bloodstone rework."""
        from engine.prompts.system_prompt import SYSTEM_PROMPT
        assert "Bloodstone" in SYSTEM_PROMPT
        assert "spell damage" in SYSTEM_PROMPT.lower()

    def test_facets_removed_hint(self):
        """System prompt mentions facets removal."""
        from engine.prompts.system_prompt import SYSTEM_PROMPT
        assert "Facets removed" in SYSTEM_PROMPT or "facets" in SYSTEM_PROMPT.lower()


# ------------------------------------------------------------------
# Phase 20: Counter-Item Intelligence test scaffolds
# ------------------------------------------------------------------


class TestComputeThreatLevel:
    """Tests for compute_threat_level utility function (pure, no engine fixture)."""

    def test_high_threat_fed_enemy(self):
        """Fed enemy (kills=7, deaths=1) classified as high."""
        ec = EnemyContext(hero_id=30, kills=7, deaths=1)
        assert compute_threat_level(ec) == "high"

    def test_behind_enemy(self):
        """Behind enemy (kills=0, deaths=5) classified as behind."""
        ec = EnemyContext(hero_id=30, kills=0, deaths=5)
        assert compute_threat_level(ec) == "behind"

    def test_normal_enemy(self):
        """Normal enemy (kills=2, deaths=2) classified as normal."""
        ec = EnemyContext(hero_id=30, kills=2, deaths=2)
        assert compute_threat_level(ec) == "normal"

    def test_high_threat_zero_deaths(self):
        """Fed enemy with zero deaths (kills=5, deaths=0) classified as high."""
        ec = EnemyContext(hero_id=30, kills=5, deaths=0)
        assert compute_threat_level(ec) == "high"

    def test_none_kda_is_normal(self):
        """Enemy with no KDA data classified as normal."""
        ec = EnemyContext(hero_id=30)
        assert compute_threat_level(ec) == "normal"


class TestAbilityHelpers:
    """Tests for ability query helper methods on RulesEngine."""

    async def test_has_channeled_witch_doctor(self, engine: RulesEngine):
        """_has_channeled_ability returns AbilityCached for Witch Doctor (Death Ward)."""
        result = engine._has_channeled_ability(30)
        assert result is not None
        assert result.dname == "Death Ward"
        assert result.is_channeled is True

    async def test_has_channeled_antimage_none(self, engine: RulesEngine):
        """_has_channeled_ability returns None for Anti-Mage (no channeled abilities)."""
        result = engine._has_channeled_ability(1)
        assert result is None

    async def test_has_passive_antimage(self, engine: RulesEngine):
        """_has_passive returns AbilityCached for Anti-Mage (Mana Break is passive)."""
        result = engine._has_passive(1)
        assert result is not None
        assert result.is_passive is True

    async def test_has_passive_witch_doctor_none(self, engine: RulesEngine):
        """_has_passive returns None for Witch Doctor (no passive abilities)."""
        result = engine._has_passive(30)
        assert result is None

    async def test_has_bkb_piercing_witch_doctor(self, engine: RulesEngine):
        """_has_bkb_piercing returns list with Death Ward for Witch Doctor."""
        result = engine._has_bkb_piercing(30)
        assert len(result) >= 1
        dnames = [a.dname for a in result]
        assert "Death Ward" in dnames

    async def test_has_escape_ability_antimage(self, engine: RulesEngine):
        """_has_escape_ability returns AbilityCached for Anti-Mage (Blink)."""
        result = engine._has_escape_ability(1)
        assert result is not None
        assert "blink" in result.key

    async def test_has_escape_ability_witch_doctor_none(self, engine: RulesEngine):
        """_has_escape_ability returns None for Witch Doctor (no escape)."""
        result = engine._has_escape_ability(30)
        assert result is None

    async def test_has_undispellable_debuff_witch_doctor(self, engine: RulesEngine):
        """_has_undispellable_debuff returns an undispellable ability for Witch Doctor."""
        result = engine._has_undispellable_debuff(30)
        assert result is not None
        # Witch Doctor has Paralyzing Cask (Strong Dispels Only) and Maledict (No)
        assert result.dname in ("Paralyzing Cask", "Maledict")


class TestCounterTargetField:
    """Test that counter_target field exists on RuleResult and serializes."""

    def test_counter_target_none_serializes(self):
        """RuleResult with counter_target=None serializes without error."""
        from engine.schemas import RuleResult
        result = RuleResult(
            item_id=100, item_name="Eul's Scepter of Divinity",
            reasoning="Test reason", phase="core", priority="situational",
            counter_target=None,
        )
        data = result.model_dump()
        assert data["counter_target"] is None

    def test_counter_target_value_serializes(self):
        """RuleResult with counter_target set serializes correctly."""
        from engine.schemas import RuleResult
        result = RuleResult(
            item_id=100, item_name="Eul's Scepter of Divinity",
            reasoning="Test reason", phase="core", priority="situational",
            counter_target="Witch Doctor: Death Ward (channeled)",
        )
        data = result.model_dump()
        assert data["counter_target"] == "Witch Doctor: Death Ward (channeled)"


# ------------------------------------------------------------------
# Phase 20 Plan 02: Ability-driven rules, new counter rules, threat escalation
# ------------------------------------------------------------------


class TestAbilityDrivenRules:
    """Verifies CNTR-01: rules query ability properties instead of only hero IDs."""

    async def test_silver_edge_via_ability(self, engine: RulesEngine):
        """Silver Edge fires via ability query for Bristleback passive."""
        req = _make_request(lane_opponents=[69], role=1)  # BB has bristleback_bristleback (Passive)
        results = engine.evaluate(req)
        se = [r for r in results if r.item_name == "Silver Edge"]
        assert len(se) >= 1
        assert se[0].counter_target is not None
        assert "passive" in se[0].counter_target.lower()

    async def test_orchid_via_ability(self, engine: RulesEngine):
        """Orchid fires via ability query for Puck escape (illusory_orb)."""
        req = _make_request(lane_opponents=[13], role=2)  # Puck has illusory_orb
        results = engine.evaluate(req)
        orchid = [r for r in results if r.item_name == "Orchid Malevolence"]
        assert len(orchid) >= 1
        assert orchid[0].counter_target is not None
        assert "escape" in orchid[0].counter_target.lower()

    async def test_raindrops_via_ability(self, engine: RulesEngine):
        """Raindrops fires via ability query for magical damage."""
        req = _make_request(lane_opponents=[30], role=1)  # WD has Magical abilities
        results = engine.evaluate(req)
        raindrop = [r for r in results if r.item_name == "Infused Raindrops"]
        assert len(raindrop) >= 1

    async def test_dust_via_ability(self, engine: RulesEngine):
        """Dust fires via ability query for Riki invis (cloak_and_dagger)."""
        req = _make_request(lane_opponents=[32], role=5)  # Riki has cloak_and_dagger
        results = engine.evaluate(req)
        dust = [r for r in results if r.item_name == "Dust of Appearance"]
        assert len(dust) >= 1
        assert dust[0].counter_target is not None

    async def test_bkb_via_ability(self, engine: RulesEngine):
        """BKB fires via ability query for Witch Doctor's magical abilities."""
        req = _make_request(lane_opponents=[30], role=1)  # WD has magical abilities
        results = engine.evaluate(req)
        bkb = [r for r in results if r.item_name == "Black King Bar"]
        assert len(bkb) >= 1
        assert bkb[0].counter_target is not None


class TestNewCounterRules:
    """Verifies CNTR-02: 5 new counter-rule categories fire correctly."""

    async def test_euls_vs_witch_doctor(self, engine: RulesEngine):
        """Eul's recommended against WD's Death Ward (channeled)."""
        req = _make_request(lane_opponents=[30], role=3)  # WD Death Ward is channeled
        results = engine.evaluate(req)
        euls = [r for r in results if r.item_name == "Eul's Scepter of Divinity"]
        assert len(euls) >= 1
        assert "Death Ward" in euls[0].reasoning
        assert "channeled" in euls[0].counter_target.lower()

    async def test_euls_vs_enigma(self, engine: RulesEngine):
        """Eul's recommended against Enigma's Black Hole (channeled)."""
        req = _make_request(lane_opponents=[33], role=3)
        results = engine.evaluate(req)
        euls = [r for r in results if r.item_name == "Eul's Scepter of Divinity"]
        assert len(euls) >= 1
        assert "Black Hole" in euls[0].reasoning

    async def test_euls_not_vs_non_channeled(self, engine: RulesEngine):
        """Eul's channel rule does NOT fire against heroes without channeled abilities."""
        req = _make_request(lane_opponents=[12], role=3)  # PA has no channeled
        results = engine.evaluate(req)
        euls_channel = [
            r for r in results
            if r.item_name == "Eul's Scepter of Divinity"
            and "channeled" in (r.counter_target or "").lower()
        ]
        assert len(euls_channel) == 0

    async def test_hex_vs_escape(self, engine: RulesEngine):
        """Scythe of Vyse recommended for cores against escape heroes."""
        req = _make_request(lane_opponents=[1], role=2)  # AM has blink (escape)
        results = engine.evaluate(req)
        hex_results = [r for r in results if r.item_name == "Scythe of Vyse"]
        assert len(hex_results) >= 1
        assert "Blink" in hex_results[0].reasoning
        assert "escape" in hex_results[0].counter_target.lower()

    async def test_atos_vs_escape_for_support(self, engine: RulesEngine):
        """Rod of Atos recommended for supports against escape heroes."""
        req = _make_request(lane_opponents=[1], role=4)  # AM has blink
        results = engine.evaluate(req)
        atos = [r for r in results if r.item_name == "Rod of Atos"]
        assert len(atos) >= 1

    async def test_bkb_pierce_warning(self, engine: RulesEngine):
        """BKB rule includes pierce warning when enemy has BKB-piercing ability."""
        req = _make_request(lane_opponents=[30], role=1)  # WD Death Ward pierces BKB
        results = engine.evaluate(req)
        bkb = [r for r in results if r.item_name == "Black King Bar"]
        assert len(bkb) >= 1
        assert "pierces BKB" in bkb[0].reasoning

    async def test_dispel_vs_undispellable(self, engine: RulesEngine):
        """Dispel item recommended against hero with undispellable debuff."""
        req = _make_request(lane_opponents=[30], role=3)  # WD maledict is dispellable=No
        results = engine.evaluate(req)
        dispel = [
            r for r in results
            if r.counter_target and "undispellable" in r.counter_target.lower()
        ]
        assert len(dispel) >= 1


class TestReasoningNamesAbility:
    """Verifies CNTR-03: ability-driven rules name the specific ability in reasoning."""

    async def test_counter_reasoning_names_ability(self, engine: RulesEngine):
        """Ability-driven rules name the specific ability in reasoning."""
        cases = [
            (30, 3, "Death Ward"),     # WD channeled -> Eul's
            (69, 1, "Bristleback"),    # BB passive -> Silver Edge (ability dname)
            (1, 2, "Blink"),           # AM escape -> Orchid or Hex
        ]
        for opp_id, role, expected_ability in cases:
            req = _make_request(lane_opponents=[opp_id], role=role)
            results = engine.evaluate(req)
            # Find results with counter_target set
            counter_results = [r for r in results if r.counter_target is not None]
            assert len(counter_results) >= 1, (
                f"No counter_target results for opponent {opp_id}"
            )
            # At least one counter result should name the expected ability
            found = any(expected_ability in r.reasoning for r in counter_results)
            assert found, (
                f"No reasoning mentions '{expected_ability}' for opponent {opp_id}. "
                f"Got: {[r.reasoning for r in counter_results]}"
            )


class TestThreatEscalation:
    """Verifies CNTR-04: threat-level priority adjustment in evaluate()."""

    async def test_fed_enemy_upgrades_priority(self, engine: RulesEngine):
        """Fed enemy upgrades counter-item priority from situational to core."""
        enemy_ctx = [EnemyContext(hero_id=69, kills=7, deaths=1)]
        req = _make_request(lane_opponents=[69], role=1, enemy_context=enemy_ctx)
        results = engine.evaluate(req)
        # Silver Edge vs BB should be "core" when BB is fed (normally "situational")
        se = [r for r in results if r.item_name == "Silver Edge"]
        assert len(se) >= 1
        assert se[0].priority == "core", f"Expected 'core' but got '{se[0].priority}'"

    async def test_behind_enemy_downgrades_priority(self, engine: RulesEngine):
        """Behind enemy downgrades counter-item priority from core to situational."""
        enemy_ctx = [EnemyContext(hero_id=30, kills=0, deaths=5)]
        req = _make_request(lane_opponents=[30], role=1, enemy_context=enemy_ctx)
        results = engine.evaluate(req)
        # BKB vs WD is normally "core" -- should downgrade when WD is behind
        bkb = [r for r in results if r.item_name == "Black King Bar"]
        if bkb and bkb[0].counter_target:
            assert bkb[0].priority == "situational"

    async def test_normal_enemy_no_adjustment(self, engine: RulesEngine):
        """Normal threat enemy gets no priority adjustment."""
        enemy_ctx = [EnemyContext(hero_id=69, kills=2, deaths=2)]
        req = _make_request(lane_opponents=[69], role=1, enemy_context=enemy_ctx)
        results = engine.evaluate(req)
        se = [r for r in results if r.item_name == "Silver Edge"]
        assert len(se) >= 1
        assert se[0].priority == "situational"  # No change

    async def test_no_enemy_context_no_adjustment(self, engine: RulesEngine):
        """Without enemy_context, no threat adjustment occurs."""
        req = _make_request(lane_opponents=[69], role=1)  # No enemy_context
        results = engine.evaluate(req)
        se = [r for r in results if r.item_name == "Silver Edge"]
        assert len(se) >= 1
        assert se[0].priority == "situational"  # Original priority preserved


# ------------------------------------------------------------------
# Phase 35: Item-vs-item counter rules tests
# ------------------------------------------------------------------


class TestNullifierRule:
    async def test_nullifier_vs_puck(self, engine: RulesEngine):
        """Nullifier recommended against Puck (escape item user)."""
        puck_id = engine._hero_id("Puck")
        if puck_id is None:
            pytest.skip("Puck not in cache")
        req = _make_request(role=1, lane_opponents=[puck_id])
        results = engine.evaluate(req)
        nullifier = [r for r in results if "Nullifier" in r.item_name]
        assert len(nullifier) >= 1
        assert nullifier[0].phase == "late_game"

    async def test_nullifier_vs_storm(self, engine: RulesEngine):
        """Nullifier recommended against Storm Spirit."""
        storm_id = engine._hero_id("Storm Spirit")
        if storm_id is None:
            pytest.skip("Storm Spirit not in cache")
        req = _make_request(role=2, lane_opponents=[storm_id])
        results = engine.evaluate(req)
        nullifier = [r for r in results if "Nullifier" in r.item_name]
        assert len(nullifier) >= 1

    async def test_nullifier_not_for_supports(self, engine: RulesEngine):
        """Nullifier NOT recommended for supports (role 4-5)."""
        puck_id = engine._hero_id("Puck")
        if puck_id is None:
            pytest.skip("Puck not in cache")
        req = _make_request(role=5, lane_opponents=[puck_id])
        results = engine.evaluate(req)
        nullifier = [r for r in results if "Nullifier" in r.item_name]
        assert len(nullifier) == 0


class TestTeamCompositionRules:
    async def test_shivas_vs_3_physical(self, engine: RulesEngine):
        """Shiva's recommended when 3+ physical carries on enemy team."""
        pa_id = engine._hero_id("Phantom Assassin")
        sven_id = engine._hero_id("Sven")
        jug_id = engine._hero_id("Juggernaut")
        if not all([pa_id, sven_id, jug_id]):
            pytest.skip("Heroes not in cache")
        req = _make_request(
            role=3, playstyle="Frontline",
            lane_opponents=[pa_id],
            all_opponents=[pa_id, sven_id, jug_id],
        )
        results = engine.evaluate(req)
        shivas = [r for r in results if r.item_name == "Shiva's Guard"
                  and "team comp" in (r.counter_target or "")]
        assert len(shivas) >= 1
        assert shivas[0].priority == "core"

    async def test_pipe_team_vs_3_magic(self, engine: RulesEngine):
        """Pipe recommended when 3+ magic damage heroes on enemy team."""
        zeus_id = engine._hero_id("Zeus")
        lina_id = engine._hero_id("Lina")
        wd_id = engine._hero_id("Witch Doctor")
        if not all([zeus_id, lina_id, wd_id]):
            pytest.skip("Heroes not in cache")
        req = _make_request(
            role=3, playstyle="Frontline",
            lane_opponents=[zeus_id],
            all_opponents=[zeus_id, lina_id, wd_id],
        )
        results = engine.evaluate(req)
        pipe_team = [r for r in results if r.item_name == "Pipe of Insight"
                     and "team comp" in (r.counter_target or "")]
        assert len(pipe_team) >= 1
        assert pipe_team[0].priority == "core"

    async def test_wraith_pact_vs_3_physical(self, engine: RulesEngine):
        """Wraith Pact recommended when 3+ physical carries on enemy team."""
        pa_id = engine._hero_id("Phantom Assassin")
        sven_id = engine._hero_id("Sven")
        jug_id = engine._hero_id("Juggernaut")
        if not all([pa_id, sven_id, jug_id]):
            pytest.skip("Heroes not in cache")
        req = _make_request(
            role=3, playstyle="Frontline",
            lane_opponents=[pa_id],
            all_opponents=[pa_id, sven_id, jug_id],
        )
        results = engine.evaluate(req)
        wp = [r for r in results if r.item_name == "Wraith Pact"]
        assert len(wp) >= 1


class TestCrimsonGuardRule:
    async def test_crimson_vs_illusion_hero(self, engine: RulesEngine):
        """Crimson Guard recommended against Phantom Lancer."""
        pl_id = engine._hero_id("Phantom Lancer")
        if pl_id is None:
            pytest.skip("PL not in cache")
        req = _make_request(role=3, playstyle="Frontline", lane_opponents=[pl_id])
        results = engine.evaluate(req)
        crimson = [r for r in results if "Crimson" in r.item_name]
        assert len(crimson) >= 1

    async def test_crimson_not_for_carries(self, engine: RulesEngine):
        """Crimson Guard NOT recommended for carries (role 1-2)."""
        pl_id = engine._hero_id("Phantom Lancer")
        if pl_id is None:
            pytest.skip("PL not in cache")
        req = _make_request(role=1, lane_opponents=[pl_id])
        results = engine.evaluate(req)
        crimson = [r for r in results if "Crimson" in r.item_name]
        assert len(crimson) == 0


class TestGlimmerCapeRule:
    async def test_glimmer_vs_magic_burst(self, engine: RulesEngine):
        """Glimmer Cape recommended for supports vs magic damage."""
        zeus_id = engine._hero_id("Zeus")
        if zeus_id is None:
            pytest.skip("Zeus not in cache")
        req = _make_request(role=5, lane_opponents=[zeus_id])
        results = engine.evaluate(req)
        glimmer = [r for r in results if "Glimmer" in r.item_name]
        assert len(glimmer) >= 1

    async def test_glimmer_not_for_cores(self, engine: RulesEngine):
        """Glimmer Cape NOT recommended for cores (role 1-3)."""
        zeus_id = engine._hero_id("Zeus")
        if zeus_id is None:
            pytest.skip("Zeus not in cache")
        req = _make_request(role=2, lane_opponents=[zeus_id])
        results = engine.evaluate(req)
        glimmer = [r for r in results if "Glimmer" in r.item_name]
        assert len(glimmer) == 0


class TestBladMailRule:
    async def test_blade_mail_vs_pa(self, engine: RulesEngine):
        """Blade Mail recommended for offlaners against PA burst."""
        pa_id = engine._hero_id("Phantom Assassin")
        if pa_id is None:
            pytest.skip("PA not in cache")
        req = _make_request(role=3, playstyle="Frontline", lane_opponents=[pa_id])
        results = engine.evaluate(req)
        bm = [r for r in results if "Blade Mail" in r.item_name]
        assert len(bm) >= 1


class TestDiffusalRule:
    async def test_diffusal_vs_wraith_king(self, engine: RulesEngine):
        """Diffusal Blade recommended against Wraith King (mana-dependent)."""
        wk_id = engine._hero_id("Wraith King")
        if wk_id is None:
            pytest.skip("WK not in cache")
        req = _make_request(role=1, lane_opponents=[wk_id])
        results = engine.evaluate(req)
        diff = [r for r in results if "Diffusal" in r.item_name]
        assert len(diff) >= 1


class TestSelfHeroRules:
    async def test_blink_initiator(self, engine: RulesEngine):
        """Blink Dagger recommended for Initiator offlaners."""
        req = _make_request(role=3, playstyle="Initiator")
        results = engine.evaluate(req)
        blink = [r for r in results if "Blink Dagger" in r.item_name]
        assert len(blink) >= 1
        assert blink[0].priority == "core"

    async def test_aghs_scepter_for_rubick(self, engine: RulesEngine):
        """Aghanim's Scepter recommended for Rubick."""
        rubick_id = engine._hero_id("Rubick")
        if rubick_id is None:
            pytest.skip("Rubick not in cache")
        req = _make_request(hero_id=rubick_id, role=4)
        results = engine.evaluate(req)
        aghs = [r for r in results if "Aghanim's Scepter" in r.item_name]
        assert len(aghs) >= 1

    async def test_aghs_shard_for_jugg(self, engine: RulesEngine):
        """Aghanim's Shard recommended for Juggernaut."""
        jug_id = engine._hero_id("Juggernaut")
        if jug_id is None:
            pytest.skip("Juggernaut not in cache")
        req = _make_request(hero_id=jug_id, role=1)
        results = engine.evaluate(req)
        shard = [r for r in results if "Aghanim's Shard" in r.item_name]
        assert len(shard) >= 1

    async def test_guardian_greaves_aura_carrier(self, engine: RulesEngine):
        """Guardian Greaves recommended for Aura-carrier offlaners."""
        req = _make_request(role=3, playstyle="Aura-carrier")
        results = engine.evaluate(req)
        gg = [r for r in results if "Guardian Greaves" in r.item_name]
        assert len(gg) >= 1
        assert gg[0].priority == "core"

    async def test_urn_for_roamer(self, engine: RulesEngine):
        """Urn of Shadows recommended for roaming supports."""
        req = _make_request(role=4, playstyle="Roamer")
        results = engine.evaluate(req)
        urn = [r for r in results if "Urn" in r.item_name]
        assert len(urn) >= 1
        assert urn[0].priority == "core"

    async def test_radiance_for_naga(self, engine: RulesEngine):
        """Radiance recommended for Naga Siren (illusion carry)."""
        naga_id = engine._hero_id("Naga Siren")
        if naga_id is None:
            pytest.skip("Naga not in cache")
        req = _make_request(hero_id=naga_id, role=1)
        results = engine.evaluate(req)
        radiance = [r for r in results if "Radiance" in r.item_name]
        assert len(radiance) >= 1

    async def test_heart_for_frontline(self, engine: RulesEngine):
        """Heart of Tarrasque recommended for Frontline offlaners."""
        req = _make_request(role=3, playstyle="Frontline")
        results = engine.evaluate(req)
        heart = [r for r in results if "Heart" in r.item_name]
        assert len(heart) >= 1


class TestMageSlayerRule:
    async def test_mage_slayer_vs_zeus(self, engine: RulesEngine):
        """Mage Slayer recommended against Zeus."""
        zeus_id = engine._hero_id("Zeus")
        if zeus_id is None:
            pytest.skip("Zeus not in cache")
        req = _make_request(role=2, lane_opponents=[zeus_id])
        results = engine.evaluate(req)
        ms = [r for r in results if "Mage Slayer" in r.item_name]
        assert len(ms) >= 1

    async def test_mage_slayer_vs_leshrac(self, engine: RulesEngine):
        """Mage Slayer recommended against Leshrac."""
        lesh_id = engine._hero_id("Leshrac")
        if lesh_id is None:
            pytest.skip("Leshrac not in cache")
        req = _make_request(role=1, lane_opponents=[lesh_id])
        results = engine.evaluate(req)
        ms = [r for r in results if "Mage Slayer" in r.item_name]
        assert len(ms) >= 1


class TestHoodRule:
    async def test_hood_for_melee_offlaner_vs_magic(self, engine: RulesEngine):
        """Hood of Defiance recommended for melee offlaner vs magic lane opponent."""
        zeus_id = engine._hero_id("Zeus")
        axe_id = engine._hero_id("Axe")
        if not all([zeus_id, axe_id]):
            pytest.skip("Heroes not in cache")
        req = _make_request(hero_id=axe_id, role=3, lane_opponents=[zeus_id])
        results = engine.evaluate(req)
        hood = [r for r in results if "Hood" in r.item_name]
        assert len(hood) >= 1
        assert hood[0].phase == "laning"


class TestMetaAwareRulesUseAllOpponents:
    async def test_shivas_team_uses_all_opponents(self, engine: RulesEngine):
        """Shiva's team armor rule reads req.all_opponents, not lane_opponents."""
        pa_id = engine._hero_id("Phantom Assassin")
        sven_id = engine._hero_id("Sven")
        jug_id = engine._hero_id("Juggernaut")
        if not all([pa_id, sven_id, jug_id]):
            pytest.skip("Heroes not in cache")
        # Only 1 lane opponent but 3 in all_opponents
        req = _make_request(
            role=3, playstyle="Frontline",
            lane_opponents=[pa_id],
            all_opponents=[pa_id, sven_id, jug_id],
        )
        results = engine.evaluate(req)
        shivas_team = [r for r in results if r.item_name == "Shiva's Guard"
                       and "team comp" in (r.counter_target or "")]
        assert len(shivas_team) >= 1, (
            "Shiva's team armor rule should fire when all_opponents has 3+ physical "
            "even if lane_opponents has only 1"
        )

"""Deterministic rules engine for obvious item recommendations.

Evaluates priority-ordered rules against game state. Each rule checks
hero IDs and role conditions, returning RuleResult objects with
enemy-hero-naming reasoning strings.

Hero and item references come from DataCache -- all lookups are
synchronous dict reads with zero DB queries.

This is NOT a fallback -- it fires on every request before Claude API.
"""

from data.cache import DataCache, AbilityCached
from engine.schemas import RecommendRequest, RuleResult


class RulesEngine:
    """Priority-ordered deterministic rules for item recommendations.

    Hero and item references come from DataCache. All lookups are
    synchronous dict reads with zero DB queries.
    """

    def __init__(self, cache: DataCache) -> None:
        self.cache = cache

    def _hero_id(self, name: str) -> int | None:
        """Lookup hero ID by localized_name. Returns None if not found."""
        return self.cache.hero_name_to_id(name)

    def _item_id(self, internal_name: str) -> int | None:
        """Lookup item ID by internal_name. Returns None if not found."""
        return self.cache.item_name_to_id(internal_name)

    def _hero_name(self, hero_id: int) -> str:
        """Lookup hero localized_name by ID. Returns 'the enemy' if not found."""
        return self.cache.hero_id_to_name(hero_id)

    def _hero_ids(self, *names: str) -> set[int]:
        """Convert hero names to IDs, skipping unknown heroes."""
        return {hid for n in names if (hid := self._hero_id(n)) is not None}

    # ------------------------------------------------------------------
    # Ability query helpers (Phase 20)
    # ------------------------------------------------------------------

    def _has_channeled_ability(self, hero_id: int) -> AbilityCached | None:
        """Return a channeled ability for hero, or None."""
        abilities = self.cache.get_hero_abilities(hero_id)
        if not abilities:
            return None
        for ability in abilities:
            if ability.is_channeled:
                return ability
        return None

    def _has_passive(self, hero_id: int) -> AbilityCached | None:
        """Return the first passive ability for hero, or None."""
        abilities = self.cache.get_hero_abilities(hero_id)
        if not abilities:
            return None
        for ability in abilities:
            if ability.is_passive:
                return ability
        return None

    def _has_bkb_piercing(self, hero_id: int) -> list[AbilityCached]:
        """Return all BKB-piercing abilities for hero."""
        abilities = self.cache.get_hero_abilities(hero_id)
        if not abilities:
            return []
        return [a for a in abilities if a.bkbpierce]

    def _has_escape_ability(self, hero_id: int) -> AbilityCached | None:
        """Return an escape-type ability (blink, invis, movement), or None.
        Uses ability key matching + hero roles as heuristic."""
        abilities = self.cache.get_hero_abilities(hero_id)
        if not abilities:
            return None
        escape_keywords = {
            "blink", "invis", "leap", "pounce", "ball_lightning",
            "waveform", "time_walk", "phase_shift", "illusory_orb",
            "shukuchi", "windrun", "shadow_dance",
        }
        for ability in abilities:
            if any(kw in ability.key for kw in escape_keywords):
                return ability
        return None

    def _has_undispellable_debuff(self, hero_id: int) -> AbilityCached | None:
        """Return an ability with undispellable or strong-dispel-only debuff, or None."""
        abilities = self.cache.get_hero_abilities(hero_id)
        if not abilities:
            return None
        for ability in abilities:
            if ability.dispellable and ability.dispellable.lower() in ("no", "strong dispels only"):
                return ability
        return None

    def evaluate(self, request: RecommendRequest) -> list[RuleResult]:
        """Run all rules in priority order and collect results."""
        results: list[RuleResult] = []
        for rule_fn in self._rules:
            results.extend(rule_fn(request))
        return results

    @property
    def _rules(self):
        """Ordered list of rule methods, highest priority first."""
        return [
            self._magic_stick_rule,
            self._quelling_blade_rule,
            self._boots_rule,
            self._raindrops_rule,
            self._bkb_rule,
            self._mkb_rule,
            self._armor_rule,
            self._force_staff_rule,
            self._spirit_vessel_rule,
            self._mana_sustain_rule,
            self._dust_sentries_rule,
            self._anti_heal_rule,
            self._silver_edge_rule,
            self._orchid_rule,
            self._mekansm_rule,
            self._pipe_rule,
            self._halberd_rule,
            self._ghost_scepter_rule,
        ]

    # ------------------------------------------------------------------
    # Rule implementations
    # ------------------------------------------------------------------

    def _magic_stick_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Magic Stick vs spell-spamming lane opponents."""
        spammers = self._hero_ids(
            "Phantom Assassin", "Zeus", "Lion", "Venomancer",
            "Bristleback", "Ogre Magi", "Rubick", "Disruptor",
            "Dark Seer", "Skywrath Mage", "Grimstroke",
        )
        stick_id = self._item_id("magic_stick")
        if stick_id is None:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in spammers:
                hero_name = self._hero_name(op_id)
                results.append(RuleResult(
                    item_id=stick_id,
                    item_name="Magic Stick",
                    reasoning=(
                        f"Against {hero_name}'s frequent spell usage, "
                        f"Magic Stick provides burst heal/mana from charge accumulation. "
                        f"Expect 10+ charges regularly in lane."
                    ),
                    phase="laning",
                    priority="core",
                ))
                break  # One Magic Stick recommendation is enough
        return results

    def _quelling_blade_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Quelling Blade for melee carry heroes (Pos 1-2)."""
        melee_carries = self._hero_ids(
            "Anti-Mage", "Sven", "Phantom Assassin", "Juggernaut",
            "Phantom Lancer", "Faceless Void", "Dragon Knight",
            "Lifestealer", "Chaos Knight", "Naga Siren", "Wraith King",
            "Slark", "Troll Warlord", "Ember Spirit", "Monkey King",
        )
        qb_id = self._item_id("quelling_blade")
        if qb_id is None:
            return []
        if req.role <= 2 and req.hero_id in melee_carries:
            return [RuleResult(
                item_id=qb_id,
                item_name="Quelling Blade",
                reasoning=(
                    "Essential starting item for melee carries. "
                    "+18 bonus damage to creeps ensures last-hit efficiency in lane."
                ),
                phase="starting",
                priority="core",
            )]
        return []

    def _boots_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Recommend appropriate boots based on role."""
        treads_id = self._item_id("power_treads")
        phase_id = self._item_id("phase_boots")
        arcane_id = self._item_id("arcane_boots")
        if req.role <= 2:
            if treads_id is None:
                return []
            return [RuleResult(
                item_id=treads_id,
                item_name="Power Treads",
                reasoning=(
                    "Power Treads provide attack speed and attribute switching "
                    "for farming efficiency and stat optimization in fights."
                ),
                phase="laning",
                priority="core",
            )]
        elif req.role == 3:
            if phase_id is None:
                return []
            return [RuleResult(
                item_id=phase_id,
                item_name="Phase Boots",
                reasoning=(
                    "Phase Boots give armor, damage, and a phase-walk active "
                    "for chasing and positioning in the offlane."
                ),
                phase="laning",
                priority="core",
            )]
        else:
            # Role 4-5 supports
            if arcane_id is None:
                return []
            return [RuleResult(
                item_id=arcane_id,
                item_name="Arcane Boots",
                reasoning=(
                    "Arcane Boots provide mana sustain for the entire team, "
                    "essential for supports who need to cast spells frequently."
                ),
                phase="laning",
                priority="core",
            )]

    def _bkb_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """BKB vs heavy magic/disable lineup opponents."""
        magic_heavy = self._hero_ids(
            "Zeus", "Lion", "Witch Doctor", "Lich", "Warlock",
            "Death Prophet", "Leshrac", "Enchantress", "Chen", "Lina",
            "Silencer", "Meepo", "Ogre Magi", "Rubick", "Disruptor",
            "Invoker", "Necrophos", "Skywrath Mage",
            # Disable-heavy heroes (expanded from original set)
            "Tidehunter", "Enigma", "Magnus", "Dark Willow",
        )
        bkb_id = self._item_id("bkb")
        if bkb_id is None:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in magic_heavy:
                hero_name = self._hero_name(op_id)
                results.append(RuleResult(
                    item_id=bkb_id,
                    item_name="Black King Bar",
                    reasoning=(
                        f"Against {hero_name}'s heavy magical damage and disables, "
                        f"BKB provides spell immunity to survive teamfights "
                        f"and maintain DPS uptime."
                    ),
                    phase="core",
                    priority="core",
                ))
                break  # One BKB recommendation is enough
        return results

    def _mkb_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """MKB vs evasion heroes. Only for cores (Pos 1-3)."""
        evasion_heroes = self._hero_ids(
            "Phantom Assassin", "Faceless Void", "Brewmaster",
            "Troll Warlord", "Arc Warden", "Monkey King",
        )
        mkb_id = self._item_id("monkey_king_bar")
        if mkb_id is None or req.role > 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in evasion_heroes:
                hero_name = self._hero_name(op_id)
                results.append(RuleResult(
                    item_id=mkb_id,
                    item_name="Monkey King Bar",
                    reasoning=(
                        f"Against {hero_name}'s evasion, MKB's True Strike "
                        f"ensures your attacks cannot be evaded, "
                        f"countering their survivability."
                    ),
                    phase="core",
                    priority="situational",
                ))
                break
        return results

    def _armor_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Assault Cuirass or Shiva's Guard vs physical damage carries."""
        physical_carries = self._hero_ids(
            "Anti-Mage", "Sven", "Phantom Assassin", "Juggernaut",
            "Phantom Lancer", "Faceless Void", "Chaos Knight",
            "Naga Siren", "Wraith King", "Slark", "Troll Warlord",
            "Ember Spirit", "Monkey King",
        )
        ac_id = self._item_id("assault")
        shivas_id = self._item_id("shivas_guard")
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in physical_carries:
                hero_name = self._hero_name(op_id)
                # AC for carry/offlane (roles 1-2), Shiva's for mid/offlane casters (role 3)
                if req.role <= 2:
                    if ac_id is None:
                        continue
                    results.append(RuleResult(
                        item_id=ac_id,
                        item_name="Assault Cuirass",
                        reasoning=(
                            f"Against {hero_name}'s physical damage output, "
                            f"Assault Cuirass provides armor aura for your team "
                            f"and armor reduction on enemies."
                        ),
                        phase="late_game",
                        priority="situational",
                    ))
                else:
                    if shivas_id is None:
                        continue
                    results.append(RuleResult(
                        item_id=shivas_id,
                        item_name="Shiva's Guard",
                        reasoning=(
                            f"Against {hero_name}'s physical damage and attack speed, "
                            f"Shiva's Guard reduces their attack speed aura "
                            f"and provides armor and int."
                        ),
                        phase="late_game",
                        priority="situational",
                    ))
                break
        return results

    def _force_staff_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Force Staff vs heroes with strong slows/roots. For supports/offlaners (Pos 3-5)."""
        slow_heroes = self._hero_ids(
            "Razor", "Night Stalker", "Bounty Hunter",
            "Slark", "Bristleback", "Underlord",
        )
        fs_id = self._item_id("force_staff")
        if fs_id is None or req.role < 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in slow_heroes:
                hero_name = self._hero_name(op_id)
                results.append(RuleResult(
                    item_id=fs_id,
                    item_name="Force Staff",
                    reasoning=(
                        f"Against {hero_name}'s slows and movement restrictions, "
                        f"Force Staff provides an instant reposition "
                        f"to escape or save allies."
                    ),
                    phase="core",
                    priority="situational",
                ))
                break
        return results

    def _spirit_vessel_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Spirit Vessel vs high-regen heroes. For supports/offlaners (Pos 3-5)."""
        high_regen = self._hero_ids(
            "Axe", "Lifestealer", "Alchemist", "Wraith King",
            "Dark Seer", "Necrophos", "Huskar",
        )
        sv_id = self._item_id("spirit_vessel")
        if sv_id is None or req.role < 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in high_regen:
                hero_name = self._hero_name(op_id)
                results.append(RuleResult(
                    item_id=sv_id,
                    item_name="Spirit Vessel",
                    reasoning=(
                        f"Against {hero_name}'s high HP regeneration, "
                        f"Spirit Vessel reduces their healing by 45% "
                        f"and deals percentage-based damage."
                    ),
                    phase="core",
                    priority="core",
                ))
                break
        return results

    def _mana_sustain_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Soul Ring for mana-hungry offlaners (Pos 3)."""
        mana_hungry = self._hero_ids(
            "Axe", "Sand King", "Tidehunter", "Razor",
            "Dragon Knight", "Timbersaw", "Dark Seer", "Underlord",
        )
        sr_id = self._item_id("soul_ring")
        if sr_id is None or req.role != 3:
            return []
        if req.hero_id in mana_hungry:
            return [RuleResult(
                item_id=sr_id,
                item_name="Soul Ring",
                reasoning=(
                    "Soul Ring provides on-demand mana for spell-reliant offlaners. "
                    "The HP cost is offset by natural regen and sustain items."
                ),
                phase="laning",
                priority="core",
            )]
        return []

    def _dust_sentries_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Dust and Sentries vs invisible heroes. For supports (Pos 4-5)."""
        invis_heroes = self._hero_ids(
            "Riki", "Treant Protector", "Nyx Assassin",
            "Mirana", "Bounty Hunter", "Clinkz", "Weaver",
        )
        dust_id = self._item_id("dust")
        sentry_id = self._item_id("ward_sentry")
        if req.role < 4:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in invis_heroes:
                hero_name = self._hero_name(op_id)
                if dust_id is not None:
                    results.append(RuleResult(
                        item_id=dust_id,
                        item_name="Dust of Appearance",
                        reasoning=(
                            f"Against {hero_name}'s invisibility, "
                            f"Dust reveals them in a large area for 12 seconds. "
                            f"Essential for securing kills."
                        ),
                        phase="laning",
                        priority="core",
                    ))
                if sentry_id is not None:
                    results.append(RuleResult(
                        item_id=sentry_id,
                        item_name="Sentry Ward",
                        reasoning=(
                            f"Against {hero_name}'s invisibility, "
                            f"Sentry Wards provide persistent true sight "
                            f"to control vision and deny juke spots."
                        ),
                        phase="laning",
                        priority="core",
                    ))
                break
        return results

    def _anti_heal_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Shiva's Guard vs sustain/heal lineups for cores (Pos 1-3)."""
        heal_sustain = self._hero_ids(
            "Axe", "Lifestealer", "Alchemist",
            "Wraith King", "Necrophos", "Huskar",
        )
        shivas_id = self._item_id("shivas_guard")
        if shivas_id is None or req.role > 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in heal_sustain:
                hero_name = self._hero_name(op_id)
                results.append(RuleResult(
                    item_id=shivas_id,
                    item_name="Shiva's Guard",
                    reasoning=(
                        f"Against {hero_name}'s sustain and healing, "
                        f"Shiva's Guard applies a healing reduction effect "
                        f"and slows their attack speed."
                    ),
                    phase="core",
                    priority="situational",
                ))
                break
        return results

    def _silver_edge_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Silver Edge vs heroes with critical passives. For cores (Pos 1-3)."""
        passive_heroes = self._hero_ids(
            "Phantom Assassin", "Lifestealer", "Bristleback",
            "Alchemist", "Timbersaw", "Huskar",
        )
        se_id = self._item_id("silver_edge")
        if se_id is None or req.role > 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in passive_heroes:
                hero_name = self._hero_name(op_id)
                results.append(RuleResult(
                    item_id=se_id,
                    item_name="Silver Edge",
                    reasoning=(
                        f"Against {hero_name}'s critical passive abilities, "
                        f"Silver Edge's Break disables their passives for 4 seconds, "
                        f"significantly reducing their effectiveness."
                    ),
                    phase="core",
                    priority="situational",
                ))
                break
        return results

    # ------------------------------------------------------------------
    # New targeted rules (Phase 14)
    # ------------------------------------------------------------------

    def _raindrops_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Infused Raindrops vs heavy magic damage in lane."""
        magic_harass = self._hero_ids(
            "Zeus", "Skywrath Mage", "Ogre Magi", "Lion",
            "Venomancer", "Lina", "Lich", "Witch Doctor",
        )
        raindrop_id = self._item_id("infused_raindrop")
        if raindrop_id is None:
            return []
        for op_id in req.lane_opponents:
            if op_id in magic_harass:
                return [RuleResult(
                    item_id=raindrop_id,
                    item_name="Infused Raindrops",
                    reasoning=(
                        f"Against {self._hero_name(op_id)}'s magic damage harass, "
                        f"Raindrops block 120 magic damage per charge. "
                        f"At 225g, the most cost-efficient magic protection in lane."
                    ),
                    phase="laning",
                    priority="core",
                )]
        return []

    def _orchid_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Orchid Malevolence vs heroes that rely on escape spells."""
        escape_heroes = self._hero_ids(
            "Anti-Mage", "Slark", "Weaver", "Ember Spirit",
            "Faceless Void", "Puck", "Storm Spirit", "Queen of Pain",
        )
        orchid_id = self._item_id("orchid")
        if orchid_id is None or req.role > 3:
            return []
        for op_id in req.lane_opponents:
            if op_id in escape_heroes:
                return [RuleResult(
                    item_id=orchid_id,
                    item_name="Orchid Malevolence",
                    reasoning=(
                        f"Against {self._hero_name(op_id)}'s escape abilities, "
                        f"Orchid's 5s silence prevents blink/leap/ball usage. "
                        f"The soul burn amplifies burst damage for the kill."
                    ),
                    phase="core",
                    priority="situational",
                )]
        return []

    def _mekansm_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Mekansm for frontline offlaners and active supports."""
        mek_id = self._item_id("mekansm")
        if mek_id is None:
            return []
        if req.role in (3, 4) and req.playstyle in (
            "Frontline", "Aura-carrier", "Lane-dominator",
        ):
            return [RuleResult(
                item_id=mek_id,
                item_name="Mekansm",
                reasoning=(
                    "Mekansm provides a 275 HP burst heal in a 1200 radius. "
                    "As a frontline/aura player, you'll be positioned to hit "
                    "3-4 heroes with every activation."
                ),
                phase="core",
                priority="situational",
            )]
        return []

    def _pipe_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Pipe of Insight vs multiple magic damage enemies."""
        magic_heroes = self._hero_ids(
            "Zeus", "Lina", "Leshrac", "Death Prophet",
            "Skywrath Mage", "Necrophos", "Invoker", "Lich",
        )
        pipe_id = self._item_id("pipe")
        if pipe_id is None or req.role not in (3, 4):
            return []
        magic_count = sum(1 for op_id in req.lane_opponents if op_id in magic_heroes)
        if magic_count >= 1:
            return [RuleResult(
                item_id=pipe_id,
                item_name="Pipe of Insight",
                reasoning=(
                    "Against magic-heavy enemies, Pipe's barrier absorbs 450 "
                    "magic damage for your team. The 15% magic resistance aura "
                    "stacks with base resistance for 40% total."
                ),
                phase="core",
                priority="situational",
            )]
        return []

    def _halberd_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Heaven's Halberd vs right-click dependent carries."""
        rightclick_carries = self._hero_ids(
            "Phantom Assassin", "Troll Warlord", "Sven",
            "Juggernaut", "Monkey King", "Faceless Void",
            "Lifestealer", "Wraith King",
        )
        halberd_id = self._item_id("heavens_halberd")
        if halberd_id is None or req.role != 3:
            return []
        for op_id in req.lane_opponents:
            if op_id in rightclick_carries:
                return [RuleResult(
                    item_id=halberd_id,
                    item_name="Heaven's Halberd",
                    reasoning=(
                        f"Against {self._hero_name(op_id)}'s right-click damage, "
                        f"Halberd's 3s disarm (5s on ranged) removes their primary "
                        f"damage source. The 25% evasion and status resist make "
                        f"you harder to kill."
                    ),
                    phase="core",
                    priority="situational",
                )]
        return []

    def _ghost_scepter_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Ghost Scepter for supports vs physical burst heroes."""
        physical_burst = self._hero_ids(
            "Phantom Assassin", "Slark", "Riki", "Clinkz",
            "Bounty Hunter", "Nyx Assassin",
        )
        ghost_id = self._item_id("ghost")
        if ghost_id is None or req.role < 4:
            return []
        for op_id in req.lane_opponents:
            if op_id in physical_burst:
                return [RuleResult(
                    item_id=ghost_id,
                    item_name="Ghost Scepter",
                    reasoning=(
                        f"Against {self._hero_name(op_id)}'s physical burst, "
                        f"Ghost Scepter's 4s ethereal form makes you immune to "
                        f"right-clicks. Buys time for teammates to respond."
                    ),
                    phase="core",
                    priority="situational",
                )]
        return []

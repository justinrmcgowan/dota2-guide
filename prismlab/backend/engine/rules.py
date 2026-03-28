"""Deterministic rules engine for obvious item recommendations.

Evaluates priority-ordered rules against game state. Each rule uses
ability-first queries via DataCache with hardcoded hero-ID fallback,
returning RuleResult objects with ability-specific reasoning strings.

Hero and item references come from DataCache -- all lookups are
synchronous dict reads with zero DB queries.

This is NOT a fallback -- it fires on every request before Claude API.
"""

from data.cache import DataCache, AbilityCached
from engine.schemas import RecommendRequest, RuleResult, EnemyContext, compute_threat_level


class RulesEngine:
    """Priority-ordered deterministic rules for item recommendations.

    Hero and item references come from DataCache. All lookups are
    synchronous dict reads with zero DB queries. Enemy-matching rules
    use ability-first queries with hero-ID fallback for edge cases.
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

    def _has_magical_ability(self, hero_id: int) -> AbilityCached | None:
        """Return the first ability with Magical damage type, or None."""
        abilities = self.cache.get_hero_abilities(hero_id)
        if not abilities:
            return None
        for ability in abilities:
            if ability.dmg_type and ability.dmg_type.lower() == "magical":
                return ability
        return None

    def _has_invis_ability(self, hero_id: int) -> AbilityCached | None:
        """Return an invisibility-related ability, or None."""
        abilities = self.cache.get_hero_abilities(hero_id)
        if not abilities:
            return None
        invis_keywords = {
            "invis", "cloak", "shadow_dance", "shukuchi",
            "wind_walk", "skeleton_walk",
        }
        for ability in abilities:
            if any(kw in ability.key for kw in invis_keywords):
                return ability
        return None

    def _count_active_abilities(self, hero_id: int) -> int:
        """Count non-passive abilities for a hero (spell-spammer heuristic)."""
        abilities = self.cache.get_hero_abilities(hero_id)
        if not abilities:
            return 0
        return sum(1 for a in abilities if not a.is_passive)

    def evaluate(self, request: RecommendRequest) -> list[RuleResult]:
        """Run all rules in priority order, then adjust for threat levels."""
        # Build threat map from enemy_context
        threat_map: dict[int, str] = {}
        for ec in request.enemy_context:
            threat_map[ec.hero_id] = compute_threat_level(ec)

        # Run all rules
        results: list[RuleResult] = []
        for rule_fn in self._rules:
            results.extend(rule_fn(request))

        # Post-process: adjust priority based on threat
        if not threat_map:
            return results

        adjusted: list[RuleResult] = []
        for result in results:
            if result.counter_target is None:
                adjusted.append(result)
                continue
            # Find which opponent this targets
            for op_id in request.lane_opponents:
                hero_name = self._hero_name(op_id)
                if hero_name in (result.counter_target or ""):
                    threat = threat_map.get(op_id, "normal")
                    if threat == "high" and result.priority == "situational":
                        result = result.model_copy(update={"priority": "core"})
                    elif threat == "behind" and result.priority == "core":
                        result = result.model_copy(update={"priority": "situational"})
                    break
            adjusted.append(result)
        return adjusted

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
            # Phase 20: New counter-item rules
            self._euls_channel_rule,
            self._lotus_linkens_rule,
            self._dispel_counter_rule,
            self._hex_root_escape_rule,
        ]

    # ------------------------------------------------------------------
    # Rule implementations (refactored to ability-first + fallback)
    # ------------------------------------------------------------------

    def _magic_stick_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Magic Stick vs spell-spamming lane opponents.

        Ability-first: heroes with 3+ non-passive abilities are frequent casters.
        Fallback: curated hero list for edge cases not caught by ability check.
        """
        stick_id = self._item_id("magic_stick")
        if stick_id is None:
            return []
        # Fallback set: heroes whose spell-spam isn't captured by active ability count
        # (missing ability data, or active count < 3 despite being known spammers)
        fallback_spammers = self._hero_ids(
            "Phantom Assassin", "Zeus", "Lion", "Venomancer",
            "Bristleback", "Ogre Magi", "Rubick", "Disruptor",
            "Dark Seer", "Skywrath Mage", "Grimstroke",
        )
        for op_id in req.lane_opponents:
            hero_name = self._hero_name(op_id)
            # Ability-first: check active ability count
            active_count = self._count_active_abilities(op_id)
            if active_count >= 3:
                abilities = self.cache.get_hero_abilities(op_id)
                ability_name = abilities[0].dname if abilities else "abilities"
                return [RuleResult(
                    item_id=stick_id,
                    item_name="Magic Stick",
                    reasoning=(
                        f"Against {hero_name}'s frequent ability usage "
                        f"({ability_name} and others), "
                        f"Magic Stick provides burst heal/mana from charge accumulation. "
                        f"Expect 10+ charges regularly in lane."
                    ),
                    phase="laning",
                    priority="core",
                    counter_target=f"{hero_name}: frequent caster",
                )]
            # Fallback: hardcoded spammer list
            if op_id in fallback_spammers:
                return [RuleResult(
                    item_id=stick_id,
                    item_name="Magic Stick",
                    reasoning=(
                        f"Against {hero_name}'s frequent spell usage, "
                        f"Magic Stick provides burst heal/mana from charge accumulation. "
                        f"Expect 10+ charges regularly in lane."
                    ),
                    phase="laning",
                    priority="core",
                    counter_target=f"{hero_name}: frequent caster",
                )]
        return []

    def _quelling_blade_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Quelling Blade for melee carry heroes (Pos 1-2). Self-hero rule, not refactored."""
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
        """Recommend appropriate boots based on role. Self-hero rule, not refactored."""
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
        """BKB vs heavy magic/disable opponents.

        Ability-first: checks for Magical damage type abilities.
        Fallback: curated magic-heavy hero set for edge cases.
        Includes BKB-pierce warning when enemy has BKB-piercing abilities (D-04 category 3).
        """
        bkb_id = self._item_id("bkb")
        if bkb_id is None:
            return []
        # Fallback set: heroes whose magic threat isn't captured by ability dmg_type
        # (missing ability data, or magic threat comes from innate mechanics)
        fallback_magic = self._hero_ids(
            "Zeus", "Lion", "Lich", "Warlock",
            "Death Prophet", "Leshrac", "Enchantress", "Chen", "Lina",
            "Silencer", "Meepo", "Ogre Magi", "Rubick", "Disruptor",
            "Invoker", "Necrophos", "Skywrath Mage",
            "Tidehunter", "Enigma", "Magnus", "Dark Willow",
        )
        for op_id in req.lane_opponents:
            hero_name = self._hero_name(op_id)
            magical = self._has_magical_ability(op_id)
            matched = False
            counter_target = None

            if magical:
                matched = True
                counter_target = f"{hero_name}: {magical.dname} ({magical.dmg_type})"
                reasoning = (
                    f"Against {hero_name}'s {magical.dname} ({magical.dmg_type} damage) "
                    f"and other magical threats, BKB provides spell immunity to survive "
                    f"teamfights and maintain DPS uptime."
                )
            elif op_id in fallback_magic:
                matched = True
                counter_target = f"{hero_name}: magical/disable threat"
                reasoning = (
                    f"Against {hero_name}'s heavy magical damage and disables, "
                    f"BKB provides spell immunity to survive teamfights "
                    f"and maintain DPS uptime."
                )

            if matched:
                # BKB-pierce warning: check all lane opponents for pierce abilities
                pierce_warnings: list[str] = []
                for check_id in req.lane_opponents:
                    piercing = self._has_bkb_piercing(check_id)
                    for ability in piercing:
                        check_name = self._hero_name(check_id)
                        pierce_warnings.append(
                            f"{check_name}'s {ability.dname} pierces BKB"
                        )

                if pierce_warnings:
                    warning_str = "; ".join(pierce_warnings)
                    reasoning += (
                        f" Note: {warning_str} -- "
                        f"BKB won't protect you from this specific threat."
                    )

                return [RuleResult(
                    item_id=bkb_id,
                    item_name="Black King Bar",
                    reasoning=reasoning,
                    phase="core",
                    priority="core",
                    counter_target=counter_target,
                )]
        return []

    def _mkb_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """MKB vs evasion heroes. Only for cores (Pos 1-3).

        Ability-first: check for passive abilities on known evasion heroes.
        Evasion is hero-specific, so hero ID set remains primary with ability enrichment.
        """
        evasion_heroes = self._hero_ids(
            "Phantom Assassin", "Faceless Void", "Brewmaster",
            "Troll Warlord", "Arc Warden", "Monkey King",
        )
        mkb_id = self._item_id("monkey_king_bar")
        if mkb_id is None or req.role > 3:
            return []
        for op_id in req.lane_opponents:
            if op_id in evasion_heroes:
                hero_name = self._hero_name(op_id)
                passive = self._has_passive(op_id)
                if passive:
                    reasoning = (
                        f"Against {hero_name}'s {passive.dname} (evasion passive), "
                        f"MKB's True Strike ensures your attacks cannot be evaded, "
                        f"countering their survivability."
                    )
                    counter_target = f"{hero_name}: {passive.dname} (evasion)"
                else:
                    reasoning = (
                        f"Against {hero_name}'s evasion, MKB's True Strike "
                        f"ensures your attacks cannot be evaded, "
                        f"countering their survivability."
                    )
                    counter_target = f"{hero_name}: evasion"
                return [RuleResult(
                    item_id=mkb_id,
                    item_name="Monkey King Bar",
                    reasoning=reasoning,
                    phase="core",
                    priority="situational",
                    counter_target=counter_target,
                )]
        return []

    def _armor_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Assault Cuirass or Shiva's Guard vs physical damage carries.

        Role-based rule -- hero IDs remain primary with counter_target tagging.
        """
        physical_carries = self._hero_ids(
            "Anti-Mage", "Sven", "Phantom Assassin", "Juggernaut",
            "Phantom Lancer", "Faceless Void", "Chaos Knight",
            "Naga Siren", "Wraith King", "Slark", "Troll Warlord",
            "Ember Spirit", "Monkey King",
        )
        ac_id = self._item_id("assault")
        shivas_id = self._item_id("shivas_guard")
        for op_id in req.lane_opponents:
            if op_id in physical_carries:
                hero_name = self._hero_name(op_id)
                counter_target = f"{hero_name}: physical damage carry"
                if req.role <= 2:
                    if ac_id is None:
                        continue
                    return [RuleResult(
                        item_id=ac_id,
                        item_name="Assault Cuirass",
                        reasoning=(
                            f"Against {hero_name}'s physical damage output, "
                            f"Assault Cuirass provides armor aura for your team "
                            f"and armor reduction on enemies."
                        ),
                        phase="late_game",
                        priority="situational",
                        counter_target=counter_target,
                    )]
                else:
                    if shivas_id is None:
                        continue
                    return [RuleResult(
                        item_id=shivas_id,
                        item_name="Shiva's Guard",
                        reasoning=(
                            f"Against {hero_name}'s physical damage and attack speed, "
                            f"Shiva's Guard (4500g in 7.41) reduces their attack speed "
                            f"and provides armor. More accessible timing for offlaners this patch."
                        ),
                        phase="late_game",
                        priority="situational",
                        counter_target=counter_target,
                    )]
        return []

    def _force_staff_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Force Staff vs heroes with strong slows/roots. For supports/offlaners (Pos 3-5).

        Movement restriction is not cleanly ability-mapped. Hero IDs with counter_target.
        """
        slow_heroes = self._hero_ids(
            "Razor", "Night Stalker", "Bounty Hunter",
            "Slark", "Bristleback", "Underlord",
        )
        fs_id = self._item_id("force_staff")
        if fs_id is None or req.role < 3:
            return []
        for op_id in req.lane_opponents:
            if op_id in slow_heroes:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=fs_id,
                    item_name="Force Staff",
                    reasoning=(
                        f"Against {hero_name}'s slows and movement restrictions, "
                        f"Force Staff provides an instant reposition "
                        f"to escape or save allies."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: movement restriction",
                )]
        return []

    def _spirit_vessel_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Spirit Vessel vs high-regen heroes. For supports/offlaners (Pos 3-5).

        Regen is innate, not ability-tagged. Hero IDs with counter_target.
        """
        high_regen = self._hero_ids(
            "Axe", "Lifestealer", "Alchemist", "Wraith King",
            "Dark Seer", "Necrophos", "Huskar",
        )
        sv_id = self._item_id("spirit_vessel")
        if sv_id is None or req.role < 3:
            return []
        for op_id in req.lane_opponents:
            if op_id in high_regen:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=sv_id,
                    item_name="Spirit Vessel",
                    reasoning=(
                        f"Against {hero_name}'s high HP regeneration, "
                        f"Spirit Vessel reduces their healing by 45% "
                        f"and deals percentage-based damage."
                    ),
                    phase="core",
                    priority="core",
                    counter_target=f"{hero_name}: high regeneration",
                )]
        return []

    def _mana_sustain_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Soul Ring for mana-hungry offlaners (Pos 3). Self-hero rule, not refactored."""
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
        """Dust and Sentries vs invisible heroes. For supports (Pos 4-5).

        Ability-first: check for invis-related ability keys.
        Fallback: curated invis hero set for heroes whose invis isn't in ability data.
        """
        dust_id = self._item_id("dust")
        sentry_id = self._item_id("ward_sentry")
        if req.role < 4:
            return []
        # Fallback set for heroes whose invis isn't captured by ability key matching
        fallback_invis = self._hero_ids(
            "Treant Protector", "Mirana", "Nyx Assassin",
        )
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            hero_name = self._hero_name(op_id)
            invis = self._has_invis_ability(op_id)
            matched = False
            counter_target = None

            if invis:
                matched = True
                counter_target = f"{hero_name}: {invis.dname} (invisibility)"
            elif op_id in fallback_invis:
                matched = True
                counter_target = f"{hero_name}: invisibility"

            if matched:
                if dust_id is not None:
                    reasoning_dust = (
                        f"Against {hero_name}'s "
                        + (f"{invis.dname} " if invis else "")
                        + "invisibility, "
                        f"Dust reveals them in a large area for 12 seconds. "
                        f"Essential for securing kills."
                    )
                    results.append(RuleResult(
                        item_id=dust_id,
                        item_name="Dust of Appearance",
                        reasoning=reasoning_dust,
                        phase="laning",
                        priority="core",
                        counter_target=counter_target,
                    ))
                if sentry_id is not None:
                    reasoning_sentry = (
                        f"Against {hero_name}'s "
                        + (f"{invis.dname} " if invis else "")
                        + "invisibility, "
                        f"Sentry Wards provide persistent true sight "
                        f"to control vision and deny juke spots."
                    )
                    results.append(RuleResult(
                        item_id=sentry_id,
                        item_name="Sentry Ward",
                        reasoning=reasoning_sentry,
                        phase="laning",
                        priority="core",
                        counter_target=counter_target,
                    ))
                break
        return results

    def _anti_heal_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Shiva's Guard vs sustain/heal lineups for cores (Pos 1-3).

        Heal/sustain is not cleanly ability-mapped. Hero IDs with counter_target.
        """
        heal_sustain = self._hero_ids(
            "Axe", "Lifestealer", "Alchemist",
            "Wraith King", "Necrophos", "Huskar",
        )
        shivas_id = self._item_id("shivas_guard")
        if shivas_id is None or req.role > 3:
            return []
        for op_id in req.lane_opponents:
            if op_id in heal_sustain:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=shivas_id,
                    item_name="Shiva's Guard",
                    reasoning=(
                        f"Against {hero_name}'s sustain and healing, "
                        f"Shiva's Guard applies a healing reduction effect "
                        f"and slows their attack speed."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: healing/sustain",
                )]
        return []

    def _silver_edge_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Silver Edge vs heroes with critical passives. For cores (Pos 1-3).

        Ability-first: use _has_passive to find passive abilities.
        Fallback: small hero set for edge cases (e.g., Spectre).
        """
        se_id = self._item_id("silver_edge")
        if se_id is None or req.role > 3:
            return []
        # Fallback set for heroes whose passive isn't in ability data
        fallback_passive = self._hero_ids(
            "Huskar", "Timbersaw",
        )
        for op_id in req.lane_opponents:
            hero_name = self._hero_name(op_id)
            passive = self._has_passive(op_id)
            if passive:
                return [RuleResult(
                    item_id=se_id,
                    item_name="Silver Edge",
                    reasoning=(
                        f"Against {hero_name}'s {passive.dname} (passive), "
                        f"Silver Edge's Break disables their passives for 4 seconds, "
                        f"significantly reducing their effectiveness."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: {passive.dname} (passive)",
                )]
            if op_id in fallback_passive:
                return [RuleResult(
                    item_id=se_id,
                    item_name="Silver Edge",
                    reasoning=(
                        f"Against {hero_name}'s critical passive abilities, "
                        f"Silver Edge's Break disables their passives for 4 seconds, "
                        f"significantly reducing their effectiveness."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: passive",
                )]
        return []

    # ------------------------------------------------------------------
    # Targeted rules (Phase 14, refactored Phase 20)
    # ------------------------------------------------------------------

    def _raindrops_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Infused Raindrops vs heavy magic damage in lane.

        Ability-first: check for Magical damage type abilities.
        Fallback: curated magic harass hero set.
        """
        raindrop_id = self._item_id("infused_raindrop")
        if raindrop_id is None:
            return []
        # Fallback set: heroes whose magic harass isn't captured by ability dmg_type
        fallback_magic = self._hero_ids(
            "Zeus", "Skywrath Mage", "Ogre Magi", "Lion",
            "Venomancer", "Lina", "Lich",
        )
        for op_id in req.lane_opponents:
            hero_name = self._hero_name(op_id)
            magical = self._has_magical_ability(op_id)
            if magical:
                return [RuleResult(
                    item_id=raindrop_id,
                    item_name="Infused Raindrops",
                    reasoning=(
                        f"Against {hero_name}'s {magical.dname} (magical damage), "
                        f"Raindrops block 120 magic damage per charge. "
                        f"At 225g, the most cost-efficient magic protection in lane."
                    ),
                    phase="laning",
                    priority="core",
                    counter_target=f"{hero_name}: {magical.dname} (magical damage)",
                )]
            if op_id in fallback_magic:
                return [RuleResult(
                    item_id=raindrop_id,
                    item_name="Infused Raindrops",
                    reasoning=(
                        f"Against {hero_name}'s magic damage harass, "
                        f"Raindrops block 120 magic damage per charge. "
                        f"At 225g, the most cost-efficient magic protection in lane."
                    ),
                    phase="laning",
                    priority="core",
                    counter_target=f"{hero_name}: magical damage",
                )]
        return []

    def _orchid_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Orchid Malevolence vs heroes that rely on escape spells.

        Ability-first: use _has_escape_ability to find escape abilities.
        Fallback: small hero set for edge cases.
        """
        orchid_id = self._item_id("orchid")
        if orchid_id is None or req.role > 3:
            return []
        # Fallback set for heroes whose escape isn't detected by ability keywords
        fallback_escape = self._hero_ids(
            "Faceless Void",
        )
        for op_id in req.lane_opponents:
            hero_name = self._hero_name(op_id)
            escape = self._has_escape_ability(op_id)
            if escape:
                return [RuleResult(
                    item_id=orchid_id,
                    item_name="Orchid Malevolence",
                    reasoning=(
                        f"Against {hero_name}'s {escape.dname} (escape), "
                        f"Orchid's 5s silence prevents escape ability usage. "
                        f"The soul burn amplifies burst damage for the kill."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: {escape.dname} (escape)",
                )]
            if op_id in fallback_escape:
                return [RuleResult(
                    item_id=orchid_id,
                    item_name="Orchid Malevolence",
                    reasoning=(
                        f"Against {hero_name}'s escape abilities, "
                        f"Orchid's 5s silence prevents blink/leap/ball usage. "
                        f"The soul burn amplifies burst damage for the kill."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: escape",
                )]
        return []

    def _mekansm_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Mekansm for frontline offlaners and active supports. Self-hero rule, not refactored."""
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
        """Pipe of Insight vs multiple magic damage enemies.

        Ability-first: check for Magical damage type abilities.
        Fallback: curated magic hero set.
        """
        pipe_id = self._item_id("pipe")
        if pipe_id is None or req.role not in (3, 4):
            return []
        fallback_magic = self._hero_ids(
            "Zeus", "Lina", "Leshrac", "Death Prophet",
            "Skywrath Mage", "Necrophos", "Invoker", "Lich",
        )
        for op_id in req.lane_opponents:
            hero_name = self._hero_name(op_id)
            magical = self._has_magical_ability(op_id)
            if magical:
                return [RuleResult(
                    item_id=pipe_id,
                    item_name="Pipe of Insight",
                    reasoning=(
                        f"Against {hero_name}'s {magical.dname} ({magical.dmg_type} damage) "
                        f"and other magic threats, Pipe's barrier absorbs 450 "
                        f"magic damage for your team. The 15% magic resistance aura "
                        f"stacks with base resistance for 40% total."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: {magical.dname} ({magical.dmg_type})",
                )]
            if op_id in fallback_magic:
                return [RuleResult(
                    item_id=pipe_id,
                    item_name="Pipe of Insight",
                    reasoning=(
                        f"Against {hero_name} and other magic-heavy enemies, "
                        f"Pipe's barrier absorbs 450 magic damage for your team. "
                        f"The 15% magic resistance aura stacks with base resistance "
                        f"for 40% total."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: magical damage",
                )]
        return []

    def _halberd_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Heaven's Halberd vs right-click dependent carries.

        Hero-ID-based (right-click carries). counter_target added.
        """
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
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=halberd_id,
                    item_name="Heaven's Halberd",
                    reasoning=(
                        f"Against {hero_name}'s right-click damage, "
                        f"Halberd's 3s disarm (5s on ranged) removes their primary "
                        f"damage source. The 25% evasion and status resist make "
                        f"you harder to kill."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: right-click carry",
                )]
        return []

    def _ghost_scepter_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Ghost Scepter for supports vs physical burst heroes.

        Hero-ID-based (physical burst heroes). counter_target added.
        """
        physical_burst = self._hero_ids(
            "Phantom Assassin", "Slark", "Riki", "Clinkz",
            "Bounty Hunter", "Nyx Assassin",
        )
        ghost_id = self._item_id("ghost")
        if ghost_id is None or req.role < 4:
            return []
        for op_id in req.lane_opponents:
            if op_id in physical_burst:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=ghost_id,
                    item_name="Ghost Scepter",
                    reasoning=(
                        f"Against {hero_name}'s physical burst, "
                        f"Ghost Scepter's 4s ethereal form makes you immune to "
                        f"right-clicks. Buys time for teammates to respond."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: physical burst",
                )]
        return []

    # ------------------------------------------------------------------
    # Phase 20: New counter-item rules
    # ------------------------------------------------------------------

    def _euls_channel_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Eul's Scepter to interrupt channeled abilities."""
        euls_id = self._item_id("cyclone")
        if euls_id is None:
            return []
        for op_id in req.lane_opponents:
            channeled = self._has_channeled_ability(op_id)
            if channeled:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=euls_id,
                    item_name="Eul's Scepter of Divinity",
                    reasoning=(
                        f"Against {hero_name}'s {channeled.dname} (channeled), "
                        f"Eul's Scepter interrupts the channel on cast. "
                        f"Also provides mana regen and movement speed."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: {channeled.dname} (channeled)",
                )]
        return []

    def _lotus_linkens_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Lotus Orb or Linken's Sphere vs high-impact single-target ultimates."""
        # Curated set of high-impact single-target ult ability keys
        single_target_ults = {
            "doom_bringer_doom", "lion_finger_of_death",
            "necrolyte_reapers_scythe", "lina_laguna_blade",
            "bane_fiends_grip", "batrider_flaming_lasso",
            "beast_master_primal_roar",
        }
        for op_id in req.lane_opponents:
            abilities = self.cache.get_hero_abilities(op_id)
            if not abilities:
                continue
            for ability in abilities:
                if ability.key in single_target_ults:
                    hero_name = self._hero_name(op_id)
                    # Linken's for cores (role <= 3), Lotus for offlaners/supports (role >= 3)
                    if req.role < 3:
                        item_id = self._item_id("sphere")
                        item_name = "Linken's Sphere"
                    else:
                        item_id = self._item_id("lotus_orb")
                        item_name = "Lotus Orb"
                    if item_id is None:
                        continue
                    return [RuleResult(
                        item_id=item_id,
                        item_name=item_name,
                        reasoning=(
                            f"Against {hero_name}'s {ability.dname} (single-target ultimate), "
                            f"{item_name} blocks/reflects the initial cast."
                        ),
                        phase="core",
                        priority="situational",
                        counter_target=f"{hero_name}: {ability.dname} (single-target ultimate)",
                    )]
        return []

    def _dispel_counter_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Dispel items vs strong undispellable debuffs."""
        euls_id = self._item_id("cyclone")
        if euls_id is None:
            return []
        for op_id in req.lane_opponents:
            undispellable = self._has_undispellable_debuff(op_id)
            if undispellable:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=euls_id,
                    item_name="Eul's Scepter of Divinity",
                    reasoning=(
                        f"Against {hero_name}'s {undispellable.dname} "
                        f"(undispellable by basic dispel), "
                        f"Eul's Scepter provides self-dispel via cyclone to "
                        f"remove debuffs and reposition."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: {undispellable.dname} (undispellable)",
                )]
        return []

    def _hex_root_escape_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Hex or Root items vs escape heroes."""
        for op_id in req.lane_opponents:
            escape = self._has_escape_ability(op_id)
            if escape:
                hero_name = self._hero_name(op_id)
                # Scythe of Vyse for cores (role <= 3), Rod of Atos for supports (role >= 3)
                if req.role <= 3:
                    item_id = self._item_id("sheepstick")
                    item_name = "Scythe of Vyse"
                else:
                    item_id = self._item_id("rod_of_atos")
                    item_name = "Rod of Atos"
                if item_id is None:
                    continue
                return [RuleResult(
                    item_id=item_id,
                    item_name=item_name,
                    reasoning=(
                        f"Against {hero_name}'s {escape.dname} (escape), "
                        f"{item_name} prevents escape with hard disable."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: {escape.dname} (escape)",
                )]
        return []

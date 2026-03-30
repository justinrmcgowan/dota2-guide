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

    def _hero_attack_type(self, hero_id: int) -> str | None:
        """Return hero attack_type ('Melee' or 'Ranged') from cache, or None."""
        hero = self.cache.get_hero(hero_id)
        return hero.attack_type if hero else None

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
            # Phase 35: Item-vs-item counter rules
            self._nullifier_rule,
            self._blade_mail_rule,
            self._diffusal_rule,
            self._butterfly_rule,
            self._satanic_rule,
            self._crimson_guard_rule,
            self._aeon_disk_rule,
            self._gleipnir_rule,
            self._solar_crest_rule,
            self._bloodthorn_rule,
            self._shivas_team_armor_rule,
            self._pipe_team_magic_rule,
            self._hood_rule,
            self._wraith_pact_rule,
            self._glimmer_cape_rule,
            # Phase 35: Extended matchup and self-hero rules
            self._blink_dagger_initiator_rule,
            self._aghanims_scepter_rule,
            self._aghanims_shard_rule,
            self._mage_slayer_rule,
            self._lotus_orb_dispel_rule,
            self._eye_of_skadi_rule,
            self._radiance_rule,
            self._vanguard_melee_rule,
            self._meteor_hammer_rule,
            self._witch_blade_rule,
            self._desolator_rule,
            self._guardian_greaves_rule,
            self._heart_rule,
            self._ethereal_blade_rule,
            self._urn_rule,
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

    # ------------------------------------------------------------------
    # Phase 35: Item-vs-item counter rules
    # ------------------------------------------------------------------

    def _nullifier_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Nullifier vs Aeon Disk/Eul's/Ghost Scepter users. For cores (role 1-3)."""
        nullifier_id = self._item_id("nullifier")
        if nullifier_id is None or req.role > 3:
            return []
        target_heroes = self._hero_ids(
            "Puck", "Storm Spirit", "Ember Spirit", "Weaver",
            "Windranger", "Winter Wyvern", "Pugna", "Necrophos",
        )
        for op_id in req.lane_opponents:
            if op_id in target_heroes:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=nullifier_id,
                    item_name="Nullifier",
                    reasoning=(
                        f"Nullifier mutes item actives, preventing {hero_name}'s "
                        f"defensive item usage (Aeon Disk, Eul's, Ghost Scepter). "
                        f"The continuous dispel ensures they can't save themselves."
                    ),
                    phase="late_game",
                    priority="situational",
                    counter_target=f"{hero_name}: item-active user",
                )]
        return []

    def _blade_mail_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Blade Mail for tanky offlaners vs burst damage. For role 3 only."""
        bm_id = self._item_id("blade_mail")
        if bm_id is None or req.role != 3:
            return []
        burst_heroes = self._hero_ids(
            "Phantom Assassin", "Sven", "Juggernaut", "Ursa",
            "Templar Assassin", "Lina", "Lion",
        )
        for op_id in req.lane_opponents:
            if op_id in burst_heroes:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=bm_id,
                    item_name="Blade Mail",
                    reasoning=(
                        f"Against {hero_name}'s burst damage, Blade Mail reflects "
                        f"100% of damage back for 5.5 seconds. Forces them to stop "
                        f"attacking or kill themselves."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: burst damage",
                )]
        return []

    def _diffusal_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Diffusal Blade vs high-mana-dependency heroes. For cores (role 1-3)."""
        diff_id = self._item_id("diffusal_blade")
        if diff_id is None or req.role > 3:
            return []
        mana_dependent = self._hero_ids(
            "Medusa", "Storm Spirit", "Wraith King",
        )
        for op_id in req.lane_opponents:
            if op_id in mana_dependent:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=diff_id,
                    item_name="Diffusal Blade",
                    reasoning=(
                        f"Against {hero_name}'s mana dependency, Diffusal Blade "
                        f"burns 40 mana per hit, crippling their ability to fight. "
                        f"The slow active also prevents escape."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: mana-dependent",
                )]
        return []

    def _butterfly_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Butterfly for agility carries vs physical lineups. For role 1-2 only."""
        bfly_id = self._item_id("butterfly")
        if bfly_id is None or req.role > 2:
            return []
        agi_carries = self._hero_ids(
            "Anti-Mage", "Phantom Assassin", "Juggernaut",
            "Phantom Lancer", "Faceless Void", "Naga Siren",
            "Slark", "Troll Warlord", "Monkey King",
        )
        if req.hero_id not in agi_carries:
            return []
        physical_carries = self._hero_ids(
            "Anti-Mage", "Sven", "Phantom Assassin", "Juggernaut",
            "Phantom Lancer", "Faceless Void", "Chaos Knight",
            "Naga Siren", "Wraith King", "Slark", "Troll Warlord",
            "Ember Spirit", "Monkey King",
        )
        phys_count = sum(1 for op_id in req.all_opponents if op_id in physical_carries)
        if phys_count >= 2:
            return [RuleResult(
                item_id=bfly_id,
                item_name="Butterfly",
                reasoning=(
                    f"Enemy draft has {phys_count} physical damage cores -- "
                    f"Butterfly's 35% evasion forces MKB purchases, delaying "
                    f"their damage timing. Attack speed and armor complement "
                    f"agility carry scaling."
                ),
                phase="late_game",
                priority="situational",
                counter_target=f"{phys_count} physical cores",
            )]
        return []

    def _satanic_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Satanic for carries vs burst damage. For role 1-2 only."""
        satanic_id = self._item_id("satanic")
        if satanic_id is None or req.role > 2:
            return []
        burst_heroes = self._hero_ids(
            "Lina", "Lion", "Zeus", "Skywrath Mage",
            "Phantom Assassin", "Sven", "Templar Assassin",
        )
        burst_count = sum(1 for op_id in req.all_opponents if op_id in burst_heroes)
        if burst_count >= 2:
            return [RuleResult(
                item_id=satanic_id,
                item_name="Satanic",
                reasoning=(
                    f"Enemy has {burst_count} burst damage heroes -- "
                    f"Satanic's Unholy Rage active heals for 200% lifesteal "
                    f"for 6 seconds, allowing you to survive burst combos "
                    f"and sustain through extended fights."
                ),
                phase="late_game",
                priority="situational",
                counter_target=f"{burst_count} burst damage heroes",
            )]
        return []

    def _crimson_guard_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Crimson Guard for offlaners vs summon/illusion heroes. For role 3 only."""
        cg_id = self._item_id("crimson_guard")
        if cg_id is None or req.role != 3:
            return []
        summon_illusion_heroes = self._hero_ids(
            "Phantom Lancer", "Naga Siren", "Chaos Knight",
            "Nature's Prophet", "Broodmother", "Lycan",
        )
        for op_id in req.lane_opponents:
            if op_id in summon_illusion_heroes:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=cg_id,
                    item_name="Crimson Guard",
                    reasoning=(
                        f"Against {hero_name}'s illusions/summons, Crimson Guard "
                        f"blocks damage from each individual attack. The active "
                        f"provides team-wide damage block for 12 seconds."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: summons/illusions",
                )]
        return []

    def _aeon_disk_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Aeon Disk for supports vs burst initiation. For role 4-5 only."""
        ad_id = self._item_id("aeon_disk")
        if ad_id is None or req.role < 4:
            return []
        # Reuse single_target_ults set from _lotus_linkens_rule
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
                    return [RuleResult(
                        item_id=ad_id,
                        item_name="Aeon Disk",
                        reasoning=(
                            f"Against {hero_name}'s {ability.dname} burst initiation, "
                            f"Aeon Disk's Strong Dispel activates at 70% max HP, "
                            f"applying 2.5s of damage immunity to survive the combo."
                        ),
                        phase="core",
                        priority="situational",
                        counter_target=f"{hero_name}: {ability.dname} (burst initiation)",
                    )]
        return []

    def _gleipnir_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Gleipnir (Maelstrom upgrade) vs illusion heroes for cores. For role 1-3."""
        # Gleipnir's internal name may be 'gungungir' or 'gleipnir' -- try both
        gleipnir_id = self._item_id("gungungir") or self._item_id("gleipnir")
        if gleipnir_id is None or req.role > 3:
            return []
        illusion_heroes = self._hero_ids(
            "Phantom Lancer", "Naga Siren", "Chaos Knight",
            "Meepo", "Terrorblade",
        )
        for op_id in req.lane_opponents:
            if op_id in illusion_heroes:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=gleipnir_id,
                    item_name="Gleipnir",
                    reasoning=(
                        f"Against {hero_name}'s illusions, Gleipnir's chain lightning "
                        f"clears illusion waves efficiently. The Eternal Chains active "
                        f"roots in AoE, preventing escape."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: illusion hero",
                )]
        return []

    def _solar_crest_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Solar Crest for supports to buff a carry or debuff enemy. For role 4-5."""
        sc_id = self._item_id("solar_crest")
        if sc_id is None or req.role < 4:
            return []
        if req.playstyle not in ("Save", "Lane-protector"):
            return []
        carry_heroes = self._hero_ids(
            "Anti-Mage", "Sven", "Phantom Assassin", "Juggernaut",
            "Phantom Lancer", "Faceless Void", "Chaos Knight",
            "Naga Siren", "Wraith King", "Slark", "Troll Warlord",
            "Monkey King",
        )
        for ally_id in req.allies:
            if ally_id in carry_heroes:
                ally_name = self._hero_name(ally_id)
                return [RuleResult(
                    item_id=sc_id,
                    item_name="Solar Crest",
                    reasoning=(
                        f"Solar Crest buffs {ally_name} with armor and attack speed, "
                        f"or debuffs an enemy to amplify your team's physical damage. "
                        f"Strong synergy with a melee carry ally."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{ally_name}: carry ally buff",
                )]
        return []

    def _bloodthorn_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Bloodthorn (Orchid upgrade) vs evasion + escape heroes. For role 1-3."""
        bt_id = self._item_id("bloodthorn")
        if bt_id is None or req.role > 3:
            return []
        # Heroes with both escape and evasion
        evasion_escape = self._hero_ids(
            "Phantom Assassin", "Windranger",
        )
        for op_id in req.lane_opponents:
            if op_id in evasion_escape:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=bt_id,
                    item_name="Bloodthorn",
                    reasoning=(
                        f"Against {hero_name}'s evasion and escape, Bloodthorn "
                        f"provides silence + true strike + critical damage. "
                        f"Prevents both dodging and running."
                    ),
                    phase="late_game",
                    priority="situational",
                    counter_target=f"{hero_name}: evasion + escape",
                )]
        return []

    def _shivas_team_armor_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Shiva's Guard for offlaners when enemy has 3+ right-click cores. META-AWARE."""
        shivas_id = self._item_id("shivas_guard")
        if shivas_id is None or req.role != 3:
            return []
        physical_carries = self._hero_ids(
            "Anti-Mage", "Sven", "Phantom Assassin", "Juggernaut",
            "Phantom Lancer", "Faceless Void", "Chaos Knight",
            "Naga Siren", "Wraith King", "Slark", "Troll Warlord",
            "Ember Spirit", "Monkey King",
        )
        phys_count = sum(1 for op_id in req.all_opponents if op_id in physical_carries)
        if phys_count >= 3:
            return [RuleResult(
                item_id=shivas_id,
                item_name="Shiva's Guard",
                reasoning=(
                    f"Enemy draft has {phys_count} physical damage cores -- "
                    f"team needs Shiva's attack speed slow and armor. "
                    f"The Arctic Blast active slows movement and attack speed in AoE."
                ),
                phase="core",
                priority="core",
                counter_target=f"{phys_count} physical cores (team comp)",
            )]
        return []

    def _pipe_team_magic_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Pipe of Insight when enemy has 3+ magic damage heroes. META-AWARE."""
        pipe_id = self._item_id("pipe")
        if pipe_id is None or req.role not in (3, 4):
            return []
        magic_count = sum(
            1 for op_id in req.all_opponents
            if self._has_magical_ability(op_id)
        )
        if magic_count >= 3:
            return [RuleResult(
                item_id=pipe_id,
                item_name="Pipe of Insight",
                reasoning=(
                    f"Enemy has {magic_count} magic damage cores -- "
                    f"Pipe's 450 damage barrier protects entire team. "
                    f"The 15% magic resistance aura stacks with base resistance."
                ),
                phase="core",
                priority="core",
                counter_target=f"{magic_count} magic damage heroes (team comp)",
            )]
        return []

    def _hood_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Hood of Defiance for offlaners vs heavy magic lane opponent. For role 3."""
        hood_id = self._item_id("hood_of_defiance")
        if hood_id is None or req.role != 3:
            return []
        for op_id in req.lane_opponents:
            magical = self._has_magical_ability(op_id)
            if magical:
                # Check if hero is melee
                attack_type = self._hero_attack_type(req.hero_id)
                if attack_type and attack_type.lower() == "melee":
                    hero_name = self._hero_name(op_id)
                    return [RuleResult(
                        item_id=hood_id,
                        item_name="Hood of Defiance",
                        reasoning=(
                            f"Against {hero_name}'s {magical.dname} in lane, "
                            f"Hood provides magic damage barrier and resistance. "
                            f"Essential sustain for melee offlaners facing magic harass."
                        ),
                        phase="laning",
                        priority="situational",
                        counter_target=f"{hero_name}: {magical.dname} (magic harass)",
                    )]
        return []

    def _wraith_pact_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Wraith Pact for offlaners/supports vs heavy physical team. META-AWARE."""
        wp_id = self._item_id("wraith_pact")
        if wp_id is None or req.role not in (3, 4):
            return []
        physical_carries = self._hero_ids(
            "Anti-Mage", "Sven", "Phantom Assassin", "Juggernaut",
            "Phantom Lancer", "Faceless Void", "Chaos Knight",
            "Naga Siren", "Wraith King", "Slark", "Troll Warlord",
            "Ember Spirit", "Monkey King",
        )
        phys_count = sum(1 for op_id in req.all_opponents if op_id in physical_carries)
        if phys_count >= 3:
            return [RuleResult(
                item_id=wp_id,
                item_name="Wraith Pact",
                reasoning=(
                    f"Reduces enemy damage in area by 30%. "
                    f"With {phys_count} physical cores on the enemy team, "
                    f"Wraith Pact's damage reduction is especially valuable."
                ),
                phase="core",
                priority="situational",
                counter_target=f"{phys_count} physical cores (team comp)",
            )]
        return []

    def _glimmer_cape_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Glimmer Cape for supports vs magic burst. For role 4-5."""
        gc_id = self._item_id("glimmer_cape")
        if gc_id is None or req.role < 4:
            return []
        for op_id in req.lane_opponents:
            magical = self._has_magical_ability(op_id)
            if magical:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=gc_id,
                    item_name="Glimmer Cape",
                    reasoning=(
                        f"Provides magic resistance + invisibility to save allies "
                        f"from {hero_name}'s {magical.dname} burst. "
                        f"Low cooldown and instant cast make it a reliable save tool."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: {magical.dname} (magic burst)",
                )]
        return []

    # ------------------------------------------------------------------
    # Phase 35: Extended matchup and self-hero rules
    # ------------------------------------------------------------------

    def _blink_dagger_initiator_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Blink Dagger for initiator offlaners. For role 3, playstyle 'Initiator'."""
        blink_id = self._item_id("blink")
        if blink_id is None or req.role != 3 or req.playstyle != "Initiator":
            return []
        return [RuleResult(
            item_id=blink_id,
            item_name="Blink Dagger",
            reasoning=(
                "Essential mobility for initiating teamfights from fog. "
                "Blink into BKB/spell combo is the standard offlaner initiation pattern."
            ),
            phase="core",
            priority="core",
            counter_target="self: initiator mobility",
        )]

    def _aghanims_scepter_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Aghanim's Scepter for heroes with strong scepter upgrades. Self-hero rule."""
        aghs_id = self._item_id("ultimate_scepter")
        if aghs_id is None:
            return []
        strong_aghs_heroes = self._hero_ids(
            "Axe", "Invoker", "Rubick", "Lion", "Ogre Magi",
            "Witch Doctor", "Shadow Shaman", "Tidehunter",
            "Enigma", "Magnus", "Dark Seer",
        )
        if req.hero_id in strong_aghs_heroes:
            hero_name = self._hero_name(req.hero_id)
            return [RuleResult(
                item_id=aghs_id,
                item_name="Aghanim's Scepter",
                reasoning=(
                    f"Aghanim's Scepter provides a strong ultimate upgrade for "
                    f"{hero_name}. The stat bonuses and ability enhancement "
                    f"make it a high-value investment."
                ),
                phase="core",
                priority="situational",
                counter_target=f"self: {hero_name} Aghanim's upgrade",
            )]
        return []

    def _aghanims_shard_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Aghanim's Shard for heroes with strong shard upgrades. Self-hero rule."""
        shard_id = self._item_id("aghanims_shard")
        if shard_id is None:
            return []
        strong_shard_heroes = self._hero_ids(
            "Juggernaut", "Phantom Assassin", "Anti-Mage",
            "Faceless Void", "Sven", "Dragon Knight",
            "Puck", "Storm Spirit",
        )
        if req.hero_id in strong_shard_heroes:
            hero_name = self._hero_name(req.hero_id)
            return [RuleResult(
                item_id=shard_id,
                item_name="Aghanim's Shard",
                reasoning=(
                    f"20-minute shard power spike -- strong ability upgrade "
                    f"for {hero_name}. Cost-efficient enhancement that doesn't "
                    f"require an item slot."
                ),
                phase="core",
                priority="situational",
                counter_target=f"self: {hero_name} shard upgrade",
            )]
        return []

    def _mage_slayer_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Mage Slayer vs spell-reliant cores. For role 1-3."""
        ms_id = self._item_id("mage_slayer")
        if ms_id is None or req.role > 3:
            return []
        spell_cores = self._hero_ids(
            "Zeus", "Leshrac", "Storm Spirit", "Invoker", "Tinker",
        )
        for op_id in req.lane_opponents:
            if op_id in spell_cores:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=ms_id,
                    item_name="Mage Slayer",
                    reasoning=(
                        f"Reduces {hero_name}'s spell damage output by 40% on hit. "
                        f"The magic resistance and mana regen make it efficient "
                        f"against spell-reliant cores."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: spell-reliant core",
                )]
        return []

    def _lotus_orb_dispel_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Lotus Orb for offlaners/supports vs debuff-heavy enemies. For role 3-5."""
        lotus_id = self._item_id("lotus_orb")
        if lotus_id is None or req.role < 3:
            return []
        debuff_count = sum(
            1 for op_id in req.lane_opponents
            if self._has_undispellable_debuff(op_id)
        )
        if debuff_count >= 2:
            return [RuleResult(
                item_id=lotus_id,
                item_name="Lotus Orb",
                reasoning=(
                    f"Against {debuff_count} enemies with strong debuffs, "
                    f"Lotus Orb's Echo Shell reflects single-target spells "
                    f"and provides a basic dispel on cast."
                ),
                phase="core",
                priority="situational",
                counter_target=f"{debuff_count} debuff-heavy enemies",
            )]
        return []

    def _eye_of_skadi_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Eye of Skadi for ranged carries vs mobile heroes. For role 1-2."""
        skadi_id = self._item_id("skadi")
        if skadi_id is None or req.role > 2:
            return []
        attack_type = self._hero_attack_type(req.hero_id)
        if not attack_type or attack_type.lower() != "ranged":
            return []
        for op_id in req.lane_opponents:
            escape = self._has_escape_ability(op_id)
            if escape:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=skadi_id,
                    item_name="Eye of Skadi",
                    reasoning=(
                        f"Against {hero_name}'s {escape.dname} mobility, "
                        f"Skadi's 50% move speed and 45% attack speed slow "
                        f"makes it nearly impossible to escape. "
                        f"The all-stats bonus scales well on ranged carries."
                    ),
                    phase="late_game",
                    priority="situational",
                    counter_target=f"{hero_name}: {escape.dname} (mobile hero)",
                )]
        return []

    def _radiance_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Radiance for illusion-based carries. Self-hero rule. For role 1-2."""
        radiance_id = self._item_id("radiance")
        if radiance_id is None or req.role > 2:
            return []
        illusion_carries = self._hero_ids(
            "Naga Siren", "Phantom Lancer", "Spectre", "Terrorblade",
        )
        if req.hero_id in illusion_carries:
            hero_name = self._hero_name(req.hero_id)
            return [RuleResult(
                item_id=radiance_id,
                item_name="Radiance",
                reasoning=(
                    f"Illusions carry the Burn aura -- each {hero_name} copy "
                    f"deals 60 DPS in area. Combined with illusion-based farming, "
                    f"Radiance accelerates farm speed and teamfight damage."
                ),
                phase="core",
                priority="situational",
                counter_target=f"self: {hero_name} illusion synergy",
            )]
        return []

    def _vanguard_melee_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Vanguard for melee offlaners in tough lanes. For role 3."""
        vg_id = self._item_id("vanguard")
        if vg_id is None or req.role != 3:
            return []
        attack_type = self._hero_attack_type(req.hero_id)
        if not attack_type or attack_type.lower() != "melee":
            return []
        ranged_harass = self._hero_ids(
            "Viper", "Venomancer", "Silencer", "Death Prophet", "Windranger",
        )
        for op_id in req.lane_opponents:
            if op_id in ranged_harass:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=vg_id,
                    item_name="Vanguard",
                    reasoning=(
                        f"Against {hero_name}'s ranged harass in lane, "
                        f"Vanguard's damage block and HP regen keeps melee "
                        f"offlaners alive to contest the lane."
                    ),
                    phase="laning",
                    priority="situational",
                    counter_target=f"{hero_name}: ranged harass",
                )]
        return []

    def _meteor_hammer_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Meteor Hammer for heroes with long stuns/roots. Self-hero rule. For role 3-5."""
        mh_id = self._item_id("meteor_hammer")
        if mh_id is None or req.role < 3:
            return []
        meteor_heroes = self._hero_ids(
            "Treant Protector", "Naga Siren", "Shadow Shaman", "Bane",
        )
        if req.hero_id in meteor_heroes:
            hero_name = self._hero_name(req.hero_id)
            return [RuleResult(
                item_id=mh_id,
                item_name="Meteor Hammer",
                reasoning=(
                    f"Meteor Hammer combos with {hero_name}'s long-duration "
                    f"disable for guaranteed damage. Also provides tower push "
                    f"and farming capability."
                ),
                phase="core",
                priority="situational",
                counter_target=f"self: {hero_name} disable combo",
            )]
        return []

    def _witch_blade_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Witch Blade for intelligence mid heroes. Self-hero rule. For role 2."""
        wb_id = self._item_id("witch_blade")
        if wb_id is None or req.role != 2:
            return []
        int_mids = self._hero_ids(
            "Puck", "Lina", "Zeus", "Outworld Destroyer", "Death Prophet",
        )
        if req.hero_id in int_mids:
            hero_name = self._hero_name(req.hero_id)
            return [RuleResult(
                item_id=wb_id,
                item_name="Witch Blade",
                reasoning=(
                    f"Witch Blade provides intelligence, attack speed, and armor "
                    f"for {hero_name}. The poison attack adds harass damage in lane "
                    f"and scales with intelligence."
                ),
                phase="laning",
                priority="situational",
                counter_target=f"self: {hero_name} int mid item",
            )]
        return []

    def _desolator_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Desolator for physical damage mid heroes. For role 2."""
        deso_id = self._item_id("desolator")
        if deso_id is None or req.role != 2:
            return []
        phys_mids = self._hero_ids(
            "Templar Assassin", "Shadow Fiend", "Pangolier", "Queen of Pain",
        )
        if req.hero_id in phys_mids:
            hero_name = self._hero_name(req.hero_id)
            return [RuleResult(
                item_id=deso_id,
                item_name="Desolator",
                reasoning=(
                    f"Desolator's -7 armor corruption amplifies {hero_name}'s "
                    f"physical damage output. Strong Roshan and tower push timing."
                ),
                phase="core",
                priority="situational",
                counter_target=f"self: {hero_name} physical damage amplifier",
            )]
        return []

    def _guardian_greaves_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Guardian Greaves for aura carriers. For role 3, playstyle 'Aura-carrier'."""
        gg_id = self._item_id("guardian_greaves")
        if gg_id is None or req.role != 3 or req.playstyle != "Aura-carrier":
            return []
        return [RuleResult(
            item_id=gg_id,
            item_name="Guardian Greaves",
            reasoning=(
                "Dispels debuffs on self, heals and restores mana to team. "
                "Core on aura builders -- the low-HP bonus heal keeps you "
                "alive as frontline."
            ),
            phase="core",
            priority="core",
            counter_target="self: aura-carrier greaves",
        )]

    def _heart_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Heart of Tarrasque for frontline heroes in long games. For role 3."""
        heart_id = self._item_id("heart")
        if heart_id is None or req.role != 3 or req.playstyle != "Frontline":
            return []
        return [RuleResult(
            item_id=heart_id,
            item_name="Heart of Tarrasque",
            reasoning=(
                "Heart provides massive HP pool and out-of-combat regen "
                "for sustained frontline presence. Allows you to reset "
                "between teamfight engagements."
            ),
            phase="late_game",
            priority="situational",
            counter_target="self: frontline sustain",
        )]

    def _ethereal_blade_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Ethereal Blade for intelligence cores vs physical carries. For role 1-2."""
        eb_id = self._item_id("ethereal_blade")
        if eb_id is None or req.role > 2:
            return []
        int_cores = self._hero_ids(
            "Morphling", "Pugna", "Tinker", "Lina",
        )
        if req.hero_id not in int_cores:
            return []
        physical_carries = self._hero_ids(
            "Anti-Mage", "Sven", "Phantom Assassin", "Juggernaut",
            "Phantom Lancer", "Faceless Void", "Chaos Knight",
            "Naga Siren", "Wraith King", "Slark", "Troll Warlord",
            "Monkey King",
        )
        for op_id in req.lane_opponents:
            if op_id in physical_carries:
                hero_name = self._hero_name(op_id)
                return [RuleResult(
                    item_id=eb_id,
                    item_name="Ethereal Blade",
                    reasoning=(
                        f"Against {hero_name}'s physical damage, Ethereal Blade "
                        f"provides ethereal form (physical immunity) while amplifying "
                        f"your magic damage burst. Strong offensive and defensive value."
                    ),
                    phase="core",
                    priority="situational",
                    counter_target=f"{hero_name}: physical carry",
                )]
        return []

    def _urn_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Urn of Shadows for roaming supports. For role 4, playstyle 'Roamer'."""
        urn_id = self._item_id("urn_of_shadows")
        if urn_id is None or req.role != 4 or req.playstyle != "Roamer":
            return []
        return [RuleResult(
            item_id=urn_id,
            item_name="Urn of Shadows",
            reasoning=(
                "Charges from ganks enable healing or damage. Essential on "
                "aggressive roaming supports -- each successful gank provides "
                "a charge for sustain or kill potential."
            ),
            phase="laning",
            priority="core",
            counter_target="self: roamer sustain",
        )]

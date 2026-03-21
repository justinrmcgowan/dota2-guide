"""Deterministic rules engine for obvious item recommendations.

Evaluates priority-ordered rules against game state. Each rule checks
hero IDs and role conditions, returning RuleResult objects with
enemy-hero-naming reasoning strings.

This is NOT a fallback -- it fires on every request before Claude API.
"""

from engine.schemas import RecommendRequest, RuleResult


# Hero ID -> localized name mapping for all heroes referenced in rules.
# Source: OpenDota API hero constants.
HERO_NAMES: dict[int, str] = {
    1: "Anti-Mage",
    2: "Axe",
    8: "Sand King",
    10: "Tidehunter",
    11: "Sven",
    12: "Phantom Assassin",
    15: "Razor",
    18: "Juggernaut",
    22: "Zeus",
    26: "Lion",
    27: "Witch Doctor",
    31: "Lich",
    32: "Riki",
    37: "Warlock",
    40: "Venomancer",
    41: "Treant Protector",
    43: "Death Prophet",
    44: "Phantom Lancer",
    47: "Faceless Void",
    48: "Nyx Assassin",
    49: "Dragon Knight",
    52: "Leshrac",
    53: "Brewmaster",
    54: "Mirana",
    57: "Lifestealer",
    58: "Enchantress",
    60: "Night Stalker",
    62: "Bounty Hunter",
    66: "Chen",
    67: "Clinkz",
    68: "Lina",
    69: "Bristleback",
    72: "Alchemist",
    73: "Timbersaw",
    75: "Silencer",
    76: "Riki",  # alias -- kept for completeness, 32 is correct
    81: "Chaos Knight",
    82: "Meepo",
    84: "Ogre Magi",
    86: "Rubick",
    87: "Disruptor",
    89: "Naga Siren",
    91: "Wraith King",
    93: "Slark",
    94: "Weaver",
    97: "Dark Seer",
    99: "Bristleback",  # duplicate note -- 69 is Bristleback
    100: "Invoker",
    101: "Troll Warlord",
    103: "Necrophos",
    104: "Underlord",
    106: "Ember Spirit",
    110: "Skywrath Mage",
    113: "Arc Warden",
    114: "Monkey King",
    119: "Dark Willow",
    120: "Huskar",
    126: "Grimstroke",
}


class RulesEngine:
    """Priority-ordered deterministic rules for item recommendations.

    Each rule method checks conditions against the RecommendRequest and
    returns a list of RuleResult objects (empty if the rule does not apply).
    Rules are evaluated in priority order; all matching results are collected.
    """

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
            self._bkb_rule,
            self._mkb_rule,
            self._armor_rule,
            self._force_staff_rule,
            self._spirit_vessel_rule,
            self._mana_sustain_rule,
            self._dust_sentries_rule,
            self._anti_heal_rule,
            self._silver_edge_rule,
        ]

    # ------------------------------------------------------------------
    # Rule implementations
    # ------------------------------------------------------------------

    def _magic_stick_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Magic Stick vs spell-spamming lane opponents."""
        SPELL_SPAMMERS = {
            12,   # Phantom Assassin (Stifling Dagger)
            22,   # Zeus
            26,   # Lion
            40,   # Venomancer
            69,   # Bristleback (Quill Spray)
            84,   # Ogre Magi
            86,   # Rubick
            87,   # Disruptor
            97,   # Dark Seer (Ion Shell)
            110,  # Skywrath Mage
            126,  # Grimstroke
        }
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in SPELL_SPAMMERS:
                hero_name = HERO_NAMES.get(op_id, "the enemy")
                results.append(RuleResult(
                    item_id=36,
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
        MELEE_CARRIES = {
            1,    # Anti-Mage
            11,   # Sven
            12,   # Phantom Assassin
            18,   # Juggernaut
            44,   # Phantom Lancer
            47,   # Faceless Void
            49,   # Dragon Knight
            57,   # Lifestealer
            81,   # Chaos Knight
            89,   # Naga Siren
            91,   # Wraith King
            93,   # Slark
            101,  # Troll Warlord
            106,  # Ember Spirit
            114,  # Monkey King
        }
        if req.role <= 2 and req.hero_id in MELEE_CARRIES:
            return [RuleResult(
                item_id=29,
                item_name="Quelling Blade",
                reasoning=(
                    f"Essential starting item for melee carries. "
                    f"+18 bonus damage to creeps ensures last-hit efficiency in lane."
                ),
                phase="starting",
                priority="core",
            )]
        return []

    def _boots_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Recommend appropriate boots based on role."""
        if req.role <= 2:
            return [RuleResult(
                item_id=48,
                item_name="Power Treads",
                reasoning=(
                    "Power Treads provide attack speed and attribute switching "
                    "for farming efficiency and stat optimization in fights."
                ),
                phase="laning",
                priority="core",
            )]
        elif req.role == 3:
            return [RuleResult(
                item_id=50,
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
            return [RuleResult(
                item_id=180,
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
        MAGIC_HEAVY = {
            22,   # Zeus
            26,   # Lion
            27,   # Witch Doctor
            31,   # Lich
            37,   # Warlock
            43,   # Death Prophet
            52,   # Leshrac
            58,   # Enchantress
            66,   # Chen
            68,   # Lina
            75,   # Silencer
            82,   # Meepo
            84,   # Ogre Magi
            86,   # Rubick
            87,   # Disruptor
            100,  # Invoker
            103,  # Necrophos
            110,  # Skywrath Mage
        }
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in MAGIC_HEAVY:
                hero_name = HERO_NAMES.get(op_id, "the enemy")
                results.append(RuleResult(
                    item_id=116,
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
        EVASION_HEROES = {
            12,   # PA (Blur)
            47,   # Faceless Void
            53,   # Brewmaster
            101,  # Troll Warlord
            113,  # Arc Warden
            114,  # Monkey King
        }
        if req.role > 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in EVASION_HEROES:
                hero_name = HERO_NAMES.get(op_id, "the enemy")
                results.append(RuleResult(
                    item_id=225,
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
        PHYSICAL_CARRIES = {
            1,    # Anti-Mage
            11,   # Sven
            12,   # PA
            18,   # Juggernaut
            44,   # Phantom Lancer
            47,   # Faceless Void
            81,   # Chaos Knight
            89,   # Naga Siren
            91,   # Wraith King
            93,   # Slark
            101,  # Troll Warlord
            106,  # Ember Spirit
            114,  # Monkey King
        }
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in PHYSICAL_CARRIES:
                hero_name = HERO_NAMES.get(op_id, "the enemy")
                # AC for carry/offlane (roles 1-2), Shiva's for mid/offlane casters (role 3)
                if req.role <= 2:
                    results.append(RuleResult(
                        item_id=235,
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
                    results.append(RuleResult(
                        item_id=119,
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
        SLOW_HEROES = {
            15,   # Razor (Static Link)
            60,   # Night Stalker
            62,   # Bounty Hunter
            93,   # Slark (Pounce)
            69,   # Bristleback
            104,  # Underlord (Pit of Malice)
        }
        if req.role < 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in SLOW_HEROES:
                hero_name = HERO_NAMES.get(op_id, "the enemy")
                results.append(RuleResult(
                    item_id=102,
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
        HIGH_REGEN = {
            2,    # Axe
            57,   # Lifestealer (Feast)
            72,   # Alchemist
            91,   # Wraith King
            97,   # Dark Seer
            103,  # Necrophos (Death Pulse)
            120,  # Huskar
        }
        if req.role < 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in HIGH_REGEN:
                hero_name = HERO_NAMES.get(op_id, "the enemy")
                results.append(RuleResult(
                    item_id=271,
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
        MANA_HUNGRY_OFFLANERS = {
            2,    # Axe
            8,    # Sand King
            10,   # Tidehunter
            15,   # Razor
            49,   # Dragon Knight
            73,   # Timbersaw
            97,   # Dark Seer
            104,  # Underlord
        }
        if req.role != 3:
            return []
        if req.hero_id in MANA_HUNGRY_OFFLANERS:
            return [RuleResult(
                item_id=99,
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
        INVIS_HEROES = {
            32,   # Riki
            41,   # Treant Protector (Nature's Guise)
            48,   # Nyx Assassin (Vendetta)
            54,   # Mirana (Moonlight Shadow ult)
            62,   # Bounty Hunter
            67,   # Clinkz
            94,   # Weaver
        }
        if req.role < 4:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in INVIS_HEROES:
                hero_name = HERO_NAMES.get(op_id, "the enemy")
                results.extend([
                    RuleResult(
                        item_id=40,
                        item_name="Dust of Appearance",
                        reasoning=(
                            f"Against {hero_name}'s invisibility, "
                            f"Dust reveals them in a large area for 12 seconds. "
                            f"Essential for securing kills."
                        ),
                        phase="laning",
                        priority="core",
                    ),
                    RuleResult(
                        item_id=43,
                        item_name="Sentry Ward",
                        reasoning=(
                            f"Against {hero_name}'s invisibility, "
                            f"Sentry Wards provide persistent true sight "
                            f"to control vision and deny juke spots."
                        ),
                        phase="laning",
                        priority="core",
                    ),
                ])
                break
        return results

    def _anti_heal_rule(self, req: RecommendRequest) -> list[RuleResult]:
        """Shiva's Guard vs sustain/heal lineups for cores (Pos 1-3)."""
        HEAL_SUSTAIN = {
            2,    # Axe
            57,   # Lifestealer
            72,   # Alchemist
            91,   # Wraith King
            103,  # Necrophos
            120,  # Huskar
        }
        # Only for cores; Spirit Vessel covers supports (handled by spirit_vessel_rule)
        if req.role > 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in HEAL_SUSTAIN:
                hero_name = HERO_NAMES.get(op_id, "the enemy")
                results.append(RuleResult(
                    item_id=119,
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
        PASSIVE_HEROES = {
            12,   # PA (Blur / Coup de Grace)
            57,   # Lifestealer (Feast)
            69,   # Bristleback (Bristleback passive)
            72,   # Alchemist (Greevil's Greed / Chemical Rage)
            73,   # Timbersaw (Reactive Armor)
            120,  # Huskar (Berserker's Blood)
        }
        if req.role > 3:
            return []
        results: list[RuleResult] = []
        for op_id in req.lane_opponents:
            if op_id in PASSIVE_HEROES:
                hero_name = HERO_NAMES.get(op_id, "the enemy")
                results.append(RuleResult(
                    item_id=249,
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
